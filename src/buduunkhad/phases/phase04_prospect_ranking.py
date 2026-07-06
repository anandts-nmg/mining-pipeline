"""Phase 04 — Preliminary Prospect Delineation & Ranking (BUILD).

Turns the Phase 03 geological-evidence package into ranked preliminary prospects, per the
methodology (v9 §04 / §5): build an evidence-scoring grid over the licence AOI, score each cell on
the **8-criterion weighted matrix** (geology 20 / historical geochem 15 / ASTER-Sentinel 15 /
structure 15 / field-pXRF 15 / drone 8 / CMCS 7 / access 5 = 100), dissolve high-score cells into
candidate prospect polygons, assign the **A/B/C/D** field-priority class (A>=75, B 55-74, C 35-54,
D<35), wire in the Phase 03 03A deposit-model outputs, and emit the four deliverables.

**Desktop-stage honesty (invariant #8):** three §5 criteria are not available at desktop Phase 04 in
this pipeline and score **0**, flagged as data gaps — **ASTER/Sentinel alteration** (Phase 02 emits it
as a method-note, not a produced layer — H-4), **field/pXRF** (Phase 06+) and **drone LiDAR**
(Phase 05+). Desktop prospects therefore realistically land B/C; the gate exists precisely to push
A/B candidates into the field phases to upgrade. Every output is stamped *"Preliminary — not ore
proof."* The scoring rules key off evidence-layer presence, so when those layers are later ingested
(e.g. an ASTER alteration human layer) the corresponding criterion activates automatically.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from buduunkhad.core import naming, registers, vector_io
from buduunkhad.core.qaqc import RECORDED_ACCEPTANCE, Decision, QAQCReport, new_report
from buduunkhad.phases.base import Phase, PhaseResult, RunContext
from buduunkhad.phases.phase03_geology_synthesis import DEPOSIT_MODELS

# Preliminary-prospect status stamp (invariant #8: never ore proof).
PROSPECT_VALIDATION = "Preliminary — not ore proof"
PROSPECT_LIMITATION = (
    "Desktop evidence-scored prospect; requires field/lab validation (drone/recon/sampling)"
)

# v9 §5 prospect ranking matrix — 8 weighted criteria summing to 100. DISTINCT from Phase 03's
# SCORING_CRITERIA (the 03A deposit-model rubric): this scores prospect *polygons*, that scores
# deposit *models*. `available` is False for criteria whose evidence does not exist at desktop
# Phase 04 in this pipeline (scored 0 + recorded as a data gap).
PROSPECT_CRITERIA: list[tuple[str, int, bool]] = [
    ("geology", 20, True),
    ("geochem", 15, True),
    ("rs", 15, False),  # ASTER/Sentinel alteration — Phase 02 method-note (H-4)
    ("structure", 15, True),
    ("field_pxrf", 15, False),  # Phase 06+
    ("drone", 8, False),  # Phase 05+
    ("cmcs", 7, True),
    ("access", 5, False),  # roads layer is a human input; absent -> gap
]
_CRIT_WEIGHT = {k: w for k, w, _ in PROSPECT_CRITERIA}

# Grid + proximity tuning (module constants, like Phase 03's CMCS_RINGS_M).
GRID_CELL_M = 250.0
CONTEXT_BUFFER_M = 1000.0  # grid the licence boundary + this context margin
SCORE_THRESHOLD = 35  # cells scoring >= this (the C floor) are promoted to candidate polygons
OCCURRENCE_NEAR_M = 750.0  # "near a known occurrence" proximity (human-ref threshold)
ACCESS_NEAR_M = 1500.0  # "accessible" = within this of a road (human-ref threshold)

_PROSPECT_LAYER = "prospect_candidate_areas"
_GRID_LAYER = "evidence_score_grid"
_FEATURE_PREFIX = "BUD-PSP"  # Appendix-A style id for preliminary prospects


# A/B/C/D field-priority bands (v9 §5).
def classify(score: float) -> str:
    if score >= 75:
        return "A"
    if score >= 55:
        return "B"
    if score >= 35:
        return "C"
    return "D"


_CLASS_VALIDATION_PRIORITY = {"A": "High", "B": "High", "C": "Medium", "D": "Low"}
_CLASS_DECISION = {"A": "Go", "B": "Go", "C": "Conditional", "D": "No-Go (monitor)"}

# ---- register / gpkg schemas ---------------------------------------------- #

_SCORE_COLS = [f"score_{k}" for k, _, _ in PROSPECT_CRITERIA]

# Prospect polygon attributes (mirrors the human reference Layer A, methodology-scored).
_PROSPECT_COLUMNS: list[str] = [
    "candidate_id",
    "rank",
    "prospect_class",
    "area_ha",
    "max_score",
    "mean_score",
    "centroid_E",
    "centroid_N",
    *_SCORE_COLS,
    "dist_fault_m",
    "dist_dyke_m",
    "dist_occ_m",
    "dist_min_point_m",
    "dist_road_m",
    "elements",
    "dominant_deposit_model",
    "model_confidence",
    "missing_model_evidence",
    "validation_priority",
    "target_interpretation",
    "recommended_followup",
    "validation_status",
    "limitation",
    "source_phase",
]

# fiona type strings for the empty dry-run schema.
_PROSPECT_PROPS: dict[str, str] = {
    "candidate_id": "str:32",
    "rank": "int",
    "prospect_class": "str:2",
    "area_ha": "float",
    "max_score": "int",
    "mean_score": "float",
    "centroid_E": "float",
    "centroid_N": "float",
    **dict.fromkeys(_SCORE_COLS, "int"),
    "dist_fault_m": "float",
    "dist_dyke_m": "float",
    "dist_occ_m": "float",
    "dist_min_point_m": "float",
    "dist_road_m": "float",
    "elements": "str:128",
    "dominant_deposit_model": "str:64",
    "model_confidence": "str:32",
    "missing_model_evidence": "str:254",
    "validation_priority": "str:16",
    "target_interpretation": "str:254",
    "recommended_followup": "str:254",
    "validation_status": "str:32",
    "limitation": "str:254",
    "source_phase": "str:8",
}

_RANKING_TABLE_COLUMNS = [
    "candidate_id",
    "rank",
    "prospect_class",
    "area_ha",
    "max_score",
    "mean_score",
    *_SCORE_COLS,
    "dominant_deposit_model",
    "model_confidence",
    "validation_priority",
    "elements",
    "target_interpretation",
    "recommended_followup",
]
_GONOGO_COLUMNS = [
    "candidate_id",
    "prospect_class",
    "max_score",
    "desktop_decision",
    "rationale",
    "next_action",
]
_DATAGAP_COLUMNS = [
    "criterion",
    "weight",
    "status",
    "acquired_in_phase",
    "note",
]

_RECOMMENDED_FOLLOWUP = (
    "First-pass field traverse; verify fault/dyke/contact + alteration + quartz/vein/gossan; "
    "rock-chip + soil/stream-sediment follow-up."
)


class Phase04ProspectRanking(Phase):
    id = "04"
    name = "Preliminary Prospect Delineation and Ranking"
    mode = "build"
    input_numbers = [*range(1, 9), *range(47, 79)]
    gate_condition = "A/B prospects selected for drone/recon; C/D retained with data gaps."
    custom_subfolders = [
        "01_Evidence_Overlay",
        "02_Prospect_Polygon_Delineation",
        "03_Scoring_Matrix",
        "04_Confidence_DataGap_NextAction",
        "05_A_B_C_D_Field_Priority",
    ]

    # run-state (set in run(), read in qaqc())
    _n_candidates: int
    _class_counts: dict[str, int]
    _grid_cells: int
    _data_gaps: list[str]
    _notes: list[str]
    _model_wired: bool

    def __init__(self) -> None:
        self._n_candidates = 0
        self._class_counts = {}
        self._grid_cells = 0
        self._data_gaps = [k for k, _, avail in PROSPECT_CRITERIA if not avail]
        self._notes = []
        self._model_wired = False

    # ------------------------------------------------------------------ #

    def run(self, ctx: RunContext) -> PhaseResult:
        pdir = ctx.phase_dir(self.id)
        result = PhaseResult(self.id, status="dry-run" if ctx.dry_run else "ok")

        if ctx.dry_run:
            self._emit_prospect_schema(ctx, pdir, result)
            self._emit_registers(ctx, pdir, result, prospects=[])
            self._write_method_note(ctx, pdir, result)
            self._notes.append(
                "dry-run: 5 folders + prospect schema + empty ranking/GoNoGo templates"
            )
            result.log("dry-run: Phase 04 scaffold + templates (no grid/scoring)")
            self._write_qaqc_log(ctx, pdir, result)
            return result

        prospects = self._delineate_and_rank(ctx, pdir, result)
        self._emit_registers(ctx, pdir, result, prospects=prospects)
        self._write_method_note(ctx, pdir, result)
        self._write_qaqc_log(ctx, pdir, result)
        result.log(
            f"grid cells={self._grid_cells}; candidate prospects={self._n_candidates} "
            f"(classes {self._class_counts}); data-gap criteria={self._data_gaps}"
        )
        return result

    # ------------------------------------------------------------------ #
    # inputs
    # ------------------------------------------------------------------ #

    def _evidence_gpkg(self, ctx: RunContext) -> Path | None:
        p03 = ctx.phase_dir("03") / "09_Geological_Evidence_Layers_GPKG"
        gpkgs = sorted(p03.glob("*Geological_Evidence*.gpkg"))
        return gpkgs[0] if gpkgs else None

    def _load_evidence(self, gpkg: Path) -> dict:  # type: ignore[type-arg]
        """Load the non-empty layers of the Phase 03 evidence GPKG into {name: GeoDataFrame}."""
        ev: dict = {}  # type: ignore[type-arg]
        for layer in vector_io.list_gpkg_layers(gpkg):
            try:
                g = vector_io.read_layer(gpkg, layer)
            except Exception:
                continue
            if g is not None and len(g):
                ev[layer] = g
        return ev

    def _load_boundary(self, ctx: RunContext, ev: dict):  # type: ignore[no-untyped-def,type-arg]
        """Licence boundary AOI: prefer the evidence GPKG's license_boundary, else Phase 01's."""
        if "license_boundary" in ev:
            return ev["license_boundary"]
        cfg = ctx.config
        name = naming.data_name(
            cfg.data_prefix,
            f"{cfg.project.license_code}_LicenseBoundary",
            crs_or_param=naming.epsg_tag(cfg.target_epsg),
            version=1,
            ext="gpkg",
        )
        path = ctx.phase_dir("01") / "05_KMZ_KML_to_GPKG" / name
        return vector_io.read_layer(path, "license_boundary") if path.exists() else None

    # ------------------------------------------------------------------ #
    # scoring + delineation
    # ------------------------------------------------------------------ #

    def _delineate_and_rank(self, ctx: RunContext, pdir: Path, result: PhaseResult) -> list[dict]:  # type: ignore[type-arg]
        import geopandas as gpd

        cfg = ctx.config
        epsg = cfg.target_epsg
        gpkg = self._evidence_gpkg(ctx)
        if gpkg is None:
            self._notes.append(
                "Phase 03 evidence GPKG not found; run Phase 03 first — no prospects"
            )
            self._emit_prospect_schema(ctx, pdir, result)
            return []
        ev = self._load_evidence(gpkg)
        boundary = self._load_boundary(ctx, ev)
        if boundary is None:
            self._notes.append(
                "Licence boundary not found; cannot build scoring grid — no prospects"
            )
            self._emit_prospect_schema(ctx, pdir, result)
            return []

        # evidence overlay (01): the non-empty layers actually used for scoring, for traceability
        overlay_path = (
            pdir
            / "01_Evidence_Overlay"
            / naming.data_name(
                cfg.data_prefix,
                "Evidence_Overlay",
                crs_or_param=naming.epsg_tag(epsg),
                version=1,
                ext="gpkg",
            )
        )
        for name, g in ev.items():
            vector_io.write_layer(g.to_crs(epsg=epsg), overlay_path, layer=name, mode="a")
        if overlay_path.exists():
            result.add_output(overlay_path)

        # scoring grid over boundary + context margin
        aoi = boundary.to_crs(epsg=epsg).copy()
        aoi["geometry"] = aoi.geometry.buffer(CONTEXT_BUFFER_M)
        cells = vector_io.make_grid(aoi, GRID_CELL_M, epsg)
        self._grid_cells = len(cells)
        cells = self._score_cells(cells, ev, epsg)
        grid_path = (
            pdir
            / "03_Scoring_Matrix"
            / naming.data_name(
                cfg.data_prefix,
                "Evidence_Score_Grid",
                crs_or_param=naming.epsg_tag(epsg),
                version=1,
                ext="gpkg",
            )
        )
        vector_io.write_layer(cells, grid_path, layer=_GRID_LAYER)
        result.add_output(grid_path)

        # delineate: dissolve high-score cells into contiguous candidate clusters
        high = cells[cells["score"] >= SCORE_THRESHOLD].copy()
        prospects: list[dict] = []  # type: ignore[type-arg]
        if len(high):
            clusters = vector_io.dissolve_adjacent(high)
            joined = gpd.sjoin(high, clusters, predicate="intersects", how="left")
            prospects = self._build_prospects(clusters, joined, ev, epsg)

        # write the prospect polygons gpkg (02)
        prospect_path = (
            pdir
            / "02_Prospect_Polygon_Delineation"
            / naming.data_name(
                cfg.data_prefix,
                "Prospect_Polygons",
                crs_or_param=naming.epsg_tag(epsg),
                version=1,
                ext="gpkg",
            )
        )
        if prospects:
            geoms = [
                p.pop("_geometry") for p in prospects
            ]  # registers reuse the geometry-less rows
            gdf = gpd.GeoDataFrame(prospects, geometry=geoms, crs=f"EPSG:{epsg}")
            gdf = gdf.reindex(columns=[*_PROSPECT_COLUMNS, "geometry"])
            vector_io.write_layer(gdf, prospect_path, layer=_PROSPECT_LAYER)
        else:
            self._emit_prospect_schema(ctx, pdir, result, path=prospect_path)
        result.add_output(prospect_path)

        self._n_candidates = len(prospects)
        counts: dict[str, int] = {}
        for p in prospects:
            counts[p["prospect_class"]] = counts.get(p["prospect_class"], 0) + 1
        self._class_counts = counts
        return prospects

    def _score_cells(self, cells, ev: dict, epsg: int):  # type: ignore[no-untyped-def,type-arg]
        """Add per-criterion score columns + total ``score`` + ``priority`` to the grid cells."""
        import pandas as pd

        n = len(cells)
        falses = pd.Series([False] * n, index=cells.index)

        def present(  # type: ignore[no-untyped-def]
            layer_names: list[str], buffer_m: float = 0.0, boundary: bool = False
        ):
            from shapely.ops import unary_union

            geoms = []
            for name in layer_names:
                g = ev.get(name)
                if g is not None and len(g):
                    m = (
                        g.geometry.union_all()
                        if hasattr(g.geometry, "union_all")
                        else g.geometry.unary_union
                    )
                    # ``boundary`` scores CONTACTS (polygon edges) rather than blanket interiors,
                    # so a map-covering unit does not flag every cell — it discriminates on the
                    # favorable-contact setting the methodology intends.
                    if boundary:
                        m = m.boundary
                    geoms.append(m.buffer(buffer_m) if buffer_m else m)
            if not geoms:
                return falses
            return cells.geometry.intersects(unary_union(geoms))

        alter_layers = [k for k in ev if "alter" in k.lower() or "aster" in k.lower()]
        road_layers = [k for k in ev if "road" in k.lower()]
        flags = {
            # geology: favorable-CONTACT setting — near a geology-unit contact (polygon boundary)
            # or an intrusive contact — not merely inside any mapped unit (which blankets the map).
            "geology": present(
                ["geology_units_50k_polygon", "geology_units_200k_polygon"],
                GRID_CELL_M,
                boundary=True,
            )
            | present(["intrusive_contacts_line"], GRID_CELL_M),
            "geochem": present(
                ["mineral_occurrences_point", "mineralized_points_point"], OCCURRENCE_NEAR_M
            ),
            "rs": present(alter_layers),
            "structure": present(
                ["faults_structures_line", "dyke_vein_line", "intrusive_contacts_line"], GRID_CELL_M
            ),
            "field_pxrf": falses,
            "drone": falses,
            # cmcs: localized nearest-deposit/metallogenic context, NOT the whole filled 25 km buffer
            # (which covers the entire AOI and gives every cell a flat +7).
            "cmcs": present(["metallogenic_zones_polygon"], GRID_CELL_M)
            | present(["cmcs_nearest_occurrences_point"], OCCURRENCE_NEAR_M),
            "access": present(road_layers, ACCESS_NEAR_M),
        }
        total = pd.Series([0] * n, index=cells.index)
        for key, _w, _a in PROSPECT_CRITERIA:
            f = flags[key].astype(bool)
            cells[f"score_{key}"] = (f * _CRIT_WEIGHT[key]).astype(int)
            cells[f"flag_{key}"] = f
            total = total + cells[f"score_{key}"]
        cells["score"] = total.astype(int)
        cells["priority"] = cells["score"].map(classify)
        return cells

    def _build_prospects(self, clusters, joined, ev: dict, epsg: int) -> list[dict]:  # type: ignore[no-untyped-def,type-arg]
        """Aggregate scored cells per contiguous cluster into ranked prospect records."""
        import geopandas as gpd
        import pandas as pd

        # nearest-feature distance sources
        dist_src = {
            "dist_fault_m": ev.get("faults_structures_line"),
            "dist_dyke_m": ev.get("dyke_vein_line"),
            "dist_occ_m": ev.get("mineral_occurrences_point"),
            "dist_min_point_m": ev.get("mineralized_points_point"),
            "dist_road_m": next((ev[k] for k in ev if "road" in k.lower()), None),
        }
        rows: list[dict] = []  # type: ignore[type-arg]
        for _, cl in clusters.iterrows():
            cid = cl["cluster_id"]
            members = joined[joined["cluster_id"] == cid]
            if members.empty:
                continue
            max_score = int(members["score"].max())
            mean_score = round(float(members["score"].mean()), 1)
            cls = classify(max_score)
            geom = cl.geometry
            rep = geom.representative_point()
            row: dict = {  # type: ignore[type-arg]
                "_geometry": geom,
                "rank": 0,  # filled after sort
                "prospect_class": cls,
                "area_ha": round(geom.area / 10_000.0, 2),
                "max_score": max_score,
                "mean_score": mean_score,
                "centroid_E": round(rep.x, 1),
                "centroid_N": round(rep.y, 1),
            }
            for key, w, _a in PROSPECT_CRITERIA:
                any_flag = bool(members[f"flag_{key}"].any())
                row[f"score_{key}"] = w if any_flag else 0
            # nearest-feature distances (from the cluster geometry)
            one = pd.DataFrame({"geometry": [geom]})
            one_gdf = gpd.GeoDataFrame(one, geometry="geometry", crs=f"EPSG:{epsg}")
            for col, src in dist_src.items():
                d = vector_io.nearest_distance(one_gdf, src).iloc[0]
                row[col] = None if pd.isna(d) else round(float(d), 1)
            row.update(self._interpret(row))
            rows.append(row)

        rows.sort(key=lambda r: r["max_score"], reverse=True)
        for i, r in enumerate(rows, start=1):
            r["rank"] = i
            r["candidate_id"] = f"{_FEATURE_PREFIX}-{i:04d}"
        return rows

    def _interpret(self, row: dict) -> dict:  # type: ignore[type-arg]
        """Deposit-model wiring + interpretive text for a prospect row (v9 §04 step 5)."""
        self._model_wired = True
        present_crit = [k for k, _w, _a in PROSPECT_CRITERIA if row.get(f"score_{k}", 0) > 0]
        interp = (
            "Structural/alteration + geochem/occurrence target"
            if {"geology", "structure", "geochem"} & set(present_crit)
            else "Contextual target (sparse desktop evidence)"
        )
        return {
            "elements": "",  # populated when geochem-anomaly attributes are ingested (data gap)
            "dominant_deposit_model": DEPOSIT_MODELS[0][0],  # primary candidate; refine in 03A
            "model_confidence": "pending (see Phase 03 03A score matrix)",
            "missing_model_evidence": "; ".join(self._data_gaps),
            "validation_priority": _CLASS_VALIDATION_PRIORITY[row["prospect_class"]],
            "target_interpretation": interp,
            "recommended_followup": _RECOMMENDED_FOLLOWUP,
            "validation_status": PROSPECT_VALIDATION,
            "limitation": PROSPECT_LIMITATION,
            "source_phase": "04",
        }

    # ------------------------------------------------------------------ #
    # outputs (registers / schema / notes)
    # ------------------------------------------------------------------ #

    def _emit_prospect_schema(
        self, ctx: RunContext, pdir: Path, result: PhaseResult, path: Path | None = None
    ) -> None:
        cfg = ctx.config
        if path is None:
            path = (
                pdir
                / "02_Prospect_Polygon_Delineation"
                / naming.data_name(
                    cfg.data_prefix,
                    "Prospect_Polygons",
                    crs_or_param=naming.epsg_tag(cfg.target_epsg),
                    version=1,
                    ext="gpkg",
                )
            )
        vector_io.create_evidence_gpkg(
            path, [(_PROSPECT_LAYER, "MultiPolygon")], _PROSPECT_PROPS, cfg.target_epsg
        )
        result.add_output(path)

    def _emit_registers(
        self,
        ctx: RunContext,
        pdir: Path,
        result: PhaseResult,
        prospects: list[dict],  # type: ignore[type-arg]
    ) -> None:
        cfg = ctx.config
        rp = cfg.register_prefix

        def reg(desc: str) -> str:
            return naming.register_name(rp, desc, ext="xlsx", version=1)

        ranking_rows = [{c: p.get(c, "") for c in _RANKING_TABLE_COLUMNS} for p in prospects]
        gonogo_rows = [
            {
                "candidate_id": p["candidate_id"],
                "prospect_class": p["prospect_class"],
                "max_score": p["max_score"],
                "desktop_decision": _CLASS_DECISION[p["prospect_class"]],
                "rationale": f"Class {p['prospect_class']} (max score {p['max_score']}/100, "
                f"{p['validation_priority'].lower()} validation priority).",
                "next_action": "Drone survey + recon mapping"
                if p["prospect_class"] in ("A", "B")
                else "Retain with data gaps; opportunistic/desk check",
            }
            for p in prospects
        ]
        gap_rows = [
            {
                "criterion": k,
                "weight": _CRIT_WEIGHT[k],
                "status": "AVAILABLE" if avail else "DATA GAP (scored 0)",
                "acquired_in_phase": {
                    "rs": "02 (ASTER/Sentinel — external SNAP/ILWIS method-note)",
                    "field_pxrf": "06 (recon mapping + pXRF)",
                    "drone": "05 (drone LiDAR/photogrammetry)",
                    "access": "human roads layer / field recon",
                }.get(k, "—"),
                "note": ""
                if avail
                else "Not available at desktop Phase 04; upgrades the score once acquired.",
            }
            for k, _w, avail in PROSPECT_CRITERIA
        ]

        tables: list[tuple[Path, list[str], list[dict], str]] = [  # type: ignore[type-arg]
            (
                pdir / "03_Scoring_Matrix" / reg("Prospect_Ranking_Table"),
                _RANKING_TABLE_COLUMNS,
                ranking_rows,
                "Prospect Ranking",
            ),
            (
                pdir / "05_A_B_C_D_Field_Priority" / reg("Go_NoGo_Desktop_Decision_Matrix"),
                _GONOGO_COLUMNS,
                gonogo_rows,
                "Go NoGo Decision",
            ),
            (
                pdir / "04_Confidence_DataGap_NextAction" / reg("Prospect_DataGap_and_NextAction"),
                _DATAGAP_COLUMNS,
                gap_rows,
                "Data Gap NextAction",
            ),
        ]
        for path, columns, rows, title in tables:
            registers.write_table_xlsx(rows, columns, path, sheet_title=title)
            result.add_output(path)

    def _write_method_note(self, ctx: RunContext, pdir: Path, result: PhaseResult) -> None:
        cfg = ctx.config
        note = (
            pdir
            / "05_A_B_C_D_Field_Priority"
            / (f"{cfg.project.project_code}_{cfg.project.name}_Phase04_Method_Note.md")
        )
        note.parent.mkdir(parents=True, exist_ok=True)
        weights = ", ".join(f"{k} {w}" for k, w, _ in PROSPECT_CRITERIA)
        note.write_text(
            f"# Phase 04 — Preliminary Prospect Delineation & Ranking (method note)\n\n"
            f"Created {date.today().isoformat()}. All outputs are **{PROSPECT_VALIDATION}**.\n\n"
            f"## Scoring (v9 §5, weights sum 100)\n{weights}\n\n"
            f"Grid {int(GRID_CELL_M)} m over the licence + {int(CONTEXT_BUFFER_M)} m context; each cell "
            f"scores a criterion's full weight when its evidence is present (occurrence proximity "
            f"{int(OCCURRENCE_NEAR_M)} m, access {int(ACCESS_NEAR_M)} m). Geology scores near unit "
            f"**contacts** (polygon boundaries + intrusive contacts), not blanket interiors, and CMCS "
            f"scores **localized** nearest-deposit/metallogenic context, not the whole filled buffer — "
            f"so scores discriminate rather than saturate. Cells scoring >= {SCORE_THRESHOLD} are "
            f"dissolved into candidate polygons; class by max score (A>=75, B 55-74, C 35-54, D<35).\n\n"
            f"## Desktop data gaps (scored 0)\n"
            f"ASTER/Sentinel alteration (Phase 02 method-note), field/pXRF (Phase 06), drone LiDAR "
            f"(Phase 05). Desktop prospects therefore land B/C; A/B advance to field to upgrade.\n\n"
            f"## Ranking map\n`..._Preliminary_Prospect_Ranking_Map.pdf` is a QGIS print layout "
            f"over the prospect polygons (human deliverable); the pipeline emits the polygons, "
            f"ranking table, Go/No-Go matrix and data-gap register.\n",
            encoding="utf-8",
        )
        result.add_output(note)

    def _write_qaqc_log(self, ctx: RunContext, pdir: Path, result: PhaseResult) -> None:
        report = self.qaqc(ctx)
        path = (
            pdir
            / "05_A_B_C_D_Field_Priority"
            / naming.register_name(
                ctx.config.register_prefix, "Phase4_QAQC_Log", ext="xlsx", version=1
            )
        )
        report.write_xlsx(path)
        result.add_output(path)

    # ------------------------------------------------------------------ #

    def qaqc(self, ctx: RunContext) -> QAQCReport:
        report = new_report(self.id, self.name)
        if ctx.dry_run:
            report.add(
                "Phase 4 scaffolding created",
                "5 folders, prospect schema + ranking/Go-NoGo/data-gap templates present (dry-run).",
                decision=Decision.PASS,
                note="Dry-run: no evidence scored.",
            )
            return report

        report.add(
            "100-point ranking matrix calculated over the evidence grid",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._grid_cells else Decision.FAIL,
            note=f"{self._grid_cells} grid cells scored on the v9 §5 8-criterion matrix.",
        )
        report.add(
            "Prospect polygons delineated and A/B/C/D class assigned",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._n_candidates else Decision.PENDING,
            note=(
                f"{self._n_candidates} candidate prospect(s): {self._class_counts}."
                if self._n_candidates
                else "No cell reached the candidate threshold on current (sparse desktop) evidence."
            ),
        )
        report.add(
            "Confidence / data-gap / next-action recorded",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS,
            note=f"Data-gap register lists {len(self._data_gaps)} desktop-unavailable criterion(s).",
        )
        report.add(
            "Deposit-model score wired from Phase 03 (03A)",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS if self._model_wired else Decision.PENDING,
            note="dominant_deposit_model + model_confidence/validation_priority set per prospect "
            "(model_confidence pending human completion of the 03A score matrix).",
        )
        report.add(
            "Field access and safety checked",
            RECORDED_ACCEPTANCE,
            decision=Decision.PENDING,
            note="Access scored from roads layer where present; field access/safety confirmed by "
            "human before drone/recon (desktop data gap).",
        )
        report.add(
            "Desktop remote-sensing / field / drone criteria recorded as data gaps",
            "RS(15)/field-pXRF(15)/drone(8) score 0 at desktop; recorded, non-blocking (invariant #8).",
            decision=Decision.PASS,
            note="; ".join(self._data_gaps),
        )
        return report


PHASE = Phase04ProspectRanking
