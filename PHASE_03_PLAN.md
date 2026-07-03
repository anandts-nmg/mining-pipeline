# Phase 03 / 03A — Geological, Metallogenic & CMCS Synthesis + Preliminary Deposit Model — implementation plan

Grounded in the master methodology (Doc A, section **03. Phase 3** + the **03A** deposit-model
sub-workflow + **Appendix A/B**) and the detailed **Phase-3 QGIS guide** (`phase03` extract, §03.1–§03.4),
reconciled with the repo invariants in `CLAUDE.md` and the adversarially-verified discrepancy findings from
the `phase03-plan` workflow. Phase 03 is the first *synthesis* phase: it consumes Phase 01/02 outputs and the
historical geology/metallogenic scans and produces the geological evidence package that Phase 04 ranks.

> **Evidence rule (non-negotiable, guide §03.1 / master 03A intro):** every Phase 03 output is
> **historical / contextual / preliminary support only — not decision-grade, not ore proof**. Every
> vector feature records `validation_status = "Historical only"` and a `limitation` note; CMCS/MRPAM
> buffer hits are stamped **"Context only — not proof of mineralization inside license"**; remote-sensing
> (Sentinel/ASTER/KOMPSAT/DEM) enters 03A as **support evidence only** (worth 10/100 pts in scoring).

## Mode: ORCHESTRATE

Phase 03 is **orchestrate**, not build. The heavy lifting — georeferencing scan maps, digitizing
lithology/structure/occurrence vectors, writing the deposit model, doing the scoring — is **human work in
QGIS/Excel/Word**. The pipeline scaffolds the folder tree, emits every register/template/schema, ingests the
machine-tractable inputs (the #68 XLSX point table, the human-digitized layers), builds the CMCS buffer, and
runs the QA/QC + gate. Dry-run = templates + schema only (no raw data needed).

## Source documents

| Source | Drives |
|---|---|
| **Doc A (master)** §03 (folder tree, inputs, expected outputs, CMCS step, gate) | Structure/schema authority; 9-folder tree; expected-output list |
| **Doc A (master)** §03A (deposit-model sub-workflow) + **Appendix A/B** | 6 candidate models, 100-pt rubric, `BUD-…` Feature-ID standard, QGIS field-calculator expressions |
| **Phase-3 guide** §03.2 (inputs), §03.3 (folder tree), §03.4 (steps 1–12), Decision gate | Per-step operator detail, the **12-folder** superset, the **17-layer GPKG**, the **13 mandatory fields + `feature_id` (14 columns)**, the **6 exit conditions** |

## Locked decisions

1. **Folder tree = the guide's 12-folder superset** (`custom_subfolders`), under
   `PHASE_DIRS['03']` = `03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis` (Doc A's long name, already
   in `core/paths.py`). The guide is a *finer superset* of Doc A's 9 folders (03-1): it adds
   `01_Input_Working_Copy`, splits occurrence-QA/QC, scoring/data-gap and QA/QC/handover into their own
   folders, and merges Doc A's standalone "CMCS Screening" folder into the buffer + evidence folders.
   Follows the Phase-1/Phase-2 precedent (01-1, 02-2) of honouring the deep-dive's richer structure.
2. **Feature IDs = adopt the master's Appendix A `BUD-…` scheme** as a `feature_id` column, **alongside** the
   guide's 13 mandatory provenance fields (03-3). The guide names layers by filename only and omits any ID
   convention; Doc A's Appendix A supplies it. Prefix per layer below.
3. **Inputs = #1-8 + #53-72** (widen the current stub's `[1-7, 53-72]` to add #8 the licence boundary and
   #53-72 in full — both docs agree on this span; 03-4). The 03A sub-workflow additionally *pulls in* the
   #9-46 / #47-78 remote-sensing/support outputs as **support evidence**, but those are not primary Phase-3
   inputs and are not handover deliverables.
4. **The authoritative evidence GPKG** is Phase 03's `Geological_Evidence_Layers_v01.gpkg` (17 scale-specific
   layers, listed below). This is the package Phase 04 ranks against.
