# Methodology Document Discrepancies — XV-023222 / Buduunkhad

This note records where the methodology documents **disagree with each other**, focused on
the phases the pipeline implements end-to-end (**Phase 00**, **Phase 01** and **Phase 02**).
It also records what the code currently implements, for reference.

> Per `CLAUDE.md`, the **master methodology document is the ultimate source of truth.**
> Where the sources conflict, the code follows the master. **The Phase 0–2 conflicts are now
> resolved & implemented** — see "Resolutions" below (verified at tags `v0.1.0` / `v0.2.0` / `v0.2.1`);
> only later-phase / documentation items (KOMPSAT EULA, BMP-as-`.jpg`) remain open.

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

## At a glance — count & status

**15 explicitly-numbered conflicts** (Phase 00: 3 · Phase 01: 7 · Phase 02: 2 · Phase 03: 3), plus ~4
doc-vs-reality reconciliations and 1 intra-document version drift. **All 15 are resolved (by decision)** —
01-7 and 02-1 / H-1 were decided 2026-06-30; the Phase-03 items (03-1/2/3 + handoff H-4) were decided
2026-07-01 during Phase-3 planning (`PHASE_03_PLAN.md`). Phase 03 module implementation is pending.

| Group | Comparison | IDs | Resolved | Open |
|---|---|---|---|---|
| Phase 00 | master Doc A vs Phase-1 doc (Doc B) | 00-1, 00-2, 00-3 | 00-1, 00-2, 00-3 | — |
| Phase 01 | master Doc A vs Phase-1 doc (Doc B) | 01-1 … 01-7 | 01-1 … 01-7 | — |
| Phase 02 | master Doc A vs `docs/phase_02` guides | 02-1, 02-2 | 02-1, 02-2 | — |
| Phase 03 | master Doc A §03 vs Phase-3 QGIS guide | 03-1, 03-2, 03-3 | 03-1, 03-2, 03-3 | — |
| Phase 01 ↔ 02 | inter-phase handoff | H-1, H-2, H-3 | H-1, H-2, H-3 | — |
| Phase 02 ↔ 03 | inter-phase handoff | H-4 (ASTER/KOMPSAT support gap) | H-4 | — |
| Doc vs reality | docs vs the real Drive archive | 7/11/9 taxonomy · 78/79 · `0. Raw Data` name · #23 EULA | all reconciled | — |
| Intra-doc | Doc A filename vs body | v6-filename / v5-body | n/a (noted) | — |

## Why these discrepancies exist (root causes)

**The key point: none of these are scientific disagreements.** All sources agree on the actual
methodology — EPSG:32647, the 7 evidence groups, the 500 m–20 km buffers, the confidence
vocabulary. Every conflict is about **structure, naming and deliverable lists** — the signature
of *document-assembly drift*, not methodological uncertainty. Five causes:

1. **Layered authoring never merged back (dominant).** One master matrix (Doc A, phases 00–99)
   with *separate, later, operator-style QGIS deep-dives written on top of it* — Doc B for
   Phase 1, the four `docs/phase_02` guides for Phase 2. Each deep-dive re-invented its own
   folder tree, deliverable set and ID scheme because its author was writing a fresh guide, not
   editing the master. (Doc B even references "existing 11 (or 12) thematic folders" — written
   against the disk, not against Doc A.) → 00-1/2/3, 01-1/2/3, 02-1/2.
2. **Three competing folder taxonomies for the same 79 files** — the methodology's **7 evidence
   groups**, the Drive archive's **11 themes**, and a **9-section DataRoom** — plus three names
   for the raw archive (`00_Raw_Files_Archive` / `00_Raw_Input_Evidence_Library` / `0. Raw Data`).
   → the folder-name / grouping conflicts.
3. **Doc-vs-disk count drift.** The methodology says **78** inputs; the disk has a **79th** (the
   SAS hand-interpreted 1:25k scan) never added to the master. → 78-vs-79.
4. **Coarse matrix vs fine operator detail.** Doc A lists outputs at a high level; the deep-dives
   enumerate every intermediate product. The "deliverable count" conflicts are granularity, not
   contradiction. → 01-3, the Phase-2 output-coverage note.
