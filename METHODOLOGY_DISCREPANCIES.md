# Methodology Document Discrepancies — XV-023222 / Buduunkhad

This note records where the two methodology PDFs in the repo root **disagree with each
other**, focused on the phases the pipeline implements end-to-end (**Phase 00** and
**Phase 01**). It also records what the code currently implements, for reference.

> Per `CLAUDE.md`, the **master methodology document is the ultimate source of truth.**
> Where the two PDFs conflict, the code generally follows the master. The open items at
> the end are documentation-reconciliation decisions, not code bugs.

## Sources

| Ref | File (repo root) | Scope | Notes |
|-----|------------------|-------|-------|
| **Doc A** (master) | `XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v6_Phasewise_File_Processing_Output_Matrix.docx.pdf` | Phases 00–99 (+ Section 1A file→phase matrix, 03A deposit model, Appendix E) | 83 pp. Filename says **v6**; body self-identifies as **v5** ("Explicit Input File Mapped") with a v2–v4 lineage. |
| **Doc B** (standalone) | `XV-023222_Buduunkhad_Phase1_Methodology.docx.pdf` | **Phase 1 only**, QGIS-focused | 16 pp. Reads as a later, separately-authored deep-dive that was **not reconciled back** into Doc A; it even references "existing 11 (or 12) thematic folders" on disk. |

Both agree on the project constants (license **XV-023222 / L23222**, CRS **EPSG:32647**,
the **7 evidence groups**, buffers **500 m / 1 / 5 / 10 / 20 km**, and the confidence
vocabulary **High / Medium / Low / Needs verification**). The disagreements below are about
**structure, ownership of work, deliverables, and naming**.

---

## Phase 00 — Raw Files Archive

