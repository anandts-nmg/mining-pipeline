# Register Reconciliation — `input_register.csv` vs the real archive

**Date:** 2026-06-30 · Metadata-only (no full re-hash; targeted SHA-256 on small files where needed).

**Sources:** the real `0. Raw Data` archive (79 files across 11 thematic folders, via Drive for Desktop)
· the DataRoom **`MasterRegister_79Inputs_v01.docx`** (authoritative) · `config/input_register.csv` ·
`config/raw_manifest.csv`.

## Verdict: the register is sound — **0 changes needed**

- **78 / 79 filenames are exact, verbatim matches** to the real archive. **0 typos/renames**, **0 unexplained
  extras**. The single non-match is the KOMPSAT EULA (#23), which is a **known absence** already flagged in
  `raw_manifest.csv` as `MISSING_in_0_Raw_Data`.
- `filename` / `evidence_group` / `is_sidecar` agree **100 %** with `raw_manifest.csv` (0 mismatches).
- The **7 evidence-groups ↔ 11 archive folders** mapping is clean — every group label is correct.

**On the 7-vs-11 taxonomy:** keep the 7 groups. The Master Register `.docx` is itself a compilation of **7
thematic source DOCXs** (= the 7 evidence groups), so the register's taxonomy *is* the authoritative one; the
11 physical folders are just storage. Ingest matches by basename, so the layouts are already decoupled. No
reorganization warranted.

## Group mapping (register 7 ↔ archive 11)

| Register evidence-group (count) | Archive folder(s) (count) |
|---|---|
| 01_Tectonic_Terrane_KMZ (8) | 11_Tectonic (7) + 01_License_boundary (1) |
| 02_DEM_ALOS_ASTERGDEM (14) | 10_DEM_Topography_and_Terrain (14) |
| 03_KOMPSAT2_MSC_L1G (24) | 23 KOMPSAT files in 09_Remote_Sensing + 1 EULA (absent) |
| 04_HeavyMineral_StreamSediment_Field (6) | 06_Geochemistry (4) + 08_Field_Observation (2) |
| 05_Geology_Mineral_Prospectivity (17) | 02_Regional_Geology (2) + 03_Detailed_Geology (3, incl. SAS #79) + 04_Mineral_Occurrences (7) + 07_Metallogeny_Prospectivity (5) |
| 06_Regional_Metallogenic_L47B (4) | 05_Regional_Metallogeny (5) − 1 dup Metallogenogram |
| 07_Basemap_Sentinel2_ASTER (6) | 6 non-KOMPSAT files in 09_Remote_Sensing (ASTER HDF, 3 Sentinel-2 tif, 2 Google basemaps) |

> The archive's 11 folders sum to 79 physical files, and the register sums to 79 inputs — but these two "79"s
> coincide via offset: the archive **+1** (a byte-duplicate Metallogenogram in two folders) and **−1** (the EULA
> absent). Not contradictory; just don't conflate them.

## Data issues (none require a register edit; triaged with SHA-256)

| # | Item | Finding | Severity | Action |
|---|---|---|---|---|
| 1 | **#56 size mismatch** | `raw_manifest` pins 1,898,113 B; on disk 2,281,723 B (same size as #53). **SHA-256 proves #56 ≠ #53** (`6e6e…` vs `b689…`) → **not a content swap**, just a coincidental size. | Low | Update `raw_manifest.csv` `#56 drive_size_bytes → 2281723` (stale pin). No register change. |
| 2 | **MUGZ500 #3–#6** | Confirmed **BMP** (magic `42 4d`) mislabelled `.jpg`; **SHA-256 confirms 4 distinct pages** (not copies). | Low | Treat as BMP on the **working copy** in Phase 03 (raw is read-only). Resolves the open ADR-0001 follow-up. |
| 3 | **#23 KOMPSAT EULA** | Absent from the archive; `raw_manifest` already marks `MISSING_in_0_Raw_Data`. Master Register spells it with spaces (`KOMPSAT EULA Form_3.1.pdf`) vs the register's spaceless form. | Known gap | Keep the row; reconcile spacing **if/when** the file is synced. Procurement/sync item. |
| 4 | **#61 Metallogenogram** | Byte-identical (7,759,874 B) in archive folders 05 **and** 07. Register correctly lists it **once** (group 05); manifest pins folder 07. | Low | No register change. Treat the folder-07 copy as canonical; note the redundant 05 copy. |
| 5 | **#79 SAS scan** | Exact filename match (archive + SAS docx). Not in the Master Register's 7 tables (those total 78); defined in the separate SAS docx and folded into group 05. | Resolved | No change — matches the `78 + SAS = 79` accounting in CLAUDE.md. |

## SHA-256 evidence (the targeted checks)

```
#53  1987_..._GeologicalMap_1-200000_..._raw-scan.jpg            b6895275ab73a155...  (2,281,723 B)
#56  2013_..._GeologicalMap_Legend_1-50000_..._raw-scan.jpg      6e6eb583e76ae908...  (2,281,723 B)  -> DIFFERENT => no swap

MUGZ500 ... Page11   2a290709b9a6a981...
MUGZ500 ... Page08   9c05be414d4630c0...   } 4 distinct hashes => 4 distinct pages
MUGZ500 ... Page09   55e66748b8593a51...
MUGZ500 ... Page10   73fcd5484c18ad68...
```

## Recommendation

- **No edits to `input_register.csv`** — it is validated against reality.
- Applied: `raw_manifest.csv` `#56 drive_size_bytes` corrected to `2281723` (verified on disk; commit `b17d3e2`).
- Phase 03 should read inputs #3–#6 as **BMP** on the working copy (extension says `.jpg`).
- The remaining items (#23 EULA spacing, #61 canonical copy) resolve when the archive is fully synced/curated.
