"""Phase 02 — Remote Sensing Preprocessing (BUILD).

Implements the *automatable* core of the four `docs/phase_02/` QGIS-4.0.2 guides:

1. Reproject every received raster to EPSG:32647 and **clip to the methodology's
   per-product buffer** (DEM = 5 km, Sentinel = licence boundary, basemap = 1 km),
   writing Cloud-Optimized GeoTIFFs (tiled + internal overviews + lossless compression).
2. Derive DEM terrain layers (multi-azimuth hillshade, slope, aspect, terrain
   ruggedness, profile/plan curvature, flow-accumulation) from the clipped DEMs.
3. Emit formula-complete method notes for the tool-bound steps we cannot run in-pipeline:
   Sentinel-2 indices/masks/composites (need bands B02-B12 via SNAP Sen2Cor — our inputs
   are received composites), ASTER HDF alteration scoring (SNAP/ILWIS), and KOMPSAT-2 RPC
   orthorectification + pan-sharpening (Global Mapper/ILWIS/GDAL).

Every output is **support evidence only — not ore proof** (guides §1/§16).
"""

from __future__ import annotations

import re
from pathlib import Path

from buduunkhad.core import crs as crs_mod
from buduunkhad.core import dem, naming, raster_writers, registers, vector_io
from buduunkhad.core.qaqc import RECORDED_ACCEPTANCE, Decision, QAQCReport, new_report
from buduunkhad.phases.base import Phase, PhaseResult, RunContext

# Support-evidence stamp required on every Phase 02 output (guides §13/§16).
SUPPORT_VALIDATION = "Support evidence only"
SUPPORT_LIMITATION = "Not ore proof; requires field/lab validation"

_RS_LOG_COLUMNS = [
    "no",
    "filename",
    "source_group",
    "native_epsg",
    "output_crs",
    "processing_action",
    "clip_buffer",
    "compression",
    "output",
    "derivative",
    "validation_status",
    "limitation",
    "decision",
    "note",
]

# Per-product input groups (raw input numbers).
_DEM_ELEV = {9, 12}  # ASTER GDEM, ALOS-PALSAR DEM -> reproject+clip+COG + terrain derivatives
_DEM_SUPPORT = {10, 16, 20}  # NumObservations (int), ALOS hillshade (uint8), ALOS slope (float)
_DEM_CATEGORICAL = {10, 16}  # nearest resampling / nearest overviews
_SENTINEL = {74, 77, 78}  # received composites/ratio stacks -> reproject+clip(licence)+COG
_BASEMAP_NOCLIP = {75}  # 2.4 m Google basemap -> reproject only
_BASEMAP_CLIP = {76}  # 0.15 m high-res basemap -> reproject + clip 1 km
_KOMPSAT_BANDS = {24, 28, 32, 36, 40}  # method-note only (RPC ortho is external)
_ASTER_HDF = {73}  # method-note only (SNAP/ILWIS band extraction)

_DEM_CLIP_M = 5000
_BASEMAP_CLIP_M = 1000

# tokens stripped from a raw filename stem when building a clean output description
_STRIP_TOKENS = re.compile(r"_(raw|received_?raw|v\d{2})$", re.IGNORECASE)


def _output_desc(filename: str, data_prefix: str) -> str:
    stem = Path(filename).stem
    if stem.startswith(data_prefix + "_"):
        stem = stem[len(data_prefix) + 1 :]
    prev = None
    while prev != stem:  # strip trailing _raw / _ReceivedRaw / _vNN, possibly stacked
        prev = stem
        stem = _STRIP_TOKENS.sub("", stem)
    return stem


