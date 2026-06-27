# Repo Inspection — Buduunkhad / XV-023222 Pipeline

**Date:** 2026-06-27 · **Inspected at:** `f8c2d06` (main) · **Tag:** `v0.2.0`

Full read of the source tree (config, pipeline, all `core/` primitives, phases 00–02 + stubs,
CLI), the config/register/manifest, and the docs, plus every quality gate.

> **Status:** all findings below were **resolved on 2026-06-27** via a 6-agent cleanup workflow
> (5 parallel edit agents by disjoint file group → gate verification) — 13 files changed,
> +21/−21 — and re-verified green on every gate. See [Resolution](#findings--all-resolved-metadata--cosmetic-nothing-was-broken).

---

## Verdict: healthy, ships green

All five gates pass on the current tree:

| Gate | Result |
|---|---|
| `pytest` | **72 passed** (~12 s, synthetic fixtures) |
| `ruff check` | clean |
| `ruff format --check` | 48 files already formatted |
| `mypy` | no issues in 34 files |
| `pyright` (CI gate) | **0 errors, 0 warnings, 0 info** |

- No tracked build artifacts — `runs/`, `outputs/`, `data/`, `*.xlsx/*.tif/*.gpkg` all correctly git-ignored.
- No `TODO/FIXME/HACK/XXX` anywhere in `src/`.
- Register parses cleanly: **79 rows, all `primary_phase` numeric** (01:1, 02:44, 03:28, 08:6);
  group counts match `project.yaml` exactly (8/14/24/6/17/4/6); 15 Phase-02 rasters = 10 processed
  + 5 KOMPSAT method-note.

---

## Architecture — solid

~5,080 LOC (src + tests). Config-driven; invariants enforced in `core/`, not just documented;
one module per phase behind a uniform `Phase` ABC. Phases **00/01/02 implemented end-to-end**;
03–11/99 are dry-run-participating stubs that raise `NotImplementedError` on a real run.

Worth preserving:

- **Lazy GIS imports** — `rasterio/fiona/geopandas` imported inside functions so non-raster paths
  don't pay GDAL startup; `raster_writers`/`dem` split out of `crs.py` for the same reason.
- **COG correctness** — `dem._write_cog` builds a *fresh* minimal profile (crs/transform/size only)
  so a source DEM's predictor/compression can't leak onto a derivative; `is_cog` requires internal
  overviews only when `min(dim) > blocksize` (tiny clips/fixtures don't false-fail).
- **Graceful no-overlap** — `reproject_clip_cog` returns `(None, False)` on a disjoint AOI → recorded
  as `Skip`, never fails the gate.
- **Data-integrity invariants in code** — raw read-only guard + SHA-256 baseline re-verification at
  the start of every real run; sidecar bundles travel with their parent; native CRS recorded as
  provenance; support-evidence stamp on every Phase 02 row + method note.

---

## Findings — all resolved (metadata / cosmetic, nothing was broken)

Resolved **2026-06-27**. Each row shows the original finding and exactly how it was solved. All
gates re-verified after the edits: `ruff` ✓ · `ruff format` ✓ · `mypy` ✓ · `pyright` ✓ (0 errors) ·
`pytest` ✓ (72 passed).

| # | Severity | Location | Finding | How it was solved | Status |
|---|---|---|---|---|---|
| 1 | Low | `pyproject.toml:7` | Package `version = "0.1.0"`, but tag/build is `v0.2.0`. | Bumped to `version = "0.2.0"`. | ✅ |
| 2 | Low | `phase00_archive.py:48`, `phase01_data_audit.py:645` (+ ~11 docstrings) | "78 vs 79" drift, incl. two **deliverable-facing** spots: inventory file `..._78Input_Master_Inventory.xlsx` (held 79 rows) and "configured 78-input register" text. | Inventory renamed `..._79Input_Master_Inventory.xlsx`; summary text → "79-input"; every count-implying docstring (`config.py`, `naming.py`, `registers.py`, `pipeline.py`, `__init__.py`, both phase modules) → 79. The explanatory **"78 methodology inputs + SAS scan = 79" comments were deliberately kept** (they are correct). Three tests updated to match the rename: `test_naming.py`, `test_phase00.py`, `conftest.py`. | ✅ |
| 3 | Low | `phase00_archive.py:24`, `phase01_data_audit.py:30` | `input_numbers = range(1, 79)` (1–78) excluded #79 — latent only, since `run()` iterates `ctx.register` (all 79). | Widened both to `range(1, 80)` so the class metadata matches the 79-row register and the base `self.records()` helper can't silently drop #79. | ✅ |
| 4 | Low | `docs/adr/0001:53` | Listed "add the 79th input (SAS hand-interpreted) to the register" as an open follow-up — already done. | Bullet rewritten: the 79th-input item is marked **Resolved** (register has 79 rows); the KOMPSAT-EULA and BMP-as-`.jpg` MUGZ items were kept open. | ✅ |
| 5 | Cosmetic | `README.md:139` | Publish example still showed `--label v0.1.0`. | Updated to `--label v0.2.0`. | ✅ |

**Verification notes.**

- `conftest.raw_archive` was confirmed to build synthetic files by iterating the register
  directly (one file per row → 79), with **no hardcoded `78`** in the fixture body — so widening
  the counts/ranges required no fixture change.
- Post-edit diff is **exactly 13 files** (`pyproject.toml`, `README.md`, `docs/adr/0001`, 5 `src`
  modules, 3 test files), all within the intended scope; a `grep` confirms **no total-implying
  "78" remains in `src/`** (input *numbers* like `#74/#77/#78` and the `= 79` derivation comments
  were correctly left untouched).

No correctness, security, or design issues were found at any point — only version/label hygiene.

---

## Open *decisions* (awaiting owner, not defects)

Tracked in `METHODOLOGY_DISCREPANCIES.md`:

- **01-7** — Phase 3/4 folder-name taxonomy (three competing schemes).
- **02-1 / H-1** — the 25 km buffer: add to Phase 01's buffer set, or treat as a methodology artefact.

---

## Resume bullet points

Pick the 3–5 that fit the role; quantities reflect the current build (Phases 00–02, v0.2.0).

### Headline / summary
- Designed and built a **config-driven geospatial data pipeline** (Python, GDAL/rasterio,
  GeoPandas, pydantic v2) automating a 12-phase mineral-exploration workflow over **79 raw
  geospatial inputs** across 7 evidence groups — from raw-data integrity through remote-sensing
  preprocessing.

### Engineering / architecture
- Architected a **phase-gated pipeline framework** (uniform `Phase` interface, ordered runner,
  per-phase QA/QC logs, go/no-go **decision gates**, dry-run scaffolding) so 12 workflow phases
  plug in behind one contract; shipped **3 phases end-to-end** with the rest as enforced stubs.
- Encoded domain invariants **in code rather than docs** — a read-only raw-data guard with
  **SHA-256 integrity baselines re-verified every run**, automatic GIS sidecar bundling, and CRS
  provenance tracking — eliminating an entire class of data-corruption and traceability defects.
- Built the remote-sensing stage end-to-end: **clip → reproject (EPSG:32647) → Cloud-Optimized
  GeoTIFF**, producing **30 validated COGs and 20 DEM terrain derivatives** per run with graceful
  AOI no-overlap handling.

### Algorithms / GIS
- Implemented **DEM terrain analytics in pure NumPy** — Horn hillshade/slope/aspect,
  Riley Terrain Ruggedness Index, Zevenbergen–Thorne curvature, and D8 flow accumulation —
  avoiding heavy native dependencies while keeping outputs reproducible.
- Wrote the COG writer to rebuild a clean raster profile per derivative, preventing
  compression/predictor leakage, and a COG validator that is correct for sub-blocksize rasters.

### Quality / tooling
- Stood up a full CI quality bar — **ruff, ruff-format, mypy, and pyright (0 type errors)** plus
  **72 pytest cases on synthetic fixtures** (no real data required) across Python 3.11/3.12 —
  keeping the build green and type-clean.
- Solved Windows production constraints: a **MAX_PATH (260-char) pre-flight** that fails real runs
  early, and short-path/junction output roots, so deep methodology folder trees don't break GDAL I/O.

### Data engineering / domain
- Designed a **storage-agnostic ingest layer** (local / Drive / GCS by config) pinning each input
  to a canonical Drive file ID + size to defeat duplication and wrong-project/CRS hazards across a
  ~700 GB workspace; authored the supporting **ADR**.
- Reconciled a 78-input methodology specification against the real archive, **documenting every
  discrepancy and its resolution** in a traceable register, and enforced the geoscience evidence
  hierarchy (remote sensing = *support*, never ore proof) in generated metadata.

---

*Inspection performed 2026-06-27; the five findings were resolved the same day via the
`phase02-cleanup` multi-agent workflow and re-verified against all gates (ruff, format, mypy,
pyright, pytest).*
