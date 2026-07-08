<!-- source: Phase_2_Remote_Sensing_Preprocessing_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

Доорх нь 02. Phase 2 — Remote Sensing Preprocessing-ийг QGIS/SNAP/ILWIS/Global Mapper дээр бодитоор хийх дэлгэрэнгүй ажлын заавар юм. Энэ заавар нь таны оруулсан workflow document-д заасан Phase 2 input буюу №9–22 DEM/ALOS/ASTERGDEM, №23–46 KOMPSAT-2, №73 ASTER HDF, №74–78 Sentinel/Google/basemap raster дээр үндэслэв.

02. Phase 2 — Remote Sensing Preprocessing хийх дэлгэрэнгүй заавар
1. Phase 2-ийн зорилго
Phase 2-ийн зорилго нь Sentinel-2, ASTER, KOMPSAT-2, ALOS-PALSAR DEM, ASTER GDEM болон Google/basemap raster-уудыг нэг CRS, нэг project standard, нэг QA/QC бүртгэлтэй болгож, дараагийн Phase 3–4-д ашиглахад бэлэн support evidence layer гаргах явдал.
Анхаарах үндсэн зарчим:
Remote sensing output нь хүдэржилтийн баталгаа биш. Энэ нь зөвхөн alteration, lithology contrast, lineament, drainage, terrain, outcrop/access support evidence юм. Эцсийн баталгааг field mapping, rock chip/channel sampling, lab assay, structural validation, trench/geophysics/drilling өгнө.

2. Ажил эхлэхийн өмнөх шаардлага
2.1 Phase 1-ээс бэлэн байх ёстой зүйл
Phase 2 эхлэхийн өмнө Phase 1 дээр дараах зүйлс бэлэн байна:
XV-023222_Buduunkhad_Master_QGIS_Project.qgz
XV-023222_Buduunkhad_Master_GIS_Database.gpkg
LicenseBoundary_EPSG32647.gpkg
XV023222_Buduunkhad_Project_Buffer_500m_1km_5km_10km_20km_25km_EPSG32647.gpkg
XV-023222_Buduunkhad_CRS_Georeference_QAQC_Log.xlsx
XV-023222_Buduunkhad_Data_Confidence_Ranking.xlsx
Project CRS заавал:
WGS 84 / UTM Zone 47N — EPSG:32647

3. Phase 2 folder structure үүсгэх
Windows Explorer дээр дараах folder бүтцийг яг ингэж үүсгэнэ:
02_Phase_2_Remote_Sensing_Preprocessing/
├── 00_Input_Working_Copy
├── 01_Sentinel2_SNAP13
│   ├── 01_Input
│   ├── 02_QAQC
│   ├── 03_Masks
│   ├── 04_Indices
│   ├── 05_Composites
│   └── 06_Export_EPSG32647
├── 02_ASTER_Workflow_v5
│   ├── 01_Input_HDF
│   ├── 02_Band_Extraction
│   ├── 03_Project_UTM47
│   ├── 04_Index_Calculation
│   ├── 05_Score_Class_Binary
│   └── 06_QAQC
├── 03_KOMPSAT2_ILWIS368_QGIS
│   ├── 01_Input_Bundle
│   ├── 02_Metadata_RPC_EPH_Check
│   ├── 03_Band_Stack
│   ├── 04_Orthorectification
│   ├── 05_Pansharpen
│   ├── 06_NDVI_Lineament_Outcrop
│   └── 07_QAQC
├── 04_ALOS_ASTERGDEM_GlobalMapper_QGIS
│   ├── 01_Input_DEM
│   ├── 02_DEM_QAQC
│   ├── 03_Reproject_Clip
│   ├── 04_Terrain_Derivatives
│   ├── 05_Drainage_Watershed
│   └── 06_Access_Safety
├── 05_Basemap_Google_HighRes
│   ├── 01_Input
│   ├── 02_Reproject_Clip
│   └── 03_QAQC
├── 06_RemoteSensing_QAQC
└── 07_Final_Export_EPSG32647
00_Input_Working_Copy дотор raw archive-оос зөвхөн copy хийж авна. Raw file дээр шууд ажиллахгүй.