class Phase02RemoteSensing(Phase):
    id = "02"
    name = "Remote Sensing Preprocessing"
    mode = "build"
    input_numbers = [*range(9, 47), *range(73, 79)]
    gate_condition = (
        "Remote-sensing rasters reprojected/clipped to EPSG:32647, written as valid COGs, "
        "labelled support evidence; QA/QC passed."
    )
    custom_subfolders = [
        "00_Input_Working_Copy",
        "01_Sentinel2_SNAP13/01_Input",
        "01_Sentinel2_SNAP13/02_QAQC",
        "01_Sentinel2_SNAP13/03_Masks",
        "01_Sentinel2_SNAP13/04_Indices",
        "01_Sentinel2_SNAP13/05_Composites",
        "01_Sentinel2_SNAP13/06_Export_EPSG32647",
        "02_ASTER_Workflow_v5/01_Input_HDF",
        "02_ASTER_Workflow_v5/02_Band_Extraction",
        "02_ASTER_Workflow_v5/03_Project_UTM47",
        "02_ASTER_Workflow_v5/04_Index_Calculation",
        "02_ASTER_Workflow_v5/05_Score_Class_Binary",
        "02_ASTER_Workflow_v5/06_QAQC",
        "03_KOMPSAT2_ILWIS368_QGIS/01_Input_Bundle",
        "03_KOMPSAT2_ILWIS368_QGIS/02_Metadata_RPC_EPH_Check",
        "03_KOMPSAT2_ILWIS368_QGIS/03_Band_Stack",
        "03_KOMPSAT2_ILWIS368_QGIS/04_Orthorectification",
        "03_KOMPSAT2_ILWIS368_QGIS/05_Pansharpen",
        "03_KOMPSAT2_ILWIS368_QGIS/06_NDVI_Lineament_Outcrop",
        "03_KOMPSAT2_ILWIS368_QGIS/07_QAQC",
        "04_ALOS_ASTERGDEM_GlobalMapper_QGIS/01_Input_DEM",
        "04_ALOS_ASTERGDEM_GlobalMapper_QGIS/02_DEM_QAQC",
        "04_ALOS_ASTERGDEM_GlobalMapper_QGIS/03_Reproject_Clip",
        "04_ALOS_ASTERGDEM_GlobalMapper_QGIS/04_Terrain_Derivatives",
        "04_ALOS_ASTERGDEM_GlobalMapper_QGIS/05_Drainage_Watershed",
        "04_ALOS_ASTERGDEM_GlobalMapper_QGIS/06_Access_Safety",
        "05_Basemap_Google_HighRes/01_Input",
        "05_Basemap_Google_HighRes/02_Reproject_Clip",
        "05_Basemap_Google_HighRes/03_QAQC",
        "06_RemoteSensing_QAQC",
        "07_Final_Export_EPSG32647",
    ]

    _rows: list[dict[str, object]]
    _outputs: list[Path]
    _derivatives: int
    _reprojected: int
    _skipped: int
    _failed: int
    _flow_skips: list[str]

    def __init__(self) -> None:
        self._rows = []
        self._outputs = []
        self._derivatives = 0
        self._reprojected = 0
        self._skipped = 0
        self._failed = 0
        self._flow_skips = []

    # ------------------------------------------------------------------ #

    def run(self, ctx: RunContext) -> PhaseResult:
        pdir = ctx.phase_dir(self.id)
        cfg = ctx.config
        result = PhaseResult(self.id, status="dry-run" if ctx.dry_run else "ok")
        rs_log = (
            pdir / "06_RemoteSensing_QAQC" / f"{cfg.register_prefix}_RemoteSensing_QAQC_Log.xlsx"
        )

        if ctx.dry_run:
            registers.write_table_xlsx(
                [], _RS_LOG_COLUMNS, rs_log, sheet_title="RemoteSensing QAQC"
            )
            self._write_method_notes(ctx, pdir)
            result.add_output(rs_log)
            result.log("dry-run: per-sensor RS folders + method notes + empty QA/QC log")
            return result

        epsg = cfg.target_epsg
        dem_aoi = self._load_buffer_aoi(ctx, _DEM_CLIP_M)
        licence_aoi = self._load_boundary_aoi(ctx)
        basemap_aoi = self._load_buffer_aoi(ctx, _BASEMAP_CLIP_M)

        dem_reproj_dir = pdir / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS" / "03_Reproject_Clip"
        deriv_dir = pdir / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS" / "04_Terrain_Derivatives"
        sentinel_dir = pdir / "01_Sentinel2_SNAP13" / "06_Export_EPSG32647"
        basemap_dir = pdir / "05_Basemap_Google_HighRes" / "02_Reproject_Clip"

        for rec in sorted(ctx.records_by_numbers(self.input_numbers), key=lambda r: r.no):
            if rec.no in _ASTER_HDF:
                self._rows.append(self._note_row(rec, "ASTER HDF → SNAP/ILWIS method note"))
                continue
            if rec.no in _KOMPSAT_BANDS:
                self._rows.append(self._note_row(rec, "KOMPSAT band → RPC ortho method note"))
                continue
            if rec.file_type != "raster":
                continue  # sidecars / browse / thumbnail / pdf

            if rec.no in _DEM_ELEV:
                self._rows.append(
                    self._do_dem_elev(ctx, rec, dem_aoi, dem_reproj_dir, deriv_dir, epsg)
                )
            elif rec.no in _DEM_SUPPORT:
                self._rows.append(
                    self._do_passthrough(
                        ctx,
                        rec,
                        aoi=dem_aoi,
                        dest_dir=deriv_dir,
                        epsg=epsg,
                        clip_label=f"{_DEM_CLIP_M // 1000}km",
                        compress="DEFLATE",
                        categorical=rec.no in _DEM_CATEGORICAL,
                    )
                )
            elif rec.no in _SENTINEL:
                self._rows.append(
                    self._do_passthrough(
                        ctx,
                        rec,
                        aoi=licence_aoi,
                        dest_dir=sentinel_dir,
                        epsg=epsg,
                        clip_label="Licence",
                        compress="DEFLATE",
                        categorical=False,
                    )
                )
            elif rec.no in _BASEMAP_NOCLIP:
                self._rows.append(
                    self._do_passthrough(
                        ctx,
                        rec,
                        aoi=None,
                        dest_dir=basemap_dir,
                        epsg=epsg,
                        clip_label="Full",
                        compress="ZSTD",
                        categorical=False,
                        require_aoi=False,
                    )
                )
            elif rec.no in _BASEMAP_CLIP:
                self._rows.append(
                    self._do_passthrough(
                        ctx,
                        rec,
                        aoi=basemap_aoi,
                        dest_dir=basemap_dir,
                        epsg=epsg,
                        clip_label=f"{_BASEMAP_CLIP_M // 1000}km",
                        compress="ZSTD",
                        categorical=False,
                    )
                )

        registers.write_table_xlsx(
            self._rows, _RS_LOG_COLUMNS, rs_log, sheet_title="RemoteSensing QAQC"
        )
        self._write_method_notes(ctx, pdir)
        result.add_output(rs_log)
        for p in self._outputs:
            result.add_output(p)
        result.log(
            f"reprojected/clipped {self._reprojected} raster(s) → COG; "
            f"{self._derivatives} terrain derivative(s); {self._skipped} skipped (no overlap); "
            f"{self._failed} failed"
        )
        return result

    # ------------------------------------------------------------------ #
    # AOI loading (from Phase 01 outputs)
    # ------------------------------------------------------------------ #

    def _phase01_gpkg_dir(self, ctx: RunContext) -> Path:
        return ctx.phase_dir("01") / "05_KMZ_KML_to_GPKG"

    def _load_buffer_aoi(self, ctx: RunContext, distance_m: int):  # type: ignore[no-untyped-def]
        cfg = ctx.config
        name = naming.data_name(
            cfg.data_prefix,
            "Project",
            crs_or_param=f"{naming.buffer_param(cfg.boundary.buffers_m)}_"
            f"{naming.epsg_tag(cfg.target_epsg)}",
            version=None,
            ext="gpkg",
        )
        path = self._phase01_gpkg_dir(ctx) / name
        if not path.exists():
            return None
        gdf = vector_io.read_layer(path, "project_buffers")
        sub = gdf[gdf["distance_m"] == distance_m]
        return sub if len(sub) else None

    def _load_boundary_aoi(self, ctx: RunContext):  # type: ignore[no-untyped-def]
        cfg = ctx.config
        name = naming.data_name(
            cfg.data_prefix,
            f"{cfg.project.license_code}_LicenseBoundary",
            crs_or_param=naming.epsg_tag(cfg.target_epsg),
            version=1,
            ext="gpkg",
        )
        path = self._phase01_gpkg_dir(ctx) / name
        if not path.exists():
            return None
        return vector_io.read_layer(path, "license_boundary")

    # ------------------------------------------------------------------ #
    # per-raster processing
    # ------------------------------------------------------------------ #

    def _do_passthrough(
        self,
        ctx: RunContext,
        rec,  # type: ignore[no-untyped-def]
        *,
        aoi,  # type: ignore[no-untyped-def]
        dest_dir: Path,
        epsg: int,
        clip_label: str,
        compress: str,
        categorical: bool,
        require_aoi: bool = True,
    ) -> dict[str, object]:
        cfg = ctx.config
        action = "reproject+clip+COG" if require_aoi else "reproject+COG"
        row = self._base_row(rec, action=action, clip_label=clip_label, compress=compress)
        wc = ctx.phase_dir("00") / rec.evidence_group / rec.filename
        if not wc.exists():
            self._failed += 1
            row.update(decision="Fail", note="working copy missing (run Phase 00 first)")
            return row
        if aoi is None and require_aoi:
            self._failed += 1
            row.update(decision="Fail", note="Phase 01 clip AOI not found (run Phase 01 first)")
            return row

        audit = crs_mod.audit_raster(wc, target_epsg=epsg)
        row["native_epsg"] = audit.epsg if audit.epsg is not None else ""
        predictor = raster_writers.predictor_for(audit.dtype) if audit.readable else None
        token = f"Clip{clip_label}" if require_aoi else "Reprojected"
        desc = f"{_output_desc(rec.filename, cfg.data_prefix)}_{token}"
        out_name = naming.data_name(
            cfg.data_prefix, desc, crs_or_param=naming.epsg_tag(epsg), version=1, ext="tif"
        )
        out_path = dest_dir / out_name
        try:
            result_path, clip_applied = crs_mod.reproject_clip_cog(
                wc,
                out_path,
                aoi,
                dst_epsg=epsg,
                cog_compress=compress,
                cog_predictor=predictor,
                cog_overview_resampling="NEAREST" if categorical else "AVERAGE",
                resampling="nearest" if categorical else "bilinear",
            )
        except Exception as exc:  # noqa: BLE001 - record and continue the batch
            self._failed += 1
            row.update(decision="Fail", note=f"{type(exc).__name__}: {exc}")
            return row

        if result_path is None:
            self._skipped += 1
            row.update(decision="Skip", note=f"no overlap with {clip_label} AOI")
            return row
        self._reprojected += 1
        self._outputs.append(result_path)
        row.update(output=result_path.name, clip_buffer=clip_label if clip_applied else "(none)")
        row.update(decision="Pass", note="")
        return row

    def _do_dem_elev(
        self, ctx: RunContext, rec, aoi, reproj_dir: Path, deriv_dir: Path, epsg: int
    ) -> dict[str, object]:  # type: ignore[no-untyped-def]
        row = self._do_passthrough(
            ctx,
            rec,
            aoi=aoi,
            dest_dir=reproj_dir,
            epsg=epsg,
            clip_label=f"{_DEM_CLIP_M // 1000}km",
            compress="DEFLATE",
            categorical=False,
        )
        if row.get("decision") != "Pass":
            return row
        cfg = ctx.config
        dem_path = reproj_dir / str(row["output"])
        dem_desc = _output_desc(rec.filename, cfg.data_prefix)

        def name(suffix: str) -> Path:
            return deriv_dir / naming.data_name(
                cfg.data_prefix,
                f"{dem_desc}_{suffix}",
                crs_or_param=naming.epsg_tag(epsg),
                version=1,
                ext="tif",
            )

        outputs = {
            "hillshade": name("Hillshade_Az315"),
            "hillshade_az045": name("Hillshade_Az045"),
            "hillshade_az090": name("Hillshade_Az090"),
            "hillshade_az135": name("Hillshade_Az135"),
            "slope": name("SlopeDeg"),
            "aspect": name("Aspect"),
            "tri": name("TerrainRuggedness"),
            "profile_curvature": name("ProfileCurvature"),
            "plan_curvature": name("PlanCurvature"),
            "flow": name("FlowAccumulation"),
        }
        written, skipped = dem.derive_terrain(dem_path, outputs)
        self._derivatives += len(written)
        self._outputs.extend(written)
        self._flow_skips.extend(skipped)
        note = f"{len(written)} terrain layer(s)" + (f"; {'; '.join(skipped)}" if skipped else "")
        row["derivative"] = note
        return row

    def _base_row(self, rec, *, action: str, clip_label: str, compress: str) -> dict[str, object]:  # type: ignore[no-untyped-def]
        return {
            "no": rec.no,
            "filename": rec.filename,
            "source_group": rec.evidence_group,
            "native_epsg": "",
            "output_crs": f"EPSG:{32647}",
            "processing_action": action,
            "clip_buffer": clip_label,
            "compression": compress,
            "output": "",
            "derivative": "",
            "validation_status": SUPPORT_VALIDATION,
            "limitation": SUPPORT_LIMITATION,
            "decision": "Pending",
            "note": "",
        }

    def _note_row(self, rec, action: str) -> dict[str, object]:  # type: ignore[no-untyped-def]
        row = self._base_row(rec, action=action, clip_label="(external)", compress="(n/a)")
        row.update(output_crs="EPSG:32647 (target)", decision="Method-note")
        row["note"] = "External tool step — see method note in the sensor subfolder."
        return row

    # ------------------------------------------------------------------ #
    # method notes (formula-complete, for the external operator)
    # ------------------------------------------------------------------ #

    def _write_method_notes(self, ctx: RunContext, pdir: Path) -> None:
        prefix = f"{ctx.config.project.project_code}_{ctx.config.project.name}"
        notes = {
            pdir
            / "01_Sentinel2_SNAP13"
            / "04_Indices"
            / f"{prefix}_Sentinel2_Method_Note.md": _SENTINEL_NOTE,
            pdir
            / "02_ASTER_Workflow_v5"
            / "04_Index_Calculation"
            / f"{prefix}_ASTER_Method_Note.md": _ASTER_NOTE,
            pdir
            / "03_KOMPSAT2_ILWIS368_QGIS"
            / "04_Orthorectification"
            / f"{prefix}_KOMPSAT2_Method_Note.md": _KOMPSAT_NOTE,
            pdir
            / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS"
            / "05_Drainage_Watershed"
            / f"{prefix}_Drainage_Watershed_Contour_Method_Note.md": _HYDRO_NOTE,
            pdir
            / "05_Basemap_Google_HighRes"
            / "03_QAQC"
            / f"{prefix}_Basemap_Interpretation_Method_Note.md": _BASEMAP_NOTE,
        }
        for path, text in notes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    # ------------------------------------------------------------------ #

    def qaqc(self, ctx: RunContext) -> QAQCReport:
        report = new_report(self.id, self.name)
        if ctx.dry_run:
            report.add(
                "Remote-sensing scaffolding created",
                "Per-sensor folders, method notes and empty QA/QC log present (dry-run).",
                decision=Decision.PASS,
                note="Dry-run: no raster data processed.",
            )
            return report

        any_fail = any(r.get("decision") == "Fail" for r in self._rows)
        report.add(
            "Rasters reprojected/clipped to EPSG:32647 (per-product buffer)",
            RECORDED_ACCEPTANCE,
            decision=Decision.FAIL if any_fail else Decision.PASS,
            note=f"{self._reprojected} reprojected/clipped; {self._skipped} skipped (no overlap); "
            f"{self._failed} failed.",
        )
        cogs_ok = all(raster_writers.is_cog(p) for p in self._outputs)
        report.add(
            "Outputs are valid COGs (tiled + overviews where larger than blocksize)",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if cogs_ok else Decision.FAIL,
            note=f"{len(self._outputs)} COG(s) verified."
            if cogs_ok
            else "Non-COG output detected.",
        )
        report.add(
            "Native CRS + compression recorded per output",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS,
            note="native_epsg, output_crs and compression captured per row in the QA/QC log.",
        )
        report.add(
            "DEM terrain derivatives generated",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._derivatives else Decision.PENDING,
            note=f"{self._derivatives} derivative(s) "
            "(multi-azimuth hillshade/slope/aspect/TRI/curvature/flow)."
            + (f" Flow notes: {'; '.join(self._flow_skips)}." if self._flow_skips else ""),
        )
        report.add(
            "Remote-sensing outputs labelled SUPPORT evidence only (not ore proof)",
            "Every output row + method note carries validation_status/limitation (invariant #8).",
            decision=Decision.PASS,
            note=f"Stamped on all {len(self._rows)} log rows and the method notes.",
        )
        report.add(
            "Sentinel indices / ASTER alteration / KOMPSAT ortho (external SNAP/ILWIS)",
            RECORDED_ACCEPTANCE,
            decision=Decision.PENDING,
            note="Orchestrated steps — formula-complete method notes emitted in 01_/02_/03_ subfolders.",
        )
        return report


