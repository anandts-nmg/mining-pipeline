<!-- source: XV-023222_Phase5_LiDAR_P1_DJI_Terra_QGIS403_Folder_and_Step_by_Step_Guide.docx (converted from Word; canonical form for LLM ingestion) -->

# XV-023222 Phase 5 — DJI Terra ба QGIS 4.0.3 дээр LiDAR–P1 боловсруулалтын ажлын фолдер ба алхамчилсан заавар
NET MINING GROUP · Exploration Operating System
2026-06-09
# XV-023222 Phase 5 — DJI Terra ба QGIS 4.0.3 дээр LiDAR–P1 боловсруулалтын ажлын фолдер ба алхамчилсан заавар
Энэхүү заавар нь өмнөх шинэчилсэн Phase 5 v0.5 логикт нийцсэн: эхлээд L3 / LiDAR-аас байрлал-өндрийн баталгаатай суурь гаргана → дараа нь тэр үр дүнг P1 камерын зураг боловсруулалт, QA/QC, QGIS тайлалд reference болгон ашиглана.
Өмнөх Phase 5 баримтад Phase 5-ийн үндсэн зорилго нь orthomosaic, LiDAR point cloud, DSM/DTM, slope/hillshade, structure/outcrop/sample/trench/drill planning base гаргах гэж тодорхойлсон. Энэ DOCX нь тухайн зорилгыг DJI Terra болон QGIS 4.0.3 дээр хэрэгжүүлэх ажлын фолдер, алхамчилсан processing, QA/QC, final deliverable-ийн бүтцийг нэгтгэнэ.
## 1. Ажлын үндсэн зарчим
Энэ workflow-д LiDAR нь байрлал ба өндөрийн үндсэн reference, харин P1 нь өндөр нарийвчлалтай RGB orthomosaic / литологи тайллын үндсэн зураг болно.
Өөрөөр хэлбэл:
L3 / LiDAR
→ байрлал, өндөр, DTM, DSM, hillshade, terrain control, structure base
P1 camera
→ өндөр нарийвчлалтай orthomosaic, outcrop, lithology, quartz vein, alteration, sampling detail
QGIS 4.0.3
→ бүх үр дүнг нэг CRS-д давхарлаж шалгах, тайлбарлах, planning layer гаргах
DJI Terra
→ L3/L2 LiDAR raw reconstruction, point cloud, DSM/DEM/orthophoto, trajectory/accuracy report
## 2. Ажлын фолдерийн бүтэц
Доорх фолдерийг яг энэ дарааллаар үүсгэнэ.
05_Phase_5_DJI_Terra_QGIS403_LiDAR_P1_Processing/
│
├── 00_Admin_Register/
│   ├── 00_Input_File_Register.xlsx
│   ├── 01_Processing_Action_Log.xlsx
│   ├── 02_QAQC_Checklist.xlsx
│   └── 03_Version_Control_Log.docx
│
├── 01_Input_Data/
│   ├── 01_License_Boundary/
│   ├── 02_Phase4_Targets_Prospects/
│   ├── 03_Geology_Mineral_Occurrence_CMCS/
│   ├── 04_DEM_Slope_Hillshade_Previous/
│   ├── 05_KOMPSAT_Sentinel_Basemap/
│   ├── 06_Lineament_Structure/
│   ├── 07_Access_Road_Drainage/
│   └── 08_GCP_Checkpoint_CSV/
│
├── 02_Raw_Data_Backup/
│   ├── 01_L3_LiDAR_Raw/
│   │   ├── BLK001/
│   │   ├── BLK002/
│   │   └── BLK003/
│   ├── 02_P1_Photo_Raw/
│   │   ├── PR01/
│   │   ├── PR02/
│   │   └── PR03/
│   ├── 03_L2_LiDAR_Raw_If_Used/
│   ├── 04_RTK_PPK_Base_Raw/
│   ├── 05_Flight_Logs/
│   └── 06_Original_SD_Card_Copy_ReadOnly/
│
├── 03_DJI_Terra_Processing/
│   ├── 01_L3_Terra_Projects/
│   ├── 02_L3_Exports/
│   │   ├── PointCloud_LAS_LAZ/
│   │   ├── DSM/
│   │   ├── DEM_DTM/
│   │   ├── DOM_Orthophoto/
│   │   └── Terra_Reports/
│   ├── 03_L2_Terra_Projects_If_Used/
│   └── 04_L2_Exports_If_Used/
│
├── 04_LiDAR_Derived_Terrain_Base/
│   ├── 01_Classified_PointCloud/
│   ├── 02_DTM_Final/
│   ├── 03_DSM_Final/
│   ├── 04_Hillshade_MultiAzimuth/
│   ├── 05_Slope_Aspect_Curvature/
│   ├── 06_LRM_Openness_SkyView/
│   ├── 07_Drainage_Contour/
│   └── 08_LiDAR_QAQC/
│
├── 05_P1_Photogrammetry_Processing/
│   ├── 01_P1_Project_PR01/
│   ├── 02_P1_Project_PR02/
│   ├── 03_P1_Project_PR03/
│   ├── 04_P1_Orthomosaic_Exports/
│   ├── 05_P1_DSM_Exports/
│   ├── 06_P1_PointCloud_Exports/
│   ├── 07_P1_Processing_Reports/
│   └── 08_P1_QAQC_LiDAR_Comparison/
│
├── 06_QGIS_403_Project/
│   ├── 01_QGIS_Project_File/
│   ├── 02_QGIS_Geopackage/
│   ├── 03_QGIS_Styles_QML/
│   ├── 04_QGIS_Layouts/
│   ├── 05_QGIS_Temporary_Working/
│   └── 06_QGIS_Final_Maps/
│
├── 07_Interpretation_Planning/
│   ├── 01_Lineament_Fault_Contact/
│   ├── 02_Outcrop_Lithology/
│   ├── 03_Alteration_Vein_Corridor/
│   ├── 04_Sample_Point_Planning/
│   ├── 05_Trench_Planning/
│   ├── 06_Drill_Pad_Planning/
│   └── 07_Field_Traverse_Planning/
│
├── 08_Crop_AI_Lithology/
│   ├── 01_L3_250x250_Context/
│   ├── 02_P1_50x50_Local/
│   ├── 03_P1_10x10_Lithology/
│   ├── 04_P1_5x5_Sample_Detail/
│   ├── 05_AI_Prompts/
│   ├── 06_AI_Responses/
│   └── 07_AI_to_QGIS_Digitized/
│
├── 09_QAQC_Final/
│   ├── 01_GCP_Checkpoint_QAQC/
│   ├── 02_LiDAR_QAQC/
│   ├── 03_P1_QAQC/
│   ├── 04_LiDAR_P1_CoRegistration_QAQC/
│   ├── 05_Map_QAQC/
│   └── 06_Final_QAQC_Report/
│
└── 10_Final_Deliverables/
    ├── 01_Orthomosaic/
    ├── 02_LiDAR_PointCloud/
    ├── 03_DTM_DSM_Hillshade_Slope/
    ├── 04_GIS_GPKG/
    ├── 05_Field_Planning_Maps/
    ├── 06_Reports/
    └── 07_Archive_Package/
