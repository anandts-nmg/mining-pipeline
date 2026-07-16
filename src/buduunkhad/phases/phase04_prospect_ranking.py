"""Phase 04 — Preliminary Prospect Delineation & Ranking (BUILD).

Turns the Phase 03 geological-evidence package into ranked preliminary prospects, per the
methodology (v9 §04 + the Phase-4 guide §6 **desktop scoring matrix** — conflict 04-1): build an
evidence-scoring grid over the licence AOI, score each cell on the 8-criterion weighted matrix
(geology 20 / occurrence 15 / geochem 20 / RS 15 / structure 10 / deposit-model fit 10 / access 5 /
confidence 5 = 100), dissolve high-score cells into candidate prospect polygons, assign the
**A/B/C/D** field-priority class (A>=75, B 55-74, C 35-54, D<35), wire in the Phase 03 03A
deposit-model outputs, and emit the four deliverables. The guide's matrix is desktop-only (no
field/drone criteria — those belong to the v9 §5 lifecycle matrix used at Phase 10), so a
well-evidenced desktop prospect CAN reach class A.

**Attribute-aware scoring.** Beyond the Phase 03 evidence GPKG (a geometry-only shared schema),
Phase 04 also reads *attribute-bearing* prospectivity layers dropped anywhere under the Phase 03/04
dirs (whitelisted by keyword, so pipeline outputs never match): **focused alteration**
(argillic / porphyry / sericite / silica, or hand-digitized alteration) activates the ``rs``
criterion, and **geochem-anomaly** polygons drive ``geochem`` and populate each prospect's
``elements`` from the anomaly's element attribute. Regional chlorite-epidote *propylitic halo* is
deliberately excluded as context — it blankets the district and would re-saturate the score. Any
layer carrying the AI handoff lifecycle is also excluded until an authoritative integration adapter
is adopted; file proximity is never sufficient authority.

**Honesty (invariant #8).** Criteria whose evidence is absent (``rs`` without fed alteration,
``model_fit`` until the human completes the 03A score matrix, ``access`` without a roads layer)
score **0** and are flagged as data gaps. Every output is stamped *"Preliminary — not ore proof"* —
class A here still means "field/lab follow-up priority", never a confirmed deposit.
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

# Phase-4 guide §6 desktop scoring matrix — 8 weighted criteria summing to 100 (conflict 04-1:
# adopted over the master v9 §5 lifecycle matrix, per the repo rule that the later per-phase
# deep-dive guide is the phase authority; §5 — which adds field/pXRF/drone criteria — remains the
# lifecycle matrix for the Phase 10 final ranking). DISTINCT from Phase 03's SCORING_CRITERIA
# (the 03A deposit-model rubric): this scores prospect *polygons*, that scores deposit *models*.
# The bool marks criteria whose evidence exists in-pipeline by default; availability is
# re-derived from the actual evidence at run time.
PROSPECT_CRITERIA: list[tuple[str, int, bool]] = [
    ("geology", 20, True),  # geological setting: lithology/contact/alteration (§6.2)
    ("occurrence", 15, True),  # known occurrence / showing in or near the prospect (§6.3)
    ("geochem", 20, True),  # stream/soil/rock/heavy-mineral anomaly (§6.4)
    ("rs", 15, False),  # ASTER/Sentinel/KOMPSAT indication (§6.5); needs fed alteration
    ("structure", 10, True),  # fault/shear/lineament control (§6.6)
    ("model_fit", 10, False),  # Phase 03 03A deposit-model fit (§6.7); pending human matrix
    ("access", 5, False),  # road/terrain/logistics (§6.8); needs a roads layer
    ("confidence", 5, True),  # evidence completeness / traceability (§6.9); always derivable
]
_CRIT_WEIGHT = {k: w for k, w, _ in PROSPECT_CRITERIA}

# Grid + proximity tuning (module constants, like Phase 03's CMCS_RINGS_M).
GRID_CELL_M = 250.0
CONTEXT_BUFFER_M = 1000.0  # grid the licence boundary + this context margin
SCORE_THRESHOLD = 35  # the C floor: only A/B/C-band cells become prospect polygons (D excluded)
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

# Attribute-evidence roles (Phase 04 reads these WITH attributes, from any gpkg dropped under the
# Phase 03/04 dirs, keyed by filename/layer keyword — whitelisted so pipeline outputs never match).
# `rs` scores only FOCUSED alteration (argillic/porphyry/sericite/silica + hand-digitized alteration)
# — the methodology's high-score indicator. Regional chlorite-epidote *propylitic halo* is deliberately
# excluded: it blankets the district and would re-saturate the score (it's context, not a target).
_ALTER_KEYS = ("argil", "porphyry", "sericite", "silica", "alter")
_GEOCHEM_KEYS = ("geochem", "anomaly", "anom")
_ELEMENT_COLS = ("main_element", "elements", "element", "element_gr", "commodity", "main_eleme")


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
    _criteria_available: dict[str, bool]
    _notes: list[str]
    _model_wired: bool
    _model_fit: dict[str, object]

    def __init__(self) -> None:
        self._n_candidates = 0
        self._class_counts = {}
        self._grid_cells = 0
        self._data_gaps = [k for k, _, avail in PROSPECT_CRITERIA if not avail]
        self._criteria_available = {k: avail for k, _, avail in PROSPECT_CRITERIA}
        self._notes = []
        self._model_wired = False
        self._model_fit = {
            "score": 0,
            "model": DEPOSIT_MODELS[0][0],
            "label": "pending (03A score matrix not yet completed)",
            "available": False,
        }

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
        expected = p03 / naming.data_name(
            ctx.config.data_prefix,
            "Geological_Evidence_Layers",
            version=1,
            ext="gpkg",
        )
        return expected if expected.is_file() else None

    def _load_evidence(self, gpkg: Path) -> dict:  # type: ignore[type-arg]
        """Load the non-empty layers of the Phase 03 evidence GPKG into {name: GeoDataFrame}."""
        ev: dict = {}  # type: ignore[type-arg]
        for layer in vector_io.list_gpkg_layers(gpkg):
            try:
                g = vector_io.read_layer(gpkg, layer)
            except Exception:
                continue
            if g is not None and len(g):
                eligible = self._legacy_evidence_rows(g)
                if len(eligible):
                    ev[layer] = eligible
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

    def _load_attribute_evidence(self, ctx: RunContext) -> dict:  # type: ignore[type-arg]
        """Load attribute-bearing prospectivity evidence dropped under the Phase 03/04 dirs.

        Unlike the Phase 03 evidence GPKG (geometry-only shared schema), these keep their source
        attributes so Phase 04 can score the methodology's real criteria: ASTER/alteration polygons
        activate ``rs``; geochem-anomaly polygons drive ``geochem`` and populate ``elements``.
        Whitelisted by filename/layer keyword, so the pipeline's own outputs never match. Returns
        ``{alteration: geom|None, geochem_union: geom|None, geochem_gdfs: [gdf, ...]}``.
        """
        from shapely.ops import unary_union

        alter_geoms: list = []  # type: ignore[type-arg]
        geochem_gdfs: list = []  # type: ignore[type-arg]
        seen: set[str] = set()
        for base in (ctx.phase_dir("03"), ctx.phase_dir("04")):
            if not base.exists():
                continue
            for src in sorted(base.rglob("*.gpkg")):
                if "AI_DRAFT" in src.name.upper():
                    continue
                try:
                    layers = vector_io.list_gpkg_layers(src)
                except Exception:
                    continue
                for layer in layers:
                    low = f"{src.name} {layer}".lower()
                    is_alter = any(k in low for k in _ALTER_KEYS)
                    is_geochem = any(k in low for k in _GEOCHEM_KEYS)
                    key = f"{src}::{layer}"
                    if not (is_alter or is_geochem) or key in seen:
                        continue
                    try:
                        g = vector_io.read_layer(src, layer)
                    except Exception:
                        continue
                    if g is None or len(g) == 0:
                        continue
                    g = self._legacy_evidence_rows(g)
                    if len(g) == 0:
                        continue
                    seen.add(key)
                    g = g.to_crs(epsg=ctx.config.target_epsg)
                    (geochem_gdfs if is_geochem else alter_geoms).append(g)

        def _union(gdfs):  # type: ignore[no-untyped-def]
            parts = [
                (
                    h.geometry.union_all()
                    if hasattr(h.geometry, "union_all")
                    else h.geometry.unary_union
                )
                for h in gdfs
            ]
            return unary_union(parts) if parts else None

        return {
            "alteration": _union(alter_geoms),
            "geochem_union": _union(geochem_gdfs),
            "geochem_gdfs": geochem_gdfs,
        }

    @staticmethod
    def _legacy_evidence_rows(gdf):  # type: ignore[no-untyped-def]
        """Exclude every AI-lifecycle row until an authoritative adapter exists.

        Untagged layers retain the legacy human-authored behavior. A standalone Phase 03 handoff
        package is not an authoritative Phase 04 input merely because it was copied beneath a
        discovered directory, even when it carries ``ACCEPTED_EVIDENCE``. A future integration
        must resolve that package explicitly before the fixed-grid comparator can consume it.
        """

        lifecycle = {
            "proposal_state",
            "review_state",
            "evidence_state",
            "review_decision",
            "review_status",
        }
        if not lifecycle & set(gdf.columns):
            return gdf
        return gdf.iloc[0:0].copy()

    def _load_model_fit(self, ctx: RunContext) -> None:
        """Score guide §6.7 (deposit-model fit, 10 pts) from the Phase 03 03A score matrix.

        The 03A matrix (criterion x 6 models + a Total row) is a human-completed artifact. When
        the human has filled numeric scores, the best model's total maps onto the §6.7 band
        (via the 03A confidence thresholds: >=70 -> 10, 50-69 -> 7, 30-49 -> 4, else 1) and names
        ``dominant_deposit_model``; while it is still an empty template, model_fit scores 0 and is
        recorded as a pending data gap.
        """
        matrices = sorted(
            (ctx.phase_dir("03") / "10_Preliminary_Deposit_Model_03A").glob(
                "*deposit_model_candidate_score_matrix*.xlsx"
            )
        )
        if not matrices:
            return
        try:
            import openpyxl

            ws = openpyxl.load_workbook(matrices[0]).active
            if ws is None:
                return
            rows = list(ws.iter_rows(values_only=True))
        except Exception:
            return
        if not rows:
            return
        header = [str(c) for c in rows[0]]
        model_cols = [
            i for i, h in enumerate(header) if h not in ("criterion", "max_points", "None")
        ]
        total_row = next((r for r in rows[1:] if str(r[0]).strip().lower() == "total"), None)
        best_score, best_model = 0.0, ""
        source = [total_row] if total_row is not None else rows[1:]
        for i in model_cols:
            vals = []
            for r in source:
                try:
                    vals.append(float(str(r[i])))
                except (TypeError, ValueError):
                    continue
            if not vals:
                continue
            score = vals[0] if total_row is not None else sum(vals)
            if score > best_score:
                best_score, best_model = score, header[i]
        if best_score <= 0:
            return  # template still empty -> stays pending
        if best_score >= 70:
            pts, label = 10, "High priority model"
        elif best_score >= 50:
            pts, label = 7, "Moderate priority model"
        elif best_score >= 30:
            pts, label = 4, "Low / conceptual model"
        else:
            pts, label = 1, "Insufficient evidence"
        self._model_fit = {
            "score": pts,
            "model": best_model,
            "label": f"{label} ({best_score:.0f}/100 in 03A)",
            "available": True,
        }

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
        attr = self._load_attribute_evidence(ctx)
        self._load_model_fit(ctx)
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
        # Rebuild from scratch: the per-layer appends below would otherwise accumulate duplicate
        # features into a file that survives between runs (a re-run must not double the overlay).
        overlay_path.unlink(missing_ok=True)
        for name, g in ev.items():
            vector_io.write_layer(g.to_crs(epsg=epsg), overlay_path, layer=name, mode="a")
        if overlay_path.exists():
            result.add_output(overlay_path)

        # scoring grid over boundary + context margin
        aoi = boundary.to_crs(epsg=epsg).copy()
        aoi["geometry"] = aoi.geometry.buffer(CONTEXT_BUFFER_M)
        cells = vector_io.make_grid(aoi, GRID_CELL_M, epsg)
        self._grid_cells = len(cells)
        cells = self._score_cells(cells, ev, attr, epsg)
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

        # delineate PER CLASS BAND: contiguous A cells -> discrete A prospects, B cells -> B
        # prospects, C cells -> retained C prospects (D = below the C floor, not a prospect).
        # A single >=threshold dissolve would merge the whole evidence-rich zone into one blob;
        # banded dissolve yields the discrete, per-priority cores the methodology's A/B/C/D
        # decision gate acts on (A/B -> drone/recon; C retained with data gaps).
        prospects: list[dict] = []  # type: ignore[type-arg]
        for cls in ("A", "B", "C"):
            sub = cells[cells["priority"] == cls].copy()
            if not len(sub):
                continue
            clusters = vector_io.dissolve_adjacent(sub)
            assert clusters is not None  # sub is non-empty, so dissolve returns a GeoDataFrame
            # "within", not "intersects": a cell belongs to exactly the cluster that covers it —
            # "intersects" would also attach it to a neighbouring cluster it merely corner-touches,
            # double-counting the cell into that cluster's max/mean scores.
            joined = gpd.sjoin(sub, clusters, predicate="within", how="left")
            prospects.extend(self._build_prospects(clusters, joined, ev, attr, epsg))
        # global rank + ids across all bands (score first, then size)
        prospects.sort(key=lambda r: (r["max_score"], r["area_ha"]), reverse=True)
        for i, r in enumerate(prospects, start=1):
            r["rank"] = i
            r["candidate_id"] = f"{_FEATURE_PREFIX}-{i:04d}"

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
            result.add_output(prospect_path)
        else:
            # emits the empty schema AND records the output (avoid a duplicate manifest entry)
            self._emit_prospect_schema(ctx, pdir, result, path=prospect_path)

        self._n_candidates = len(prospects)
        counts: dict[str, int] = {}
        for p in prospects:
            counts[p["prospect_class"]] = counts.get(p["prospect_class"], 0) + 1
        self._class_counts = counts
        return prospects

    def _score_cells(self, cells, ev: dict, attr: dict, epsg: int):  # type: ignore[no-untyped-def,type-arg]
        """Add per-criterion score columns + total ``score`` + ``priority`` to the grid cells."""
        import pandas as pd

        n = len(cells)
        falses = pd.Series([False] * n, index=cells.index)

        def hit(geom):  # type: ignore[no-untyped-def]
            return cells.geometry.intersects(geom) if geom is not None else falses

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

        def _has(layers: list[str]) -> bool:
            for x in layers:
                g = ev.get(x)
                if g is not None and len(g) > 0:
                    return True
            return False

        # availability = the evidence SOURCE exists (drives the data-gap register, qaqc, and the
        # §6.9 confidence points), independent of whether any cell happened to flag it.
        self._criteria_available = {
            "geology": _has(
                [
                    "geology_units_50k_polygon",
                    "geology_units_200k_polygon",
                    "intrusive_contacts_line",
                ]
            ),
            "occurrence": _has(["mineral_occurrences_point", "mineralized_points_point"]),
            "geochem": attr.get("geochem_union") is not None,
            "rs": bool(alter_layers) or attr.get("alteration") is not None,
            "structure": _has(
                ["faults_structures_line", "dyke_vein_line", "intrusive_contacts_line"]
            ),
            "model_fit": bool(self._model_fit["available"]),
            "access": bool(road_layers),
            "confidence": True,  # §6.9 completeness is always derivable
        }
        # §6.9 confidence points = evidence completeness across the 7 evidence criteria.
        n_avail = sum(1 for k, v in self._criteria_available.items() if k != "confidence" and v)
        confidence_pts = 5 if n_avail >= 6 else 3 if n_avail >= 4 else 1 if n_avail >= 2 else 0
        self._data_gaps = [k for k in self._criteria_available if not self._criteria_available[k]]

        trues = ~falses
        flags = {
            # geology (§6.2): favorable-CONTACT setting — near a geology-unit contact (polygon
            # boundary) or an intrusive contact — not merely inside any mapped unit (which
            # blankets the map).
            "geology": present(
                ["geology_units_50k_polygon", "geology_units_200k_polygon"],
                GRID_CELL_M,
                boundary=True,
            )
            | present(["intrusive_contacts_line"], GRID_CELL_M),
            # occurrence (§6.3): a known occurrence / mineralized point in or near the cell.
            "occurrence": present(
                ["mineral_occurrences_point", "mineralized_points_point"], OCCURRENCE_NEAR_M
            ),
            # geochem (§6.4): inside an attribute-bearing geochem-anomaly polygon.
            "geochem": hit(attr.get("geochem_union")),
            # rs (§6.5): overlaps a focused ASTER/alteration polygon (attribute-evidence path).
            "rs": present(alter_layers) | hit(attr.get("alteration")),
            # structure (§6.6): near a fault / dyke / intrusive contact.
            "structure": present(
                ["faults_structures_line", "dyke_vein_line", "intrusive_contacts_line"], GRID_CELL_M
            ),
            # model_fit (§6.7) + confidence (§6.9) are run-level (not spatial): applied uniformly.
            "model_fit": trues if int(str(self._model_fit["score"])) > 0 else falses,
            "access": present(road_layers, ACCESS_NEAR_M),
            "confidence": trues if confidence_pts > 0 else falses,
        }
        # per-criterion points: spatial criteria award the full §6 band weight on presence;
        # model_fit/confidence award their derived (graded) points.
        points = dict(_CRIT_WEIGHT)
        points["model_fit"] = int(str(self._model_fit["score"]))
        points["confidence"] = confidence_pts
        total = pd.Series([0] * n, index=cells.index)
        for key, _w, _a in PROSPECT_CRITERIA:
            f = flags[key].astype(bool)
            cells[f"score_{key}"] = (f * points[key]).astype(int)
            cells[f"flag_{key}"] = f
            total = total + cells[f"score_{key}"]
        cells["score"] = total.astype(int)
        cells["priority"] = cells["score"].map(classify)
        return cells

    def _build_prospects(self, clusters, joined, ev: dict, attr: dict, epsg: int) -> list[dict]:  # type: ignore[no-untyped-def,type-arg]
        """Aggregate scored cells per contiguous cluster into ranked prospect records."""
        import geopandas as gpd
        import pandas as pd

        geochem_gdfs = attr.get("geochem_gdfs") or []

        def elements_for(geom):  # type: ignore[no-untyped-def]
            """Distinct commodity/element tokens from geochem-anomaly polygons the prospect overlaps."""
            vals: set[str] = set()
            for gg in geochem_gdfs:
                cols = {c.lower(): c for c in gg.columns}
                ecol = next((cols[k] for k in _ELEMENT_COLS if k in cols), None)
                if ecol is None:
                    continue
                sel = gg[gg.geometry.intersects(geom)]
                for raw in sel[ecol].dropna().astype(str):
                    for tok in raw.replace("/", ",").replace(";", ",").split(","):
                        t = tok.strip()
                        if t and t.lower() != "nan":
                            vals.add(t)
            return ",".join(sorted(vals))

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
            for key, _w, _a in PROSPECT_CRITERIA:
                # the cells already carry the correct per-criterion points (graded for
                # model_fit/confidence); the prospect takes the best member cell's value
                row[f"score_{key}"] = int(members[f"score_{key}"].max())
            # nearest-feature distances (from the cluster geometry)
            one = pd.DataFrame({"geometry": [geom]})
            one_gdf = gpd.GeoDataFrame(one, geometry="geometry", crs=f"EPSG:{epsg}")
            for col, src in dist_src.items():
                d = vector_io.nearest_distance(one_gdf, src).iloc[0]
                row[col] = None if pd.isna(d) else round(float(d), 1)
            row.update(self._interpret(row))
            row["elements"] = elements_for(geom)  # from geochem-anomaly attributes (data-driven)
            rows.append(row)

        return rows  # rank + candidate_id are minted by the caller across all class bands

    def _interpret(self, row: dict) -> dict:  # type: ignore[type-arg]
        """Deposit-model wiring + interpretive text for a prospect row (v9 §04 step 5 / guide §6.7)."""
        self._model_wired = True
        present_crit = [k for k, _w, _a in PROSPECT_CRITERIA if row.get(f"score_{k}", 0) > 0]
        interp = (
            "Structural/alteration + geochem/occurrence target"
            if {"geology", "structure", "geochem", "occurrence"} & set(present_crit)
            else "Contextual target (sparse desktop evidence)"
        )
        return {
            "elements": "",  # overwritten by the caller from geochem-anomaly attributes (if fed)
            "dominant_deposit_model": str(self._model_fit["model"]),
            "model_confidence": str(self._model_fit["label"]),
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
                "status": "AVAILABLE" if self._criteria_available.get(k) else "DATA GAP (scored 0)",
                "acquired_in_phase": {
                    "rs": "02 (ASTER/Sentinel — external SNAP/ILWIS) or ingested alteration layer",
                    "geochem": "ingested geochem-anomaly polygons (attribute evidence)",
                    "model_fit": "03 (human completes the 03A deposit-model score matrix)",
                    "access": "human roads layer / field recon",
                }.get(k, "—"),
                "note": ""
                if self._criteria_available.get(k)
                else "Not available at desktop Phase 04; upgrades the score once acquired.",
            }
            for k, _w, _a in PROSPECT_CRITERIA
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
            f"## Scoring (Phase-4 guide §6 desktop matrix, weights sum 100 — conflict 04-1)\n"
            f"{weights}\n\n"
            f"(The master v9 §5 lifecycle matrix — which adds field/pXRF and drone criteria — is "
            f"used at Phase 10 final ranking, not here; see METHODOLOGY_DISCREPANCIES.md 04-1.)\n\n"
            f"Grid {int(GRID_CELL_M)} m over the licence + {int(CONTEXT_BUFFER_M)} m context; each cell "
            f"scores a criterion's full weight when its evidence is present (occurrence proximity "
            f"{int(OCCURRENCE_NEAR_M)} m, access {int(ACCESS_NEAR_M)} m). Geology scores near unit "
            f"**contacts** (polygon boundaries + intrusive contacts), not blanket interiors, and CMCS "
            f"scores **localized** nearest-deposit/metallogenic context, not the whole filled buffer — "
            f"so scores discriminate rather than saturate. Cells are dissolved into candidate "
            f"polygons PER CLASS BAND (contiguous A cells -> discrete A prospects, likewise B and C; "
            f"D = below the {SCORE_THRESHOLD} C-floor, not a prospect); class bands A>=75, B 55-74, "
            f"C 35-54, D<35.\n\n"
            f"## Attribute-aware evidence\n"
            f"Attribute-bearing layers dropped under the Phase 03/04 dirs are read for richer scoring: "
            f"focused alteration (argillic/porphyry/sericite/silica or hand-digitized) activates `rs`; "
            f"geochem-anomaly polygons drive `geochem` + populate `elements`. Regional chlorite-epidote "
            f"propylitic halo is excluded as context (it blankets the district).\n\n"
            f"## Data gaps (scored 0)\n"
            f"`rs` without fed focused alteration; `model_fit` until the 03A score matrix is "
            f"human-completed; `access` without a roads layer. `confidence` (5) grades evidence "
            f"completeness. Field/pXRF/drone evidence enters at Phases 05-06 and is scored by the "
            f"v9 §5 lifecycle matrix at Phase 10.\n\n"
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
            "Deposit-model score wired from Phase 03 (03A) — guide §6.7",
            RECORDED_ACCEPTANCE,
            decision=Decision.PASS
            if (self._model_wired and self._model_fit["available"])
            else Decision.PENDING,
            note=f"model_fit={self._model_fit['score']}/10; dominant model "
            f"'{self._model_fit['model']}' ({self._model_fit['label']}).",
        )
        report.add(
            "Field access and safety checked",
            RECORDED_ACCEPTANCE,
            decision=Decision.PENDING,
            note="Access scored from roads layer where present; field access/safety confirmed by "
            "human before drone/recon (desktop data gap).",
        )
        report.add(
            "Desktop-unavailable criteria recorded as data gaps",
            "Criteria without evidence at desktop Phase 04 score 0; recorded, non-blocking "
            "(invariant #8).",
            decision=Decision.PASS,
            note=(
                f"Data gaps: {'; '.join(self._data_gaps)}."
                if self._data_gaps
                else "All 8 criteria have evidence sources."
            ),
        )
        return report


PHASE = Phase04ProspectRanking