# --------------------------------------------------------------------------- #
# method-note bodies
# --------------------------------------------------------------------------- #

_SUPPORT_FOOTER = (
    "\n\n> **validation_status:** Support evidence only.  \n"
    "> **limitation:** Not ore proof; requires field/lab validation.\n"
)

_SENTINEL_NOTE = (
    "# Phase 02 — Sentinel-2 indices/masks/composites (orchestrated)\n\n"
    "Our raw Sentinel inputs (#74/#77/#78) are *received composites / ratio stacks*, not the\n"
    "individual bands B02–B12, so the pipeline only **reprojects them to EPSG:32647 and clips to\n"
    "the licence boundary** (see 06_Export_EPSG32647). The products below need the band stack\n"
    "(SNAP 13.0.0 Sen2Cor L1C→L2A, then resample B11/B12 to 10 m). Place results here / in\n"
    "03_Masks / 05_Composites and log them.\n\n"
    "Formulas (EPSG:32647, 10 m, bilinear):\n"
    "- NDVI = (B08 − B04) / (B08 + B04); vegetation mask NDVI > 0.3\n"
    "- NDWI = (B03 − B08) / (B03 + B08); water mask NDWI > 0.2\n"
    "- shadow/dark mask: B04 < 0.05 (reflectance) or < 500 (DN scale)\n"
    "- usable-pixel mask = (VegetationMask==0) AND (WaterShadowMask==0)\n"
    "- Natural RGB = B04/B03/B02; Geology RGB = B12/B08/B03; FalseColor = B08/B04/B03\n"
    "- lithology index stack = ratios B11/B12, B08/B11, B04/B03\n" + _SUPPORT_FOOTER
)