5. **Inconsistent versioning inside the master itself** — Doc A's filename says v6, its body says
   v5 with a v2–v4 lineage.

**Resolution rule applied throughout:** master methodology (Doc A) = source of truth for
structure / schema / gates; the later deep-dives are honoured as **supersets** (we also emit
their extra deliverables and follow their richer Phase-2 tree); physical reality is reconciled
by **filename + Drive file-ID** (`config/raw_manifest.csv`), never by folder name.

---

## Phase 00 — Raw Files Archive (master Doc A vs Phase-1 deep-dive Doc B)

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

## Phase 01 — Data Audit & Master GIS Setup (master Doc A vs Phase-1 deep-dive Doc B)

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

**Resolved 2026-06-30 — follow Doc A (the longer names).** `core/paths.py → PHASE_DIRS` already uses
Doc A's names (`03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis`,
`04_Phase_4_Preliminary_Prospect_Delineation_and_Ranking`), so this ratifies the status quo (no code
change). Rationale: Doc A is the authoritative 00–99 master; its folder names are load-bearing (later
handoffs reference them verbatim); and the longer names are more self-documenting (CMCS = deposit-model
synthesis; "Delineation and Ranking" = both Phase-4 steps). Doc B's short forms are not adopted, and the
standalone Phase-1 PDF is superseded for folder structure.

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

## Phase 02 — Remote Sensing Preprocessing (master Doc A vs the docs/phase_02 guides)

The four detailed QGIS-4.0.2 guides under `docs/phase_02/` (a later, deeper deep-dive, like
Doc B was for Phase 1) introduce two disagreements against the core methodology and Phase 01:

**02-1 — A 25 km buffer that no other source defines.** The Phase-2 master guide's
prerequisites list (§2.1) expects
`XV023222_Buduunkhad_Project_Buffer_500m_1km_5km_10km_20km_25km_EPSG32647.gpkg` — i.e. a **25 km**
ring in addition to the five. But both root methodology PDFs (Doc A / Doc B) state the buffers as
**500 m / 1 / 5 / 10 / 20 km** (no 25 km), and Phase 01 (`config/project.yaml → boundary.buffers_m`)
produced only those five. So the Phase-2 guide is the *only* source mentioning 25 km.

**Code status:** non-blocking. Phase 02's actual clips use the licence boundary and the 1 km / 5 km
buffers (DEM = 5 km, Sentinel = licence, basemap = 1 km), none of which need a 25 km ring, so Phase 02
runs go/go without it.

**Resolved 2026-06-30 — treat the 25 km as a documentation artefact (do not add it).** It is named in
exactly one source (the Phase-2 guide's prerequisite filename), contradicted by both root methodology
PDFs, consumed by no processing step, and breaks the 500 m→1→5→10→20 km pattern — i.e. a copy-paste slip,
not a deliberate ring. `boundary.buffers_m` stays `[500, 1000, 5000, 10000, 20000]`. **Add-on-demand:**
if a 25 km regional-context ring is ever genuinely wanted, it is a one-line config change + a Phase-01
re-run.

**02-2 — Phase-2 folder structure (Doc A vs the detailed guide).** Doc A's Phase 02 tree (master,
p.39) is **6 folders**: `01_Sentinel2_SNAP13 / 02_ASTER_Workflow_v5 / 03_KOMPSAT2_ILWIS368_QGIS /
04_ALOS_ASTERGDEM_GlobalMapper_QGIS / 05_RemoteSensing_QAQC / 06_Export_EPSG32647`. The detailed
guide (`docs/phase_02`, §3) adds `00_Input_Working_Copy` and a dedicated `05_Basemap_Google_HighRes`,
renumbering QA/QC→`06` and Export→`07` (8 folders, each with nested subfolders).
**Resolution:** follow the **detailed guide** (the more specific, later Phase-2 authority, like Doc B
was for Phase 1) — it is a superset that keeps every Doc A concept and gives Google basemaps their own
home (`config/.../phase02 custom_subfolders`). Mirrors the Phase-1 precedent (01-1) of honouring the
deep-dive's richer structure.