4. Phase 2 input файлуудыг зөв байрлуулах
4.1 DEM / ALOS / ASTER GDEM input
Дараах №9–22 файлуудыг:
04_ALOS_ASTERGDEM_GlobalMapper_QGIS/01_Input_DEM
дотор хуулна.
Үүнд:
№9  ASTER-GDEM-v3_N45E096_DEM_1arcsec_WGS84_v01_raw.tif
№10 ASTER-GDEM-v3_N45E096_NumObservations_1arcsec_WGS84_v01_raw.tif
№11 XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tfw
№12 XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif
№13 XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.aux.xml
№14 XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.ovr
№15–22 ALOS hillshade/slope sidecar болон derived raster files
Анхаарах зүйл: .tfw, .aux.xml, .ovr файлуудыг parent .tif файлаас салгаж болохгүй.

4.2 KOMPSAT-2 input
Дараах №23–46 файлуудыг:
03_KOMPSAT2_ILWIS368_QGIS/01_Input_Bundle
дотор хуулна.
KOMPSAT bundle нь дараах бүтэцтэй байна:
PAN:
MSC_111127030410_28454_08621344PN00_1G.tif
MSC_111127030410_28454_08621344PN00_1G.txt
MSC_111127030410_28454_08621344PN00_1G.rpc
MSC_111127030410_28454_08621344PN00_1G.eph

Green:
MSC_111127030410_28454_08621344M1N00G_1G.tif
.txt / .rpc / .eph

Blue:
MSC_111127030410_28454_08621344M2N00B_1G.tif
.txt / .rpc / .eph

NIR:
MSC_111127030410_28454_08621344M3N00N_1G.tif
.txt / .rpc / .eph

Red:
MSC_111127030410_28454_08621344M4N00R_1G.tif
.txt / .rpc / .eph

Browse/thumbnail:
MSC_111127030410_28454_08621344N00_1G_br.jpg
MSC_111127030410_28454_08621344N00_1G_br.jgw
MSC_111127030410_28454_08621344N00_1G_tn.jpg
.txt, .rpc, .eph нь metadata/geometry sidecar учраас устгаж, салгаж, rename хийж болохгүй.

4.3 ASTER HDF input
№73 файлыг:
02_ASTER_Workflow_v5/01_Input_HDF
дотор хуулна.
2005-09-05_MN_ASTER-L1B_MultispectralImagery_00409052005043503_v01_raw.hdf

4.4 Sentinel / Google / basemap input
№74–78 файлуудыг:
01_Sentinel2_SNAP13/01_Input
болон basemap бол:
05_Basemap_Google_HighRes/01_Input
дотор ангилж хуулна.
№74 2025-05-28_MN_T46TGS_GeoreferencedSatelliteRaster_v01_raw.tif
№75 XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif
№76 XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif
№77 XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_GeologicalInterpretation_RGB_B12-B08-B03_10m_UTM46N_ReceivedRaw_v01.tif
№78 XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_LithologyIndex_B11B12_B08B11_B04B03_10m_UTM46N_ReceivedRaw_v01.tif
№77, №78 нь нэрнээсээ харахад UTM46N байж болзошгүй тул заавал EPSG:32647 руу reproject хийнэ.

5. QGIS project тохируулах
QGIS нээнэ.
Доорх тохиргоог хийнэ:
Project CRS: EPSG:32647
Project name: XV-023222_Buduunkhad_Phase2_RemoteSensing.qgz
Дараах layer-үүдийг эхэлж оруулна:
License boundary EPSG:32647
500 m buffer
1 km buffer
5 km / 10 km / 20 km / 25 km buffer
Phase 1 Master GIS base layers
Дараа нь бүх raster-уудыг нэг нэгээр нь QGIS-д оруулж CRS, extent, pixel size, band count, NoData шалгана.

6. DEM / ALOS-PALSAR / ASTER GDEM боловсруулах заавар
6.1 DEM metadata шалгах
QGIS дээр DEM raster дээр right click:
Layer Properties → Information
Шалгах зүйл:
CRS
Extent
Pixel size
Band count
Data type
NoData value
Statistics
Resolution
QA/QC register-д дараах багануудыг бөглөнө:
source_raw_input_no
source_raw_filename
raster_type
native_crs
pixel_size
extent
nodata_value
band_count
sidecar_available
processing_action
qaqc_status
reviewer
review_date
comment