_ASTER_NOTE = (
    "# Phase 02 — ASTER HDF alteration workflow v5 (orchestrated)\n\n"
    "ASTER L1B #73 is `.hdf`; band extraction + UTM47 projection + index scoring run in\n"
    "SNAP/ILWIS 3.6.8 / ASTER workflow v5 (do **not** use a haze/edge filter in ratio\n"
    "calculations). Extract b1..b9 → project to EPSG:32647 → compute the 15 Float32 score\n"
    "rasters, then the weighted porphyry-alteration score:\n\n"
    "score_porphyry_alteration =\n"
    "  0.12282·sericite + 0.08776·aloh + 0.07022·clay + 0.05265·argilic + 0.05765·quartz\n"
    "  + 0.08020·silicification + 0.06013·silica + 0.08270·iron_oxide + 0.06766·ferric\n"
    "  + 0.06013·chlorite + 0.04511·mgoh + 0.03008·carbonate + 0.01503·carbonate_swir\n"
    "  + 0.03760·structure_v1 + 0.10527·lithology\n\n"
    "Outputs (05_Score_Class_Binary): raw Float32 score; 3-class map (percentiles 0–60 / 60–85\n"
    "/ 85–100 → 1/2/3); binary mask (class==3 → 1 else 0). Keep score/class/binary separate.\n"
    + _SUPPORT_FOOTER
)

