# Buduunkhad / XV-023222 Exploration Pipeline

A config-driven Python geospatial pipeline implementing the *automatable* parts of the
**Buduunkhad / XV-023222 Exploration Workflow Methodology** (79 raw inputs, phases 00–99).

This repository is the **foundation build**: the project skeleton, the conventions enforced
in code, the 79-input register, the phase-runner architecture, **Phases 00, 01, 02 and 03 implemented
end-to-end**, and every later phase registered as a stub behind a uniform interface.

> The methodology is phase-gated. Remote sensing / pXRF / drone outputs are **support**
> evidence, not ore proof — final confidence comes from lab assay + field geology +
> structural control. See `CLAUDE.md` for the governing invariants.

## What's built

| Phase | Name | Mode | Status |
|------|------|------|--------|
| 00 | Raw Files Archive | build | **implemented** — inventory, SHA-256 integrity, readme, working copies, raw read-only verification |
| 01 | Data Audit & Master GIS Setup | build | **implemented** — KMZ→GeoPackage boundary (EPSG:32647), buffers, raster CRS audit, master GPKG schema, confidence ranking, QGIS project |
| 02 | Remote Sensing Preprocessing | build | **implemented** — per-product clip (DEM 5 km / Sentinel licence / basemap 1 km) → reproject to EPSG:32647 → Cloud-Optimized GeoTIFF; DEM terrain derivatives (multi-azimuth hillshade, slope, aspect, TRI, profile/plan curvature, flow); Sentinel indices / ASTER-HDF / KOMPSAT-ortho as formula-complete method notes. See `PHASE_02_PLAN.md` |
| 03/03A | Geology / Metallogenic / CMCS Synthesis + Deposit Model | orchestrate | **implemented** — 12-folder scaffold; 17-layer evidence GPKG (13 provenance fields + `BUD-` feature IDs); CMCS 5/10/20/25 km context buffer; #68 mineralized-point XLSX→validated points; human-layer ingest; 03A deposit-model template + 6-model evidence table + 100-pt scoring; all outputs stamped *Historical only*. See `PHASE_03_PLAN.md` |
| 04 | Preliminary Prospect Delineation & Ranking | build | stub |
| 05 | DJI Matrice 400 Drone / LiDAR / Photogrammetry | orchestrate | stub |
| 06 | Recon Mapping & Portable XRF | orchestrate | stub |
| 07 | Rock Chip / Channel / Verification Sampling | orchestrate | stub |
| 08 | Orientation Soil / Stream / Heavy Mineral | orchestrate | stub |
| 09 | Systematic Soil Grid & Lab QA/QC | build | stub |
| 10 | Integrated Interpretation & Final Target Ranking | build | stub |
| 11 | Follow-up Trench / Geophysics / Scout Drill | orchestrate | stub |
| 99 | Final Deliverables | build | stub |

Stubs create their folders and a method/status note during `--dry-run`, and raise a clear
`NotImplementedError("Phase NN — build pending")` if run for real.

## Project constants (in `config/project.yaml`)

- **Project / license:** Buduunkhad — `XV-023222 / L23222`
- **Standard deliverable CRS:** WGS 84 / UTM Zone 47N, **EPSG:32647**
- **79 raw inputs** in 7 evidence groups (8, 14, 24, 6, 17, 4, 6) — `config/input_register.csv`
  (78 from the methodology + the reconciled SAS hand-interpreted 1:25k scan; see `DRIVE_MAP.md`)
- **Boundary input:** №8 license-boundary KMZ
- **Buffers:** 500 m, 1 km, 5 km, 10 km, 20 km, 25 km (25 km per methodology v8/v9)

## Setup

GDAL/rasterio/geopandas/fiona need the geospatial toolchain. Two routes:

**pip (wheels bundle GDAL on Windows/Linux):**

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# POSIX:    source .venv/bin/activate
pip install -e ".[dev]"
```

**conda (recommended for heavy raster work / Phase 02 DEM tooling):**

```bash
conda env create -f environment.yml
conda activate buduunkhad
pip install -e ".[dev]"
```

Verify the install:

```bash
buduunkhad --help        # lists run / list / info / validate / phase00 ... phase99
```

## Usage

```bash
buduunkhad list                       # phase registry
buduunkhad info                       # project constants + resolved paths
buduunkhad validate                   # are the 79 raw inputs present under raw_root? (+ manifest coverage)

# Build the FULL 00–99 folder tree + empty registers + master GPKG schema, no data needed:
buduunkhad run --dry-run

# Real runs of the built phases (require raw data — see below):
buduunkhad run --from 00 --to 01
buduunkhad phase00
buduunkhad phase01