## 3. Файлын нэршлийн стандарт
### 3.1 Raw data нэршил
YYYYMMDD_PROJECT_SENSOR_BLOCK_MISSION_RAW
Жишээ:
20260609_XV023222_L3_BLK001_M001_RAW
20260609_XV023222_P1_PR01_M001_RAW
20260609_XV023222_L2_PR01_M001_RAW
### 3.2 Processed output нэршил
XV023222_SENSOR_OUTPUT_BLOCKorPR_DATE_UTM47N.ext
Жишээ:
XV023222_L3_PointCloud_BLK001_20260609_UTM47N.laz
XV023222_L3_DTM_BLK001_20260609_UTM47N.tif
XV023222_L3_Hillshade315_BLK001_20260609_UTM47N.tif
XV023222_P1_Orthomosaic_PR01_20260610_UTM47N.tif
XV023222_P1_DSM_PR01_20260610_UTM47N.tif
XV023222_QGIS_Interpretation_PR01_20260610_UTM47N.gpkg
### 3.3 CRS стандарт
Бүх өгөгдөл нэг координатын системтэй байна:
WGS 84 / UTM Zone 47N
EPSG:32647
Өмнөх Phase 5 баримтад мөн QGIS project CRS-ийг WGS 84 / UTM Zone 47N, EPSG:32647 гэж ашиглахаар заасан.
## 4. Алхам 1 — Input data бүртгэх
### 4.1 Бүртгэлийн файл үүсгэх
00_Admin_Register/00_Input_File_Register.xlsx файл үүсгээд дараах баганатай болгоно.

| Багана | Тайлбар |
| --- | --- |
| file_id | Дотоод дугаар |
| file_name_original | Эх файлын нэр |
| file_name_standard | Стандарт нэр |
| folder_path | Хадгалсан фолдер |
| data_type | license / DEM / L3 raw / P1 photo / GCP гэх мэт |
| CRS | EPSG код |
| date_received | Авсан огноо |
| source | DJI / QGIS / CMCS / field team |
| used_in_step | Аль алхамд ашиглах |
| remarks | Тайлбар |

### 4.2 Оруулах үндсэн input
01_Input_Data/ дотор дараах өгөгдлийг байрлуулна.
License boundary
Phase 4 target / prospect polygon
Geological map, mineral occurrence, CMCS/MRPAM data
DEM, slope, hillshade
KOMPSAT / Sentinel / basemap
Lineament / structure layer
Road, drainage, access route
GCP / checkpoint coordinate CSV
### 4.3 Шалгах зүйл

| Шалгах зүйл | Хүлээн авах нөхцөл |
| --- | --- |
| CRS | Бүх layer EPSG:32647 эсвэл зөв reproject хийх боломжтой |
| License boundary | Бодит байршил зөв |
| DEM | gap, NoData, shift байхгүй |
| Phase 4 target | License дотор зөв давхцсан |
| GCP/checkpoint | X, Y, Z багана бүрэн |
| CMCS/geology | Ашигт малтмалын илрэл, геологийн контакттай давхарлаж болохуйц |

## 5. Алхам 2 — Raw data backup хийх
### 5.1 Backup зарчим
Raw data дээр шууд ажиллахгүй. Эхлээд 3 хувь хуулна.

| Хувь | Байршил | Зорилго |
| --- | --- | --- |
| Copy 1 | Field laptop | Ажлын үндсэн хуулбар |
| Copy 2 | External SSD | Нөөц |
| Copy 3 | Office/cloud/server | Архив |