6.2 DEM reproject хийх
QGIS:
Raster → Projections → Warp (Reproject)
Тохиргоо:
Input layer: ALOS-PALSAR DEM эсвэл ASTER GDEM
Source CRS: native CRS
Target CRS: EPSG:32647
Resampling: Bilinear
Output resolution: эх raster-ийн resolution-д ойролцоо
NoData: эх NoData-г хадгална
Output нэр:
XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif
ASTER GDEM output:
XV023222_Buduunkhad_ASTERGDEM_DEM_EPSG32647_v01.tif

6.3 License + buffer-аар clip хийх
QGIS:
Raster → Extraction → Clip Raster by Mask Layer
Тохиргоо:
Input raster: reprojected DEM
Mask layer: license_boundary_buffer_1km эсвэл 5km
Crop to cutline: checked
Keep resolution of input raster: checked
Target CRS: EPSG:32647
Output:
XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_Clip1km_EPSG32647_v01.tif

6.4 Hillshade гаргах
QGIS:
Raster → Analysis → Hillshade
Тохиргоо:
Input: clipped DEM
Z factor: 1
Azimuth: 315
Vertical angle: 45
Output:
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_12p5m_EPSG32647_v01.tif
Нэмэлтээр lineament харахад өөр азимуттай hillshade гаргаж болно:
Azimuth 045
Azimuth 090
Azimuth 135
Azimuth 315

6.5 Slope гаргах
QGIS:
Raster → Analysis → Slope
Тохиргоо:
Input: clipped DEM
Slope expressed as: degrees
Output:
XV023222_Buduunkhad_ALOS_PALSAR_SlopeDeg_12p5m_EPSG32647_v01.tif

6.6 Aspect гаргах
QGIS:
Raster → Analysis → Aspect
Output:
XV023222_Buduunkhad_ALOS_PALSAR_Aspect_12p5m_EPSG32647_v01.tif

6.7 Contour гаргах
QGIS:
Raster → Extraction → Contour
Тохиргоо:
Input: DEM
Interval: 5 m эсвэл 10 m
Attribute name: elev
Output:
XV023222_Buduunkhad_Contour_10m_EPSG32647_v01.gpkg

6.8 Drainage / watershed гаргах
QGIS Processing Toolbox ашиглана.
Дараалал:
Fill sinks
Flow direction
Flow accumulation
Channel network
Watershed / catchment
Output:
XV023222_Buduunkhad_Drainage_Network_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Watershed_Catchments_EPSG32647_v01.gpkg
Үүнийг Phase 8 stream sediment / heavy mineral follow-up-д ашиглана.

6.9 Terrain ruggedness / curvature гаргах
QGIS эсвэл SAGA tools:
Terrain Ruggedness Index
Profile curvature
Plan curvature
Output:
XV023222_Buduunkhad_Terrain_Ruggedness_EPSG32647_v01.tif
XV023222_Buduunkhad_Curvature_EPSG32647_v01.tif

6.10 DEM final package
DEM хэсгийн final output:
XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ASTERGDEM_DEM_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_SlopeDeg_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_Aspect_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_Contour_10m_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Drainage_Network_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Watershed_Catchments_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Terrain_Derivatives_EPSG32647_v01.gpkg
XV023222_Buduunkhad_DEM_QAQC_Log.xlsx

7. Sentinel-2 боловсруулах заавар
7.1 Sentinel raster status шалгах
№74, №77, №78-г QGIS дээр нээнэ.
Шалгах зүйл:
CRS: UTM46N эсэх, EPSG:32647 эсэх
Pixel size: 10 m эсэх
Band count
Band order
Extent license boundary-тэй давхцаж байгаа эсэх
NoData
Хэрэв raster аль хэдийн derivative product бол дахин Sen2Cor хийхгүй. Зөвхөн metadata бүртгэж, EPSG:32647 руу reproject/clip хийнэ.
Хэрэв raw Sentinel-2 L1C SAFE folder байгаа бол SNAP 13.0.0 дээр Sen2Cor ашиглаж L2A болгоно.

7.2 SNAP дээр L1C → L2A болгох
SNAP 13.0.0 нээнэ.
File → Open Product
Sentinel SAFE product оруулна.
Дараа нь:
Optical → Thematic Land Processing → Sen2Cor
Output:
L2A product
L2A болсны дараа 10 m bands:
B02 Blue
B03 Green
B04 Red
B08 NIR
20 m bands:
B11 SWIR1
B12 SWIR2
Эдгээрийг 10 m grid рүү resample хийнэ.

