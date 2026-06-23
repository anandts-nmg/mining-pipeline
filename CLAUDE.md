# CLAUDE.md — Buduunkhad / XV-023222 exploration pipeline

Conventions for working in this repo. Keep this loaded; the methodology document is
the ultimate source of truth.

## What this is

A config-driven Python geospatial pipeline implementing the *automatable* parts of the
**Buduunkhad / XV-023222 Exploration Workflow Methodology** (79 raw inputs, phases 00–99).
Phases are either **BUILD** (real geoprocessing) or **ORCHESTRATE** (scaffold folders,
emit templates, ingest human/field outputs, run QA/QC). Phase 00 and Phase 01 are
implemented end-to-end. Phase 02 has the automated core implemented: raster reprojection,
DEM derivatives, QA/QC logging, and method notes for SNAP/ILWIS/KOMPSAT steps that need
manual or external tooling. Phase 03 and later phases are registered stubs unless their
module explicitly implements real work.

## Project constants (never invent — they live in `config/project.yaml`)

- Project / license: **Buduunkhad — XV-023222 / L23222**
- Standard deliverable CRS: **WGS 84 / UTM Zone 47N, EPSG:32647**
- 79 raw inputs in 7 evidence groups (8, 14, 24, 6, 17, 4, 6) — 78 from the methodology
  + the reconciled SAS hand-interpreted 1:25k geology scan (#79). See `DRIVE_MAP.md`.
- Primary boundary input: **№8** `MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz`
- Buffers: **500 m, 1 km, 5 km, 10 km, 20 km**.

## Non-negotiable invariants (enforced in `core/`, not just docs)

1. **Raw is read-only.** Never write/rename/move/clip/reproject a raw file. Use
   `core.raw_guard` — it refuses write-mode opens inside `raw_root`. The pipeline re-verifies
   raw SHA-256 checksums against the Phase 00 baseline at the start of every real run
   (`pipeline.verify_raw_integrity`) and stops loudly on drift unless `--override` is passed.
2. **Work on copies only.** Each phase reads raw / prior-phase outputs and writes to its
   own subfolders under `output_root`.
3. **Sidecars travel with their parent.** `.tfw .jgw .pgw .aux.xml .ovr .rpc .eph .txt`
   move as a bundle with the parent raster/image — never orphaned. Use `core.sidecars`.
4. **EPSG:32647 for all deliverables.** Always record the native/source CRS in metadata;
   never silently drop it. Use `core.crs`.
5. **Versioning.** Outputs are versioned `v01, v02, …`; drafts get a `_DRAFT` suffix.
6. **QA/QC per phase.** Every phase writes a QA/QC log (item / acceptance / reviewer /
   date / decision) and ends at a **decision gate**. A blocked gate stops the runner unless
   `--override` is passed (which is logged).
7. **Traceability.** Every output records source raw input(s) (by № and name), processing
   date, operator/reviewer, and a limitation note.
8. **Evidence hierarchy.** Remote sensing / pXRF / drone = *support* evidence; lab assay +
   field geology + structural control = *decision* evidence. Never label a support layer as
   ore proof.

## Output naming

`XV023222_Buduunkhad_<Description>_<CRSorParam>_v01.<ext>` for GIS data layers
(`core.naming.data_name`), and the hyphenated `XV-023222_Buduunkhad_<Description>.<ext>`
for admin registers/logs (`core.naming.register_name`). Build names through `core.naming`,
never by f-string in phase code.

## Layout

- `config/` — `project.yaml` (constants/paths), `input_register.csv` (the 79 inputs), and
  `raw_manifest.csv` (each input pinned to its canonical Google Drive file ID + size).
- `src/buduunkhad/config.py` — typed (pydantic v2) config + register loaders.
- `src/buduunkhad/core/` — the enforced primitives (paths, naming, raw_guard, sidecars,
  crs, qaqc, registers, gates).
- `src/buduunkhad/phases/` — one module per phase, all subclassing `phases.base.Phase`.
- `src/buduunkhad/pipeline.py` — registry + ordered runner (`--from/--to/--only/--dry-run/--override`).
- `src/buduunkhad/cli.py` — typer app (`run`, `list`, and `phaseNN` commands).
- `tests/` — pytest, runs entirely on tiny synthetic fixtures (no real data needed).

## The Phase interface

Every phase subclasses `Phase` and implements:

```python
prepare(ctx) -> None        # create folders, copy working inputs + sidecars
run(ctx) -> PhaseResult     # do the work; in dry-run emit empty registers/templates
qaqc(ctx) -> QAQCReport     # acceptance checks
gate(qaqc) -> GateDecision  # go / no-go / blocked
```

Class attributes: `id`, `name`, `mode` ("build"|"orchestrate"), `input_numbers`,
`subfolders`.

- **Dry run** (`--dry-run`) must work with **no raw data**: build the full folder tree,
  write empty registers/templates and the Master GPKG schema, then stop short of real work.
- **Stub phases** participate in dry-run (folders + template) but raise
  `NotImplementedError("Phase NN — build pending")` on a real run.

## Data availability

The 79 raw inputs live in a cloud-only Google Drive folder; `raw_root` may be empty.
The canonical archive (`0. Raw Data`, ~1.8 GiB) and its layout are mapped in `DRIVE_MAP.md`;
the storage approach (no S3; local-first; GCS only if ever) is `docs/adr/0001`.
Real runs validate the register against `raw_root` and **fail loudly** with the list of
missing files. Dry runs skip that check. Build and test against synthetic fixtures.

## Working style

- Match surrounding code; keep functions small and typed. Run `ruff` + `mypy` + `pytest`
  before declaring done.
- When unsure about a phase's exact inputs/outputs/QA-QC, follow the methodology document,
  not assumptions.
- Filenames in `config/input_register.csv` were seeded from the methodology PDF and should
  be reconciled against the real archive once it is synced (the register is editable config).