### 5.2 SD card copy
SD card-аас шууд дараах фолдерт хуулна.
02_Raw_Data_Backup/06_Original_SD_Card_Copy_ReadOnly/
Энэ фолдерийг Read Only болгож хадгална.
### 5.3 L3 raw хадгалах
02_Raw_Data_Backup/01_L3_LiDAR_Raw/BLK001/
Энд дараах төрлийн файл бүрэн байх ёстой.
- .LDR
*.IMU
*.RTK / *.RTL / *.RTS
*.RTB эсвэл base *.DAT / RINEX
*.CLC / *.CLI / *.CMI
*.JPG
*.RPOS / *.RPT
### 5.4 P1 raw хадгалах
02_Raw_Data_Backup/02_P1_Photo_Raw/PR01/
Энд дараах файл байна.
DJI_*.JPG
DJI_*.DNG / if available
*.MRK
EXIF metadata
RTK/PPK trajectory
GCP/checkpoint CSV
Flight log
### 5.5 Backup шалгах

| Шалгах зүйл | Хүлээн авах нөхцөл |
| --- | --- |
| Файлын тоо | SD card ба backup дээр ижил |
| File size | 0 KB файл байхгүй |
| Folder name | Mission ID-тэй таарч байх |
| LiDAR raw | LDR, IMU, RTK, calibration файл бүрэн |
| P1 photo | Зургийн дараалал тасраагүй |
| Flight log | Mission бүрээр бүрэн |

## 6. Алхам 3 — QGIS 4.0.3 project бэлтгэх
### 6.1 Project үүсгэх
QGIS 4.0.3 нээгээд:
Project → New
Project CRS → EPSG:32647
Save As:
06_QGIS_403_Project/01_QGIS_Project_File/XV023222_Phase5_LiDAR_P1_QGIS403.qgz
### 6.2 Layer-ууд оруулах
QGIS-д дараах layer-уудыг оруулна.
License boundary
Phase 4 target polygon
DEM
Slope
Hillshade
KOMPSAT / Sentinel basemap
Geological map
Mineral occurrence
Lineament
Drainage
Road / access
GCP / checkpoint
### 6.3 GeoPackage үүсгэх
06_QGIS_403_Project/02_QGIS_Geopackage/ дотор нэг master GeoPackage үүсгэнэ.
XV023222_Phase5_Master_Interpretation_UTM47N.gpkg
Дотор нь дараах layer-уудыг үүсгэнэ.

| Layer name | Geometry | Зориулалт |
| --- | --- | --- |
| Drone_Survey_Blocks | Polygon | L3 survey block |
| Drone_Prospect_Targets | Polygon | P1 prospect target |
| GCP_Checkpoints | Point | GCP/checkpoint |
| L3_Lineaments | Line | L3 hillshade lineament |
| L3_Structural_Corridors | Polygon | Structural corridor |
| P1_Outcrops | Polygon | P1 outcrop |
| P1_Lithology_Preliminary | Polygon | Урьдчилсан литологи |
| P1_Contacts | Line | Контакт |
| P1_Vein_Corridors | Line/Polygon | Судал, alteration corridor |
| Sample_Planning | Point | Дээж авах цэг |
| Trench_Planning | Line/Polygon | Суваг төлөвлөлт |
| Drill_Pad_Planning | Point/Polygon | Өрөмдлөгийн талбай |
| Field_Traverse | Line | Маршрут |

### 6.4 Атрибутын стандарт
Бүх planning болон interpretation layer дараах үндсэн талбартай байна.

| Field | Type | Жишээ |
| --- | --- | --- |
| project_id | text | XV023222 |
| prospect_id | text | PR01 |
| block_id | text | BLK001 |
| source | text | L3 / P1 / L2 / CMCS |
| interpretation | text | preliminary / reviewed |
| confidence | text | High / Medium / Low |
| reason | text | lineament + alteration + outcrop |
| needs_fieldcheck | text | yes / no |
| date | date | 2026-06-09 |
| author | text | initials |
| remarks | text | тайлбар |

## 7. Алхам 4 — L3 LiDAR-ийг DJI Terra дээр боловсруулах
Энэ алхам бол P1 боловсруулалтын өмнөх хамгийн чухал суурь алхам. L3-ээс гарсан DTM/DSM/point cloud/hillshade/trajectory accuracy нь дараа нь P1-ийн байрлал ба өндөрийн reference болно.
### 7.1 DJI Terra project үүсгэх
DJI Terra нээгээд:
New Mission → LiDAR Point Cloud
Mission name:
XV023222_L3_BLK001_20260609_Terra
Project-ийг дараах фолдерт хадгална.
03_DJI_Terra_Processing/01_L3_Terra_Projects/
### 7.2 Raw folder import хийх
Terra дээр:
Files → Select Folder
Дараах фолдерийг сонгоно.
02_Raw_Data_Backup/01_L3_LiDAR_Raw/BLK001/
### 7.3 PPK / RTK тохируулах
Хэрэв D-RTK base ашигласан бол:
Base Station Center Point Settings
Дараах мэдээллийг оруулна.

| Мэдээлэл | Оруулах утга |
| --- | --- |
| Base coordinate | RTK хэмжсэн X/Y/Z |
| CRS | EPSG:32647 |
| Antenna height | Field log дээрх өндөр |
| Base file | *.DAT / RINEX / RTB |

### 7.4 Output тохиргоо
Terra тохиргоо:

| Setting | Утга |
| --- | --- |
| Output CRS | EPSG:32647 |
| Point cloud density | High |
| RGB coloring | ON |
| Output LAS/LAZ | ON |
| DSM | ON |
| DEM/DTM | ON |
| Orthophoto/DOM | ON |
| Accuracy optimization | ON, боломжтой бол |
| Report | ON |

