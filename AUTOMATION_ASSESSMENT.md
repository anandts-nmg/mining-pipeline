# Automation Assessment — Buduunkhad / XV-023222 Exploration Pipeline

**As of:** 2026-07-07 · **Repo state:** v0.6.0 (Phases 00–04 implemented; 05–11, 99 stubs)
**Basis:** the per-phase methodology guides in the human workspace
(`…\0. BuduunKhad_Exploration_Work_Flow`), read end-to-end (Phases 1–11, 99), cross-checked
against the implemented pipeline.

This answers two questions: **(A)** how much of the whole 13-phase workflow *could* be automated
by a pipeline on **any input**, and **(B)** how much the repo automates **today**.

> Percentages below are **engineering estimates** (share of a phase's work that is deterministic /
> codifiable / physical), not measured metrics. They are for prioritisation, not contract.

---

## 1. The three automation tiers

Every step in every phase falls into one of three tiers, and the tier — not the software — sets the
ceiling:

- **Tier 1 — fully automatable on any input.** Deterministic geoprocessing / data ops: same input →
  same correct output, no judgment. (CRS, buffers, DEM derivatives, band-math, grid generation,
  scoring arithmetic, QA/QC math, packaging.)
- **Tier 2 — automatable only if expert judgment is codified/trained.** Interpretation a pipeline can
  apply *via an expert-supplied rule, lookup, or trained model* — but the rule/labels must be
  provided once by a geologist; they are not derivable from the inputs alone. (Map digitizing,
  deposit-model favorable-setting, anomaly thresholds, scoring rubrics.)
- **Tier 3 — not desktop-automatable.** Physical-world data collection. (Flying drones, field
  mapping/observation, sampling, pXRF-on-rock, lab assays, trenching, geophysics acquisition,
  drilling.) A pipeline can *plan before* and *process after*, never *perform*.

---

## 2. Whole-workflow automation potential (ceiling)

| Phase | Nature | Auto ceiling | Biggest blocker (tier) |
|---|---|--:|---|
| 00 Raw archive & integrity | desktop | ~95% | none of substance — deterministic |
| 01 Data audit & master GIS | desktop | ~85% | scan-map georeferencing GCPs (T2) |
| 02 Remote-sensing preprocessing | desktop | ~82% | lineament/outcrop digitizing; threshold-locking (T2) |
| 03 Geology/metallogenic/CMCS synthesis | desktop | ~45% | georeference + **digitize scanned maps** + deposit-model judgment (T2) |
| 04 Prospect delineation & ranking | desktop | ~72% | quality of Phase-3 interpreted layers; deposit-model fit (T2) |
| 05 Drone LiDAR & photogrammetry | field+proc | ~60% (→85% post-Terra) | physical flight (T3) + DJI Terra raw-LiDAR decode lock-in |
| 06 Recon mapping + pXRF | field | ~40% | physical ground-truthing / pXRF-on-rock (T3) |
| 07 Rock-chip/channel sampling | field+lab | ~42% | physical sampling + lab assay (T3) |
| 08 Orientation soil/stream/HM | field+lab | ~50% | physical method-calibration experiment (T3) |
| 09 Systematic soil grid + lab QA/QC | field+lab | ~60% | physical collection + lab assay (T3) |
| 10 Integrated interpretation + **final ranking** | desktop | ~67% | qualitative sub-scoring + deposit-model call + Go/No-Go (T2) |
| 11 Follow-up trench/geophysics/drill planning | desktop→field | ~52% | collar/line placement judgment (T2) + physical execution (T3) |
| 99 Final deliverables | desktop | ~90% | include/exclude + narrative report (T2, minor) |

**Read:** desktop phases (00–04, 10, 99) are 45–95% automatable; field phases (05–11) are capped at
35–60% because their core deliverable is physical. Whole-workflow automatable potential ≈ **two-thirds**.

---

## 3. What the repo automates TODAY (v0.6.0)

