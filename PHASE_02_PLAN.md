# Phase 02 — Remote Sensing Preprocessing — implementation plan

Grounded in the four detailed QGIS-4.0.2 guides in `docs/phase_02/` (the methodology's
step-by-step source of truth), reconciled with the repo invariants in `CLAUDE.md` and the
adversarially-verified technical spec from the `phase02-plan` workflow.

> **Evidence rule (non-negotiable, guide §1/§16):** every Phase 02 output is **support
> evidence only — not ore proof**. Each output records
> `validation_status = "Support evidence only"` and
> `limitation = "Not ore proof; requires field/lab validation"`.

## Source guides

| File (`docs/phase_02/`) | Drives |
|---|---|
| `Phase_2_Remote Sensing Preprocessing … заавар` | Master workflow, folder tree, QA/QC, completion criteria |
| `…QGIS402_DEM_ALOS_PALSAR_ASTERGDEM_Detailed_Guide` | DEM reproject/clip + terrain derivatives + hydrology |
| `…Sentinel2_QGIS402_Detailed_Guide_v01` | Sentinel reproject/clip + indices/masks/composites (band-math) |
| `QGIS_4_0_2_Google_HighResolution_Basemap_Detailed_Guide` | Basemap reproject/clip + COG (tiled/overviews/compress) |

## Locked decisions

1. **KOMPSAT-2** → **method-note only**. RPC orthorectification (PAN+RPC+EPH+DEM) is the real
   first step and is external (ILWIS/Global Mapper/GDAL). A plain reproject of un-orthorectified
   1G imagery is geometrically wrong, so we do **not** produce one. We QA the bundle, record band
   identity, and emit notes for ortho/stack/pansharpen/NDVI/lineament.
2. **DEM derivatives** → automate the pure-numpy **rasters** now; leave **vector hydrology**
   (drainage network, watershed) and **contour** as method-notes (they need SAGA/GRASS /
   gdal_contour, not available in the pipeline env).
3. **Clip buffers (per product)** → **DEM = 5 km · Sentinel = licence boundary · Basemap = 1 km**.
   (All exist from Phase 01: `project_buffers` GPKG + `license_boundary` in the master GPKG.)
4. **CRS / resampling** → all deliverables EPSG:32647; **Bilinear** for continuous rasters,
   **Nearest** for categorical; record native CRS always.
5. **COG** → clip → reproject → Cloud-Optimized GeoTIFF (tiled 512 + internal overviews +
   lossless compression). Matches basemap guide §10–11 (tiled/overviews/LZW/BIGTIFF).

## What the pipeline AUTOMATES vs leaves as METHOD-NOTE

| Group (inputs) | Automated (BUILD) | Method-note (external) |
|---|---|---|
| **DEM** ALOS #12, ASTER-GDEM #9 (+NumObs #10, ALOS hillshade #16 / slope #20) | reproject→32647, clip 5 km, COG; **multi-azimuth hillshade (315/045/090/135), slope, aspect, TRI, profile+plan curvature, flow-accumulation** | contour (gpkg), drainage-network (gpkg), watershed/catchments (gpkg) — SAGA/GRASS |
| **Sentinel-2** #74, #77, #78 | reproject (46N→32647, 10 m, bilinear), clip to **licence**, COG, support-labelled | NDVI/NDWI, veg/water/shadow masks, Natural/Geology/FalseColor RGB, lithology ratio stack — need bands B02–B12 (SNAP Sen2Cor on raw L1C) |
| **Google basemap** #75 (2.4 m), #76 (0.15 m) | #75 reproject 4326→32647; #76 reproject 3857→32647 + clip 1 km; both COG (tiled+overviews+compress) | field-access / outcrop / old-workings / road-track digitising (manual interpretation) |
| **ASTER** #73 (.hdf) | — (file_type=hdf, skipped by raster loop; explicit method-note row) | HDF band extraction → 15 weighted scores → porphyry score → class → binary mask (SNAP/ILWIS) |
| **KOMPSAT-2** #24 PAN, #28/32/36/40 MS (+ rpc/eph/txt) | bundle QA + band-identity record only | RPC ortho + band stack + pansharpen + NDVI + lineament/outcrop interp |

### Formulas captured for the method-notes (so the external operator has everything)
- **Sentinel** NDVI=(B08−B04)/(B08+B04) [veg mask >0.3]; NDWI=(B03−B08)/(B03+B08) [water >0.2];
  shadow B04<0.05 (reflectance) / <500 (DN); Natural RGB=B04/B03/B02; Geology RGB=B12/B08/B03;
  FalseColor=B08/B04/B03; lithology ratios B11/B12, B08/B11, B04/B03.