5. **6 candidate deposit models, one 100-pt rubric, three CMCS rings (5/10/20 km).** Both docs agree
   verbatim (03-4) — no scientific conflict to resolve.
6. **Gate = the guide's 6 exit conditions** (below).

## Inputs (#1-8 + #53-72) mapped to the 12 folders / steps

| Input(s) | Evidence | Step (guide §03.4) | Folder |
|---|---|---|---|
| **#1-7** | Tectonic / terrane context maps + explanatory text | Step 2 — build `Tectonic_Terrane_Context_Register` (no ore-target use; regional setting only) | `02_Tectonic_Terrane_Context` |
| **#8** | Licence boundary (from Phase 01, EPSG:32647) | Step 1 readiness + Step 7 buffer origin | `01_Input_Working_Copy`, `08_CMCS_..._Buffer_Check` |
| **#69-72** | 1:500k regional metallogenic map (#70), legend (#69), reports (#71-72) | Step 3 — georef #70, legend dictionary, overlay licence + 20 km buffer, PDF context register | `03_Regional_Metallogenic_1M500K` |
| **#53-54, #57-58** | 1:200k geology map (#53) + legend (#54); mineral-resources map (#57) + legend (#58) | Step 4 — georef, digitize geology polygons + structure lines, occurrence/mineralized points | `04_Regional_Geology_Mineral_1M200K` |
| **#55-56, #60, #63-68** | 1:50k geology map (#55) + legend (#56); occurrence points (#60); prospectivity polygons (#63); route/observation/trench (#64); source-material dictionary (#65); gold occurrence text (#66); PDF register (#67); **XLSX mineralized-point table (#68)** | Step 5 — the most important local-scale evidence; digitize all vectors; **#68 XLSX → validated points (automatable)** | `05_Local_Geology_Occurrence_1M50K`, `06_Source_Materials_and_Prospectivity` |
| **#66, #67, #68** cross-check | Occurrence/mineralized point reconciliation | Step 6 — coordinate + attribute QA/QC (CRS 4326→32647, duplicate, commodity coding, map-register match, confidence flag) | `07_Occurrence_Register_and_Coordinate_QAQC` |
| **#8** (buffer) + CMCS/MRPAM | 5/10/20 km context screening | Step 7 — **buffer build (automatable)** + nearest-deposit register + context map | `08_CMCS_..._Buffer_Check` |
| all Phase-3 vectors | 17-layer merge | Step 8 — authoritative evidence GPKG | `09_Geological_Evidence_Layers_GPKG` |
| #1-8 + #53-72 + 03A support (#9-46/#47-78) | 6 candidate models | Steps 9-10 — 03A deposit model + evidence table + 100-pt scoring | `10_Preliminary_Deposit_Model_03A` |
| all Phase-3 outputs | scoring + data-gap | Steps 10-11 — score matrix + data-gap / validation-priority register | `11_Evidence_Scoring_and_DataGap` |
| all Phase-3 outputs | QA/QC + handover | Steps 11-12 — Phase-3 QA/QC log + handover package to Phase 4/10 | `12_Phase3_QAQC_and_Handover` |

## Folder structure — the guide's 12-folder superset (§03.3)

```
03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis/
├ 01_Input_Working_Copy
├ 02_Tectonic_Terrane_Context
├ 03_Regional_Metallogenic_1M500K
├ 04_Regional_Geology_Mineral_1M200K
├ 05_Local_Geology_Occurrence_1M50K
├ 06_Source_Materials_and_Prospectivity
├ 07_Occurrence_Register_and_Coordinate_QAQC
├ 08_CMCS_MRPAM_Buffer_Check_5km_10km_20km
├ 09_Geological_Evidence_Layers_GPKG
├ 10_Preliminary_Deposit_Model_03A
├ 11_Evidence_Scoring_and_DataGap
└ 12_Phase3_QAQC_and_Handover
```