7.3 SNAP дээр resample хийх
Raster → Geometric Operations → Resampling
Тохиргоо:
Reference band: B08 эсвэл B04 10 m
Resampling method: Bilinear
Output: 10 m aligned product

7.4 QGIS дээр EPSG:32647 руу reproject хийх
QGIS:
Raster → Projections → Warp (Reproject)
Тохиргоо:
Target CRS: EPSG:32647
Resampling: Bilinear
Output:
XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_Geology_RGB_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_LithologyIndex_EPSG32647_v01.tif

7.5 Cloud / shadow / snow / water / vegetation mask
Sentinel дээр дараах mask-ууд үүсгэнэ.
NDVI
NDVI = (B08 - B04) / (B08 + B04)
Vegetation mask:
NDVI > 0.3
NDWI
NDWI = (B03 - B08) / (B03 + B08)
Water mask:
NDWI > 0.2
Shadow / dark pixel mask
B02 эсвэл B04 маш бага reflectance-тэй pixel
Жишээ threshold:
B04 < 0.05
Threshold-ийг тухайн raster-ийн DN/reflectance scale-аас хамаарч тохируулна.
Output:
XV023222_Buduunkhad_Sentinel2_NDVI_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_NDWI_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_VegetationMask_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_WaterShadowMask_EPSG32647_v01.tif

7.6 Sentinel composite гаргах
QGIS дээр Build Virtual Raster эсвэл Raster Calculator / Merge ашиглаж composite үүсгэнэ.
Natural RGB
R = B04
G = B03
B = B02
Output:
XV023222_Buduunkhad_Sentinel2_NaturalRGB_EPSG32647_v01.tif
Geological SWIR-NIR-Red composite
R = B12
G = B08
B = B03
Output:
XV023222_Buduunkhad_Sentinel2_Geology_RGB_B12_B08_B03_EPSG32647_v01.tif
False color vegetation / lithology support
R = B08
G = B04
B = B03
Output:
XV023222_Buduunkhad_Sentinel2_FalseColor_B08_B04_B03_EPSG32647_v01.tif

7.7 Sentinel lithology / alteration index
№78 файл дээр аль хэдийн lithology index байж болзошгүй тул эхлээд band composition-г шалгана. Таны workflow нэршлээс харахад:
B11/B12
B08/B11
B04/B03
гэсэн band ratio stack байх магадлалтай.
Үүнийг reproject/clip хийгээд support layer гэж тэмдэглэнэ.
Output:
XV023222_Buduunkhad_Sentinel2_LithologyIndex_B11B12_B08B11_B04B03_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_LithologyIndex_QAQC_Log.xlsx

7.8 Sentinel final package
XV023222_Buduunkhad_Sentinel2_NaturalRGB_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_Geology_RGB_B12_B08_B03_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_LithologyIndex_B11B12_B08B11_B04B03_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_NDVI_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_NDWI_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_VegetationMask_EPSG32647_v01.tif
XV023222_Buduunkhad_Sentinel2_QAQC_Log.xlsx

8. ASTER HDF workflow v5 хийх заавар
8.1 ASTER raw HDF-г хадгалах
№73 raw HDF-г:
02_ASTER_Workflow_v5/01_Input_HDF
дотор хадгална.
Raw HDF-г өөрчлөхгүй.

8.2 ASTER band extraction
ASTER HDF-г ILWIS 3.6.8, QGIS/GDAL, эсвэл SNAP ашиглан нээж боломжтой band-уудыг гаргана.
Гарах band-уудыг дараах байдлаар хадгална:
b1_project.tif
b2_project.tif
b3_project.tif
b4_project.tif
b5_project.tif
b6_project.tif
b7_project.tif
b8_project.tif
b9_project.tif
Output folder:
02_ASTER_Workflow_v5/02_Band_Extraction

8.3 ASTER band-уудыг UTM47 / EPSG:32647 болгох
QGIS:
Raster → Projections → Warp (Reproject)
Target CRS:
EPSG:32647
Output:
b1_project_EPSG32647.tif
b2_project_EPSG32647.tif
...
b9_project_EPSG32647.tif