The repo implements **5 of 13 phases (00–04)** — the desktop front-half. Phases 05–11 and 99 are
registered **stubs**: they build folders in dry-run but raise `NotImplementedError` on a real run, so
they automate **0%** today.

### By phase — ceiling vs. realised now

| Phase | Ceiling | Built? | **Realised now** | Gap vs. ceiling |
|---|--:|:--:|--:|---|
| 00 | 95% | ✅ | **~95%** | complete — deterministic integrity/inventory/checksums |
| 01 | 85% | ✅ | **~75%** | Tier-1 spine done; **master GPKG ships as an empty schema** (evidence lives in the Phase-03 GPKG, not back-populated); georef manual |
| 02 | 82% | ✅ | **~72%** | DEM + Sentinel-clip + basemap COGs + **ASTER alteration chain (automated 2026-07-07** — indices/binaries/target score/polygons, validated r≈0.92–0.98 vs the geologist's reference**)**; KOMPSAT / Sentinel-indices remain method-notes |
| 03 | 45% | ✅ (ORCH) | **~40%** | scaffold + registers + evidence-GPKG assembly + CMCS buffer + #68 ingest + human-layer ingest done; **digitizing / georef / deposit-model matrix = human** |
| 04 | 72% | ✅ | **~55%** | grid + scoring + banding + ranking + Go/No-Go run, **but `model_fit` is uniform/dead and it over-flags** (see §7); scoring quality is compromised |
| 05–11, 99 | 40–90% | ❌ stub | **0%** | not implemented |

### By tier — how much of each tier the repo realises (whole workflow)

| Tier | Realised | Why |
|---|--:|---|
| **Tier 1** (deterministic) | **~45%** | Front phases (00–04) automate their Tier-1 spine well; the field-phase Tier-1 (soil-grid generation, drainage/catchment analysis, the assay QA/QC engine, geometry planning) is all **unbuilt** in the stubs. |
| **Tier 2** (codifiable judgment) | **~0%** | The repo **defers** all interpretation to humans (ORCHESTRATE emits templates + ingests human-digitized layers). It codifies **none** of the 6 expert inputs yet — `model_fit` is applied uniformly (broken), no digitizing, no georeferencing, no anomaly thresholds. |
| **Tier 3** (physical) | **0%** | n/a — not automatable by anything. |

### Overall

- **~38% of the whole workflow by phase count** (5 of 13), and — coincidentally — **~40% of the
  workflow's total automatable *potential*** is realised today (sum of realised ≈ 320 vs. sum of
  ceilings ≈ 840 across the 13 phases).
- The realised work is almost entirely **Tier 1 on the desktop front-half**. The repo is a strong,
  correct **deterministic engine through preliminary prospect ranking**, with **no Tier-2 codification
  yet** and the **entire field/lab back-half (05–11) + packaging (99) unbuilt**.
- Two known quality gaps *within* the built phases: the **empty master GPKG** (Phase 01) and the
  **uniform/dead `model_fit` + prospect over-flagging** (Phase 04, see §7).

---

## 4. The Tier-1 spine — fully automatable on any input

Confirmed deterministic and generalisable across all phases (much already built for 00–04; the rest
is the build target for the stubs):

- **Data ops:** ingest, SHA-256 integrity, inventory, CRS unification, reprojection, buffers, GPKG
  assembly, naming, packaging, checksums, ZIP (00/01/99).
