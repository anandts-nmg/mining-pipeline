# ADR 0001 — Raw data storage & ingest strategy

- **Status:** Accepted (2026-06-23)
- **Context owner:** anandts-nmg
- **Related:** `DRIVE_MAP.md`, `config/raw_manifest.csv`, `METHODOLOGY_DISCREPANCIES.md`, `CLAUDE.md`

## Context

The exploration data lives in a Google Drive mine-lifecycle workspace, ~700 GB total and
growing daily. Inspection (metadata-only) established:

- The **canonical raw archive** (`0. Raw Data`, 79 inputs = 78 methodology + the reconciled SAS
  hand-interpreted 1:25k scan) is only **~1.8 GiB** — it fits locally.
- The **700 GB is the drone survey** (`5. Drone`, daily LiDAR/orthophoto flights) = methodology
  **Phase 05**, irrelevant to Phases 00–04.
- The wider drive has heavy **duplication** and even **other licences** (XV-022905, L08718) and a
  stray EPSG:32649 boundary — so identity must be pinned, not name-matched.
- Drive for Desktop streams on demand: **opening file content hydrates the whole file**, so a
  bulk local sync is infeasible and unnecessary. The connector exposes size but **not md5**.

## Decision

1. **Do not adopt AWS S3, and do not adopt any object store now.** The data is Google-native;
   S3 would add a second cloud, cross-cloud auth, and 700 GB of egress for no benefit.
2. **Local-first for Phases 00–01 (and 02).** The canonical ~1.8 GiB set is ingested locally;
   nothing cloud is required to run the implemented phases.
3. **Keep the pipeline storage-agnostic.** `paths.raw_root` plus a new manifest/ingest layer
   abstracts the source so it can be `local | drive | gcs` by config, not code change.
4. **Pin identity by Drive file ID** via `config/raw_manifest.csv` (register № → file ID + size
   + theme folder). This is the authoritative ingest source — it defeats duplication and the
   wrong-project/CRS hazards. Scope strictly to `0. Raw Data`.
5. **Integrity = size + locally-computed SHA-256** on materialised files (md5 unavailable from
   the connector); per-run quick check uses size (+ mtime). Phase 00's SHA-256 baseline is
   computed only on files actually pulled local.
6. **Tiered materialisation with a cache budget.** Copy the small files (KMZ, sidecars, tables,
   scans); reference the few big rasters (KOMPSAT/Sentinel/Google/ASTER ~1.5 GiB) on demand;
   Phase 02 reads them AOI-windowed and writes COGs. Never duplicate raw into the output tree.
7. **The drone 700 GB stays in Drive.** It is processed by its own software per-flight; the
   pipeline ingests and QA/QCs only the *deliverables* (orthomosaic/DTM/point-cloud), by date.
   No full sync, ever.
8. **If we ever outgrow local processing, use GCS — not S3.** Google-native, server-side
   Drive→GCS transfer (not via a workstation), GDAL `/vsigs/` range reads. Because of (3) this
   is a config change.

## Consequences

- **+** Phases 00–01 are unblocked today on <2 GiB; the storage problem is decoupled from the pipeline.
- **+** Duplication, mixed-project, and CRS-drift hazards are eliminated by file-ID pinning.
- **+** No new cloud spend or migration; the team's Google ecosystem is preserved.
- **−** No md5 from Drive → first local SHA-256 baseline requires pulling the ~1.5 GiB of big
  rasters once (one-time, acceptable).
- **−** A new ingest layer (`core/ingest.py` + manifest support in Phase 00) must be built; until
  then, runs require a local copy of `0. Raw Data` (or a Drive-synced path) at `raw_root`.
- **Resolved:** the 79th input (SAS hand-interpreted 1:25k scan) is in the register (79 rows); the BMP-as-`.jpg`
  MUGZ tectonic files are characterized — 4 files in folder 11, confirmed BMP (magic `42 4d`) and SHA-256-verified
  as 4 *distinct* pages, so read them as BMP on the Phase-03 working copy. **Open follow-up:** locate/flag the
  missing KOMPSAT EULA (#23, absent from the archive). See `REGISTER_RECONCILIATION.md` for the full reconciliation.