Өмнөх баримтад L3/L2 LiDAR reconstruction-д DJI Terra-г raw decode/calibration хийх vendor программ гэж заасан бөгөөд LiDAR reconstruction-д Terra-г ашиглах логиктой.
### 7.5 Processing эхлүүлэх
Start Processing
Дууссаны дараа дараах гаралтыг экспортолно.
03_DJI_Terra_Processing/02_L3_Exports/PointCloud_LAS_LAZ/
03_DJI_Terra_Processing/02_L3_Exports/DSM/
03_DJI_Terra_Processing/02_L3_Exports/DEM_DTM/
03_DJI_Terra_Processing/02_L3_Exports/DOM_Orthophoto/
03_DJI_Terra_Processing/02_L3_Exports/Terra_Reports/
### 7.6 L3 output нэрлэх
XV023222_L3_PointCloud_BLK001_20260609_UTM47N.laz
XV023222_L3_DSM_BLK001_20260609_UTM47N.tif
XV023222_L3_DTM_BLK001_20260609_UTM47N.tif
XV023222_L3_DOM_BLK001_20260609_UTM47N.tif
XV023222_L3_Terra_Report_BLK001_20260609.pdf
## 8. Алхам 5 — L3 LiDAR QA/QC хийх
### 8.1 DJI Terra report шалгах
Terra report-оос дараах үзүүлэлтийг шалгана.

| QA/QC item | Хүлээн авах нөхцөл |
| --- | --- |
| Trajectory residual | ≤ 3.0 см |
| Strip height difference | ≤ 5.0 см |
| Checkpoint horizontal RMSE | ≤ 5.0 см |
| Checkpoint vertical RMSE | ≤ 5.0 см |
| L3 point density | ≥ 20 pts/m² |
| Coverage | Block бүрэн бүрхсэн |
| Void / gap | ≤ 1% |

Өмнөх баримтад L3 reconnaissance-ийн цэгийн нягтын босгыг ≥20 pts/m², checkpoint RMSE-ийг ≤5 см, strip өндрийн зөрүүг ≤5 см гэж тогтоосон.
### 8.2 QGIS дээр L3 output шалгах
QGIS 4.0.3 дээр дараах raster-уудыг оруулна.
L3_DTM.tif
L3_DSM.tif
L3_DOM.tif
Шалгах:
License boundary-тэй давхцаж байгаа эсэх
GCP/checkpoint-тэй shift байгаа эсэх
DTM-д нүх, spike, artefact байгаа эсэх
DSM ба DOM хооронд байрлалын зөрүү байгаа эсэх
L3 DOM ба previous basemap хооронд том зөрүү байгаа эсэх
## 9. Алхам 6 — L3 DTM-ээс terrain derivative гаргах
### 9.1 QGIS дээр hillshade гаргах
QGIS:
Raster → Analysis → Hillshade
4 чиглэлээр hillshade гаргана.

| Output | Azimuth | Altitude |
| --- | --- | --- |
| Hillshade045 | 45 | 45 |
| Hillshade135 | 135 | 45 |
| Hillshade225 | 225 | 45 |
| Hillshade315 | 315 | 45 |

Файлуудыг хадгалах:
04_LiDAR_Derived_Terrain_Base/04_Hillshade_MultiAzimuth/
Нэршил:
XV023222_L3_Hillshade045_BLK001_20260609_UTM47N.tif
XV023222_L3_Hillshade135_BLK001_20260609_UTM47N.tif
XV023222_L3_Hillshade225_BLK001_20260609_UTM47N.tif
XV023222_L3_Hillshade315_BLK001_20260609_UTM47N.tif
### 9.2 Slope гаргах
QGIS:
Raster → Analysis → Slope
Output:
04_LiDAR_Derived_Terrain_Base/05_Slope_Aspect_Curvature/
XV023222_L3_Slope_BLK001_20260609_UTM47N.tif
### 9.3 Contour гаргах
QGIS:
Raster → Extraction → Contour
Contour interval:

| Масштаб | Interval |
| --- | --- |
| Regional / L3 | 1–5 м |
| Prospect / P1 | 0.5–1 м |
| Trench planning | 0.25–0.5 м, боломжтой бол |

Output:
04_LiDAR_Derived_Terrain_Base/07_Drainage_Contour/
XV023222_L3_Contour_1m_BLK001_20260609_UTM47N.gpkg
## 10. Алхам 7 — L3 дээр prospect / structure ялгах
### 10.1 Ашиглах layer
QGIS дээр дараах layer-уудыг зэрэг харуулна.
L3_DTM
L3_Hillshade045/135/225/315
L3_Slope
L3_DOM
License boundary
Phase 4 target
Geological map
Mineral occurrence
Lineament
Drainage
### 10.2 Lineament digitize хийх
L3_Lineaments layer дээр дараах шинжийг зурна.

| Шинж | Тайлбар |
| --- | --- |
| Шулуун жалга | fault-controlled drainage байж болно |
| Ridge alignment | структурын чиглэл |
| Drainage offset | хагарал / шилжилт |
| Slope break | контакт / fault scarp |
| Linear valley | fault corridor |
| Quartz ridge possible | судлын морфологи |

Атрибут бөглөх:
source = L3_Hillshade
confidence = High / Medium / Low
reason = straight drainage + slope break
### 10.3 Prospect polygon үүсгэх
Drone_Prospect_Targets layer дээр prospect polygon зурна.
Prospect зэрэглэл:

