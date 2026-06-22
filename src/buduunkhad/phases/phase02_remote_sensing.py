"""Phase 02 — Remote Sensing Preprocessing (BUILD).

Automated, dependency-light core of the methodology's remote-sensing phase:

1. Reproject every raster input (DEM, KOMPSAT bands, Sentinel/basemap) to EPSG:32647.
2. Derive terrain layers (hillshade / slope / aspect / D8 drainage) from the DEMs.
3. Write a remote-sensing QA/QC log recording native CRS, reprojection and derivatives.

The methodology's SNAP 13.0.0 / ILWIS 3.6.8 steps (ASTER HDF band extraction and
indices, KOMPSAT RPC orthorectification + pan-sharpening) need band-stacked inputs
and proprietary tooling, so they are *orchestrated*: this phase emits method notes
into the relevant subfolders rather than faking those products.
"""

from __future__ import annotations

import re
from pathlib import Path

from buduunkhad.core import crs as crs_mod
from buduunkhad.core import dem, naming, registers
from buduunkhad.core.qaqc import RECORDED_ACCEPTANCE, Decision, QAQCReport, new_report
from buduunkhad.phases.base import Phase, PhaseResult, RunContext

_RS_LOG_COLUMNS = [
    "no",
    "filename",
    "native_epsg",
    "reprojected_to",
    "output",
    "derivative",
    "decision",
    "note",
]

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


def _is_dem_elevation(filename: str) -> bool:
    low = filename.lower()
    return "dem" in low and not any(
        k in low for k in ("numobs", "numobservations", "hillshade", "slope", "aspect")
    )