8.4 ASTER index тооцох
ASTER workflow v5-ийн зарчим:
HDF import
Band extraction
UTM47 project grid
b*_project band-аас index тооцох
Haze/edge filter-ийг ratio calculation-д ашиглахгүй
Raw score, class, binary mask-г тусад нь хадгалах
Үндсэн index/score layer-үүд
Таны өмнөх workflow-т ашигласан logic-ийг баримталбал дараах score layer-үүдийг гаргана:
score_sericite
score_aloh
score_clay
score_argilic
score_quartz
score_silicification
score_silica
score_iron_oxide
score_ferric
score_chlorite
score_mgoh
score_carbonate
score_carbonate_swir
score_structure_v1
score_lithology
Эдгээр нь бүгд Float32 raw score raster хэлбэрээр хадгалагдана.

8.5 Porphyry alteration score тооцох
ASTER final alteration score-г дараах weighted score хэлбэрээр тооцно:
score_porphyry_alteration =
0.12282 * score_sericite +
0.08776 * score_aloh +
0.07022 * score_clay +
0.05265 * score_argilic +
0.05765 * score_quartz +
0.08020 * score_silicification +
0.06013 * score_silica +
0.08270 * score_iron_oxide +
0.06766 * score_ferric +
0.06013 * score_chlorite +
0.04511 * score_mgoh +
0.03008 * score_carbonate +
0.01503 * score_carbonate_swir +
0.03760 * score_structure_v1 +
0.10527 * score_lithology
Output:
XV023222_Buduunkhad_ASTER_score_porphyry_alteration_raw_v01.tif
Data type:
Float32

8.6 ASTER class map гаргах
Raw score-г 3 ангилал болгоно.
Жишээ:
Class 1 = Low
Class 2 = Moderate
Class 3 = High
Ангиллын threshold-г тухайн raster-ийн histogram/statistics дээр үндэслэнэ.
Жишээ арга:
Low: доод 0–60 percentile
Moderate: 60–85 percentile
High: 85–100 percentile
Output:
XV023222_Buduunkhad_ASTER_porphyry_potential_class_v01.tif

8.7 ASTER binary mask гаргах
High class буюу class 3-ыг 1, бусдыг 0 болгоно.
QGIS Raster Calculator:
("ASTER_porphyry_potential_class@1" = 3) * 1
Output:
XV023222_Buduunkhad_ASTER_porphyry_final_target_binary_mask_v01.tif
Binary mask утга:
0 = not selected
1 = ASTER high alteration support

8.8 ASTER QA/QC
ASTER QA/QC дээр дараахыг заавал шалгана:
HDF import амжилттай эсэх
Band extraction бүрэн эсэх
Band alignment зөв эсэх
Projection EPSG:32647 болсон эсэх
Raw score Float32 хэвээр хадгалагдсан эсэх
Class raster 1/2/3 тусдаа гарсан эсэх
Binary mask 0/1 тусдаа гарсан эсэх
Haze/edge filter ratio calculation-д ороогүй эсэх
Output нь ore proof биш support evidence гэж тэмдэглэгдсэн эсэх
Output:
XV023222_Buduunkhad_ASTER_QAQC_Log.xlsx

9. KOMPSAT-2 боловсруулах заавар
9.1 KOMPSAT bundle бүрэн эсэхийг шалгах
KOMPSAT folder дотор PAN, Green, Blue, NIR, Red band тус бүрийн:
.tif
.txt
.rpc
.eph
байгаа эсэхийг шалгана.
QA/QC register-д:
PAN tif/txt/rpc/eph complete?
Green complete?
Blue complete?
NIR complete?
Red complete?
Browse image available?
Thumbnail available?
гэж бүртгэнэ.

9.2 Band identity шалгах
Файлын нэрээр band identity:
PN00 = PAN
M1N00G = Green
M2N00B = Blue
M3N00N = NIR
M4N00R = Red
QA/QC-д band order-г ингэж бүртгэнэ:
Blue = M2
Green = M1
Red = M4
NIR = M3
PAN = PN

9.3 KOMPSAT orthorectification
Хэрэв RPC ашиглан orthorectification хийх боломжтой бол Global Mapper, QGIS/GDAL, эсвэл photogrammetry-capable software ашиглана.
Оруулах input:
PAN tif + PAN rpc + PAN eph + DEM
MS band tif + rpc + eph + DEM
Target CRS:
EPSG:32647
Output:
XV023222_Buduunkhad_KOMPSAT2_PAN_Orthorectified_EPSG32647_v01.tif
XV023222_Buduunkhad_KOMPSAT2_MS_Orthorectified_Bundle_EPSG32647_v01.tif