| Зэрэглэл | Шалгуур |
| --- | --- |
| A | Lineament intersection + alteration/contact + mineral occurrence + outcrop |
| B | Structure эсвэл alteration шинж дунд зэрэг |
| C | Сул шинжтэй, field check шаардлагатай |

Өмнөх баримтад prospect-ийн зэрэглэлийг A/B/C, prospect ID-г PR01, PR02… гэж ашиглахаар заасан.
## 11. Алхам 8 — P1 боловсруулахын өмнөх LiDAR reference package бэлтгэх
Энэ бол шинэчилсэн workflow-ийн гол хэсэг.
### 11.1 P1-д ашиглах L3/LiDAR reference багц
P1 prospect бүрийн хувьд дараах файлуудыг reference болгон бэлтгэнэ.
L3_DTM clipped to PR01
L3_DSM clipped to PR01
L3_DOM clipped to PR01
L3_Hillshade clipped to PR01
L3_Contour clipped to PR01
GCP/checkpoint clipped to PR01
Prospect boundary PR01
### 11.2 QGIS дээр clip хийх
QGIS:
Raster → Extraction → Clip Raster by Mask Layer
Mask layer:
Drone_Prospect_Targets → PR01
Output folder:
05_P1_Photogrammetry_Processing/08_P1_QAQC_LiDAR_Comparison/PR01_LiDAR_Reference/
Файлын нэр:
XV023222_L3_DTM_PR01_Reference_UTM47N.tif
XV023222_L3_DSM_PR01_Reference_UTM47N.tif
XV023222_L3_Hillshade_PR01_Reference_UTM47N.tif
XV023222_L3_Contour_PR01_Reference_UTM47N.gpkg
### 11.3 Яагаад энэ хэрэгтэй вэ?
P1 боловсруулалт хийхэд дараах алдаа гарч болно.

| Боломжит алдаа | LiDAR reference-аар шалгах арга |
| --- | --- |
| Orthomosaic XY shift | P1 ortho-г L3 DOM / GCP-тэй давхарлаж шалгах |
| P1 DSM Z bias | P1 DSM − L3 DSM/DTM difference raster гаргах |
| SfM alignment сул | L3 hillshade/terrain shape-тэй таарах эсэхийг шалгах |
| Vegetation нөлөө | P1 DSM ба L3 DTM ялгаагаар таних |
| Outcrop texture алдаа | P1 ortho-г L3 terrain morphology-той хамт тайлах |

## 12. Алхам 9 — P1 фотограмметрийн processing хийх
P1 боловсруулалтыг DJI Terra эсвэл photogrammetry software дээр хийж болно. Энэ зааварт DJI Terra + QGIS 4.0.3 workflow-д нийцүүлнэ.
### 12.1 P1 project үүсгэх
DJI Terra дээр:
New Mission → Visible Light / Photogrammetry
Mission name:
XV023222_P1_PR01_20260610_Terra
Project folder:
05_P1_Photogrammetry_Processing/01_P1_Project_PR01/
### 12.2 P1 raw photo import хийх
Import хийх raw folder:
02_Raw_Data_Backup/02_P1_Photo_Raw/PR01/
Оруулах:
DJI_*.JPG
DJI_*.DNG, if available
MRK / EXIF
RTK/PPK data
GCP/checkpoint CSV
### 12.3 Coordinate system тохируулах
Output CRS = EPSG:32647
Vertical datum = төслийн GNSS/RTK datum-тай ижил
### 12.4 GCP/checkpoint оруулах
GCP/checkpoint CSV-г import хийнэ.

| Point type | Ашиглалт |
| --- | --- |
| GCP | Adjustment-д ашиглана |
| Checkpoint | Зөвхөн accuracy шалгана |

Өмнөх баримтад block/prospect бүрд хамгийн багадаа 5 GCP + 2–3 checkpoint, P1 prospect-д GCP хоорондын зайг ойролцоогоор 100 м байхаар заасан.
### 12.5 P1 processing тохиргоо

| Setting | Утга |
| --- | --- |
| Output | Orthomosaic, DSM, point cloud, report |
| Quality | High |
| Camera calibration | Auto + fixed camera metadata |
| GCP adjustment | ON |
| Checkpoint residual | ON |
| Output CRS | EPSG:32647 |
| DSM | ON |
| Orthomosaic | ON |

### 12.6 Processing эхлүүлэх
Start Reconstruction / Start Processing
Output:
05_P1_Photogrammetry_Processing/04_P1_Orthomosaic_Exports/
05_P1_Photogrammetry_Processing/05_P1_DSM_Exports/
05_P1_Photogrammetry_Processing/06_P1_PointCloud_Exports/
05_P1_Photogrammetry_Processing/07_P1_Processing_Reports/
Файлын нэр:
XV023222_P1_Orthomosaic_PR01_20260610_UTM47N.tif
XV023222_P1_DSM_PR01_20260610_UTM47N.tif
XV023222_P1_PointCloud_PR01_20260610_UTM47N.laz
XV023222_P1_Processing_Report_PR01_20260610.pdf
## 13. Алхам 10 — P1 output-ийг LiDAR reference-тай шалгах
### 13.1 QGIS дээр давхарлах
QGIS-д дараах layer-уудыг оруулна.
P1_Orthomosaic_PR01.tif
P1_DSM_PR01.tif
L3_DTM_PR01_Reference.tif
L3_DSM_PR01_Reference.tif
L3_Hillshade_PR01_Reference.tif
GCP_Checkpoints
Prospect boundary PR01
### 13.2 XY shift шалгах
P1 orthomosaic-г дараах reference-тэй харьцуулна.