(Doc A's 9-folder tree — `01_Tectonic_Terrane_Context … 09_Geological_Evidence_GPKG`, with deposit-model at
`07_Preliminary_Deposit_Model_Preparation` — maps entirely into this set; see Resolutions 03-1/03-2.)

## What the pipeline AUTOMATES (BUILD) vs leaves to the human (QGIS/Excel/Word)

| Step | Automated (BUILD now) | Human (ORCHESTRATE — QGIS/Excel/Word) |
|---|---|---|
| 0 Scaffold | Create all **12 folders**; emit every register/template/schema below | — |
| 1 Readiness | Check Phase 01/02 prerequisites present (Master QGIS, licence boundary, georef QA/QC log, RS support layers, confidence ranking) | Resolve any missing prerequisite |
| 2 Tectonic | Emit `Tectonic_Terrane_Context_Register.xlsx` template (9 cols) | Fill from #1-7 (terrane, evidence type, relevance, confidence, limitation) |
| 3 Metallogenic 1:500k | Emit legend-dictionary + evidence-register templates | Georef #70, digitize `metallogenic_zones_polygons`, overlay 20 km buffer, extract from #71-72 PDF |
| 4 Geology 1:200k | Emit legend-dictionary template + empty GPKG layer schemas | Georef #53/#57, digitize geology polygons + structure lines + occurrence points |
| 5 Local 1:50k | Emit empty GPKG layer schemas; **#68 XLSX → validated point layer** (clean, coordinate-validate, 4326→32647) | Georef #55, digitize lithology/contact/fault/vein/prospectivity/source-material vectors |
| 6 Coordinate QA/QC | Emit `Occurrence_Coordinate_QAQC_Log` + `Occurrence_CrossReference` templates; run duplicate/CRS checks on ingested points | Reconcile #66/#67/#68, set confidence flags, commodity coding |
| 7 CMCS buffer | **Build 5/10/20 km buffers off #8** → `CMCS_MRPAM_Buffer_..._EPSG32647.gpkg`; emit nearest-deposit register template stamped "Context only" | Populate register from CMCS/MRPAM; classify by distance/rank; make context map PDF |
| 8 Evidence GPKG | **Build the 17-layer `Geological_Evidence_Layers_v01.gpkg`** with the 13 mandatory provenance fields + `feature_id` (= 14 columns); **ingest human-digitized layers** into it | Digitize the vector content (the pipeline provides the schema + ingests) |
| 9 Deposit model 03A | Emit `Preliminary_Deposit_Model.docx` template + `preliminary_deposit_model_evidence_table.xlsx` (6 rows pre-seeded) | Write the deposit model; fill supporting/missing evidence, validation work, preliminary confidence |
| 10 Scoring | Emit `deposit_model_candidate_score_matrix.xlsx` (8 criteria × 6 models, weighted) | Score each model, assign confidence class |
| 11 QA/QC + data-gap | Emit `Phase3_QAQC_Log.xlsx` (9 acceptance items) + `Phase3_DataGap_and_Validation_Priority.xlsx` | Review, sign off (reviewer/date/decision) |
| 12 Handover | Assemble the 7-file handover package; run the 6-condition gate | — |

**Human-in-the-loop pattern:** the pipeline emits the *schema* and *ingests* what the human produces in QGIS
— it never fabricates digitized geology. Georeferencing of the geology/metallogenic/mineral-resources scans
happens **in-phase as Steps 3-5** (03-6), even though ownership of georef QA/QC logging nominally belongs to
Phase 01.

## Expected outputs (full list, guide §03.4 + Doc A §03)

**Registers / dictionaries (XLSX):**
- `XV023222_Buduunkhad_Tectonic_Terrane_Context_Register_v01.xlsx` (Step 2)
- `XV023222_Buduunkhad_L47B_RegionalMetallogenic_Legend_Dictionary_v01.xlsx`,
  `..._RegionalMetallogenic_Evidence_Register_v01.xlsx` (Step 3)