9.4 KOMPSAT MS band stack
QGIS:
Raster → Miscellaneous → Build Virtual Raster
эсвэл GDAL merge stack ашиглана.
Band order:
Band 1 = Blue
Band 2 = Green
Band 3 = Red
Band 4 = NIR
Output:
XV023222_Buduunkhad_KOMPSAT2_MS_BandStack_BGRNIR_EPSG32647_v01.tif

9.5 KOMPSAT true color composite
RGB display:
R = Red
G = Green
B = Blue
Output:
XV023222_Buduunkhad_KOMPSAT2_TrueColor_RGB_EPSG32647_v01.tif

9.6 KOMPSAT false color composite
False color:
R = NIR
G = Red
B = Green
Output:
XV023222_Buduunkhad_KOMPSAT2_FalseColor_NIR_Red_Green_EPSG32647_v01.tif

9.7 KOMPSAT NDVI гаргах
Formula:
NDVI = (NIR - Red) / (NIR + Red)
Output:
XV023222_Buduunkhad_KOMPSAT2_NDVI_EPSG32647_v01.tif
Use:
vegetation mask
outcrop visibility
drainage/access planning

9.8 KOMPSAT pan-sharpen хийх
Input:
PAN orthorectified
MS band stack orthorectified
Method:
Brovey / Gram-Schmidt / IHS
Output:
XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif
Use:
lineament interpretation
outcrop mapping support
access road / track / disturbance mapping
field route planning

9.9 KOMPSAT lineament / outcrop interpretation
QGIS дээр pan-sharpened image + hillshade + slope overlay хийнэ.
Digitize layer үүсгэнэ:
lineament_interpretation_line
outcrop_interpretation_polygon
access_track_line
disturbance_surface_polygon
Layer fields:
feature_id
feature_type
interpretation_basis
source_raw_input_no
source_raw_filename
processing_phase
confidence
validation_status
limitation
reviewer
date
Output:
XV023222_Buduunkhad_KOMPSAT2_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg

9.10 KOMPSAT QA/QC
Шалгах зүйл:
PAN/MS alignment зөв эсэх
RPC/EPH/TXT хадгалагдсан эсэх
Orthorectified output EPSG:32647 болсон эсэх
Pansharpened image license boundary-тэй давхцаж байгаа эсэх
NDVI range -1 to +1 эсэх
Lineament interpretation нь support evidence гэж тэмдэглэгдсэн эсэх
Output:
XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx

10. Google / high-resolution basemap боловсруулах
10.1 №75 WGS84 basemap
Input:
XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif
QGIS дээр CRS шалгана.
Reproject:
Target CRS: EPSG:32647
Output:
XV023222_Buduunkhad_GoogleMaps_Basemap_RGB_2p4m_EPSG32647_v01.tif

10.2 №76 EPSG3857 high-resolution basemap
Input:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif
Reproject:
Source CRS: EPSG:3857
Target CRS: EPSG:32647
Clip:
license + 500 m эсвэл 1 km buffer
Output:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_v01.tif
Use:
field access
outcrop visibility
old workings/disturbance
track/road mapping

11. Бүх output-уудыг EPSG:32647 final export хийх
Дараах output-ууд бүгд:
07_Final_Export_EPSG32647
folder дотор нэгтгэгдэнэ.
Final output package:
XV023222_Buduunkhad_Sentinel2_Processed_Products_EPSG32647_v01.tif/gpkg
XV023222_Buduunkhad_ASTER_score_porphyry_alteration_raw_v01.tif
XV023222_Buduunkhad_ASTER_porphyry_potential_class_v01.tif
XV023222_Buduunkhad_ASTER_porphyry_final_target_binary_mask_v01.tif
XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif
XV023222_Buduunkhad_KOMPSAT2_NDVI_EPSG32647_v01.tif
XV023222_Buduunkhad_KOMPSAT2_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg
XV023222_Buduunkhad_ALOS_PALSAR_Terrain_Derivatives_EPSG32647_v01.gpkg
XV023222_Buduunkhad_RemoteSensing_QAQC_Report_v01.docx

12. Phase 2 QA/QC checklist
QA/QC register-д дараах checklist-ийг заавал бөглөнө.

