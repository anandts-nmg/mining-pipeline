# Drive Data Map — XV-023222 / Buduunkhad

Where the real exploration data lives in Google Drive, how it maps to this pipeline,
and the size reality. Built **metadata-only (no downloads)** via the claude.ai Google
Drive connector on 2026-06-23. The authoritative per-file pin is `config/raw_manifest.csv`.

## TL;DR

- The linked top folder **"Buduun khad"** (`1nI4h-aYwG003HxmMIuJnGXFWwLvAVyoL`) is the whole
  **mine-lifecycle workspace**, not a clean input archive.
- The **canonical raw archive** is `… / 1. Exploration Stage / 1. Geological Data Acquisition /
  0. Raw Data` (`1EhF1o7ilDD8f-u73-fUHO5EXnEjkvlDP`) — holds **78 of the 79 registered inputs**
  (the KOMPSAT EULA is absent) in **11 geology themes**.
- **The canonical raw set is ~1.8 GiB total** — it fits on a laptop. Phases 00–01 do not
  need cloud storage.
- **The 700 GB is the drone survey** (`5. Drone`, daily LiDAR/ortho flights, still growing) —
  that's methodology **Phase 05** and never needs to enter Phases 00–01.
- Heavy **duplication** inflates the wider drive (KOMPSAT PAN 699 MB copied ≥3×, license
  boundary gpkg ×40+); other licences (XV-022905, L08718 Suujiin Bulag) and a stray
  EPSG:32649 boundary also live in the drive — so we **pin file IDs**, never match by name.
- **Verified end-to-end:** Phases 00–01 ran **go/go on this real data** (tag `v0.1.0`) — 78 files
  checksummed, boundary → EPSG:32647 + 5 buffers, 13-layer master GeoPackage; the EULA gap was
  recorded (not fatal).

## Structure (Exploration Stage)

```
Buduun khad/
└─ 1. Exploration Stage/
   ├─ 1. Geological Data Acquisition/
   │   ├─ 0. Raw Data/                ★ CANONICAL ARCHIVE (~1.8 GiB)  id 1EhF1o7ilDD8f-u73-fUHO5EXnEjkvlDP
   │   │   ├─ 01_License_boundary … 11_Tectonic_and_Terrane_Framework   (11 theme folders)
   │   │   │     └─ 09_Remote_Sensing/ → 9.1 Aster · 9.2 Sentinel-2 · 9.3 Google Maps · 9.4 Kompsat2
   │   │   └─ XV023222_..._DataRoom_v01/   (register DOCX + a curated 9-section "ideal" tree)
   │   ├─ 0.1 Processed data/          (mirrors 09_Remote_Sensing — DUPLICATES)
   │   ├─ 1. Mapping & Sampling/       (LIVE 2026 field campaign: QField, pXRF, sampling sheets)
   │   ├─ 2. Geophysics · 3. Geochemistry · 4. Drilling · 7. Laboratory
   │   └─ 5. Drone/                    ★ THE 700 GB — 1. Raw data / 2. Processed, daily flights 2026-05-24→…
   ├─ 2. Geological Data Management   ├─ 3. Interpretation & Modeling   ├─ 4. Resource Definition
   ├─ 5. Metallurgy-Geotech-Hydro     ├─ 6. Exploration Reporting       └─ 7. Project Management
```
(The 6 non-acquisition Exploration-Stage folders were mapped at the top level only.)

## Canonical size census (78 files present in `0. Raw Data`; the EULA #23 is absent)

| Theme | Files | Size |
|---|--:|--:|
| 01_License_boundary | 1 | 0.0 MiB |
| 02_Regional_Geology_1_200K | 2 | 6.4 MiB |
| 03_Detialed_Geology_1_50K (+Hand_Interpreted) | 3 | 14.8 MiB |
| 04_Mineral_Occurrences_and_Resources | 7 | 45.0 MiB |
| 05_Regional_Metallogeny | 4 | 41.3 MiB |
| 06_Geochemistry_and_Heavy_Mineral_Sampling | 4 | 4.6 MiB |
| 07_Metallogeny_and_Prospectivity | 5 | 71.2 MiB |
| 08_Field_Observation_and_Routes | 2 | 42.2 MiB |
| 09_Remote_Sensing (ASTER/Sentinel/Google/KOMPSAT) | 29 | **1548.5 MiB** |
| 10_DEM_Topography_and_Terrain | 14 | 58.0 MiB |
| 11_Tectonic_and_Terrane_Framework | 7 | 11.1 MiB |
| **TOTAL** | **78** | **~1.80 GiB** |

Largest single files: KOMPSAT PAN 699 MB · ASTER HDF 124 MB · Sentinel rasters ~100–116 MB ·
Google basemaps 185 MB (0.15 m) + 105 MB (2.4 m). Everything else is small scans/DEM/sidecars.

## Pipeline 7 evidence groups ↔ real 11 themes

| Pipeline `evidence_group` | Real `0. Raw Data` theme folder(s) |
|---|---|
| 01_Tectonic_Terrane_KMZ (8) | `01_License_boundary` (1) + `11_Tectonic_and_Terrane_Framework` (7) |
| 02_DEM_ALOS_ASTERGDEM (14) | `10_DEM_Topography_and_Terrain` (14) |
| 03_KOMPSAT2_MSC_L1G (24) | `09…/9.4 Kompsat2` (23) — **EULA pdf absent** |
| 04_HeavyMineral_StreamSediment_Field (6) | `06_Geochemistry…` (4) + `08_Field_Observation…` (2) |
| 05_Geology_Mineral_Prospectivity (16) | `02_Regional_Geology` + `03_Detailed_Geology` + `04_Mineral_Occurrences` + `07_Metallogeny_Prospectivity` |
| 06_Regional_Metallogenic_L47B (4) | `05_Regional_Metallogeny` (4) |
| 07_Basemap_Sentinel2_ASTER (6) | `09…/9.1 Aster (2) + 9.2 Sentinel (2) + 9.3 Google (2)` |

## Reconciliation results (see `config/raw_manifest.csv`)

- The register holds **79 inputs**; **78 of 79 are present** in `0. Raw Data` and matched to a
  canonical Drive file ID, **size-verified (0 mismatches)**.
- **1 missing:** `#23 KOMPSATEULAForm_3.1.pdf` (KOMPSAT licence/EULA — provenance only). Recorded
  as an **acknowledged data gap** — it is logged and flows to the data-gap register, and does
  **not** block the run.
- The **SAS hand-interpreted 1:25k scan** (`XV023222_Buduunkhad_SAS_HandInterpreted_GeologyMap_1-25000_RawScan_v01.jpg`)
  was in the archive but not in the original 78; it is now **input #79** in the register
  (the DataRoom register is titled "…79Inputs").
- Note: a few `…MUGZ500…Page*.jpg` tectonic files are actually **BMP** payloads with a `.jpg`
  extension (confirm reader handling in Phase 02/03).

## Reading the data without filling the disk

- Metadata (names/sizes/IDs) is free via the connector; **content access hydrates the file**
  (Drive for Desktop) — so never bulk-sync. Ingest is **manifest/file-ID driven**: pull the
  small files, reference the few big rasters on demand (AOI-windowed in Phase 02).
- See the storage decision in `docs/adr/0001-raw-data-storage-and-ingest.md`.

---
*Generated metadata-only via the Google Drive connector, 2026-06-23. The master methodology
remains the source of truth per `CLAUDE.md`; see `METHODOLOGY_DISCREPANCIES.md` for the
7-group vs 11-theme reconciliation context.*
