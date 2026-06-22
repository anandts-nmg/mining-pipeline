"""Phase 00 — Raw Files Archive (BUILD).

Inventory the 78 raw inputs, compute SHA-256 checksums, verify the raw archive is
unchanged (read-only), and materialise working copies (parent + sidecars) into the
control archive under the output root. Raw originals in ``raw_root`` are never
touched.
"""

from __future__ import annotations

from pathlib import Path

from buduunkhad.core import raw_guard, registers, sidecars
from buduunkhad.core.qaqc import RECORDED_ACCEPTANCE, Decision, QAQCReport, new_report
from buduunkhad.core.raw_guard import assert_not_raw_write
from buduunkhad.phases.base import Phase, PhaseResult, RunContext


class Phase00Archive(Phase):
    id = "00"
    name = "Raw Files Archive"
    mode = "build"
    input_numbers = list(range(1, 79))
    gate_condition = "All files archived, checksum complete, processing copies available."

    # filled during run() so qaqc() can report on it
    _checksums: list[raw_guard.ChecksumRecord]
    _copied_parents: int
    _missing: list[str]
    _raw_unchanged: bool

    def __init__(self) -> None:
        self._checksums = []
        self._copied_parents = 0
        self._missing = []
        self._raw_unchanged = True

    # ------------------------------------------------------------------ #

    def run(self, ctx: RunContext) -> PhaseResult:
        archive_dir = ctx.phase_dir(self.id)
        result = PhaseResult(self.id, status="dry-run" if ctx.dry_run else "ok")

        reg_prefix = ctx.config.register_prefix
        inv_path = archive_dir / f"{reg_prefix}_78Input_Master_Inventory.xlsx"
        integ_path = archive_dir / f"{reg_prefix}_Raw_Data_Integrity_Log.xlsx"
        checksum_path = archive_dir / "SHA-256_Checksum_Register.csv"
        readme_path = archive_dir / f"{reg_prefix}_Source_Data_Readme.docx"

        if ctx.dry_run:
            # Empty, header-only scaffolding so the foundation is verifiable with no data.
            registers.write_inventory_xlsx([], inv_path)
            registers.write_integrity_log_xlsx([], integ_path)
            registers.write_checksum_register_csv([], checksum_path)
            self._write_readme(ctx, readme_path)
            for p in (inv_path, integ_path, checksum_path, readme_path):
                result.add_output(p)
            result.log("dry-run: empty inventory/integrity/checksum/readme scaffolding written")
            return result

        # --- real run --------------------------------------------------- #
        raw_root = ctx.raw_root
        index = {p.name: p for p in raw_guard.iter_files(raw_root)}

        # 1. checksums of the originals (integrity baseline)
        self._checksums = raw_guard.build_checksum_records(raw_root)
        before = {r.relative_path: r.sha256 for r in self._checksums}

        # 2. working copies (parent + sidecars) into the control archive by group
        size_by_name = {r.relative_path.split("/")[-1]: r.size_bytes for r in self._checksums}
        inv_rows: list[dict[str, object]] = []
        copied_targets: list[Path] = []
        for rec in sorted(ctx.register, key=lambda r: r.no):
            group_dir = archive_dir / rec.evidence_group
            src = index.get(rec.filename)
            working_copy = group_dir / rec.filename
            if src is None:
                self._missing.append(rec.filename)
                open_status, copy_status = "Missing", "Not copied"
            else:
                assert_not_raw_write(working_copy, raw_root)  # never write into raw
                if not rec.is_sidecar:
                    bundle = sidecars.copy_bundle(src, group_dir, overwrite=True)
                    copied_targets.extend(bundle.all_files)
                    self._copied_parents += 1
                open_status, copy_status = "Opens", "Copied"
            inv_rows.append(
                self._inventory_row(
                    ctx, rec, src, working_copy, size_by_name, open_status, copy_status
                )
            )

        # 3. verify raw archive unchanged after all copying
        after = raw_guard.verify_against(raw_root, before)
        self._raw_unchanged = after.ok
        ctx.logger.info("Phase 00: %s", after.summary())

        # 4. write registers + readme
        registers.write_inventory_xlsx(inv_rows, inv_path)
        registers.write_integrity_log_xlsx(self._checksums, integ_path)
        registers.write_checksum_register_csv(self._checksums, checksum_path)
        self._write_readme(ctx, readme_path)
        for p in (inv_path, integ_path, checksum_path, readme_path):
            result.add_output(p)
        result.log(
            f"archived {self._copied_parents} parent bundles, "
            f"{len(self._checksums)} files checksummed, {len(self._missing)} missing"
        )
        return result

    # ------------------------------------------------------------------ #

    def _inventory_row(
        self,
        ctx: RunContext,
        rec,  # type: ignore[no-untyped-def]
        src: Path | None,
        working_copy: Path,
        size_by_name: dict[str, int],
        open_status: str,
        copy_status: str,
    ) -> dict[str, object]:
        size_mb = round(size_by_name.get(rec.filename, 0) / (1024 * 1024), 4)
        checksum = next((c.sha256 for c in self._checksums if c.filename == rec.filename), "")
        return {
            "no": rec.no,
            "evidence_group": rec.evidence_group,
            "primary_phase": rec.primary_phase,
            "original_filename": rec.filename,
            "standardized_filename": rec.filename,
            "file_type": rec.file_type,
            "is_sidecar": rec.is_sidecar,
            "parent_file": rec.parent_file,
            "raw_path": str(src) if src else "",
            "working_copy_path": str(working_copy),
            "file_size_mb": size_mb,
            "checksum_sha256": checksum,
            "read_status": "read-only",
            "open_status": open_status,
            "processing_copy_status": copy_status,
            "scan_quality": "",
            "has_coordinate_grid": "",
            "georef_required": "",
            "georef_status": "Not started",
            "vectorization_status": "Not started",
            "handover_status": "",
            "source_note": "",
            "owner": "",
            "methodology_action": rec.methodology_action,
        }

    def _write_readme(self, ctx: RunContext, path: Path) -> Path:
        groups = [(g.name, g.count) for g in ctx.config.evidence_groups]
        return registers.write_source_readme_docx(
            path,
            title=f"{ctx.config.project.name} ({ctx.config.project.project_code}) — Source Data Readme",
            project=ctx.config.project.name,
            license_code=ctx.config.project.license_code,
            target_crs=f"{ctx.config.crs.target_name}, {ctx.config.crs.target_authority}",
            evidence_groups=groups,
        )

    # ------------------------------------------------------------------ #

    def qaqc(self, ctx: RunContext) -> QAQCReport:
        report = new_report(self.id, self.name)
        if ctx.dry_run:
            report.add(
                "Archive scaffolding created",
                "Inventory/integrity/checksum/readme present (dry-run).",
                decision=Decision.PASS,
                note="Dry-run: no raw data processed.",
            )
            return report

        report.add(
            "Checksum match",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._checksums else Decision.FAIL,
            note=f"{len(self._checksums)} files checksummed.",
        )
        report.add(
            "Raw overwrite not done",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._raw_unchanged else Decision.FAIL,
            note="Raw archive checksums unchanged after copying."
            if self._raw_unchanged
            else "Raw archive changed during run!",
        )
        report.add(
            "Sidecar completeness",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if not self._missing else Decision.FAIL,
            note="All registered files present."
            if not self._missing
            else f"Missing: {', '.join(self._missing[:10])}",
        )
        report.add(
            "Source note and owner registered",
            RECORDED_ACCEPTANCE,
            decision=Decision.PENDING,
            note="Source note / owner columns to be completed by the operator.",
        )
        return report


# Registered with the pipeline.
PHASE = Phase00Archive