- **Raster/DEM:** clip, reproject, COG, multi-azimuth hillshade, slope, aspect, TRI, curvature,
  flow/drainage/**watershed-catchment**, Sentinel band-math/indices, ASTER alteration algebra
  (02/05/08).
- **Geometry generation:** soil grids, drone flight blocks, trench/geophysics/drill lines, sample
  points, GCP layouts — parameter-driven from an AOI + strike (05/09/11).
- **QA/QC + scoring math:** assay validation (CRM/blank/duplicate RPD, detection-limit handling),
  pXRF-vs-lab bias, percentile anomaly classing, scoring arithmetic + A/B/C/D banding, ranking tables,
  register emission (04/06/07/08/09/10).

---

## 5. The Tier-2 unlock — codify once, run many

The interpretation bottleneck across **all 13 phases** reduces to a small, reusable set of expert
inputs. Supply each once (as a rule, lookup, or labelled training set) and the desktop workflow
generalises to any licence:

1. **ML-assisted / rule-based digitizing of scanned maps + lineament/outcrop extraction** — the
   single highest-leverage unlock; gates Phases 02, 03, 05 and everything downstream.
2. **Georeferencing GCPs / grid-reading rules** per scan series (01, 03).
3. **Deposit-model favorable-setting definition** + deposit-model → element/method lookups
   (03, 04, 07–10). *This is the wall the Phase-04 investigation hit; the human encodes it as a
   per-cell `deposit_model_setting` layer.*
4. **Per-element anomaly thresholds** (06–10).
5. **Structural strike / trend layer** (05, 08, 09, 11).
6. **Scoring weights + band cutoffs + Go/No-Go criteria** (03, 04, 10).

These are the *same class* of input — an expert artifact provided once, not per run. This is the
"codify-once, run-many" model: the geologist moves from *doing* the interpretation on every project to
*defining/validating* it once.

---

## 6. Hard limits (irreducible)

- **Physical Tier-3 work:** flying drones, field observation/mapping, sampling, pXRF-on-rock, lab
  assays, trenching, geophysics acquisition, drilling. The pipeline plans-before and processes-after,
  never performs.
- **Only two genuine tool locks** (everything else — QGIS / SNAP / ILWIS / Office / 7-Zip / DEM
  plugins — is replaceable by open Python: geopandas, shapely, rasterio, pysheds/pyflwdir, PDAL,
  pandas, python-docx): **DJI Terra** raw-LiDAR decode/PPK (Phase 05), and **DJI Pilot** mission
  execution (physical). **CMCS** (`cmcs.mrpam.gov.mn`) is a live government web portal — a manual pull
  unless an API/scrape exists.

---

## 7. Cross-guide discrepancies (ranked)

1. **Three different "100-point" scoring matrices, easily conflated.** Phase 3 (03A deposit-model:
   geochem 15, +ASTER/field), Phase 4 (prospect: geochem 20, +model-fit/confidence — *what the
   pipeline codes*), and **Phase 10 (final ranking: adds assay 15 + field-mineralization 10)** — each
   with **different band cutoffs** (30/50/70 vs 35/55/75 vs 25/50/75). Intentionally progressive
   (desktop → with-data) but the guides never cross-reference them. **The final ranking (Phase 10)
   uses a matrix the pipeline does not yet implement** — reconcile before the final ranking can be
   called methodology-faithful.
2. **CRS: fixed vs variable.** Phases 8/9 guides say "UTM zone by location"; the pipeline hard-codes
   EPSG:32647. For a truly *any-input* tool, auto-UTM-from-centroid is the correct behavior — a real
   generalisation divergence to decide.
3. **78 vs 79 inputs.** Guides say 78; repo tracks 79 (SAS #79). Recurs in Phases 1, 3, 99
   traceability. Repo already reconciled; guides stale.
4. **25 km buffer.** Guides list only 5/10/20 km; pipeline + methodology v8/v9 add 25 km (Step 7A).
   Guides stale.
5. **`model_fit` is non-discriminating (Phase 04 defect).** Applied **uniformly** to every cell
   instead of spatially, so it cannot separate targets from background — the direct cause of the
   prospect **over-flagging** (~35 km² flagged vs the human's ~6 km²). Fixing it needs the
   deposit-model favorable-setting (§5 item 3), not a code tweak (a mechanical proxy was tried and
   made it worse).
6. **Naming drift.** Phases 5/6/7 guides use hyphenated `XV-023222_` for GIS *data* layers, violating
   the repo rule (data layers = underscored `data_name`; only registers hyphenated).
7. **Sentinel thresholds inconsistent** — NDVI >0.3 vs >0.25; shadow reflectance-vs-DN scale — need
   canonical values + scale auto-detection.
8. **Phase 6 gate is 3-state** (Proceed / Hold / Downgrade) — richer than the binary Go/No-Go; the
   gate model needs a hold state.
9. Minor: ASTER porphyry weights hard-coded (should be config); Phase-2 basemap sub-guide mislabeled
   "Phase 10"; Phase-5 altitude inconsistent (80–120 vs 250–300 m → must be a parameter);
   `00_Raw_Files_Archive` vs `00_Raw_Input_Evidence_Library`.

---

## 8. Build plan for the stub phases (05–11, 99)

All fit the repo's **BUILD vs ORCHESTRATE** split cleanly: automate the *plan-before* + *process-after*
halves, ingest the physical returns, run deterministic QA/QC.

| Phase | Mode | Automate now (Tier 1) | Needs expert input (Tier 2) | Physical (Tier 3) |
|---|---|---|---|---|
| 05 Drone LiDAR | ORCH + BUILD | flight-block generation (AOI-driven), terrain derivatives, LiDAR QA/QC metrics, crop export | block prioritisation, flight-param tables, lineament interpretation | flight + GCP survey; Terra raw decode |
| 06 Recon + pXRF | ORCH | QField project gen, pXRF ETL + QA/QC stats, anomaly + deposit-model index maps, re-ranking | traverse route rules, upgrade/downgrade rule, anomaly thresholds | field observation + pXRF readings |
| 07 Rock-chip sampling | ORCH | registers, Sample-ID gen, QA/QC scheduling + reconciliation, assay ingest | target-point selection (reuse Phase-04 grid), element package lookup | physical sampling + lab assay |
| 08 Orientation geochem | ORCH + BUILD | **drainage/catchment analysis**, orientation-line geometry, returned-data stats/maps | anomaly thresholds, residual-vs-transported rule, "best method" call | multi-depth/mesh field test + lab |
| 09 Soil grid + lab QA/QC | BUILD + ORCH | **soil-grid generation** (highest Tier-1 in the field set), full assay-validation engine, anomaly maps | spacing/orientation rule (needs strike), target-area threshold | soil collection + lab assay |
| 10 Integrated interpretation | BUILD | data integration, assay QA/QC, CMCS buffers, target-overlap polygons, scoring arithmetic, packaging | **Phase-10 scoring rubric (differs from Phase 4)**, deposit-model classification, Go/No-Go | none (desk phase) |
| 11 Follow-up planning | BUILD + ORCH | trench/IP/mag line geometry, infill-grid, slope/access constraint screening, budget/schedule tables | line/collar placement (needs trend), method selection, drill Go decision | trenching/geophysics/drilling |
| 99 Final deliverables | BUILD | folder tree, naming check, CRS validate, metadata register, checksums, ZIP — **~90% ready via existing `core/`** | include/exclude + narrative report | none |

**Highest-leverage next builds:** Phase 09 soil-grid + assay-QA/QC engine (mostly Tier 1, near-template
of Phase 04's grid), Phase 08 catchment analysis, and Phase 99 packaging (~90% already in `core/`).
The Tier-2 blockers everywhere trace back to the **6 codifiable inputs in §5** — capturing the
map-digitizing model and the deposit-model setting unlocks the most across phases.

---

## Bottom line

- The repo is a **correct, deterministic engine for the desktop front-half** (Phases 00–04) — it
  realises ~40% of the workflow's automatable potential today, almost all of it Tier 1.
- It codifies **no Tier-2 judgment yet** (it defers to humans, correctly, via ORCHESTRATE) and the
  **field/lab back-half + packaging are unbuilt**.
- A single pipeline **can** own the entire desktop spine on any input — and most of the field phases'
  desktop halves — once the **6 expert inputs in §5** are captured. Full autonomy is neither
  achievable nor appropriate: the physical Tier-3 work and the final Go/No-Go sign-off stay human.
</content>