| Reference | Шалгах зүйл |
| --- | --- |
| GCP/checkpoint | Цэг дээр зураг таарч байгаа эсэх |
| L3 DOM | Зам, жалга, ridge, outcrop shift |
| L3 hillshade | Terrain shape таарч байгаа эсэх |
| License / prospect boundary | Байршил алдаагүй эсэх |

Шалгах арга:
P1 orthomosaic-г 50% transparency болгоно.
Доор нь L3 DOM эсвэл hillshade тавина.
Outcrop edge, drainage, ridge line, road, GCP marker дээр зөрүү байгаа эсэхийг шалгана.
Shift байвал хэмжинэ.
Хүлээн авах нөхцөл:
Checkpoint RMSE ≤ 5 см
P1 ortho relative accuracy ≤ 2 × GSD
Өмнөх баримтад P1-ийн үнэмлэхүй байрлалын босго нь checkpoint RMSE ≤5 см, харьцангуй ortho нарийвчлал нь ≤2 × GSD гэж тусгасан.
### 13.3 Z difference шалгах
P1 DSM болон L3 DSM/DTM-ийн өндрийн зөрүүг raster calculator-аар гаргана.
QGIS:
Raster Calculator
Expression:
"P1_DSM@1" - "L3_DSM@1"
Output:
09_QAQC_Final/04_LiDAR_P1_CoRegistration_QAQC/
XV023222_P1_minus_L3_DSM_PR01_20260610_UTM47N.tif
Тайлбар:

| Difference | Боломжит шалтгаан |
| --- | --- |
| 0–5 см | Маш сайн таарч байна |
| 5–10 см | Хүлээн зөвшөөрөх боломжтой, тайлбар шаардлагатай |
| 10 см-ээс их | GCP, PPK, vertical datum, processing дахин шалгах |
| Vegetation area дээр өндөр зөрүү | P1 DSM ургамлын гадарга, L3 DTM bare-earth байж болно |
| Outcrop дээр системтэй өндөр зөрүү | Z bias байж болно |

### 13.4 Co-registration QA хүснэгт
09_QAQC_Final/04_LiDAR_P1_CoRegistration_QAQC/ дотор Excel үүсгэнэ.
XV023222_LiDAR_P1_CoRegistration_QAQC.xlsx
Багана:

| Багана | Тайлбар |
| --- | --- |
| prospect_id | PR01 |
| checkpoint_id | CP001 |
| lidar_z | L3/L2 өндөр |
| p1_dsm_z | P1 DSM өндөр |
| dz | p1_dsm_z - lidar_z |
| xy_offset_cm | Хэвтээ зөрүү |
| surface_type | outcrop / soil / vegetation / road |
| accepted | yes/no |
| reason | тайлбар |

## 14. Алхам 11 — Хэрэв L2 ашигласан бол боловсруулах
L2-г зөвхөн дараах нөхцөлд ашиглана.

| Нөхцөл | L2 хэрэгтэй эсэх |
| --- | --- |
| Ургамалтай, bare-earth DTM хэрэгтэй | Тийм |
| Текстургүй outcrop, P1 SfM сул | Тийм |
| Trench/detail structural mapping-д 0.1 м terrain хэрэгтэй | Тийм |
| Ил, ургамалгүй, L3 хангалттай | Үгүй |

Өмнөх баримтад Stage 2-ийн default нь P1 бөгөөд L2-г зөвхөн ургамалтай, текстургүй outcrop, эсвэл 0.1 м микро-рельеф шаардсан тохиолдолд нэмнэ гэж заасан.
### 14.1 L2 Terra processing
L2 нь L3-тэй ижил workflow-той.
DJI Terra → New Mission → LiDAR Point Cloud
Import L2 raw
Set CRS EPSG:32647
PPK/base settings
Output LAS/LAZ + DSM + DEM/DTM + DOM + report
### 14.2 L2 output
XV023222_L2_PointCloud_PR01_20260610_UTM47N.laz
XV023222_L2_DTM_PR01_20260610_UTM47N.tif
XV023222_L2_DSM_PR01_20260610_UTM47N.tif
XV023222_L2_Hillshade_PR01_20260610_UTM47N.tif
### 14.3 P1-тэй давхарлаж ашиглах
QGIS дээр:
P1 Orthomosaic = литологи, өнгө, outcrop detail
L2 DTM/Hillshade = structure, micro-relief, trench planning
L3 DTM/Hillshade = regional context
## 15. Алхам 12 — QGIS 4.0.3 дээр тайлал хийх
### 15.1 Layer stack дараалал
QGIS дээр layer-уудыг дараах дарааллаар байрлуулна.
Top:
Sample_Planning
Trench_Planning
P1_Contacts
P1_Vein_Corridors
P1_Outcrops
P1_Lithology_Preliminary
L3/L2 Lineaments
Prospect boundary
GCP/checkpoints

Raster:
P1 Orthomosaic
L2 Hillshade, if used
L3 Hillshade
L3/L2 Slope
L3/L2 DTM
Basemap / geology
### 15.2 P1 orthomosaic дээр outcrop digitize хийх
P1_Outcrops layer дээр дараах шинжийг зурна.

| Шинж | Тайлбар |
| --- | --- |
| Ил гарсан чулуулаг | vegetation/soil бага |
| Өнгөний ялгаа | lithology/contact байж болно |
| Барзгар texture | outcrop эсвэл breccia байж болно |
| Цайвар linear feature | quartz vein байж болно |
| Улаан/шар/бор өнгө | oxidation/alteration байж болно |

