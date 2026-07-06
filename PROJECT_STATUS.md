# Project Status — Buduunkhad / XV-023222 Exploration Pipeline

**As of:** 2026-07-06 · **Release:** v0.3.3 · **Health:** 🟢 On track

A brief for management. One-page snapshot of what the automated exploration pipeline
has delivered, what's next, and where the gaps are. (Technical detail lives in
`METHODOLOGY_DISCREPANCIES.md`, `REGISTER_RECONCILIATION.md`, and the phase docs.)

---

## Bottom line

The desk-based half of the exploration workflow is **built, tested, and delivered**.
Phases 00–03 — from raw-data safekeeping through the geological/metallogenic synthesis —
run end-to-end on the real project data and are published to the shared Drive as **v0.3.3**.
Field and lab campaigns are already **underway** (a Phase I field program has run and produced
data); the work from here is **extending the pipeline** to ingest and process that data through
the later phases.

## Progress at a glance

The methodology has **13 phases (00–99)**. **4 are complete**; the rest are scaffolded and
waiting on either the next build increment or on field/lab work.

| # | Phase | Status |
|---|-------|--------|
| 00 | Raw Data Archive & Integrity | ✅ Complete |
| 01 | Data Audit & Master GIS Setup | ✅ Complete |
| 02 | Remote Sensing (satellite/terrain) Preprocessing | ✅ Complete |
| 03 | Geological, Metallogenic & Deposit-Model Synthesis | ✅ Complete |
| 04 | Preliminary Prospect Ranking | ⏭️ Next to build |
| 05–11, 99 | Drone, field sampling, soil/geochem, integration, final delivery | 🕓 Scaffolded; **build-limited** — field/lab data already in hand for 06–09 |

## What has been delivered (v0.3.1)

- **A secured, verified raw-data archive** — every one of the 79 source inputs checksummed
  and locked read-only, so nothing is accidentally altered.
- **A master GIS database** — all layers standardized to the project coordinate system
  (UTM 47N), with the licence boundary and the 500 m–25 km buffers.
- **Processed satellite & terrain products** — clipped, reprojected, cloud-optimized imagery
  and DEM derivatives, with QA/QC.
- **A geological evidence package** — a 17-layer database including the **7 historical
  mineralized points** digitized from the source registers, plus the deposit-model and
  scoring templates. All of it is labelled **"Historical / supporting evidence — not proof
  of ore."**
- **Published to the shared Drive** and version-tagged, with an index and audit trail.

Quality bar: all automated checks pass (linting, type-checking, 107 tests), and the work
went through a full correctness audit with every finding fixed.

## What's next

1. **Phase 04 — Preliminary Prospect Ranking** (recommended next). Scores and ranks target
   areas using the geological evidence already assembled. This is the last major step that
   runs mostly on existing desktop data.
2. **Phases 06–09** are now **buildable** — the field & lab data (pXRF field readings, rock-chip
   and soil sampling, lab assay reports) **already exists** from the Phase I program, so these
   phases are limited by pipeline build, not by data. Drone LiDAR, geophysics and drilling data
   are still outstanding.

## Open decisions & risks (all minor, none blocking)

- **One decision pending:** whether a phase that is *automatically* complete but still waiting
  on a human sign-off step should pause the pipeline or advance with a flag. It currently
  advances, clearly marked "provisional." Low stakes; needs a one-line call.
- **No scientific disagreements outstanding.** All 15 documentation conflicts between the
  methodology versions were reconciled and recorded.

## Data gaps

- **One genuinely missing file:** the KOMPSAT satellite licence form (EULA). It's logged as a
  known gap and does **not** block anything — procurement/sync item.
- **Field & lab data — largely collected, not yet processed by the pipeline.** The Phase I field
  program has produced pXRF field readings, rock-chip/soil sampling and lab assay reports (held in
  the master data directory); the pipeline's later phases simply haven't been built to ingest them
  yet. Still genuinely outstanding: **drone LiDAR, geophysics, and drilling**. Until the
  decision-grade lab data is integrated, the *published* evidence remains supporting
  (historical/remote-sensing).
- **A few external imagery products** (certain ASTER/KOMPSAT/Sentinel steps) require
  specialist software and are captured as documented method-notes rather than automated output.

---

*Prepared from the live repository state (branch `main`, tag `v0.3.3`). For the engineering
detail behind any line above, see the referenced documents in the repo root.*
