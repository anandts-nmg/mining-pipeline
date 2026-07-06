# Phase 04 — Preliminary Prospect Delineation & Ranking (design + status)

**BUILD.** Implemented and run (v0.4.0). Turns the Phase 03 geological-evidence package into ranked
preliminary prospects, per the methodology **v9 §04 / §5**. Source of truth is the methodology; the
human folder `4. Phase_04/` (Drive) is a comparison reference, not ground truth.

## Inputs
- **Phase 03 evidence GPKG** (`03/09_Geological_Evidence_Layers_GPKG/*Geological_Evidence*.gpkg`) —
  the 17 evidence layers (geology 50k/200k, intrusive contacts, faults/dykes, occurrences,
  mineralized points, prospectivity zones, metallogenic zones, CMCS buffer, boundary).
- **Phase 01 licence boundary** (AOI for the grid), when the evidence GPKG's `license_boundary` is
  empty.
- **Phase 03 03A deposit-model score matrix** (for the per-prospect model wiring).

## Folders (v9)
`01_Evidence_Overlay` · `02_Prospect_Polygon_Delineation` · `03_Scoring_Matrix` ·
`04_Confidence_DataGap_NextAction` · `05_A_B_C_D_Field_Priority`.

## Scoring — v9 §5 weighted matrix (sum 100)
geology 20 · historical geochem 15 · ASTER/Sentinel 15 · structure 15 · field/pXRF 15 · drone 8 ·
CMCS 7 · access 5. Classes **A ≥75 · B 55–74 · C 35–54 · D <35**. (This is a *separate* framework
from Phase 03's `SCORING_CRITERIA`, the 03A deposit-model rubric ≥70/50/30 — that scores deposit
*models*; this scores prospect *polygons*. Phase 04 consumes the former as `model_confidence` /
`validation_priority`.)

## Algorithm (auto-grid, mirrors the human 250 m-grid method, methodology-scored)
1. **Evidence overlay** — copy the non-empty Phase 03 evidence layers into one overlay GPKG (01).
2. **Score grid** — a `GRID_CELL_M`=250 m fishnet over the boundary + `CONTEXT_BUFFER_M`=1000 m; each
   cell scores a criterion's full §5 weight when its evidence is present (occurrence proximity
   `OCCURRENCE_NEAR_M`=750 m, access `ACCESS_NEAR_M`=1500 m). **Discriminating rules:** geology scores
   near unit *contacts* (polygon boundaries + intrusive contacts), not blanket interiors; CMCS scores
   *localized* nearest-deposit/metallogenic context, not the whole filled 25 km buffer — otherwise
   those two criteria flag ~100% of cells and the result saturates into one blob. Written as
   `Evidence_Score_Grid` (03).
3. **Delineate** — dissolve contiguous cells scoring ≥ `SCORE_THRESHOLD`=35 (the C floor) into
   candidate polygons; per polygon: `max_score`/`mean_score`, area, centroid, nearest-feature
   distances, per-criterion evidence flags, `BUD-PSP-####` id, rank. Written as `Prospect_Polygons`
   (02).
4. **Class + deposit-model wiring** — `classify(max_score)` → A/B/C/D; add `dominant_deposit_model`,
   `model_confidence` (pending 03A human completion), `missing_model_evidence`, `validation_priority`.
5. **Registers** — `Prospect_Ranking_Table.xlsx` (03), `Go_NoGo_Desktop_Decision_Matrix.xlsx` (05),
   `Prospect_DataGap_and_NextAction.xlsx` (04). The `Preliminary_Prospect_Ranking_Map.pdf` is a QGIS
   print layout (human) — see the phase method note.

## Desktop data gaps (invariant #8)
Three §5 criteria are unavailable at desktop Phase 04 and score **0**, recorded in the data-gap
register: **ASTER/Sentinel** (Phase 02 method-note, H-4), **field/pXRF** (Phase 06+), **drone**
(Phase 05+). All outputs stamped *"Preliminary — not ore proof."* Desktop prospects therefore land
B/C; the gate pushes A/B into the field phases to upgrade.

## Prospect schema (`prospect_candidate_areas`, mirrors the human Layer A)
`candidate_id, rank, prospect_class, area_ha, max_score, mean_score, centroid_E/N,` the 8
per-criterion `score_*`, `dist_fault_m/dist_dyke_m/dist_occ_m/dist_min_point_m/dist_road_m,
elements, dominant_deposit_model, model_confidence, missing_model_evidence, validation_priority,
target_interpretation, recommended_followup, validation_status, limitation, source_phase`.

## Status note (v0.4.0)
Two states, both honest:
- **Bare Phase 03 templates** (7 #68 points + CMCS buffer + boundary only): grid tops out at 22/100
  → **0 candidates** — correct; the geology/structure/alteration layers aren't digitized yet.
- **Human evidence fed in** (the `4. Phase_04/Input` digitized geology/faults/dykes/occurrences
  ingested via Phase 03's human-layer path — done 2026-07-06): Phase 04 delineates **6 discrete
  C-class prospects** (`BUD-PSP-0001..0006`, max score 50/100, 31–1288 ha) — the **same count** as
  the human's 6 PCAs, ranked by score. They cap at **C** (not the human's A) because ASTER/field/drone
  score 0 at desktop and the geometry-only evidence GPKG can't score favorable-lithology / geochem-
  element / alteration *attributes* — the fuller fidelity upgrade (attribute-aware scoring +
  ASTER) is the planned next increment.

Prospects populate once the Phase 03 evidence layers are digitized/ingested; the scoring rules key
off layer presence, so an ingested ASTER/roads layer activates its criterion automatically.

## Reuse
`core.vector_io.make_grid / dissolve_adjacent / nearest_distance` (added for this phase);
`registers.write_table_xlsx`; `naming.*`; `EVIDENCE_FIELDS` / `DEPOSIT_MODELS` from
`phase03_geology_synthesis`.