### 15.3 Contact / vein / lineament digitize хийх

| Layer | Digitize хийх зүйл |
| --- | --- |
| P1_Contacts | Өнгө, texture, ridge/slope break-ийн зааг |
| P1_Vein_Corridors | Цайвар судал, quartz ridge, oxide vein |
| L3_Lineaments | Том структур |
| Sample_Planning | Сорьц авах саналтай цэг |
| Trench_Planning | Structure/contact-ийг хөндлөн огтлох шугам |

### 15.4 Confidence тэмдэглэх

| Confidence | Утга |
| --- | --- |
| High | P1 зураг + LiDAR terrain + geology давхцсан |
| Medium | 2 төрлийн evidence байгаа |
| Low | Зөвхөн зураг эсвэл зөвхөн terrain шинж |

## 16. Алхам 13 — Crop бэлтгэх
Өмнөх баримтад AI lithology SOP-д нэг prospect бүр дээр L3 250×250, P1 50×50, P1 10×10, P1 5×5 crop ашиглахаар заасан.
### 16.1 Crop хэмжээ

| Crop | Sensor | Зорилго |
| --- | --- | --- |
| 250×250 м | L3 | Prospect context |
| 50×50 м | P1 | Local geology |
| 10×10 м | P1 | Lithology |
| 5×5 м | P1 | Sample detail |

### 16.2 QGIS дээр crop хийх
QGIS:
Raster → Extraction → Clip Raster by Extent
Жишээ: 10×10 м crop хийх бол төв координатаас:
xmin = E - 5
xmax = E + 5
ymin = N - 5
ymax = N + 5
### 16.3 Crop хадгалах
08_Crop_AI_Lithology/01_L3_250x250_Context/
08_Crop_AI_Lithology/02_P1_50x50_Local/
08_Crop_AI_Lithology/03_P1_10x10_Lithology/
08_Crop_AI_Lithology/04_P1_5x5_Sample_Detail/
Нэршил:
PR01_L3_250x250_T001_E512000_N5321000.png
PR01_P1_50x50_C001_E512345_N5321456.png
PR01_P1_10x10_C001_E512345_N5321456.png
PR01_P1_5x5_D001_E512348_N5321459.png
### 16.4 Layout дээр бичих мэдээлэл
Зураг бүр дээр:
Project name
Prospect ID
Crop ID
North arrow
Scale bar
Center coordinate
Sensor
Flight height
Flight speed
Crop size
Projection EPSG:32647
Legend
## 17. Алхам 14 — Field planning layer гаргах
### 17.1 Sample point planning
Sample_Planning layer дээр дараах газарт цэг тавина.

| Priority | Шалгуур |
| --- | --- |
| SP High | Quartz vein + oxidation + contact/lineament intersection |
| SP Medium | Outcrop + alteration color |
| SP Low | Uncertain lithology, field-check хэрэгтэй |

Атрибут:
sample_id = SP-PR01-001
sample_type = rock chip / channel / soil
reason = qz vein + oxide + contact
priority = High
### 17.2 Trench planning
Trench_Planning layer дээр trench line зурна.
Шалгуур:
Contact/vein/structure-ийг хөндлөн огтлох
Налуу хэт огцом биш
Техник очих боломжтой
Drainage, water, protected area-аас зайлсхийсэн
License boundary дотор
### 17.3 Drill pad planning
Drill_Pad_Planning layer дээр боломжит pad polygon/point зурна.
Шалгуур:
Target geometry зөв
Налуу бага
Access ойр
Environmental risk бага
Ус, логистик боломжтой
License дотор
## 18. Алхам 15 — QA/QC final check
### 18.1 LiDAR QA/QC

| Item | Босго |
| --- | --- |
| L3 point density | ≥20 pts/m² |
| L2 point density, if used | ≥100 pts/m² |
| Checkpoint RMSE XY | ≤5 см |
| Checkpoint RMSE Z | ≤5 см |
| Strip difference | ≤5 см |
| DTM void | ≤1% |

### 18.2 P1 QA/QC

| Item | Босго |
| --- | --- |
| Checkpoint RMSE XY/Z | ≤5 см |
| Ortho relative accuracy | ≤2 × GSD |
| Blur | Тайлбарт саад болохгүй |
| Seamline | Том эвдрэлгүй |
| Coverage | Prospect бүрэн |
| CRS | EPSG:32647 |
| Pixel size | Төлөвлөсөн GSD-тэй нийцсэн |

Өмнөх баримтад P1-ийн flight altitude-г ойролцоогоор 60 м AGL, 35 мм линзтэй үед GSD-г ойролцоогоор 0.8 см/pixel гэж заасан.
### 18.3 LiDAR–P1 co-registration QA/QC

| Item | Хүлээн авах нөхцөл |
| --- | --- |
| P1 ortho vs L3 DOM | XY shift байхгүй эсвэл ≤5 см |
| P1 DSM vs L3/L2 DSM | Системтэй Z bias байхгүй |
| P1 orthomosaic vs L3 hillshade | Terrain feature таарч байх |
| GCP/checkpoint | Цэгүүд зөв байрласан |
| Difference raster | Outcrop дээр зөрүү бага |