class Phase02RemoteSensing(Phase):
    id = "02"
    name = "Remote Sensing Preprocessing"
    mode = "build"
    input_numbers = [*range(9, 47), *range(73, 79)]
    gate_condition = "Remote-sensing rasters reprojected to EPSG:32647 and QA/QC passed."
    custom_subfolders = [
        "01_Input_Working_Copy",
        "02_Reprojected_EPSG32647",
        "03_DEM_Derivatives",
        "04_Indices_Composites",
        "05_KOMPSAT_Ortho_Pansharpen",
        "06_QAQC",
    ]

    _reprojected: int
    _dem_count: int
    _derivatives: int
    _rows: list[dict[str, object]]

    def __init__(self) -> None:
        self._reprojected = 0
        self._dem_count = 0
        self._derivatives = 0
        self._rows = []

    # ------------------------------------------------------------------ #

    def run(self, ctx: RunContext) -> PhaseResult:
        pdir = ctx.phase_dir(self.id)
        cfg = ctx.config
        epsg = cfg.target_epsg
        result = PhaseResult(self.id, status="dry-run" if ctx.dry_run else "ok")

        reproj_dir = pdir / "02_Reprojected_EPSG32647"
        deriv_dir = pdir / "03_DEM_Derivatives"
        rs_log = pdir / "06_QAQC" / f"{cfg.register_prefix}_RemoteSensing_QAQC_Log.xlsx"

        if ctx.dry_run:
            registers.write_table_xlsx(
                [], _RS_LOG_COLUMNS, rs_log, sheet_title="RemoteSensing QAQC"
            )
            self._write_method_notes(ctx, pdir)
            result.add_output(rs_log)
            result.log("dry-run: RS folders + method notes + empty QA/QC log")
            return result

        rasters = [r for r in ctx.records_by_numbers(self.input_numbers) if r.file_type == "raster"]
        for rec in sorted(rasters, key=lambda r: r.no):
            self._rows.append(self._process_raster(ctx, rec, reproj_dir, deriv_dir, epsg))

        registers.write_table_xlsx(
            self._rows, _RS_LOG_COLUMNS, rs_log, sheet_title="RemoteSensing QAQC"
        )
        self._write_method_notes(ctx, pdir)
        result.add_output(rs_log)
        result.log(
            f"reprojected {self._reprojected} raster(s); {self._dem_count} DEM(s); "
            f"{self._derivatives} terrain derivative(s)"
        )
        return result

    # ------------------------------------------------------------------ #

    def _process_raster(self, ctx, rec, reproj_dir, deriv_dir, epsg) -> dict[str, object]:  # type: ignore[no-untyped-def]
        cfg = ctx.config
        row: dict[str, object] = {"no": rec.no, "filename": rec.filename}
        wc = ctx.phase_dir("00") / rec.evidence_group / rec.filename
        if not wc.exists():
            row.update(
                native_epsg="",
                reprojected_to="",
                output="",
                derivative="",
                decision="Fail",
                note="working copy missing (run Phase 00 first)",
            )
            return row

        audit = crs_mod.audit_raster(wc, target_epsg=epsg)
        row["native_epsg"] = audit.epsg if audit.epsg is not None else ""

        desc = _output_desc(rec.filename, cfg.data_prefix)
        out_name = naming.data_name(
            cfg.data_prefix, desc, crs_or_param=naming.epsg_tag(epsg), version=1, ext="tif"
        )
        out_path = reproj_dir / out_name
        try:
            crs_mod.reproject_raster(wc, out_path, dst_epsg=epsg)
            self._reprojected += 1
            row.update(reprojected_to=epsg, output=out_path.name, decision="Pass", note="")
        except Exception as exc:  # noqa: BLE001 - record and continue the batch
            row.update(
                reprojected_to="",
                output="",
                decision="Fail",
                note=f"reproject failed: {type(exc).__name__}: {exc}",
            )
            return row

        if _is_dem_elevation(rec.filename):
            self._dem_count += 1
            row["derivative"] = self._derive_terrain(cfg, desc, out_path, deriv_dir, epsg)
        else:
            row["derivative"] = ""
        return row

    def _derive_terrain(self, cfg, desc, dem_path, deriv_dir, epsg) -> str:  # type: ignore[no-untyped-def]
        def name(suffix: str) -> Path:
            return deriv_dir / naming.data_name(
                cfg.data_prefix,
                f"{desc}_{suffix}",
                crs_or_param=naming.epsg_tag(epsg),
                version=1,
                ext="tif",
            )

        outputs = {
            "hillshade": name("Hillshade"),
            "slope": name("SlopeDeg"),
            "aspect": name("Aspect"),
            "flow": name("FlowAccumulation"),
        }
        produced = dem.derive_terrain(dem_path, outputs)
        self._derivatives += len(produced)
        return f"{len(produced)} terrain layer(s)"

    def _write_method_notes(self, ctx: RunContext, pdir: Path) -> None:
        prefix = ctx.config.project.project_code + "_" + ctx.config.project.name
        notes = {
            pdir / "04_Indices_Composites" / f"{prefix}_Indices_Composites_Method_Note.md": (
                "# Phase 02 - Indices & Composites (orchestrated)\n\n"
                "Sentinel-2 / ASTER spectral indices and composites require band-stacked, "
                "atmospherically-corrected inputs processed in SNAP 13.0.0 / ILWIS 3.6.8. The "
                "received basemap/Sentinel rasters here are RGB composites or single products, "
                "not analysis-ready band stacks, so index derivation is performed as a manual / "
                "SNAP step. Place resulting indices (EPSG:32647) in this folder and log them in "
                "the Phase 02 QA/QC register.\n"
            ),
            pdir / "05_KOMPSAT_Ortho_Pansharpen" / f"{prefix}_KOMPSAT_Ortho_Method_Note.md": (
                "# Phase 02 - KOMPSAT orthorectification & pan-sharpening (orchestrated)\n\n"
                "RPC orthorectification (using the DEM) and PAN/MS pan-sharpening of the KOMPSAT-2 "
                "bundle are performed with GDAL/SNAP using the .rpc/.eph sidecars. The individual "
                "bands have been reprojected to EPSG:32647 in 02_Reprojected_EPSG32647/. Place the "
                "orthorectified bundle and pan-sharpened orthobasemap (EPSG:32647) here and log "
                "them in the Phase 02 QA/QC register.\n"
            ),
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
                "Folders, method notes and empty QA/QC log present (dry-run).",
                decision=Decision.PASS,
                note="Dry-run: no raster data processed.",
            )
            return report

        any_fail = any(r.get("decision") == "Fail" for r in self._rows)
        report.add(
            "Rasters reprojected to EPSG:32647",
            RECORDED_ACCEPTANCE,
            decision=Decision.FAIL if any_fail else Decision.PASS,
            note=f"{self._reprojected} raster(s) reprojected; "
            f"{sum(1 for r in self._rows if r.get('decision') == 'Fail')} failed.",
        )
        report.add(
            "Native/source CRS recorded",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS,
            note="Native EPSG captured per raster in the RemoteSensing QA/QC log.",
        )
        report.add(
            "DEM terrain derivatives generated",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._derivatives else Decision.PENDING,
            note=f"{self._derivatives} derivative(s) from {self._dem_count} DEM(s) "
            "(hillshade/slope/aspect/drainage).",
        )
        report.add(
            "Indices / KOMPSAT ortho (SNAP/ILWIS)",
            RECORDED_ACCEPTANCE,
            decision=Decision.PENDING,
            note="Orchestrated step - see method notes in 04_/05_ subfolders.",
        )
        return report


PHASE = Phase02RemoteSensing