| QA/QC item | Acceptance criterion |
| --- | --- |
| Raw preservation | Raw file overwrite хийгдээгүй |
| Sidecar completeness | .tfw, .aux.xml, .ovr, .rpc, .eph, .txt parent file-тэй хамт хадгалагдсан |
| CRS control | Final spatial output бүгд EPSG:32647 |
| Sentinel mask | Cloud/shadow/water/vegetation mask үүсгэсэн буюу шаардлагагүй гэж тайлбарласан |
| Sentinel reproject | UTM46N input-ууд EPSG:32647 болсон |
| ASTER raw score | Float32 raw score тусдаа хадгалагдсан |
| ASTER class | 1/2/3 class map тусдаа хадгалагдсан |
| ASTER binary | 0/1 binary mask тусдаа хадгалагдсан |
| KOMPSAT metadata | PAN/MS .txt, .rpc, .eph бүртгэгдсэн |
| KOMPSAT alignment | PAN/MS alignment checked |
| DEM derivatives | Hillshade, slope, aspect, drainage, contour шалгагдсан |
| Support evidence flag | Remote sensing output-ыг ore proof гэж ашиглаагүй |
| Source traceability | Output бүрт source_raw_input_no/source_raw_filename хадгалагдсан |

13. Output бүрт заавал байх metadata fields
GeoPackage layer, raster index, QA/QC register, report бүрт дараах талбаруудыг хадгална:
source_raw_input_no
source_raw_filename
source_group
processing_phase
processing_software
processing_action
native_crs
output_crs
pixel_size
output_filename
processing_version
qaqc_status
validation_status
confidence
limitation
reviewer
review_date
Remote sensing output дээр:
validation_status = Support evidence only
limitation = Not ore proof; requires field/lab validation

14. Phase 2 completion criteria
Phase 2 дууссан гэж үзэх нөхцөл:
№9–22 DEM/ALOS/ASTERGDEM input бүгд QA/QC хийгдсэн.
ALOS/ASTER DEM-ээс hillshade, slope, aspect, contour, drainage, watershed гарсан.
№23–46 KOMPSAT PAN/MS bundle бүрэн шалгагдсан.
KOMPSAT orthobasemap, NDVI, lineament/outcrop interpretation support гарсан.
№73 ASTER HDF-ээс raw score, class, binary mask гарсан.
№74–78 Sentinel/basemap raster EPSG:32647 руу reproject/clip хийгдсэн.
Sentinel geology composite, lithology index, NDVI/NDWI/masks бэлэн болсон.
Бүх final output 07_Final_Export_EPSG32647 folder дотор нэгтгэгдсэн.
XV023222_Buduunkhad_RemoteSensing_QAQC_Report_v01.docx бэлэн болсон.
Phase 3-д handover хийхэд бүх output support evidence гэж тэмдэглэгдсэн.

15. Phase 3 руу шилжүүлэх handover package
Phase 2-оос Phase 3 руу дараах package өгнө:
01_Sentinel2_Processed_Products/
02_ASTER_Alteration_Products/
03_KOMPSAT2_Orthobasemap_Lineament/
04_Terrain_Derivatives/
05_Basemap_Reference/
06_RemoteSensing_QAQC/
Phase 3 дээр эдгээрийг дараах байдлаар ашиглана:

| Phase 2 output | Phase 3 use |
| --- | --- |
| Sentinel geology RGB | lithology contrast support |
| Sentinel lithology index | alteration/lithology support |
| ASTER porphyry score | alteration support |
| ASTER binary mask | target support, not proof |
| KOMPSAT pansharpened image | outcrop/access/lineament support |
| KOMPSAT NDVI | vegetation/outcrop visibility mask |
| DEM hillshade/slope | structure, drainage, access |
| Drainage/watershed | stream sediment and heavy mineral follow-up |

16. Хамгийн чухал анхааруулга
Phase 2-ийн хамгийн том алдаа нь remote sensing output-ыг шууд “орд байна” гэж тайлбарлах явдал. Тиймээс report, map, layer attribute бүр дээр:
Remote sensing derivative = support evidence only.
Not mineralization proof.
Requires field validation and laboratory confirmation.
гэж заавал бичнэ.
Phase 2-ийн зөв гарц бол “эрдэсжилт батлах” биш, харин:
хаана шалгах вэ,
ямар structure харагдаж байна,
аль хэсэгт alteration support байна,
аль хэсэгт terrain/access тохиромжтой байна,
аль хэсгийг Phase 3–4 дээр илүү нягт overlay хийх вэ
гэсэн шийдвэрт ашиглах support layer бэлтгэх юм.