- **ASTER** porphyry score = 0.12282·sericite + 0.08776·aloh + 0.07022·clay + 0.05265·argilic +
  0.05765·quartz + 0.08020·silicification + 0.06013·silica + 0.08270·iron_oxide + 0.06766·ferric +
  0.06013·chlorite + 0.04511·mgoh + 0.03008·carbonate + 0.01503·carbonate_swir +
  0.03760·structure_v1 + 0.10527·lithology (Float32 raw); class = histogram percentiles
  (0–60 / 60–85 / 85–100); binary mask = (class==3).
- **KOMPSAT** band identity PN=PAN, M1=Green, M2=Blue, M3=NIR, M4=Red; NDVI=(NIR−Red)/(NIR+Red);
  pansharpen Brovey/Gram-Schmidt/IHS.

## Folder structure (aligned to master guide §3)

```
02_Phase_2_Remote_Sensing_Preprocessing/
├ 00_Input_Working_Copy
├ 01_Sentinel2_SNAP13/        {01_Input,02_QAQC,03_Masks,04_Indices,05_Composites,06_Export_EPSG32647}
├ 02_ASTER_Workflow_v5/       {01_Input_HDF,02_Band_Extraction,03_Project_UTM47,04_Index_Calculation,05_Score_Class_Binary,06_QAQC}
├ 03_KOMPSAT2_ILWIS368_QGIS/  {01_Input_Bundle,02_Metadata_RPC_EPH_Check,03_Band_Stack,04_Orthorectification,05_Pansharpen,06_NDVI_Lineament_Outcrop,07_QAQC}
├ 04_ALOS_ASTERGDEM_GlobalMapper_QGIS/ {01_Input_DEM,02_DEM_QAQC,03_Reproject_Clip,04_Terrain_Derivatives,05_Drainage_Watershed,06_Access_Safety}
├ 05_Basemap_Google_HighRes/  {01_Input,02_Reproject_Clip,03_QAQC}
├ 06_RemoteSensing_QAQC
└ 07_Final_Export_EPSG32647
```

## Code changes

- **`core/raster_writers.py`** (new) — `clip_to_aoi_raster()` (rasterio.mask, returns `None` on
  no-overlap), `write_cog()` (driver='COG', tiled+overviews+compress; predictor as **str**),
  `is_cog()` (valid = `LAYOUT==COG` + tiling; overviews required **only when** `min(dim)>blocksize`).
- **`core/crs.py`** — `reproject_clip_cog(src, dst, aoi_gdf, …)`: clip **in the raster's native
  CRS** → reproject to 32647 → COG; refactor existing reproject body into a shared private helper;
  keep `reproject_raster` for back-compat. Intermediates go in a `tempfile.TemporaryDirectory()`.
- **`core/dem.py`** — add **TRI**, **profile/plan curvature**, **multi-azimuth hillshade**; write
  derivatives as COGs (per-derivative profile built **fresh** — never inherit the float DEM's
  PREDICTOR onto a uint8 hillshade); return `(written, skipped_notes)` so a flow-accumulation
  `>MAX_CELLS` skip is logged, not silent.
- **`phases/phase02_remote_sensing.py`** — rewrite to the per-sensor folder tree + per-product clip
  buffers; classify each raster; route through `reproject_clip_cog`; emit the formula-complete
  method-notes; #73 method-note row; KOMPSAT method-note-only; expand QA/QC columns to the guide
  §13 metadata set incl. the support-evidence flag.
- **`config/project.yaml`** — phase02 block (clip buffer per product, compression). Note the **25 km
  buffer discrepancy** (guide prereq lists it; Phase 01 produced up to 20 km) — flagged, not
  auto-fixed.
- **`tests/test_phase02_clip_cog.py`** (new) — synthetic fixtures **larger than blocksize**; assert
  clip bounds, CRS=32647, valid COG (+overviews when >blocksize), no-overlap Skip, DEM derivatives
  incl. TRI/curvature, support-evidence flag, dry-run columns.

## Runbook

```powershell
$env:BUDUUNKHAD_RAW_ROOT='C:\bk\raw'; $env:BUDUUNKHAD_OUTPUT_ROOT='C:\bk\out'
buduunkhad run --only 02 --dry-run     # per-sensor folders + method notes + empty QA/QC log
buduunkhad run --only 02               # re-verify raw SHA-256 → reproject+clip+COG + DEM derivatives
# verify: python -m rasterio info <out.tif>  → EPSG:32647, COMPRESS, tiled, bounds inside the clip buffer
# gate GO → buduunkhad publish --label v0.2.0 ; git tag v0.2.0 (account: anandts-nmg)
```

## Verifier fixes folded in (from the planning workflow)
COG validity = layout+tiling (overviews only when >blocksize, else small fixtures false-fail) ·
per-derivative profile built fresh (no predictor leakage) · predictor passed as string ·
intermediates in auto-cleaned temp dirs · pre-read PAN size guard (moot now KOMPSAT is note-only) ·
support-evidence flag is **added**, not assumed · `python -m rasterio info` for verification
(no system gdalinfo on PATH).
