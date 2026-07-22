"""Phase 02 — Remote Sensing Preprocessing (BUILD).

Implements the adopted automatable Phase 02 core recorded in
``config/methodology/phase02.yaml`` and the approved external methodology:

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

from buduunkhad.core import (
    aster,
    dem,
    hydrology,
    lineaments,
    naming,
    raster_writers,
    registers,
    vector_io,
)
from buduunkhad.core import crs as crs_mod
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

_TERRAIN_INDEX_COLUMNS = [
    "dem_source_no",
    "dem_source_file",
    "derivative",
    "output_filename",
    "output_crs",
    "validation_status",
    "limitation",
]

# Per-product input groups (raw input numbers).
_DEM_ELEV = {9, 12}  # ASTER GDEM, ALOS-PALSAR DEM -> reproject+clip+COG + terrain derivatives
_DEM_SUPPORT = {10, 16, 20}  # NumObservations (int), ALOS hillshade (float), ALOS slope (float)
_DEM_CATEGORICAL = {10}  # only #10 (NumObservations) is a true count raster; #16 is continuous
_SENTINEL = {74, 77, 78}  # received composites/ratio stacks -> reproject+clip(licence)+COG
_BASEMAP_NOCLIP = {75}  # 2.4 m Google basemap -> reproject only
_BASEMAP_CLIP = {76}  # 0.15 m high-res basemap -> reproject + clip 1 km
_KOMPSAT_BANDS = {24, 28, 32, 36, 40}  # method-note only (RPC ortho is external)
_ASTER_HDF = {73}  # frozen support chain when HDF4-capable gdalwarp exists, else method note

_DEM_CLIP_M = 5000
_BASEMAP_CLIP_M = 1000

# NumObservations (#10) is a uint8 count where 0 is a valid reading, so the clip must not leave
# out-of-AOI margins as 0 (that conflates with genuine zero-observation cells). Flag the margin
# with 255 (uint8 max, above the observed count range) so it is recorded as nodata instead.
_SUPPORT_NODATA_FALLBACK: dict[int, float] = {10: 255.0}

# A few received Sentinel "composites" bundle extra raw-reflectance bands alongside the named
# product. #78 (LithologyIndex) ships 8 bands, but the deliverable is the 3 named ratios
# (B11/B12, B08/B11, B04/B03) = bands 1-3; keep those, drop the rest. (Confirmed in the register
# reconciliation: bands 4-8 are raw reflectance DN, not part of the lithology index.)
_SENTINEL_BAND_SUBSET: dict[int, tuple[int, ...]] = {78: (1, 2, 3)}

# The Sentinel composites (#74, #77) are float32 with NO source nodata, so clipping to the
# (non-rectangular) licence boundary fills ~36% out-of-licence margin with 0.0 that then reads as
# valid reflectance. Flag the margin with -9999.0 (far outside any reflectance/index/RGB range) so
# it is recorded as nodata — same fix class as #10 above. #78 already carries its own source nodata
# and is left untouched (no entry here -> .get() returns None -> source nodata preserved).
_SENTINEL_NODATA_FALLBACK: dict[int, float] = {74: -9999.0, 77: -9999.0}

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
    _terrain_rows: list[dict[str, object]]
    _derivatives: int
    _reprojected: int
    _skipped: int
    _failed: int
    _flow_skips: list[str]
    _aster_processed: bool
    _aster_targets: int
    _aster_extras: list[Path]  # non-COG ASTER outputs (polygons gpkg, threshold register)
    _hydrology_note: str  # "" until attempted; then a produced/skipped summary
    _lineaments_note: str
    _vector_outputs: list[Path]  # hydrology/lineament GPKGs (not COGs)

    def __init__(self) -> None:
        self._rows = []
        self._outputs = []
        self._terrain_rows = []
        self._derivatives = 0
        self._reprojected = 0
        self._skipped = 0
        self._failed = 0
        self._flow_skips = []
        self._aster_processed = False
        self._aster_targets = 0
        self._aster_extras = []
        self._hydrology_note = ""
        self._lineaments_note = ""
        self._vector_outputs = []

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
            self._write_handover(ctx, pdir, [], result)
            result.add_output(rs_log)
            result.log("dry-run: per-sensor RS folders + method notes + empty QA/QC log + report")
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
                self._rows.append(self._do_aster(ctx, rec, pdir, dem_aoi))
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
                        nodata_fallback=_SUPPORT_NODATA_FALLBACK.get(rec.no),
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
                        band_subset=_SENTINEL_BAND_SUBSET.get(rec.no),
                        nodata_fallback=_SENTINEL_NODATA_FALLBACK.get(rec.no),
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

        # Post-loop vector products derived from the clipped DEM + its hillshades: the
        # contour/drainage/watershed package (guide §04.5, previously method-note-only) and the
        # first-pass lineament draft. Both degrade to a note when their optional dep is absent.
        self._do_hydrology(ctx, dem_reproj_dir, pdir)
        self._do_lineaments(ctx, deriv_dir)

        registers.write_table_xlsx(
            self._rows, _RS_LOG_COLUMNS, rs_log, sheet_title="RemoteSensing QAQC"
        )
        self._write_method_notes(ctx, pdir)
        self._write_handover(ctx, pdir, self._terrain_rows, result)
        result.add_output(rs_log)
        for p in self._outputs:
            result.add_output(p)
        for p in self._aster_extras:
            result.add_output(p)
        for p in self._vector_outputs:
            result.add_output(p)
        result.log(
            f"reprojected/clipped {self._reprojected} raster(s) → COG; "
            f"{self._derivatives} terrain derivative(s); {self._skipped} skipped (no overlap); "
            f"{self._failed} failed"
            + (
                f"; ASTER frozen support chain: {self._aster_targets} target polygon(s)"
                if self._aster_processed
                else "; ASTER: method-note fallback"
            )
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
        nodata_fallback: float | None = None,
        band_subset: tuple[int, ...] | None = None,
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
                nodata_fallback=nodata_fallback,
            )
        except Exception as exc:  # noqa: BLE001 - record and continue the batch
            self._failed += 1
            row.update(decision="Fail", note=f"{type(exc).__name__}: {exc}")
            return row

        if result_path is None:
            self._skipped += 1
            row.update(decision="Skip", note=f"no overlap with {clip_label} AOI")
            return row
        note = ""
        if band_subset is not None and audit.band_count and audit.band_count > len(band_subset):
            raster_writers.subset_cog_bands(result_path, list(band_subset))
            note = (
                f"kept bands {list(band_subset)}; dropped "
                f"{audit.band_count - len(band_subset)} extra received band(s)"
            )
        self._reprojected += 1
        self._outputs.append(result_path)
        row.update(output=result_path.name, clip_buffer=clip_label if clip_applied else "(none)")
        row.update(decision="Pass", note=note)
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
            nodata_fallback=-9999.0,
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
        written_set = set(written)
        for key, path in outputs.items():
            if path in written_set:
                self._terrain_rows.append(
                    {
                        "dem_source_no": rec.no,
                        "dem_source_file": rec.filename,
                        "derivative": key,
                        "output_filename": path.name,
                        "output_crs": f"EPSG:{epsg}",
                        "validation_status": SUPPORT_VALIDATION,
                        "limitation": SUPPORT_LIMITATION,
                    }
                )
        note = f"{len(written)} terrain layer(s)" + (f"; {'; '.join(skipped)}" if skipped else "")
        row["derivative"] = note
        return row

    def _write_handover(
        self,
        ctx: RunContext,
        pdir: Path,
        terrain_rows: list[dict[str, object]],
        result: PhaseResult,
    ) -> None:
        """Emit the master-doc-named Phase 02 outputs: the Terrain Derivatives index and the
        RemoteSensing QA/QC report (.docx), alongside the per-raster QA/QC log."""
        cfg = ctx.config
        index_path = (
            pdir
            / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS"
            / "04_Terrain_Derivatives"
            / naming.data_name(cfg.data_prefix, "Terrain_Derivatives_Index", version=1, ext="xlsx")
        )
        registers.write_table_xlsx(
            terrain_rows, _TERRAIN_INDEX_COLUMNS, index_path, sheet_title="Terrain Derivatives"
        )
        report_path = (
            pdir
            / "06_RemoteSensing_QAQC"
            / naming.register_name(
                cfg.register_prefix, "RemoteSensing_QAQC_Report", ext="docx", version=1
            )
        )
        self.qaqc(ctx).write_docx(report_path)
        result.add_output(index_path)
        result.add_output(report_path)

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

    # ------------------------------------------------------------------ #
    # ASTER frozen support chain (#73): extract → project → indices → score → targets
    # ------------------------------------------------------------------ #

    def _do_aster(self, ctx: RunContext, rec, pdir: Path, stats_aoi) -> dict[str, object]:  # type: ignore[no-untyped-def]
        """Run the frozen ASTER support chain, degrading to the method note on any obstacle.

        ``stats_aoi`` (the 5 km buffer GeoDataFrame, or None) is the frozen METH-DISC-021
        anomaly-statistics basis: thresholds from AOI pixels, applied full-scene. Degradation
        (missing working copy, no HDF4-capable gdalwarp, extraction/processing failure) is
        recorded as a Method-note row rather than a batch failure; ASTER remains an explicit
        provisional data gap under METH-READY-003.
        """
        row = self._base_row(
            rec,
            action="HDF4 extract → EPSG:32647 → frozen alteration support score",
            clip_label="Full scene",
            compress="DEFLATE",
        )
        wc = ctx.phase_dir("00") / rec.evidence_group / rec.filename
        if not wc.exists():
            row.update(
                output_crs="EPSG:32647 (target)",
                decision="Method-note",
                note="working copy missing (run Phase 00 first) — method-note fallback.",
            )
            return row
        gdalwarp = aster.find_hdf4_gdalwarp()
        if gdalwarp is None:
            row.update(
                output_crs="EPSG:32647 (target)",
                decision="Method-note",
                note="No HDF4-capable GDAL found (install QGIS or set BUDUUNKHAD_GDAL_BIN) — "
                "method-note fallback.",
            )
            return row
        try:
            res = self._run_aster_chain(ctx, wc, pdir / "02_ASTER_Workflow_v5", gdalwarp, stats_aoi)
        except Exception as exc:  # noqa: BLE001 - degrade to the note, keep the batch going
            ctx.logger.warning("ASTER chain failed; method-note fallback: %s", exc)
            row.update(
                output_crs="EPSG:32647 (target)",
                decision="Method-note",
                note=f"ASTER processing failed ({type(exc).__name__}: {str(exc)[:160]}) — "
                "method-note fallback.",
            )
            return row
        self._aster_processed = True
        self._aster_targets = res.n_targets
        score_file = res.score_files[-1] if res.score_files else None
        row.update(
            native_epsg="(swath GCPs)",
            output_crs=f"EPSG:{ctx.config.target_epsg}",
            output=str(score_file) if score_file else "",
            derivative=f"{len(res.index_files)} indices + {len(res.score_files) - 1} binaries "
            f"+ score + {res.n_targets} target polygon(s)",
            decision="Pass",
            note="Frozen support chain: 11 bands → 7 indices → mean+1.5σ binaries → weighted score "
            "(2·clay+ferric+chlorite+silica) → targets ≥3.",
        )
        return row

    def _run_aster_chain(
        self,
        ctx: RunContext,
        hdf_wc: Path,
        aster_dir: Path,
        gdalwarp: Path,
        stats_aoi,  # type: ignore[no-untyped-def]
    ) -> aster.AsterResult:
        cfg = ctx.config
        epsg = cfg.target_epsg
        params = aster.AsterParams(epsg=epsg)

        def out_name(desc: str, ext: str = "tif") -> str:
            return naming.data_name(
                cfg.data_prefix, desc, crs_or_param=naming.epsg_tag(epsg), version=1, ext=ext
            )

        bands = aster.extract_bands(hdf_wc, aster_dir / "03_Project_UTM47", gdalwarp, epsg=epsg)
        arrays, profile = aster.read_aligned(bands)
        indices = aster.compute_indices(arrays)
        res = aster.AsterResult(band_files=list(bands.values()))

        idx_dir = aster_dir / "04_Index_Calculation"
        for name, arr in indices.items():
            out = idx_dir / out_name(f"ASTER_{name}")
            aster.write_index_raster(arr, profile, out)
            res.index_files.append(out)

        # Threshold statistics basis: the licence-area subset (5 km buffer) per the geologist's
        # 2026-07-07 decision (02-3) — matching how the reference outputs were thresholded on
        # licence-clipped rasters. Thresholds apply full-scene (district context preserved).
        if stats_aoi is not None:
            stats_mask = aster.aoi_mask(stats_aoi, profile)
            stats_basis = "5 km buffer AOI (licence-area subset)"
        else:
            stats_mask = None
            stats_basis = "full scene (no Phase-01 buffer AOI found)"
        binaries, score, stats = aster.score_targets(
            indices, params=params, stats_mask=stats_mask, stats_basis=stats_basis
        )
        res.stats_rows = stats
        score_dir = aster_dir / "05_Score_Class_Binary"
        for short, binary in binaries.items():
            out = score_dir / out_name(f"ASTER_{short.capitalize()}_Anomaly_Binary")
            aster.write_index_raster(binary, profile, out)
            res.score_files.append(out)
        score_out = score_dir / out_name("ASTER_Porphyry_Target_Score")
        aster.write_index_raster(score, profile, score_out)
        res.score_files.append(score_out)  # kept last: _do_aster reports it as THE output

        gdf = aster.polygonize_targets(score, profile, params=params)
        res.n_targets = len(gdf)
        if len(gdf):
            poly_out = score_dir / out_name("ASTER_Porphyry_Target_Polygons", ext="gpkg")
            vector_io.write_layer(gdf, poly_out, layer="aster_porphyry_targets")
            res.polygon_file = poly_out
            self._aster_extras.append(poly_out)

        reg = aster_dir / "06_QAQC" / f"{cfg.register_prefix}_ASTER_Anomaly_Threshold_Register.xlsx"
        registers.write_table_xlsx(
            stats,
            [
                "component",
                "index",
                "weight",
                "threshold_basis",
                "mean",
                "std",
                "threshold",
                "anomaly_pixels",
                "valid_pixels",
            ],
            reg,
            sheet_title="ASTER thresholds",
        )
        self._aster_extras.append(reg)
        self._outputs.extend(res.index_files + res.score_files)  # COGs (is_cog-checked in qaqc)
        return res

    # ------------------------------------------------------------------ #
    # DEM vector products: hydrology package + lineament first pass
    # ------------------------------------------------------------------ #

    def _primary_clipped_dem(self, dem_reproj_dir: Path) -> Path | None:
        """The clipped ALOS-PALSAR 12.5 m DEM COG (the primary DEM for vector products)."""
        hits = sorted(dem_reproj_dir.glob("*ALOS-PALSAR_DEM*Clip*_v01.tif"))
        return hits[0] if hits else None

    def _do_hydrology(self, ctx: RunContext, dem_reproj_dir: Path, pdir: Path) -> None:
        """Contours + drainage network + watersheds from the clipped DEM (WhiteboxTools).

        Degrades to a note (method note stays authoritative) when whitebox is unavailable
        or fails — the vector package is a Doc A expected output but support evidence only.
        """
        import tempfile

        cfg = ctx.config
        dem_cog = self._primary_clipped_dem(dem_reproj_dir)
        if dem_cog is None:
            self._hydrology_note = "skipped: clipped ALOS DEM not found"
            return
        wbt = hydrology.find_whitebox()
        if wbt is None:
            self._hydrology_note = "skipped: whitebox not installed (pip install whitebox)"
            return
        out_dir = pdir / "04_ALOS_ASTERGDEM_GlobalMapper_QGIS" / "05_Drainage_Watershed"
        params = hydrology.HydrologyParams()
        try:
            with tempfile.TemporaryDirectory(prefix="wbt_") as tmp:
                contours, streams, basins = hydrology.build_hydrology(
                    dem_cog, Path(tmp), wbt=wbt, params=params
                )
        except Exception as exc:  # noqa: BLE001 - degrade to the note
            ctx.logger.warning("hydrology chain failed: %s", exc)
            self._hydrology_note = f"failed: {type(exc).__name__}: {str(exc)[:120]}"
            return
        epsg = cfg.target_epsg
        named = [
            (contours, f"DEM_Contours_{int(params.contour_interval_m)}m", "contours"),
            (streams, "DEM_Drainage_Network", "drainage_network"),
            (basins, "DEM_Watersheds", "watersheds"),
        ]
        for gdf, desc, layer in named:
            if not len(gdf):
                continue
            gdf["validation_status"] = SUPPORT_VALIDATION
            gdf["limitation"] = SUPPORT_LIMITATION
            out = out_dir / naming.data_name(
                cfg.data_prefix, desc, crs_or_param=naming.epsg_tag(epsg), version=1, ext="gpkg"
            )
            vector_io.write_layer(gdf.to_crs(epsg=epsg), out, layer=layer)
            self._vector_outputs.append(out)
        self._hydrology_note = (
            f"{len(contours)} contour line(s) @ {int(params.contour_interval_m)} m, "
            f"{len(streams)} stream segment(s) (threshold "
            f"{params.stream_threshold_cells} cells), {len(basins)} watershed(s)"
        )

    def _do_lineaments(self, ctx: RunContext, deriv_dir: Path) -> None:
        """First-pass lineament draft from the ALOS multi-azimuth hillshades (Canny+Hough).

        The output is a MACHINE DRAFT of an interpretive product — stamped for geologist
        review, never fed to scoring unreviewed. Degrades to a note without scikit-image.
        """
        cfg = ctx.config
        shades = sorted(deriv_dir.glob("*ALOS-PALSAR_DEM*Hillshade_Az*_v01.tif"))
        if len(shades) < 2:
            self._lineaments_note = "skipped: <2 ALOS azimuth hillshades found"
            return
        try:
            gdf = lineaments.extract_lineaments(shades)
        except lineaments.LineamentError as exc:
            self._lineaments_note = f"skipped: {exc}"
            return
        except Exception as exc:  # noqa: BLE001 - degrade to the note
            ctx.logger.warning("lineament extraction failed: %s", exc)
            self._lineaments_note = f"failed: {type(exc).__name__}: {str(exc)[:120]}"
            return
        if not len(gdf):
            self._lineaments_note = "0 segments above the length threshold"
            return
        out = deriv_dir / naming.data_name(
            cfg.data_prefix,
            "DEM_Lineament_Draft",
            crs_or_param=naming.epsg_tag(cfg.target_epsg),
            version=1,
            ext="gpkg",
        )
        vector_io.write_layer(gdf.to_crs(epsg=cfg.target_epsg), out, layer="lineament_draft")
        self._vector_outputs.append(out)
        self._lineaments_note = (
            f"{len(gdf)} draft segment(s) from {len(shades)} azimuth hillshades "
            "(machine draft — geologist review required)"
        )

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
            "ASTER alteration indices + porphyry target score produced (frozen support chain)",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._aster_processed else Decision.NA,
            note=(
                f"7 ratio indices, mean+1.5σ binaries (licence-subset stats basis), weighted "
                f"target score, {self._aster_targets} target polygon(s); thresholds logged."
                if self._aster_processed
                else "Method-note fallback (no HDF4-capable GDAL, or extraction failed) — "
                "acceptable: ASTER is support evidence."
            ),
        )
        hydro_ok = self._hydrology_note and not self._hydrology_note.startswith(
            ("skipped", "failed")
        )
        report.add(
            "Vector hydrology package (contours / drainage network / watersheds)",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if hydro_ok else Decision.NA,
            note=self._hydrology_note or "not attempted",
        )
        lin_ok = self._lineaments_note and not self._lineaments_note.startswith(
            ("skipped", "failed")
        )
        report.add(
            "Lineament first-pass draft (multi-azimuth hillshade Canny+Hough)",
            "MACHINE DRAFT stamped for geologist review; never scored unreviewed.",
            decision=Decision.PASS if lin_ok else Decision.NA,
            note=self._lineaments_note or "not attempted",
        )
        report.add(
            "Remote-sensing outputs labelled SUPPORT evidence only (not ore proof)",
            "Every output row + method note carries validation_status/limitation (invariant #8).",
            decision=Decision.PASS,
            note=f"Stamped on all {len(self._rows)} log rows and the method notes.",
        )
        report.add(
            "Sentinel indices / KOMPSAT ortho (external SNAP/ILWIS steps)",
            RECORDED_ACCEPTANCE,
            decision=Decision.PENDING,
            note="Orchestrated steps — formula-complete method notes in the 01_/03_ subfolders. "
            "(ASTER alteration is automated in-pipeline since v0.7.0 — see the ASTER item above.)",
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
    "- lithology index stack = ratios B11/B12, B08/B11, B04/B03\n"
    "- alteration indices (master step 17): iron-oxide B04/B02, ferric B11/B08, clay/SWIR B11/B12,\n"
    "  ferrous B12/B08, brightness (B02+B03+B04)/3\n" + _SUPPORT_FOOTER
)

_ASTER_NOTE = (
    "# Phase 02 — ASTER L1B alteration processing (frozen support-evidence chain)\n\n"
    "The exact master requires the ASTER HDF/band/project/index/score/class/mask sequence. The\n"
    "standalone `ASTER_QGIS_402_SOP_non_geologist_MN` is unlocated and obsolete as authority\n"
    "under METH-DISC-063. For reproducibility, the repository retains its historical numeric\n"
    "algorithm from METH-DISC-020/021 without claiming independent reference-output validation:\n"
    "11 swath\n"
    "bands (VNIR/SWIR/TIR) GCP-warped to EPSG:32647 via an HDF4-capable `gdalwarp`\n"
    "(QGIS-bundled; `BUDUUNKHAD_GDAL_BIN` overrides discovery), aligned to the 30 m SWIR grid\n"
    "(bilinear), then:\n\n"
    "- **Frozen indices:** Ferric_Iron=B02/B01 · Clay_AlOH=B05/B06 (≡ Sericite/\n"
    "  Illite) · Advanced_Argillic=B04/B06 · Chlorite_Epidote_MgOH=B07/B08 (≡ Carbonate/\n"
    "  Mg-OH) · Silica=B13/B12 · Quartz_Rich=B14/B12 · NDVI=(B3N−B02)/(B3N+B02)\n"
    "- **Anomaly binaries:** index > mean + 1.5·σ with the statistics computed on the\n"
    "  **licence-area subset (5 km buffer AOI)** — the frozen METH-DISC-021 statistics basis —\n"
    "  and the threshold applied full-scene (thresholds + basis logged in the\n"
    "  `ASTER_Anomaly_Threshold_Register`).\n"
    "- **Porphyry target score:** 2·clay + ferric + chlorite + silica (0–5); **target\n"
    "  polygons** = score ≥ 3, area ≥ 0.5 ha; confidence High ≥ 5 / Moderate 3–4.\n\n"
    "Without an HDF4-capable GDAL the chain degrades to this note (install QGIS or set\n"
    "`BUDUUNKHAD_GDAL_BIN`).\n\n"
    '**Workflow-v5 weighted score (NOT automated).** The older ILWIS "workflow v5" formula —\n'
    "0.12282·sericite + 0.08776·aloh + 0.07022·clay + 0.05265·argilic + 0.05765·quartz\n"
    "+ 0.08020·silicification + 0.06013·silica + 0.08270·iron_oxide + 0.06766·ferric\n"
    "+ 0.06013·chlorite + 0.04511·mgoh + 0.03008·carbonate + 0.01503·carbonate_swir\n"
    "+ 0.03760·structure_v1 + 0.10527·lithology — mixes spectral scores with non-spectral\n"
    "inputs (structure_v1, lithology) whose derivations are not documented in any available\n"
    "source; retained for reference only (see config/methodology/discrepancies.yaml, "
    "METH-DISC-005).\n" + _SUPPORT_FOOTER
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
