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
   `OCCURRENCE_NEAR_M`=750 m, access `ACCESS_NEAR_M`=1500 m). Written as `Evidence_Score_Grid` (03).
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
On the current real data the Phase 03 evidence GPKG holds only the 7 #68 mineralized points + the
CMCS buffer + boundary (geology/structure/alteration are empty templates awaiting human digitizing),
so the grid tops out at 22/100 and Phase 04 yields **0 candidate prospects** — correct and honest.
The machinery is complete and test-proven (a delineation test with injected geology + ingested #68
produces ranked A/B/C/D prospects). Prospects populate once the Phase 03 evidence layers are
digitized/ingested (or the human `4. Phase_04/Input` layers are brought in via Phase 03's human-layer
ingest — the scoring rules key off layer presence, so ASTER/roads criteria activate automatically).

## Reuse
`core.vector_io.make_grid / dissolve_adjacent / nearest_distance` (added for this phase);
`registers.write_table_xlsx`; `naming.*`; `EVIDENCE_FIELDS` / `DEPOSIT_MODELS` from
`phase03_geology_synthesis`.
