"""Phase 05 — DJI Matrice 400 Drone / LiDAR / Photogrammetry Survey (ORCHESTRATE).

Flight planning + ingest of orthomosaic / point cloud / DTM. No automated acquisition.
"""

from __future__ import annotations

from buduunkhad.phases.base import StubPhase


class Phase05DroneLidar(StubPhase):
    id = "05"
    name = "DJI Matrice 400 Drone / LiDAR / Photogrammetry Survey"
    mode = "orchestrate"
    input_numbers = [*range(9, 23), *range(75, 79)]
    software = "DJI Matrice 400, Zenmuse P1/L2/L3, processing software, QGIS"
    output_summary = (
        "Drone flight plan, orthomosaic, LiDAR point cloud, DTM/DSM, interpretation layers"
    )
    gate_condition = "Survey products ingested, reprojected to EPSG:32647 and QA/QC passed."


PHASE = Phase05DroneLidar