_KOMPSAT_NOTE = (
    "# Phase 02 — KOMPSAT-2 orthorectification & pan-sharpening (orchestrated)\n\n"
    "KOMPSAT-2 needs RPC orthorectification **first** (PAN/MS .tif + .rpc + .eph + DEM) in\n"
    "Global Mapper / ILWIS 3.6.8 / GDAL — a plain reproject of the un-orthorectified 1G\n"
    "imagery is geometrically invalid, so the pipeline does **not** produce one. Band identity:\n"
    "PN=PAN, M1=Green, M2=Blue, M3=NIR, M4=Red. Steps: ortho each band → EPSG:32647; MS band\n"
    "stack (B1=Blue,B2=Green,B3=Red,B4=NIR); true-colour (R/G/B = Red/Green/Blue); false-colour\n"
    "(NIR/Red/Green); NDVI = (NIR − Red)/(NIR + Red); pan-sharpen (Brovey / Gram-Schmidt / IHS)\n"
    "→ orthobasemap; digitise lineament/outcrop/access/disturbance. Keep .rpc/.eph/.txt with\n"
    "their parent.\n" + _SUPPORT_FOOTER
)

_HYDRO_NOTE = (
    "# Phase 02 — Contour / drainage network / watershed (orchestrated)\n\n"
    "The pipeline produces the raster terrain derivatives (multi-azimuth hillshade, slope,\n"
    "aspect, TRI, profile/plan curvature, flow-accumulation) in 04_Terrain_Derivatives. The\n"
    "**vector** products below use SAGA/GRASS hydrology + gdal_contour in QGIS 4.0.2 (not\n"
    "available in the pipeline runtime):\n\n"
    "- Contour (gpkg): interval 10 m (5 m low relief / 20–25 m high), attribute `elev`.\n"
    "- Drainage network (gpkg): Fill sinks → Flow direction → Flow accumulation → Channel\n"
    "  network (threshold ~1000 cells for 12.5 m DEM; 100–1000 for 30 m).\n"
    "- Watershed / catchments (gpkg) + pour points at drainage outlets.\n"
    "Used in Phase 8 stream-sediment / heavy-mineral follow-up.\n" + _SUPPORT_FOOTER
)

_BASEMAP_NOTE = (
    "# Phase 02 — Google / high-resolution basemap interpretation (orchestrated)\n\n"
    "The pipeline reprojects #75 (2.4 m, WGS84→EPSG:32647) and reprojects+clips #76 (0.15 m,\n"
    "EPSG:3857→EPSG:32647, licence + 1 km) as COGs in 02_Reproject_Clip. Manual digitising on\n"
    "the high-res basemap produces (EPSG:32647 gpkg): field-access tracks, outcrop-visibility\n"
    "zones, old-workings/disturbance, road/track mapping — for field access & route planning.\n"
    + _SUPPORT_FOOTER
)


PHASE = Phase02RemoteSensing