# A blocked decision gate stops the run; advance explicitly (logged):
buduunkhad run --from 00 --to 01 --override
```

Each run writes a per-run log and a `run_manifest.json` under `runs/<run_id>/`, recording
which phases ran, their gate decisions, and their outputs.

## The cloud-data caveat (important)

The 79 raw inputs live in a **Google Drive folder (cloud-only by default)**. The pipeline runs on
real data once that archive is synced/copied to a local folder — Phases 00–03 have been run
end-to-end against a local copy (gates GO). The design keeps the data decoupled from the code:

- The raw archive path is a config value (`config/project.yaml → paths.raw_root`); nothing is
  hard-coded.
- On a real run the register is validated against `raw_root` and the pipeline **fails loudly**
  with the list of missing files (it does not crash deep in processing).
- `--dry-run` builds the entire foundation (folder tree, empty registers, master GPKG schema)
  **with no raw data present** — this is how you verify the foundation before data arrives.
- The whole pipeline is tested against **tiny synthetic fixtures** (`tests/`), so `pytest`
  is green with zero real data.

**Getting the data local (~1.8 GiB — the canonical `0. Raw Data`, not the 700 GB drone set):**
make `0. Raw Data` available locally — either add a shortcut to it in Google Drive and mark it
*Available offline* in Drive for Desktop, or `rclone copy` it — then point the pipeline at that
folder. Per-machine paths go in an **environment variable** (so nothing machine-specific is
committed):

```powershell
# Windows PowerShell (per-machine paths via env vars; use SHORT paths — see below):
$env:BUDUUNKHAD_RAW_ROOT    = "C:\bk\rawdata"  # a REAL local copy of "0. Raw Data" (a Drive symlink under-enumerates via Python rglob)
$env:BUDUUNKHAD_OUTPUT_ROOT = "C:\bk\out"   # where generated outputs go
buduunkhad validate                 # confirms inputs resolve + manifest coverage (size match)
buduunkhad run --from 00 --to 01    # --override only if a *non-acknowledged* gap stops it
```

`BUDUUNKHAD_RAW_ROOT` / `BUDUUNKHAD_OUTPUT_ROOT` override `paths.*` from `project.yaml`. The
pipeline reads files by basename, so the archive's 11-theme layout works as-is. See
`DRIVE_MAP.md` for the layout and `config/raw_manifest.csv` for the canonical Drive file IDs.

**Where outputs go.** Generated outputs are **build artifacts** (git-ignored, regenerable) and
should **not** live in the repo: on Windows the deep methodology folder names + long raster
filenames breach the 260-char `MAX_PATH` limit, and they would bloat the working tree. Use a
**short path outside the repo** via `BUDUUNKHAD_OUTPUT_ROOT` (e.g. `C:\bk\out`). The committed
default `outputs/` is only for dry-runs/tests, or when Windows long paths are enabled. Run logs
and `run_manifest.json` land under `runs/` (also git-ignored). Because the real Drive path is
very deep, point `raw_root` at a short path too. Prefer a **real local copy** (e.g.
`robocopy "G:\…\0. Raw Data" C:\bk\rawdata /E`) over a Drive-for-Desktop junction: the
virtual filesystem can under-enumerate files under `rglob`, so a run may see only some
inputs. Final *deliverables* can be published to the
project Google Drive separately so teammates can see them:

```powershell
# Publish ONLY the deliverables (not the 1.8 GiB raw working copies) to a Drive folder:
$env:BUDUUNKHAD_OUTPUT_ROOT  = "C:\bk\out"
$env:BUDUUNKHAD_PUBLISH_ROOT = "G:\My Drive\Buduunkhad_Deliverables"   # a Drive-for-Desktop folder
buduunkhad publish --label v0.3.1
```

This copies the GIS layers, registers, logs and reports into a versioned `PhaseNN/` folder with
an `INDEX.md` + the run manifest; raw working copies are excluded. Then **share that folder in
Google Drive** to give teammates access (Drive for Desktop uploads it automatically).

> The `config/input_register.csv` filenames were reconciled against the real archive on
> 2026-06-30 (see `REGISTER_RECONCILIATION.md`): validated with 0 edits. The register is plain
> editable config, and `buduunkhad validate` reports any manifest mismatches.

## Run-start safety checks (real runs)

Before any phase executes, a real run performs two guards (a dry run only warns):

- **Raw integrity baseline** — once Phase 00 has written `SHA-256_Checksum_Register.csv`,
  every later real run re-verifies `raw_root` against it and **stops loudly** if any raw file
  changed or vanished (enforcing "raw is read-only" across runs). If a change is intentional,
  re-run Phase 00 to refresh the baseline, or pass `--override` to proceed (logged).
- **Path-length pre-flight** — see below.

## Windows path length (MAX_PATH)

A few raw filenames are long (~117 chars); with a deep `output_root` and the phase folder
names, generated paths can approach the Windows 260-char `MAX_PATH` limit, where GDAL/IO start
failing cryptically. The pipeline runs a **pre-flight**: if long-path support is disabled and a
generated path would exceed the limit, a real run stops with a clear message (a dry run warns).

The most convenient fix is to enable long paths once (elevated PowerShell, then restart shells):

```powershell
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' `
  -Name LongPathsEnabled -Value 1 -Type DWord
```

Otherwise keep `paths.output_root` shallow (e.g. `C:\bk\outputs`). `core.winpath` also exposes
`extended_length_path()` (the `\\?\` prefix) for code paths that need to bypass the limit.

## Continuous integration

`.github/workflows/ci.yml` runs ruff (lint + format), mypy, pyright and pytest on Python 3.11 and 3.12.

## Layout

```
config/            project.yaml (constants/paths) + input_register.csv (79 inputs) + raw_manifest.csv (Drive pins)
src/buduunkhad/
  config.py        typed (pydantic v2) config + register loaders
  core/            enforced primitives: paths, naming, raw_guard, sidecars, crs, vector_io,
                   raster_writers, dem, qaqc, registers, gates, winpath
  phases/          base.py (Phase ABC + StubPhase) + one module per phase
  pipeline.py      registry + ordered runner (--from/--to/--only/--dry-run/--override)
  cli.py           typer app
tests/             pytest suite on synthetic fixtures (no real data needed)
```

## Development

```bash
pytest          # tests on synthetic fixtures
ruff check .    # lint
ruff format .   # format
mypy            # type-check (src/)
pyright         # type-check (CI gate); or: npx pyright --pythonpath .venv/Scripts/python.exe
pre-commit install && pre-commit run --all-files
```

See `CLAUDE.md` for the non-negotiable invariants (raw read-only, sidecar bundling,
EPSG:32647, versioned naming, QA/QC + decision gates, traceability, evidence hierarchy)
and how new phases plug into the `Phase` interface.
