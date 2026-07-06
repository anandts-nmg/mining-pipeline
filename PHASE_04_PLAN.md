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

## Scoring — Phase-4 guide §6 desktop matrix (sum 100; conflict 04-1, adopted v0.6.0)
geology 20 · occurrence 15 · geochem 20 · RS 15 · structure 10 · deposit-model fit 10 · access 5 ·
confidence 5. Classes **A ≥75 · B 55–74 · C 35–54 · D <35**. Desktop-only — no field/drone
criteria, so a well-evidenced desktop prospect can reach **A** (the v9 §5 *lifecycle* matrix, which
adds field-pXRF 15 + drone 8, is used at Phase 10 final ranking — see METHODOLOGY_DISCREPANCIES
04-1). Model-fit (§6.7) is scored from the Phase 03 03A score matrix once human-completed
(pending → 0 + data gap); confidence (§6.9) grades evidence completeness across the other seven
criteria (≥6 available → 5, 4–5 → 3, 2–3 → 1). This framework is *separate* from Phase 03's
`SCORING_CRITERIA` (the 03A deposit-model rubric, which scores deposit *models*).

## Algorithm (auto-grid, mirrors the human 250 m-grid method, methodology-scored)
1. **Evidence overlay** — copy the non-empty Phase 03 evidence layers into one overlay GPKG (01).
2. **Score grid** — a `GRID_CELL_M`=250 m fishnet over the boundary + `CONTEXT_BUFFER_M`=1000 m; each
   cell scores a criterion's §6 weight when its evidence is present (occurrence proximity
   `OCCURRENCE_NEAR_M`=750 m, access `ACCESS_NEAR_M`=1500 m); model-fit/confidence apply as graded
   run-level points. **Discriminating rule:** geology scores near unit *contacts* (polygon
   boundaries + intrusive contacts), not blanket interiors — otherwise it flags ~100% of cells and
   the result saturates into one blob. Written as `Evidence_Score_Grid` (03).
3. **Delineate per class band** — contiguous **A** cells dissolve into discrete A prospects,
   likewise B and C (D = below the 35 C-floor, not a prospect; a single ≥35 dissolve would merge
   the evidence-rich zone into one blob). Per polygon: `max_score`/`mean_score`, area, centroid,
   nearest-feature distances, per-criterion scores, `BUD-PSP-####` id, global rank. Written as
   `Prospect_Polygons` (02).
4. **Class + deposit-model wiring** — the polygon's band = its class; add `dominant_deposit_model` +
   `model_confidence` (from the 03A matrix when human-completed), `missing_model_evidence`,
   `validation_priority`.
5. **Registers** — `Prospect_Ranking_Table.xlsx` (03), `Go_NoGo_Desktop_Decision_Matrix.xlsx` (05),
   `Prospect_DataGap_and_NextAction.xlsx` (04). The `Preliminary_Prospect_Ranking_Map.pdf` is a QGIS
   print layout (human) — see the phase method note.

## Data gaps (invariant #8)
Criteria without evidence score **0** and are recorded in the data-gap register: `rs` without fed
focused alteration (Phase 02 emits ASTER as a method-note — H-4), `model_fit` until the human
completes the 03A score matrix, `access` without a roads layer. All outputs stamped *"Preliminary —
not ore proof"* — class A means field/lab follow-up priority, never a confirmed deposit. Field/pXRF
and drone evidence enter at Phases 05–06 and are scored by the v9 §5 lifecycle matrix at Phase 10.

## Prospect schema (`prospect_candidate_areas`, mirrors the human Layer A)
`candidate_id, rank, prospect_class, area_ha, max_score, mean_score, centroid_E/N,` the 8
per-criterion `score_*`, `dist_fault_m/dist_dyke_m/dist_occ_m/dist_min_point_m/dist_road_m,
elements, dominant_deposit_model, model_confidence, missing_model_evidence, validation_priority,
target_interpretation, recommended_followup, validation_status, limitation, source_phase`.

## Attribute-aware scoring (v0.5.0)
Beyond the geometry-only Phase 03 evidence GPKG, Phase 04 reads *attribute-bearing* prospectivity
layers dropped under the Phase 03/04 dirs (whitelisted by keyword — pipeline outputs never match):
- **focused alteration** (argillic/porphyry/sericite/silica or hand-digitized) activates the `rs`
  criterion (0 → 15). Regional chlorite-epidote *propylitic halo* is excluded as context — it
  blankets the district and would re-saturate the score.
- **geochem-anomaly** polygons drive `geochem` and populate each prospect's `elements` from the
  anomaly's element attribute.

## Status note (v0.6.0, guide §6 matrix)
States, all honest:
- **Bare Phase 03 templates** (7 #68 points + CMCS buffer + boundary): sparse scores → few/no
  candidates — correct; no geology/structure/alteration digitized yet.
- **Full evidence fed** (digitized geology/faults/dykes/occurrences + hand-digitized alteration +
  geochem-anomaly via Phase 03 human-layer + attribute paths, 2026-07-06): **47 discrete prospects —
  7 A (83/100, 6–31 ha) + 15 B + 25 C** — delineated per class band, each carrying `elements`
  (Au/Cu/Mo/Ba/Co/Ni/…). Directly comparable to the human reference's **6 A-class PCAs** (6–450 ha).
  Remaining data gaps: `model_fit` (03A matrix pending human completion → +up to 10) and `access`
  (no roads layer → +up to 5).

The pixel-broad ASTER masks (`Advanced_argillic`/`Porphyry`/`Ch_Ep_halo`, thousands of polygons)
are district-scale context and saturate presence-based `rs` into one blob — so the target-defining
alteration input is the geologist's **hand-digitized** layer, not the raw ASTER masks. Finer
intensity/grade-thresholded scoring of the raw masks is a future calibration with the geologist.

## Reuse
`core.vector_io.make_grid / dissolve_adjacent / nearest_distance` (added for this phase);
`registers.write_table_xlsx`; `naming.*`; `EVIDENCE_FIELDS` / `DEPOSIT_MODELS` from
`phase03_geology_synthesis`.