**Expected-output coverage vs Doc A (p.39).** Doc A lists `Terrain_Derivatives.gpkg` and
`RemoteSensing_QAQC_Report.docx` among Phase-2 outputs. The pipeline now emits a
`..._Terrain_Derivatives_Index.xlsx` (catalogues the derivative COGs) and the
`..._RemoteSensing_QAQC_Report.docx`; the *vector* terrain package (contour/drainage/watershed gpkg)
remains a method-note (SAGA/GRASS), and the Sentinel/ASTER/KOMPSAT processed products stay method-notes
(external tooling). All other Doc A Phase-2 outputs map to produced COGs or method notes.

The Phase-2 guides otherwise *agree* with the core methodology on the project constants, the
EPSG:32647 target, the support-evidence-only rule, and the per-sensor processing — the pipeline
implements their automatable core (clip → reproject → COG + DEM terrain derivatives) and emits
formula-complete method notes for the tool-bound Sentinel/ASTER/KOMPSAT steps.

---

## Phase 03 — Geological, Metallogenic & CMCS Synthesis (master Doc A §03 vs the Phase-3 QGIS guide)

The detailed Phase-3 QGIS guide (`docs/phase_03`, a later deep-dive like Doc B for Phase 1 and the
`docs/phase_02` guides for Phase 2) introduces three disagreements against Doc A §03. **None are scientific** —
both agree on the **#1-8 + #53-72** inputs, the **6 candidate deposit models**, the identical **100-pt scoring
rubric** and thresholds (≥70 / 50-69 / 30-49 / <30), the **CMCS 5/10/20 km** rings, and the **historical-only
support** framing. The conflicts are structure, folder labels and an ID scheme.

**03-1 — Phase-3 folder count (Doc A 9 vs guide 12).** Doc A §03 lists **9** subfolders
(`01_Tectonic_Terrane_Context … 09_Geological_Evidence_GPKG`, deposit model at
`07_Preliminary_Deposit_Model_Preparation`); the guide §03.3 lists **12**
(`01_Input_Working_Copy … 12_Phase3_QAQC_and_Handover`). The guide is a **finer superset**: adds
`01_Input_Working_Copy`, splits occurrence-QA/QC (07), scoring/data-gap (11) and QA/QC-handover (12) into their
own folders, and folds Doc A's standalone CMCS-screening folder into the buffer + evidence folders — every
Doc A concept is present. **Resolved 2026-07-01 — follow the guide's 12-folder superset** (same rule as
01-1 / 02-2), as `phase03 custom_subfolders` under Doc A's long name
`03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis`.

**03-2 — Deposit-model folder label.** Doc A's `07_Preliminary_Deposit_Model_Preparation` and the guide's
`10_Preliminary_Deposit_Model_03A` are the **same 03A sub-workflow**, different label. **Resolved 2026-07-01 —
use the guide's `10_Preliminary_Deposit_Model_03A`** (consistent with 03-1).

**03-3 — Feature-ID naming standard (Doc A defines it; the guide omits it).** Doc A **Appendix A** defines
Feature-ID prefixes — `geology_units_50k→BUD-GEO50`, `…_200k→BUD-GEO200`, `structures_faults→BUD-STR`,
`mineral_occurrences→BUD-MIN`, `prospectivity_target_zones→BUD-TGT`, `source_material_observation→BUD-OBS`,
`…_route→BUD-RTE`, `metallogenic_zones→BUD-MET`, `heavy_mineral_anomaly→BUD-HM-AN`,
`stream_sediment_anomaly→BUD-SS-AN`, `data_gap_register→BUD-GAP` — generated via
`concat('BUD-MIN-', lpad(@row_number,4,'0'))` (Appendix B); the guide names layers by filename only.
**Resolved 2026-07-01 — adopt the `BUD-…` scheme as a `feature_id` column, alongside the guide's 14 mandatory
provenance fields.** **Caveat:** the `BUD-STR-001` tokens elsewhere in the master are Phase-7/8 field **sample
IDs** (BUD-RC/CH/SOIL/STR/HM) — a different namespace, not these feature-ID prefixes. `BUD-HM-AN` / `BUD-SS-AN`
are reserved for Phase-8/9 anomaly layers (not digitized in Phase 3).