- `XV023222_Buduunkhad_Mineral_Occurrences_Register_v01.xlsx` (Step 5)
- `XV023222_Buduunkhad_Occurrence_CrossReference_..._v01.xlsx`, `..._Occurrence_Coordinate_QAQC_Log_v01.xlsx` (Step 6)
- `XV023222_Buduunkhad_CMCS_Nearest_Deposit_Register_v01.xlsx` (Step 7)
- `preliminary_deposit_model_evidence_table_v01.xlsx`, `deposit_model_candidate_score_matrix_v01.xlsx` (Steps 9-10)
- `XV023222_Buduunkhad_Phase3_QAQC_Log_v01.xlsx`, `..._Phase3_DataGap_and_Validation_Priority_v01.xlsx` (Steps 11-12)

**Georeferenced rasters (TIF, human):** 1:500k metallogenic (#70), 1:200k geology (#53) + mineral-resources
(#57), 1:50k geology (#55) — each `..._Georeferenced_EPSG32647_v01.tif`.

**Vector layers (GPKG, human-digitized, ingested):** `geology_units_200k_polygons`,
`structures_faults_200k_lines`, `regional_mineral_occurrences_points`, `regional_mineralized_zones_polygons`,
`metallogenic_zones_polygons`, `geology_units_50k_polygons`, `structures_faults_50k_lines`,
`intrusive_contacts_lines`, `dyke_vein_lines`, `mineral_occurrences_points`,
`prospectivity_target_zones_polygons`, `source_material_observation_points`, `source_material_route_lines`,
`source_material_trench_pit_points`, `Validated_Historical_Occurrence_Points` (all `_EPSG32647_v01.gpkg`).

**Pipeline-built:** `CMCS_MRPAM_Buffer_5km_10km_20km_EPSG32647_v01.gpkg` (Step 7),
`Validated_Historical_Occurrence_Points` from #68 (Step 5), and the authoritative merged GPKG (Step 8):

**`XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg`** — the authoritative evidence GPKG.

**Documents / maps (human):** `Preliminary_Deposit_Model_v01.docx` (Step 9),
`RegionalMetallogenic_Context_Map_v01.pdf` (Step 3), `CMCS_Context_Map_v01.pdf` (Step 7).

**Handover package (Step 12):** the 17-layer evidence GPKG, CMCS nearest-deposit register, regional
metallogenic context map, deposit model .docx, score matrix, Phase-3 QA/QC log, data-gap / validation-priority
register.

## The authoritative evidence GPKG — 17-layer schema (Step 8)

`XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg` bundles every Phase-3 vector into one package.
17 layers (guide §03.4 Step 8):

| # | Layer | Geometry | Feature-ID prefix (Appendix A) |
|---|---|---|---|
| 1 | `license_boundary` | polygon | — (inherited from Phase 01) |
| 2 | `buffer_5km_10km_20km` | polygon | — |
| 3 | `tectonic_terrane_context_polygon` | polygon | — |
| 4 | `metallogenic_zones_polygon` | polygon | `BUD-MET` |
| 5 | `ore_district_node_context_polygon` | polygon | — |
| 6 | `geology_units_200k_polygon` | polygon | `BUD-GEO200` |
| 7 | `geology_units_50k_polygon` | polygon | `BUD-GEO50` |
| 8 | `faults_structures_line` | line | `BUD-STR` |
| 9 | `intrusive_contacts_line` | line | — |
| 10 | `dyke_vein_line` | line | — |
| 11 | `mineral_occurrences_point` | point | `BUD-MIN` |
| 12 | `mineralized_points_point` | point | `BUD-MIN` |
| 13 | `prospectivity_target_zones_polygon` | polygon | `BUD-TGT` |
| 14 | `source_material_observation_point` | point | `BUD-OBS` |
| 15 | `source_material_route_line` | line | `BUD-RTE` |
| 16 | `source_material_trench_pit_point` | point | `BUD-OBS` |
| 17 | `cmcs_nearest_occurrences_point` | point | — |

(Appendix A also defines `BUD-HM-AN` / `BUD-SS-AN` for heavy-mineral / stream-sediment anomaly polygons —
**not digitized in Phase 3** (those are Phase 8/9 scope); the prefixes are reserved for those later layers.)

### The 13 mandatory provenance fields + `feature_id` (14 columns, on every layer)

Per guide §03.4 Step 8, plus the adopted `feature_id`:

| Field | Meaning |
|---|---|
| `feature_id` | Appendix-A `BUD-<PREFIX>-0001` (via `concat('BUD-MIN-', lpad(@row_number,4,'0'))`) — **adopted from Doc A** (03-3) |
| `source_raw_input_no` | raw input № 1-78 |
| `source_raw_filename` | exact raw filename |
| `source_group` | evidence group |
| `processing_phase` | `03` or `03A` |
| `source_scale` | 1:50k / 1:200k / 1:500k |
| `geometry_type` | point / line / polygon |
| `evidence_type` | geology / structure / occurrence / metallogenic / prospectivity |
| `validation_status` | **Historical only** / Field checked / Sampled / Lab confirmed |
| `confidence` | High / Medium / Low / Needs verification |
| `limitation` | scale, scan, georef, coordinate uncertainty |
| `processing_version` | v01, v02 … |
| `reviewer` | checker |
| `review_date` | date |

## 03A — deposit-model candidates + 100-pt scoring rubric

The 03A sub-workflow (guide Steps 9-10 / Doc A §03A, both agree) evaluates **6 candidate models**, each with a
supporting/missing-evidence/validation-work/preliminary-confidence row:

| Candidate model | Preliminary confidence |
|---|---|
| Au-Cu hydrothermal vein | High / Moderate / Low |
| Intrusion-related Cu-Au-Mo | Moderate |
| Skarn / contact metasomatic | Moderate / Low |
| Polymetallic vein | Moderate / Low |
| VMS possibility | Conceptual |
| Heavy mineral / placer | Contextual |

**100-point scoring rubric** (Step 10, identical in both docs):

| Criterion | Points |
|---|---|
| Favorable geology / host lithology | 20 |
| Intrusive / contact / structure control | 15 |
| Known mineral occurrence | 15 |
| Historical geochemistry / shlich / stream sediment | 15 |
| Metallogenic context | 10 |
| ASTER/Sentinel alteration support | 10 |
| Field mapping / pXRF support | 10 |
| Access / workability | 5 |
| **Total** | **100** |

**Confidence class:** ≥70 High priority · 50-69 Moderate priority · 30-49 Low/conceptual · <30 Insufficient
evidence. (Note ASTER/Sentinel support is worth only 10/100 — an absent ASTER/KOMPSAT layer cannot block the
gate; see Handoffs.)

## Decision gate — the guide's 6 exit conditions (§03.4)

Phase 3 is complete when:

1. Geology, structure, occurrence, prospectivity & metallogenic context from **#1-8, #53-72** are in the
   Master GIS.
2. Occurrence / mineralized-point **coordinate QA/QC** done.
3. **CMCS/MRPAM 5/10/20 km buffer register** ready.
4. **Preliminary Deposit Model.docx** and **score matrix** ready.
5. All historical evidence stamped **`validation_status = "Historical only"`**.
6. The **geological evidence package** for Phase 4's A/B/C prospect ranking is ready.

A blocked gate stops the runner unless `--override` (logged), per CLAUDE.md invariant 6.

## Resolutions (03-1 / 03-2 / 03-3)

**03-1 — Folder count (Doc A 9 vs guide 12).** **Resolved — adopt the guide's 12-folder superset.** Confirmed
(workflow verdict): Doc A lists exactly 9 subfolders, the guide 12. The guide is a *finer superset in intent*
— it adds `01_Input_Working_Copy`, splits occurrence-QA/QC (07), scoring/data-gap (11) and QA/QC/handover (12)
into their own folders, and folds Doc A's standalone CMCS-screening folder into the buffer + evidence folders.
Not a strict 1:1 rename, but every Doc A concept is present. Mirrors 01-1 / 02-2 (honour the deep-dive's
richer tree). Implemented as `custom_subfolders` under Doc A's long folder name (already in `core/paths.py`).

**03-2 — Deposit-model folder label.** **Resolved — same sub-workflow, use the guide's label.** Doc A folder
`07_Preliminary_Deposit_Model_Preparation` == guide folder `10_Preliminary_Deposit_Model_03A` — identical 03A
content, different number/label. We use the guide's `10_Preliminary_Deposit_Model_03A`.

**03-3 — Feature-ID scheme (Doc A has it, guide omits it).** **Resolved — adopt Doc A's Appendix A `BUD-…`
scheme as a `feature_id` column, alongside the guide's 13 provenance fields (14 columns total).** The guide names layers by filename only and
has no ID table; Doc A Appendix A defines `BUD-GEO50 / BUD-GEO200 / BUD-STR / BUD-MIN / BUD-TGT / BUD-OBS /
BUD-RTE / BUD-MET / BUD-HM-AN / BUD-SS-AN / BUD-GAP`, generated via
`concat('BUD-MIN-', lpad(@row_number,4,'0'))` (Appendix B). **Caveat:** the `BUD-STR-001` tokens elsewhere in
the master are **Phase-7/8 field SAMPLE IDs** (BUD-RC/CH/SOIL/STR/HM sample convention), a *different
namespace* — do not conflate them with these Appendix-A feature-ID prefixes.

*(03-4 and 03-5 are non-conflicts: both docs agree on the #1-8+#53-72 inputs, the same 6 candidate models, the
identical 100-pt rubric and thresholds, the CMCS 5/10/20 km rings, and the historical-only support framing.
Both also expect Sentinel/ASTER/KOMPSAT/DEM as 03A support — see Handoffs.)*

## Handoffs

**01 → 03 (georeferencing straddle, 03-6).** The guide's Step-1 readiness assumes Phase 01 already logged each
scan's GCP / residual / scale / confidence, yet the guide then **does the actual georeferencing in-phase** as
Steps 3-5 (#70, #53, #57, #55). Doc A assigns georeferencing ownership + the Georeferencer SOP to Phase 1
(Appendix E). Ownership genuinely straddles — matching CLAUDE.md's note that the Phase-01 module *scaffolds*
the georef QA/QC log but leaves per-scan GCP/residual pending. **Resolution:** Phase 03 owns the actual
georeferencing of the geology/metallogenic/mineral-resources scans; the georef QA/QC log carries forward.
(This is also where the BMP-as-`.jpg` MUGZ tectonic files finally get characterized on georeferencing — the
open item flagged in `METHODOLOGY_DISCREPANCIES.md`.)

**02 → 03 (the ASTER/KOMPSAT support gap).** Both docs expect Phase 2's Sentinel/ASTER/KOMPSAT/DEM derivative
outputs in 03A as **support evidence** (guide Step-1 + master 03A.2). But Phase 02
(`phase02_remote_sensing.py`) emits **ASTER #73 and KOMPSAT #24/28/32/36/40 as method-note only** — a note
row, not a produced/reprojected layer. So the handoff gap is **real but non-blocking**: (a) all remote sensing
is classified support / "ore proof биш"; (b) it is worth only **10/100 pts** in scoring, so an absent
ASTER/KOMPSAT layer cannot fail any threshold; and (c) the master handover table's Phase-3 required-layers row
lists only *geology, structures, metallogenic zones, occurrence context* — **remote sensing is not even a
required Phase-3 handover layer**. Phase 03 records the missing ASTER/KOMPSAT layers in the data-gap register
and proceeds.

**03 → 04.** Phase 3's output feeds Phase 4's prospect ranking directly. Per the guide, Phase 4 adds to each
prospect polygon: `dominant_deposit_model`, `model_confidence`, `missing_model_evidence`,
`validation_priority`. The Phase-3 → Phase-4 handover deliverable is the **17-layer evidence GPKG** + the
CMCS register + metallogenic context map + deposit model .docx + score matrix + QA/QC log + data-gap register
(7 files, guide Step 12).

## Implementation notes (code changes)

- **`phases/phase03_geology_synthesis.py`** — promote from `StubPhase` to a full `Phase` subclass
  (`mode="orchestrate"`). Set `custom_subfolders` to the 12-folder list above. Implement `prepare` (folder
  tree), `run` (emit all templates/schemas; ingest #68 + human layers; build CMCS buffer + merged GPKG),
  `qaqc` (9 acceptance items), `gate` (6 exit conditions).
- **Fix `input_numbers`** — widen the stub's `[*range(1, 8), *range(53, 73)]` to
  **`[*range(1, 9), *range(53, 73)]`** (add #8 the licence boundary; #53-72 already covered). (03-4.)
- **New helper — `xlsx → validated points`** (Step 5, #68): read the mineralized-point XLSX, clean, detect
  coordinate format (WGS84 lat/long / UTM / local grid), validate + transform EPSG:4326→EPSG:32647, write a
  point GPKG with the 13 mandatory provenance fields + `feature_id` (= 14 columns). Likely `core/points_io.py` (or extend
  `core/vector_io.py`). Reuse `core.crs` for the transform.
- **New helper — evidence-GPKG builder** (Step 8): create the 17-layer GPKG with the correct geometry type +
  the 13 mandatory provenance fields + `feature_id` (= 14 columns) per layer, ingest human-digitized layers (validating schema on
  ingest), and stamp `validation_status="Historical only"` where empty. Likely extend `core/vector_io.py`;
  wire `feature_id` generation to the Appendix-A prefix map (a small `{layer: prefix}` dict in the phase
  module).
- **New helper — CMCS buffer builder** (Step 7): 5/10/20 km multi-ring buffer off #8 licence boundary →
  `CMCS_MRPAM_Buffer_..._EPSG32647.gpkg`. Reuse the Phase-01 buffer primitive if one exists; otherwise a thin
  `shapely` multi-ring wrapper. Stamp the "Context only — not proof of mineralization inside license"
  limitation.
- **Template emitters** — XLSX registers (tectonic, metallogenic legend/evidence, occurrence register +
  cross-reference + coordinate QA/QC, CMCS nearest-deposit, deposit-model evidence table [6 rows pre-seeded],
  score matrix [8×6], QA/QC log [9 items], data-gap/validation-priority) via `core.registers`; the
  `Preliminary_Deposit_Model_v01.docx` template. Build all filenames through `core.naming` (`data_name` for
  data layers, `register_name` for admin XLSX/logs) — never f-strings.
- **Dry-run** — templates + the 17-layer GPKG schema (empty) + empty registers only; no raw data needed; stop
  short of ingest/buffer/merge.
- **Tests — `tests/test_phase03_synthesis.py`** (new) — synthetic fixtures: assert the 12 folders scaffold;
  the 17-layer GPKG schema has exactly the 13 mandatory provenance fields + `feature_id` (= 14 columns) per layer with correct geometry;
  `BUD-…` IDs generate per the prefix map; #68 XLSX→points validates + reprojects to 32647; CMCS 5/10/20 km
  buffer geometry; ingest of a human-digitized layer; the 9 QA/QC items + 6-condition gate; dry-run emits
  schema/templates only.

## Runbook

```powershell
$env:BUDUUNKHAD_RAW_ROOT='C:\bk\rawdata'; $env:BUDUUNKHAD_OUTPUT_ROOT='C:\bk\out'  # rawdata = the real local copy (the C:\bk\raw symlink under-enumerates via Python rglob)
buduunkhad run --only 03 --dry-run     # 12 folders + all templates + empty 17-layer GPKG schema
buduunkhad run --only 03               # + #68 XLSX→points, CMCS buffer, ingest human layers, merged evidence GPKG
# human loop (QGIS): georeference #70/#53/#57/#55; digitize geology/structure/occurrence/prospectivity/source vectors;
#                    write Preliminary_Deposit_Model.docx; fill evidence table + score matrix
buduunkhad run --only 03               # re-run to ingest the digitized layers + re-run QA/QC + gate
# gate GO → buduunkhad publish --label v0.3.0 ; git tag v0.3.0 (account: anandts-nmg)
```