## 19. Алхам 16 — Final deliverables бэлтгэх
10_Final_Deliverables/ дотор дараах багцыг бүрдүүлнэ.
10_Final_Deliverables/
├── 01_Orthomosaic/
│   └── XV023222_P1_Orthomosaic_PR##_UTM47N.tif
│
├── 02_LiDAR_PointCloud/
│   └── XV023222_L3_or_L2_PointCloud_*.laz
│
├── 03_DTM_DSM_Hillshade_Slope/
│   ├── DTM.tif
│   ├── DSM.tif
│   ├── Hillshade.tif
│   ├── Slope.tif
│   └── Contour.gpkg
│
├── 04_GIS_GPKG/
│   └── XV023222_Phase5_Master_Interpretation_UTM47N.gpkg
│
├── 05_Field_Planning_Maps/
│   ├── PR01_Field_Planning_Map.pdf
│   ├── PR01_Sample_Planning_Map.pdf
│   └── PR01_Trench_Drill_Planning_Map.pdf
│
├── 06_Reports/
│   ├── DJI_Terra_L3_Report.pdf
│   ├── P1_Processing_Report.pdf
│   ├── LiDAR_P1_CoRegistration_QAQC_Report.docx
│   └── Final_Phase5_Interpretation_Report.docx
│
└── 07_Archive_Package/
    ├── Input_Register.xlsx
    ├── Processing_Action_Log.xlsx
    ├── QAQC_Checklist.xlsx
    └── Version_Control_Log.docx
## 20. Алхам бүрийн action log бөглөх загвар
00_Admin_Register/01_Processing_Action_Log.xlsx файлд дараах байдлаар бүртгэнэ.

| step_no | date | operator | software | input | action | output | QA/QC result | issue | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 2026-06-09 | ___ | QGIS 4.0.3 | License, DEM | Project setup | qgz | OK | none | accept |
| 02 | 2026-06-09 | ___ | DJI Terra | L3 raw | LiDAR process | LAZ/DTM/DSM | OK | none | accept |
| 03 | 2026-06-09 | ___ | QGIS 4.0.3 | L3 DTM | Hillshade/slope | tif | OK | none | accept |
| 04 | 2026-06-10 | ___ | DJI Terra | P1 raw | Ortho/DSM | tif | RMSE OK | none | accept |
| 05 | 2026-06-10 | ___ | QGIS 4.0.3 | P1 + L3 | Co-registration | QA raster | OK | none | accept |

## 21. Нэг prospect дээр хийх богино дараалал
Жишээ нь PR01 дээр ажиллах бол:
PR01 prospect boundary-г QGIS дээр баталгаажуулна.
L3 DTM/DSM/Hillshade-ийг PR01 boundary-р clip хийнэ.
PR01-ийн P1 raw photo-г backup-аас processing folder руу хуулна.
DJI Terra дээр P1 project үүсгэнэ.
P1 photo + RTK/PPK + GCP/checkpoint import хийнэ.
Output CRS-г EPSG:32647 болгоно.
Orthomosaic, DSM, point cloud, report гаргана.
QGIS дээр P1 orthomosaic-г L3 hillshade/DOM/DTM-тэй давхарлаж шалгана.
P1 DSM − L3 DSM difference raster гаргана.
XY/Z shift байхгүй бол accept хийнэ.
P1 orthomosaic дээр outcrop, contact, vein, alteration digitize хийнэ.
L3/L2 hillshade дээр structure, lineament баталгаажуулна.
Sample, trench, drill planning layer гаргана.
250×250, 50×50, 10×10, 5×5 crop export хийнэ.
QA/QC checklist бөглөнө.
Final map, GPKG, report folder-т хуулна.
## 22. Хүлээн авах эцсийн шалгуур

| Бүлэг | Accept condition |
| --- | --- |
| Folder | Стандарт бүтэц бүрэн |
| Raw backup | 3 хувь, file count шалгасан |
| DJI Terra L3 | LAZ, DTM, DSM, DOM, report гарсан |
| L3 QA/QC | RMSE, density, strip difference босго хангана |
| P1 processing | Orthomosaic, DSM, report гарсан |
| LiDAR–P1 comparison | XY/Z shift зөвшөөрөх хэмжээнд |
| QGIS project | Бүх layer EPSG:32647 |
| Interpretation | Lineament, contact, outcrop, vein, sample/trench layer үүссэн |
| Crop | L3 250×250 + P1 50/10/5 бүрэн |
| Deliverables | GeoTIFF, LAZ, GPKG, PDF map, report бүрэн |

## 23. Чухал анхаарах зүйл
P1 зураг нь литологи, outcrop, quartz vein, alteration тайллын хувьд хамгийн нарийвчилсан зураг боловч өндөр ба terrain-ийн хувьд LiDAR reference-гүйгээр дангаар нь эцэслэж болохгүй. L3/L2 LiDAR-аас гарсан DTM, DSM, hillshade, checkpoint QA/QC нь P1 orthomosaic ба DSM-ийн байрлал-өндрийн үндсэн хяналт болно.
Эцсийн зарчим:
LiDAR controls position and elevation.
P1 controls visual geology.
QGIS integrates both.
QA/QC decides acceptance.
Field work confirms interpretation.
## 24. Эх сурвалжийн тэмдэглэл
Энэхүү DOCX нь хавсралтаар өгсөн XV-023222_Phase5_Drone_LiDAR_Photogrammetry_v0.4.docx баримтын Phase 5 workflow, Stage 1 L3 reconnaissance, Stage 2 P1/L2 prospect processing, Appendix A–C-ийн raw файл мөшгөлт, QA/QC босго, crop/AI lithology SOP-д үндэслэн боловсруулав.
