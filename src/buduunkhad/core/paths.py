"""Phase folder tree and standard subfolders.

The phase folder names are *load-bearing* - later handoffs in the methodology
reference them verbatim, so they are reproduced exactly. Phase 00 and Phase 01
get their methodology-specific subfolder trees; the orchestrate/stub phases get a
sensible standard set.
"""

from __future__ import annotations

from pathlib import Path

# Ordered phase id -> top-level folder name (exactly per the methodology).
PHASE_DIRS: dict[str, str] = {
    "00": "00_Raw_Files_Archive",
    "01": "01_Phase_1_Data_Audit_and_Master_GIS_Setup",
    "02": "02_Phase_2_Remote_Sensing_Preprocessing",
    "03": "03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis",
    "04": "04_Phase_4_Preliminary_Prospect_Delineation_and_Ranking",
    "05": "05_Phase_5_DJI_Matrice_400_Drone_LiDAR_Photogrammetry_Survey",
    "06": "06_Phase_6_Recon_Mapping_and_Portable_XRF_Field_Screening",
    "07": "07_Phase_7_Rock_Chip_Channel_and_Verification_Sampling",
    "08": "08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check",
    "09": "09_Phase_9_Systematic_Soil_Grid_and_Laboratory_QAQC",
    "10": "10_Phase_10_Integrated_Interpretation_and_Final_Target_Ranking",
    "11": "11_Phase_11_Follow_Up_Trench_Geophysics_and_Scout_Drill_Planning",
    "99": "99_Final_Deliverables",
}

# Evidence-group subfolders under 00_Raw_Files_Archive (mirror the archive layout).
EVIDENCE_GROUP_DIRS: list[str] = [
    "01_Tectonic_Terrane_KMZ",
    "02_DEM_ALOS_ASTERGDEM",
    "03_KOMPSAT2_MSC_L1G",
    "04_HeavyMineral_StreamSediment_Field",
    "05_Geology_Mineral_Prospectivity",
    "06_Regional_Metallogenic_L47B",
    "07_Basemap_Sentinel2_ASTER",
]

# Phase 01 functional subfolders (integrated 00-99 workflow, methodology section 2).
PHASE01_SUBFOLDERS: list[str] = [
    "01_File_Inventory",
    "02_Metadata_Check",
    "03_CRS_Check",
    "04_Raster_Scan_Georeference_QAQC",
    "05_KMZ_KML_to_GPKG",
    "06_Master_GeoPackage_Schema",
    "07_Data_Confidence_Ranking",
    "08_Master_QGIS_Project_Setup",
    "09_Handover_Package",
]

# Standard subfolders for the orchestrate/stub phases (02-99).
STANDARD_SUBFOLDERS: list[str] = [
    "00_Admin_and_Method",
    "01_Input_Working_Copy",
    "02_Inventory_and_Metadata",
    "03_Processing",
    "08_QAQC_and_Confidence",
    "09_Handover_Package",
]


def phase_dir(output_root: Path, phase_id: str) -> Path:
    """Top-level folder for a phase under ``output_root``."""
    try:
        return Path(output_root) / PHASE_DIRS[phase_id]
    except KeyError as exc:  # pragma: no cover - guarded by config
        raise KeyError(f"Unknown phase id: {phase_id!r}") from exc


def subfolders_for(phase_id: str) -> list[str]:
    """Return the standard subfolder names for a phase."""
    if phase_id == "00":
        return list(EVIDENCE_GROUP_DIRS)
    if phase_id == "01":
        return list(PHASE01_SUBFOLDERS)
    return list(STANDARD_SUBFOLDERS)


def ensure_dir(path: Path) -> Path:
    """Create ``path`` (and parents) if missing; return it."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_phase_tree(output_root: Path, phase_id: str, subfolders: list[str] | None = None) -> Path:
    """Create a phase's top-level folder and its subfolders. Returns the phase dir."""
    root = ensure_dir(phase_dir(output_root, phase_id))
    for sub in subfolders if subfolders is not None else subfolders_for(phase_id):
        ensure_dir(root / sub)
    return root


def build_full_tree(output_root: Path) -> list[Path]:
    """Create the full 00-99 phase tree. Returns the list of phase directories."""
    ensure_dir(output_root)
    return [build_phase_tree(output_root, pid) for pid in PHASE_DIRS]
