# CLAUDE.md — Buduunkhad / XV-023222 exploration pipeline

Conventions for working in this repo. Keep this loaded; the methodology document is
the ultimate source of truth.

## What this is

A config-driven Python geospatial pipeline implementing the *automatable* parts of the
**Buduunkhad / XV-023222 Exploration Workflow Methodology** (79 raw inputs, phases 00–99).
Phases are either **BUILD** (real geoprocessing) or **ORCHESTRATE** (scaffold folders,
emit templates, ingest human/field outputs, run QA/QC). Phases 00, 01, 02, 03 and 04 are
implemented end-to-end. Phase 02 follows the `docs/phase_02` guides: per-product clip
(DEM 5 km / Sentinel licence / basemap 1 km) → reproject to EPSG:32647 → Cloud-Optimized
GeoTIFF; DEM terrain derivatives (multi-azimuth hillshade, slope, aspect, TRI, profile/plan
curvature, flow); a terrain-derivatives index + QA/QC report; and formula-complete method
notes for the external SNAP/ILWIS/ASTER-HDF/KOMPSAT-ortho steps. Phase 03 (ORCHESTRATE) follows
`docs/phase_03` / `PHASE_03_PLAN.md`: scaffold the 12-folder tree, emit registers/templates + the
Preliminary Deposit Model, build the CMCS 5/10/20/25 km buffer, ingest the #68 mineralized-point XLSX +
human-digitized layers into a 17-layer evidence GPKG (all *Historical only* support evidence). Phase 04
(BUILD) follows `PHASE_04_PLAN.md`: a 250 m evidence-scoring grid over the AOI scored on the v9 §5
8-criterion weighted matrix (desktop-unavailable ASTER/field/drone criteria score 0 as data gaps),
high-score cells dissolved into A/B/C/D-ranked prospect polygons + ranking table + Go/No-Go matrix
(all *Preliminary — not ore proof*). Phase 05 and later phases are registered stubs unless their
module explicitly implements real work.

## Project constants (never invent — they live in `config/project.yaml`)

- Project / license: **Buduunkhad — XV-023222 / L23222**
- Standard deliverable CRS: **WGS 84 / UTM Zone 47N, EPSG:32647**
- 79 raw inputs in 7 evidence groups (8, 14, 24, 6, 17, 4, 6) — 78 from the methodology
  + the reconciled SAS hand-interpreted 1:25k geology scan (#79). See `DRIVE_MAP.md`.
- Primary boundary input: **№8** `MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz`
- Buffers: **500 m, 1 km, 5 km, 10 km, 20 km, 25 km** (25 km added per methodology v8/v9 — Phase 3 Step 7/7A near-occurrence coverage buffer).

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

- Match surrounding code; keep functions small and typed. Run `ruff` + `mypy` + `pyright`
  + `pytest` before declaring done (all four are CI gates). If `pyright` is not in the venv,
  run `npx pyright --pythonpath .venv/Scripts/python.exe`.
- When unsure about a phase's exact inputs/outputs/QA-QC, follow the methodology document,
  not assumptions.
- The `config/input_register.csv` filenames were reconciled against the real archive on
  2026-06-30 (see `REGISTER_RECONCILIATION.md`): validated, 0 edits. It remains editable config.
