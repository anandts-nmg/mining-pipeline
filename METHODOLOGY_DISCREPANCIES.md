# Methodology Document Discrepancies — XV-023222 / Buduunkhad

This note records where the methodology documents **disagree with each other**, focused on
the phases the pipeline implements end-to-end (**Phase 00**, **Phase 01** and **Phase 02**).
It also records what the code currently implements, for reference.

> Per `CLAUDE.md`, the **master methodology document is the ultimate source of truth.**
> Where the sources conflict, the code follows the master. **The Phase 0–2 conflicts are now
> resolved & implemented** — see "Resolutions" below (verified at tags `v0.1.0` / `v0.2.0`);
> only later-phase / documentation items remain open.

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

**12 explicitly-numbered conflicts** (Phase 00: 3 · Phase 01: 7 · Phase 02: 2), plus ~4
doc-vs-reality reconciliations and 1 intra-document version drift. **10 of 12 are resolved &
implemented; 2 remain open** (decision-only, non-blocking).

| Group | Comparison | IDs | Resolved | Open |
|---|---|---|---|---|
| Phase 00 | master Doc A vs Phase-1 doc (Doc B) | 00-1, 00-2, 00-3 | 00-1, 00-2, 00-3 | — |
| Phase 01 | master Doc A vs Phase-1 doc (Doc B) | 01-1 … 01-7 | 01-1 … 01-6 | **01-7** (Phase 3/4 names) |
| Phase 02 | master Doc A vs `docs/phase_02` guides | 02-1, 02-2 | 02-2 | **02-1** (25 km buffer) |
| Phase 01 ↔ 02 | inter-phase handoff | H-1, H-2, H-3 | H-2, H-3 | **H-1** (= 02-1) |
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

**Code status / resolution:** **non-blocking, deferred.** Phase 02's actual clips use the
licence boundary and the 1 km / 5 km buffers (DEM = 5 km, Sentinel = licence, basemap = 1 km),
none of which need the 25 km ring, so Phase 02 runs go/go without it. Decision still open: whether
to add a 25 km ring to `boundary.buffers_m` (which would re-run Phase 01) for literal
prerequisite-list compliance, or treat the guide's 25 km as a documentation artefact. Tracked in
`PHASE_02_PLAN.md`.

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

Three interface points (two resolved, one open):

**H-1 — the 25 km buffer (= 02-1).** The Phase-2 guide's prerequisite filename includes a 25 km
ring; Phase 01 produced only 500 m–20 km. **Open** — non-blocking (Phase 02 clips to licence /
1 km / 5 km only). Decide: add a 25 km ring to Phase 01, or treat it as a guide artefact.

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
data** (`v0.2.0`).

## Still open (later phases / documentation)

- **Phase 3 / Phase 4 folder names** (01-7) — code uses Doc A's longer names; confirm when those phases are built.
- Whether the **standalone Phase-1 PDF** should be formally marked "superseded for folder structure" (or updated to match Doc A).
- **KOMPSAT EULA** — source the file, or keep it as a permanent documented gap.
- **BMP-as-`.jpg`** MUGZ tectonic files — confirm reader handling in Phase 02/03.
- **25 km buffer (02-1)** — decide whether to add a 25 km ring to `boundary.buffers_m` (re-runs
  Phase 01) for the Phase-2 guide's prerequisite list, or treat 25 km as a documentation artefact.

---

*Generated from analysis of the master methodology PDF (repo root), the Phase-1 deep-dive
(`docs/phase_01`) and the four Phase-2 guides (`docs/phase_02`), against the `src/buduunkhad` +
`config/` implementation (first drafted 2026-06-23, extended for Phase 02 on 2026-06-26). Phase
0–1 resolutions verified at `v0.1.0`; Phase 02 at `v0.2.0`. The master methodology remains the
stated source of truth per `CLAUDE.md`.*
