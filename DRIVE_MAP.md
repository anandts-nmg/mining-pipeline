# Drive Data Map — XV-023222 / Buduunkhad

Where the real exploration data lives in Google Drive, how it maps to this pipeline,
and the size reality. Built **metadata-only (no downloads)** via the claude.ai Google
Drive connector on 2026-06-23. The authoritative per-file pin is `config/raw_manifest.csv`.

## TL;DR

- The linked top folder **"Buduun khad"** (`1nI4h-aYwG003HxmMIuJnGXFWwLvAVyoL`) is the whole
  **mine-lifecycle workspace**, not a clean input archive.
- The **canonical raw archive** is `… / 1. Exploration Stage / 1. Geological Data Acquisition /
  0. Raw Data` (`1EhF1o7ilDD8f-u73-fUHO5EXnEjkvlDP`) — ~78 inputs in **11 geology themes**.
- **The canonical raw set is ~1.8 GiB total** — it fits on a laptop. Phases 00–01 do not
  need cloud storage.
- **The 700 GB is the drone survey** (`5. Drone`, daily LiDAR/ortho flights, still growing) —
  that's methodology **Phase 05** and never needs to enter Phases 00–01.
- Heavy **duplication** inflates the wider drive (KOMPSAT PAN 699 MB copied ≥3×, license
  boundary gpkg ×40+); other licences (XV-022905, L08718 Suujiin Bulag) and a stray
  EPSG:32649 boundary also live in the drive — so we **pin file IDs**, never match by name.

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

## Canonical size census (the 78-input set in `0. Raw Data`)

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

- **77 / 78** register inputs matched to a canonical Drive file ID.
- **1 MISSING** from `0. Raw Data`: `#23 KOMPSATEULAForm_3.1.pdf` (KOMPSAT licence/EULA — provenance only).
- **1 EXTRA** present in Drive, not in the register: `XV023222_Buduunkhad_SAS_HandInterpreted_GeologyMap_1-25000_RawScan_v01.jpg`
  → this is the **79th input** (the DataRoom register is titled "…79Inputs"). Add to register as a Phase-03 hand-interpreted geology scan.
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