**Coverage:** Only **Doc A** defines a Phase 00. **Doc B has no Phase 00 at all** — it folds
raw preservation, checksums, working-copy creation and the file inventory into **Phase 1,
Step 1** ("Raw archive хамгаалах ба working copy үүсгэх", incl. "SHA-256 / checksum
бүртгэх"). So the discrepancy here is primarily *structural*: the master separates raw
archiving from data audit; the standalone merges them.

| # | Topic | Doc A (master) | Doc B (standalone) |
|---|-------|----------------|--------------------|
| 00-1 | **Phase exists?** | Dedicated **Phase 00** with its own decision gate | **No Phase 00**; the work lives in Phase 1, Step 1 |
| 00-2 | **Raw folder name** | `00_Raw_Files_Archive` | `00_Raw_Input_Evidence_Library` (framed as the read-only "Input Evidence Library") |
| 00-3 | **Checksum / inventory ownership** | Phase 00 outputs: `..._78Input_Master_Inventory.xlsx`, `..._Raw_Data_Integrity_Log.xlsx`, `SHA-256_Checksum_Register.csv`, `..._Source_Data_Readme.docx` | Same work appears as **Phase 1 Day-1** deliverables (`..._Phase1_File_Inventory.xlsx` + a checksum register) |

Both agree the 7 evidence-group subfolders are identical (`01_Tectonic_Terrane_KMZ` …
`07_Basemap_Sentinel2_ASTER`) — only the **parent folder name** (00-2) conflicts.

**Code status:** implements a dedicated **Phase 00** per Doc A — folder `00_Raw_Files_Archive`,
all 4 outputs verbatim, QA/QC items (Checksum match · Raw overwrite not done · Sidecar
completeness · Source note+owner), and the gate wording — an **exact match to Doc A**.

---

## Phase 01 — Data Audit & Master GIS Setup

Both docs cover Phase 1, and this is where they diverge most.

### Genuine conflicts (same thing, different answer)

**01-1 — Internal folder taxonomy** (different *organizing principle*, not just renames):

| Doc A (master) | Doc B (standalone) |
|----------------|--------------------|
| `01_File_Inventory` | `00_Admin_and_Method` |
| `02_Metadata_Check` | `01_Input_Working_Copy` |
| `03_CRS_Check` | `02_Inventory_and_Metadata` |
| `04_Raster_Scan_Georeference_QAQC` | `03_CRS_Check` |
| `05_KMZ_KML_to_GPKG` | `04_Georeference_Check` |
| `06_Master_GeoPackage_Schema` | `05_Master_GIS_Database` |
| `07_Data_Confidence_Ranking` | `06_QAQC_and_Confidence` |
| `08_Master_QGIS_Project_Setup` | `07_Output` |

**01-2 — Where the Master GPKG / QGIS project live** (consequence of 01-1):
- Doc A: `.gpkg` → `06_Master_GeoPackage_Schema`; `.qgz` → `08_Master_QGIS_Project_Setup`.
- Doc B: both → `05_Master_GIS_Database` (with a `Styles_QML/` subfolder Doc A never mentions).

**01-3 — Expected-output count:**
- Doc A lists **4** outputs: `Master_GIS_Database.gpkg`, `Master_QGIS_Project.qgz`,
  `CRS_Georeference_QAQC_Log.xlsx`, `Data_Confidence_Ranking.xlsx`.
- Doc B lists **8** — those 4 plus `Phase1_File_Inventory.xlsx`, `Data_Gap_Register.xlsx`,
  `Phase1_Master_GIS_Index_Map.pdf`, `Phase1_Desktop_Study_Summary.docx`.
- Doc B also adds admin files Doc A never lists: `Phase1_Action_Log.xlsx`,
  `Phase1_QAQC_Checklist.xlsx`.

**01-4 — Inventory schema & record ID scheme:**
- Doc A (Phase 00 step 2): filename, standardized name, file type, source note, owner,
  read/copy status; records keyed by raw input **№ 1–78**.
- Doc B (Step/Алхам 2): richer columns (File_ID, Spatial_Type, Has_CRS / Native_CRS,
  Has_Georeference, Sidecar_Files, Open_Status, Main_Use, Confidence …) and a different ID
  convention **`BK-P1-001`** instead of № 1–78.

**01-5 — Master GeoPackage contents (schema vs grouping):**
- Doc A enumerates **13 named layers** (`license_boundary`, `geology_units_polygon`,
  `faults_structures_line`, `intrusive_contacts_line`, `mineral_occurrences_point`,
  `stream_sediment_anomaly_polygon`, `heavy_mineral_anomaly_polygon`,
  `lineament_interpretation_line`, `preliminary_prospect_polygon`, `target_polygon`,
  `field_observation_point`, `sample_point`, `pXRF_reading_table`) but no internal grouping.
- Doc B describes a **4-group organization** (`01_Rasters / 02_Vectors / 03_Metadata /
  04_QAQC`) but never lists the 13 specific layers.
- Each omits what the other specifies (not strictly contradictory, but unaligned).

**01-6 — Buffer-creation ownership:**
- Doc B makes the 500 m–20 km buffers an explicit **Phase 1** step (Алхам 5, with named layers).
- Doc A's Phase 01 step list **does not mention buffers** — they appear only as the № 8
  register action and as a Phase 3 (CMCS) input. The docs disagree on which phase owns them.

**01-7 — Downstream phase folder names** (referenced in Doc B's top-level tree):
- Phase 3: `…_Geological_Metallogenic_and_CMCS_Synthesis` (A) vs `…_Geological_Metallogenic_Synthesis` (B).
- Phase 4: `…_Preliminary_Prospect_Delineation_and_Ranking` (A) vs `…_Preliminary_Prospect_Ranking` (B).

### Differences in scope/emphasis (additions, not contradictions)

- **Doc B only:** a Day 1–5 work schedule; a detailed scan-georeference priority table
  (1:50k → 200k → 500k; Polynomial 1 → Thin Plate Spline; RMSE/residual handling) — which
  **Doc A defers to Appendix E**; and an explicit "Sentinel-2 T46 tile may be UTM46N
  (EPSG:32646) → reproject" caution in Phase 1 (Doc A assigns the actual reprojection to Phase 2).
- **Doc A only:** the full 00–99 context, the 13-layer GPKG schema, Section 1A file→phase
  assignment matrix, the 03A deposit-model sub-workflow, and Appendix E.

**Code status:** the implementation sides with **Doc A** on structure (folder names 01–08,
the 13-layer schema, the 5 QA/QC items, and the gate wording) and with **Doc B** on the
richer deliverable set (it additionally emits the inventory, data-gap register, index map and
desktop-study summary via an added `09_Handover_Package` folder — a folder present in neither
PDF). It generates the buffers (per Doc B / the № 8 register action).

---

## Top-level project tree (cross-cutting)

| Item | Doc A (master) | Doc B (standalone) |
|------|----------------|--------------------|
| Project root | (implied) | `XV-023222_Buduunkhad_Project/` |
| Raw archive | `00_Raw_Files_Archive` | `00_Raw_Input_Evidence_Library` |
| Phase list shown | 00–11, 99 (full) | 00, 01, 02, 03, 04, 99 (abbreviated) |

---

## Open decisions (documentation reconciliation)

1. **Which Phase-1 folder taxonomy is canonical** — Doc A's `01_File_Inventory … 08_…`
   (what the code builds) or Doc B's `00_Admin_and_Method … 07_Output`? (See 01-1.)
2. **Raw archive folder name** — `00_Raw_Files_Archive` (A / code) vs
   `00_Raw_Input_Evidence_Library` (B)? (See 00-2.)
3. **Inventory record ID scheme** — № 1–78 (A / code) vs `BK-P1-xxx` (B)? (See 01-4.)
4. **Buffer ownership** — keep buffers in Phase 1 explicitly (B / code), or treat as a № 8
   register action only (A)? (See 01-6.)
5. **Phase 3 / Phase 4 folder names** — adopt the longer A names (code) or the shorter B
   names? (See 01-7.)

If the rule is simply "the master (Doc A) always wins," items 1, 2, 3, 5 resolve in favour of
the current code; only the standalone PDF would need a note that it is superseded for folder
structure. If Doc B is meant to govern Phase 1 specifically, `core/paths.PHASE01_SUBFOLDERS`
and the inventory ID scheme would need to change.

---

*Generated from analysis of the two repo-root methodology PDFs and the `src/buduunkhad` +
`config/` implementation on 2026-06-23. The master methodology remains the stated source of
truth per `CLAUDE.md`.*