*(Non-conflicts: the inputs, the 6 models, the 100-pt rubric/thresholds, the CMCS rings and the support-only
framing all agree. Deliverable naming differs cosmetically — guide `v01`/`XV023222` data form vs Doc A
unversioned/`XV-023222` admin form — consistent with the repo's `core.naming` `data_name`/`register_name` split.)*

---

## Phase 01 ↔ Phase 02 handoff (what each expects from the other)

Phase 02 is the first phase that *consumes another phase's outputs*, so the sources also have to
agree on the **interface** between Phase 1 and Phase 2. What the Phase-2 guide (§2.1) expects to
already exist from Phase 1:

| Phase 02 expects from Phase 01 | Produced by Phase 01? | Where |
|---|---|---|
| Master GIS database (`Master_GIS_Database.gpkg`) | ✅ yes | `01_.../06_Master_GeoPackage_Schema` |
| Licence boundary (EPSG:32647 gpkg) | ✅ yes | `01_.../05_KMZ_KML_to_GPKG` |
| Project buffers gpkg | ⚠️ partial — 500 m–20 km, **no 25 km** (H-1) | `01_.../05_KMZ_KML_to_GPKG` |
| CRS / georeference QA/QC log | ✅ yes | `01_.../03_CRS_Check` |
| Data confidence ranking | ✅ yes | `01_.../07_Data_Confidence_Ranking` |
| Master QGIS project (`.qgz`) | ✅ yes | `01_.../08_Master_QGIS_Project_Setup` |

Three interface points (all resolved):

**H-1 — the 25 km buffer (= 02-1).** The Phase-2 guide's prerequisite filename includes a 25 km
ring; Phase 01 produced only 500 m–20 km. **Resolved 2026-06-30 — treated as a guide artefact (not
added)**, the same decision as 02-1 (not double-counted). Non-blocking (Phase 02 clips to licence /
1 km / 5 km only); `boundary.buffers_m` stays the five rings 500 m–20 km, add-on-demand if ever needed.

**H-2 — who reprojects the Sentinel UTM46N tile.** Doc B's *Phase 1* flags that the Sentinel
T46 tile may be UTM46N (EPSG:32646) and cautions to reproject; Doc A assigns the *actual*
reprojection to **Phase 2**. **Resolved:** the code reprojects in **Phase 2** (per Doc A) — Phase 1
only records the caution in its CRS audit. (Confirmed live: #77/#78 are 46N and Phase 02
reprojects them to 32647.)

**H-3 — buffer-creation ownership (= 01-6).** Doc A is silent on which phase builds the buffers;
Doc B puts it in Phase 1. **Resolved:** Phase 1 builds the 5 rings; Phase 2 consumes them as clip
AOIs (DEM = 5 km, Sentinel = licence, basemap = 1 km) — a clean producer→consumer handoff.

Everything else lines up: the AOIs Phase 02 clips to are exactly the layers Phase 01 writes, read
back by **filename via `core.naming`**, so the two phases agree on the names without hard-coding.

## Phase 02 ↔ Phase 03 handoff (03A remote-sensing support)

**H-4 — Sentinel/ASTER/KOMPSAT/DEM as 03A support, but ASTER/KOMPSAT are method-note-only from Phase 02.**
Both Doc A (03A.2) and the guide (Step-1 readiness) expect Phase 2's Sentinel/ASTER/KOMPSAT/DEM derivatives in
03A as **support evidence**. But Phase 02 emits ASTER (#73) and KOMPSAT (#24/28/32/36/40) as **method-note
only** — a note row, not a produced layer (RPC ortho / HDF extraction are external SNAP/ILWIS steps).
**Resolved 2026-07-01 — real but non-blocking; record in the data-gap register and proceed:** (a) all remote
sensing is support / "not ore proof"; (b) it is worth only **10/100 pts** in scoring, so an absent
ASTER/KOMPSAT layer cannot fail a threshold; and (c) the master handover table's Phase-3 required-layers row
lists only *geology, structures, metallogenic zones, occurrence context* — remote sensing is **not even a
required Phase-3 handover layer**. Phase 03 logs the gap in `Phase3_DataGap_and_Validation_Priority.xlsx`.

**Georeferencing straddle (links 01-7 / the open BMP item).** The guide's Step-1 readiness assumes Phase 01
already logged each scan's GCP/residual/scale/confidence, yet the guide **does the actual georeferencing
in-phase** (Steps 3-5: #70/#53/#57/#55); Doc A assigns georef ownership + the Georeferencer SOP to Phase 1
(Appendix E). **Resolution:** Phase 03 owns the actual georeferencing of the geology/metallogenic/
mineral-resources scans; the georef QA/QC log carries forward. This is where the **BMP-as-`.jpg`** MUGZ
tectonic files finally get characterized on georeferencing.

---

## Top-level project tree (cross-cutting)

| Item | Doc A (master) | Doc B (standalone) |
|------|----------------|--------------------|
| Project root | (implied) | `XV-023222_Buduunkhad_Project/` |
| Raw archive | `00_Raw_Files_Archive` | `00_Raw_Input_Evidence_Library` |
| Phase list shown | 00–11, 99 (full) | 00, 01, 02, 03, 04, 99 (abbreviated) |

---

## Resolutions (how each was decided & implemented)

### Phases 0–1 (verified at tag `v0.1.0`)

**Rule applied:** the **master methodology (Doc A) is the source of truth** for
structure / schema / naming / gates; the standalone PDF (Doc B) is honoured by *also*
producing its extra deliverables (a superset); and physical reality is reconciled via
`config/raw_manifest.csv` (by **filename + Drive file ID**, not folder name). Concretely:

| Discrepancy | What we chose for Phases 0–1 | Where |
|---|---|---|
| 00-2 raw-archive folder name | Output archive = Doc A's `00_Raw_Files_Archive`. The *input* `raw_root` points at the real on-disk folder, actually named **`0. Raw Data`** (a third name) — matched by **filename**, not folder name. | `core/paths.py`; `BUDUUNKHAD_RAW_ROOT` |
| 01-1 / 01-2 Phase-1 folder taxonomy | **Doc A** (`01_File_Inventory … 08_Master_QGIS_Project_Setup`) + an added `09_Handover_Package`. Doc B's tree is superseded. | `core/paths.PHASE01_SUBFOLDERS` |
| 7 groups vs 11 themes vs 9-section | Register keeps the methodology's **7 evidence groups**; the **manifest maps each input to its real 11-theme folder + file ID**. The DataRoom 9-section tree is informational only. | `input_register.csv` + `raw_manifest.csv` |
| 78 vs 79 inputs | **79** = 78 methodology + the reconciled **SAS hand-interpreted 1:25k** scan (#79). | register row 79; group 05 → 17 |
| #23 KOMPSAT EULA (absent) | Recorded as an **acknowledged data gap** — logged, flows to the data-gap register, does **not** block the run. | manifest `match_status`; pipeline tolerance |
| 01-3 deliverable count (4 vs 8) | **Superset** — Doc A's 4 core + Doc B's 4 extras + a Phase-2-ready list (11 artifacts). | Phase 01 outputs |
| 01-4 inventory ID scheme | Doc A's **№ 1–79** numbering (not Doc B's `BK-P1-xxx`). | `input_register.csv` |
| 01-5 master GPKG schema | Doc A's **13 named layers** (polygon layers written as MultiPolygon). | `project.yaml master_gpkg_layers` |
| 01-6 buffer ownership | Buffers built in **Phase 1** (per Doc B + the №8 register action) — 5 rings 500 m–20 km. | Phase 01 output |

**Net:** Phases 0–1 are master-methodology-faithful, also emit Doc B's deliverables, and ran
**go/go on the real data** (`v0.1.0`).

### Phase 02 (verified at tag `v0.2.0`)

Same rule — master = truth; the `docs/phase_02` guides honoured as the more-specific Phase-2
authority (as Doc B was for Phase 1):

| Discrepancy | What we chose for Phase 02 | Where |
|---|---|---|
| 02-2 folder structure (6 vs 8) | The guide's **8-folder** per-sensor tree (adds `00_Input_Working_Copy` + `05_Basemap_Google_HighRes`; QA/QC→06, Export→07) — a superset of Doc A's 6. | `phase02 custom_subfolders` |
| Expected outputs (Doc A p.39) | Emit `Terrain_Derivatives_Index.xlsx` + `RemoteSensing_QAQC_Report.docx`; the produced COGs cover the raster products. | Phase 02 outputs |
| KOMPSAT / ASTER-HDF / Sentinel indices | **Method-notes** (external SNAP/ILWIS/ortho tooling) — not faked; formulas captured. | `01_/02_/03_` method notes |
| Contour / drainage / watershed (vector) | **Method-note** (SAGA/GRASS); the raster terrain derivatives are automated. | `04_.../05_Drainage_Watershed` note |
| Per-product clip buffer | DEM = 5 km, Sentinel = licence, basemap = 1 km (per the guides). | `phase02_remote_sensing.py` |
| H-2 Sentinel 46N→47N | Reprojected in **Phase 2** (per Doc A). | `phase02` Sentinel path |

**Net:** Phase 02 is master-faithful + follows the Phase-2 guides, and ran **go/go on the real
data** — most recently `v0.2.1`, 00→02 end-to-end on the local archive.

### Phase 03 (planned — decided 2026-07-01; implementation pending)

Same rule — master = truth; the `docs/phase_03` guide honoured as the more-specific Phase-3 authority:

| Discrepancy | What we chose for Phase 03 | Where |
|---|---|---|
| 03-1 folder tree (9 vs 12) | The guide's **12-folder** superset (adds input-working-copy; splits occurrence-QAQC / scoring / QAQC-handover) — superset of Doc A's 9. | `phase03 custom_subfolders` (planned) |
| 03-2 deposit-model folder | The guide's `10_Preliminary_Deposit_Model_03A` (= Doc A's `07_…_Preparation`). | `phase03` folder tree |
| 03-3 feature-ID scheme | Adopt Doc A **Appendix A** `BUD-…` as a `feature_id` column + the guide's 14 provenance fields. | evidence-GPKG schema (planned) |
| H-4 ASTER/KOMPSAT support gap | Non-blocking; recorded in the data-gap register (RS = 10/100 pts, not a required handover layer). | `Phase3_DataGap` register (planned) |
| georef straddle | Phase 03 owns the actual georeferencing of the geology/metallogenic scans; Phase 01 scaffolds the log. | `phase03` steps 3-5 |

**Net:** Phase 03 is fully planned in `PHASE_03_PLAN.md` (ORCHESTRATE: scaffold 12 folders + templates + the
17-layer evidence GPKG + #68 XLSX→points + CMCS buffer + human-layer ingest); module implementation is the
next build.

## Still open (later phases / documentation)

- **KOMPSAT EULA** — source the file, or keep it as a permanent documented gap.
- **BMP-as-`.jpg`** MUGZ tectonic files — characterized (4 distinct BMP pages; read as BMP on the
  working copy per ADR 0001); confirm when Phase 03 georeferences them.

*(01-7 and 02-1 / H-1 were **resolved 2026-06-30** — see above: follow Doc A's Phase 3/4 folder names,
and treat the Phase-2 guide's 25 km buffer as an artefact (add-on-demand). The standalone Phase-1 PDF is
superseded for folder structure per 01-7. **03-1/2/3 + H-4 were decided 2026-07-01** during Phase-3 planning —
see `PHASE_03_PLAN.md`; the BMP-as-`.jpg` files get characterized when Phase 03 georeferences them.)*

---

*Generated from analysis of the master methodology PDF (repo root), the Phase-1 deep-dive
(`docs/phase_01`), the four Phase-2 guides (`docs/phase_02`) and the Phase-3 guide (`docs/phase_03`),
against the `src/buduunkhad` + `config/` implementation (first drafted 2026-06-23, extended for Phase 02
on 2026-06-26 and Phase 03 planning on 2026-07-01). Phase 0–1 resolutions verified at `v0.1.0`; Phase 02
at `v0.2.0` / `v0.2.1`; Phase 03 decided-by-plan (`PHASE_03_PLAN.md`), implementation pending. The master
methodology remains the stated source of truth per `CLAUDE.md`.*
