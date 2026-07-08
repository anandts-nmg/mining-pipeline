<!-- source: XV-023222_Buduunkhad_Phase1_Methodology.docx (converted from Word; canonical form for LLM ingestion) -->

БҮДҮҮНХАД ХАЙГУУЛЫН ТАЛБАЙ
XV-023222 / L23222
PHASE 1 — Өгөгдлийн аудит ба Master GIS бэлтгэл
Гүйцэтгэх дэлгэрэнгүй арга зүй ба ажлын дараалал
Стандарт CRS: WGS 84 / UTM Zone 47N — EPSG:32647
Оролт: 78 raw input файл  •  Програм: QGIS

# Агуулга

# 1. Phase 1-ийн зорилго ба үндсэн зарчим
Phase 1 нь Бүдүүнхад талбайн хайгуулын дараагийн бүх шатны суурь болно. Энэ шатанд raw өгөгдлийг засварлахгүйгээр зөвхөн working copy дээр шалгалт, CRS тохируулга, бүртгэл, georeference хийж, бүх орон зайн өгөгдлийг нэг стандарт координатын системд (EPSG:32647) нэгтгэн Master GIS суурийг бий болгоно.
## 1.1. Эцсийн зорилго
- Бүх 78 raw input файлыг GIS-д ашиглах боломжтой эсэхээр шалгах;
- License boundary болон бүх орон зайн өгөгдлийг EPSG:32647 стандарт CRS-д нэгтгэх;
- Scan map, JPG, PDF, GeoTIFF, KMZ/KML, DEM, Sentinel, KOMPSAT, металлогени/геологийн зурагт CRS / georeference / resolution / extent / metadata QA/QC хийх;
- Master GIS Database (.gpkg) болон Master QGIS Project (.qgz) үүсгэх;
- Өгөгдөл тус бүрийн итгэлцлийн зэрэглэл (data confidence ranking) гаргах;
- Phase 2 (Remote Sensing) болон Phase 3 (Geological Synthesis)-д ашиглахад бэлэн GIS суурь бүрдүүлэх.
## 1.2. Удирдах зарчим

| Зарчим | Хэрэгжүүлэх дүрэм |
| --- | --- |
| Raw preservation | 00_Raw_Files_Archive доторх эх файлыг read-only хадгална. Нэр солих шаардлагатай бол register-д бичнэ, эх файлыг overwrite хийхгүй. |
| Processing copy | Бүх боловсруулалтыг зөвхөн working copy дээр хийнэ. Эх raster, KMZ, PDF, scan-г шууд дарж хадгалахгүй. |
| CRS control | Эцсийн бүтээгдэхүүн EPSG:32647-д хадгалагдана. Native/source CRS-г metadata болон QA/QC log-д хадгална. |
| Sidecar integrity | .tfw, .jgw, .aux.xml, .ovr, .rpc, .eph, .txt зэрэг туслах файлуудыг үндсэн raster/image-ээс салгахгүй хамт хадгална. |
| Evidence hierarchy | Remote sensing / pXRF / drone = support evidence. Lab assay + field geology + structural control = decision evidence. |
| Decision gate | Phase 1 төгсгөлд QA/QC болон go/no-go шалгуурыг хангаж байж дараагийн шат руу шилжинэ. |

# 2. Folder бүтэц
Одоо байгаа 11 (эсвэл 12) сэдэвчилсэн folder-ийг устгахгүй, нэрийг нь солихгүй. Үүнийг Raw / Input Evidence Library болгон ашиглаж, дээр нь тусдаа Phase 1 ажлын орчныг нэмнэ. Ингэснээр raw өгөгдөл ба боловсруулалт хоёр тусдаа байрлана.
## 2.1. Төслийн дээд түвшний бүтэц
XV-023222_Buduunkhad_Project/
│
├── 00_Raw_Input_Evidence_Library/        (эх өгөгдөл — read-only)
│     ├── 01_Tectonic_Terrane_KMZ/
│     ├── 02_DEM_ALOS_ASTERGDEM/
│     ├── 03_KOMPSAT2_MSC_L1G/
│     ├── 04_HeavyMineral_StreamSediment_Field/
│     ├── 05_Geology_Mineral_Prospectivity/
│     ├── 06_Regional_Metallogenic_L47B/
│     └── 07_Basemap_Sentinel2_ASTER/
│
├── 01_Phase_1_Data_Audit_and_Master_GIS_Setup/   (энэ шатны ажлын орчин)
├── 02_Phase_2_Remote_Sensing_Preprocessing/
├── 03_Phase_3_Geological_Metallogenic_Synthesis/
├── 04_Phase_4_Preliminary_Prospect_Ranking/
└── 99_Final_Deliverables/
## 2.2. Phase 1-ийн дотоод бүтэц
01_Phase_1_Data_Audit_and_Master_GIS_Setup/
│
├── 00_Admin_and_Method/
│     ├── Phase1_Methodology.docx
│     ├── Phase1_Action_Log.xlsx
│     └── Phase1_QAQC_Checklist.xlsx
│
├── 01_Input_Working_Copy/         (raw-аас хуулсан ажлын хувь)
│     ├── 01_Tectonic_Terrane_KMZ/ ... 07_Basemap_Sentinel2_ASTER/
│
├── 02_Inventory_and_Metadata/
│     ├── XV-023222_Buduunkhad_Phase1_File_Inventory.xlsx
│     ├── XV-023222_Buduunkhad_Phase1_Metadata_Register.xlsx
│     └── XV-023222_Buduunkhad_Sidecar_File_Check.xlsx
│
├── 03_CRS_Check/
│     ├── Vector_CRS_Check/   Raster_CRS_Check/
│     ├── Native_CRS_Notes/   Reprojected_EPSG32647/
│
├── 04_Georeference_Check/
│     ├── Scan_Maps_To_Georeference/   GCP_Tables/
│     ├── Georeferenced_Rasters/        Georeference_Residual_Reports/
│     └── Low_Confidence_Georef/
│
├── 05_Master_GIS_Database/
│     ├── XV-023222_Buduunkhad_Master_GIS_Database.gpkg
│     ├── XV-023222_Buduunkhad_Master_QGIS_Project.qgz
│     └── Styles_QML/
│
├── 06_QAQC_and_Confidence/
│     ├── XV-023222_Buduunkhad_CRS_Georeference_QAQC_Log.xlsx
│     ├── XV-023222_Buduunkhad_Data_Confidence_Ranking.xlsx
│     └── XV-023222_Buduunkhad_Data_Gap_Register.xlsx
│
└── 07_Output/
      ├── XV-023222_Buduunkhad_Phase1_Desktop_Study_Summary.docx
      ├── XV-023222_Buduunkhad_Phase1_Master_GIS_Index_Map.pdf
      └── XV-023222_Buduunkhad_Phase1_Deliverables_Readme.txt

# 3. Оролтын өгөгдөл (78 файл, 7 evidence group)
Phase 1-д бүх 78 raw input файл хамрагдана. Эдгээрийг 7 evidence group-т ангилсан бөгөөд group тус бүрд хийх гол шалгалт доор үзүүлэв.

| № | Evidence group | Файл | Phase 1-д хийх гол шалгалт |
| --- | --- | --- | --- |
| 01 | Tectonic / Terrane KMZ | 8 | License boundary, террейн контекст, KMZ/KML координат шалгах; scan-уудыг georeference-д бэлтгэх. |
| 02 | DEM (ALOS / ASTER GDEM) | 14 | DEM-ийн CRS, resolution, extent, NoData, өндрийн нэгж шалгах; sidecar (tfw/aux/ovr) холбох. |
| 03 | KOMPSAT-2 MSC L1G | 24 | PAN/MS raster, RPC, metadata, band identity, georeference шалгах; bundle бүрэн эсэхийг шалгах. |
| 04 | Heavy Mineral / Stream Sediment / Field | 6 | Scan map, legend, хээрийн дэвтэр, координатын мэдээллийг бүртгэх. |
| 05 | Geology / Mineral Prospectivity | 16 | 1:50,000 ба 1:200,000 геологи/ашигт малтмалын зургийг georeference-д бэлтгэх; occurrence хүснэгт цэвэрлэх. |
| 06 | Regional Metallogenic L47B | 4 | 1:500,000 металлогений зураг, legend, тайлан scan бүртгэх; региональ контекстээр georeference. |
| 07 | Basemap / Sentinel-2 / ASTER | 6 | GeoTIFF, Sentinel derived raster, ASTER HDF, Google basemap-ийн CRS шалгах; reproject шаардлага тэмдэглэх. |

Анхааруулга: Sidecar файлууд (.tfw, .jgw, .aux.xml, .ovr, .rpc, .eph, .txt) нь дангаараа орон зайн layer биш. Тэдгээрийг үндсэн raster/image-тэй хамт archive хийж, ганцаар нь GIS-д нээхгүй.

# 4. Ажлын дэлгэрэнгүй дараалал
## Алхам 1. Raw archive хамгаалах ба working copy үүсгэх
Эхний зарчим: 00_Raw_Input_Evidence_Library доторх эх файлыг огт өөрчлөхгүй. Phase 1-д ашиглах файлуудыг зөвхөн 01_Input_Working_Copy руу хуулна.

| № | Ажил | Тайлбар |
| --- | --- | --- |
| 1 | Raw folder-оос working copy үүсгэх | 7 evidence group-ийн бүтцийг хэвээр хадгална. |
| 2 | Файл бүрийн нэр, өргөтгөл, хэмжээ, эх сурвалж бүртгэх | Inventory Excel-д оруулна. |
| 3 | Sidecar бүрийг үндсэн файлтай холбох | .tfw, .jgw, .aux.xml, .ovr, .rpc, .eph, .txt бүрэн эсэхийг шалгах. |
| 4 | Дутуу sidecar байгаа эсэхийг шалгах | KOMPSAT bundle, GeoTIFF, scan map-д онцгой чухал. |
| 5 | SHA-256 / checksum бүртгэх | Raw ба working copy зөрсөн эсэхийг хянах. |

Phase 1 Action Log-ийн баганууд:
Date • Operator • File group • Action • Software • Input file • Output file • Issue • Status
## Алхам 2. Master inventory үүсгэх
Файл бүрийг нэг мөрөөр бүртгэнэ. Inventory-ийн баганууд:

| Багана | Тайлбар / жишээ |
| --- | --- |
| File_ID | BK-P1-001 гэх мэт давтагдашгүй дугаар |
| Evidence_Group | 01_Tectonic_Terrane_KMZ ... 07_Basemap_Sentinel2_ASTER |
| Original_Filename | Raw файлын нэр |
| Working_Copy_Path | Phase 1 working copy дахь зам |
| File_Type | KMZ, KML, TIF, JPG, PDF, DOCX, XLSX, HDF гэх мэт |
| Spatial_Type | Vector / Raster / Scan / Table / Text / Report |
| Has_CRS / Native_CRS | Yes / No / Unknown ба EPSG код эсвэл тайлбар |
| Target_CRS | EPSG:32647 |
| Has_Georeference | Yes / No / Approx / Unknown |
| Sidecar_Files | TFW / RPC / AUX / OVR байгаа эсэх |
| Open_Status | Opens / Error / Needs conversion |
| Main_Use | Boundary, DEM, geology, occurrence, basemap гэх мэт |
| Confidence | High / Medium / Low / Needs verification |
| Note | Асуудал, тайлбар |

## Алхам 3. QGIS project тохируулах
QGIS дээр шинэ project үүсгээд дараах үндсэн тохиргоог хийнэ:

| Тохиргоо | Утга |
| --- | --- |
| Project CRS | WGS 84 / UTM Zone 47N — EPSG:32647 |
| Distance unit | meters |
| Area unit | square kilometers / hectares |
| Ellipsoid | WGS84 |
| Project name | XV-023222_Buduunkhad_Master_QGIS_Project |
| Save format | .qgz |
| Main database | GeoPackage (.gpkg) |

Анхаарах: Native/raw CRS-г устгахгүй. Эцсийн layer-уудыг EPSG:32647-д хадгалж, эх CRS болон source metadata-г attribute эсвэл QA/QC log-д хадгална.
## Алхам 4. License boundary шалгах ба EPSG:32647 руу хөрвүүлэх
MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz нь L23222 тусгай зөвшөөрлийн хил (WGS84 polygon). QGIS дээр хийх дараалал:
- Layer → Add Layer → Add Vector Layer; KMZ/KML файлыг нээх.
- Layer CRS-г шалгах (ихэвчлэн EPSG:4326 / WGS84).
- Polygon зөв байрлалтай эсэхийг Google/Bing/OSM суурь зурагтай харьцуулах.
- Right click → Export → Save Features As → Format: GeoPackage; CRS: EPSG:32647.
- Layer name: license_boundary_L23222_EPSG32647_v01.
- Үүссэн layer-ийг Master GeoPackage-д хадгалах.

Нэмэх attribute талбарууд:

| Field | Жишээ утга |
| --- | --- |
| license_no | L23222 |
| project | Buduunkhad |
| code | XV-023222 |
| source_file | MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz |
| source_crs | EPSG:4326 |
| final_crs | EPSG:32647 |
| confidence | High |
| note | Original WGS84 KMZ converted to UTM47N |

## Алхам 5. Buffer layer үүсгэх
Phase 3-д CMCS болон региональ контекст шалгахад ашиглах buffer-уудыг Phase 1-д урьдчилан үүсгэнэ (Vector → Geoprocessing Tools → Buffer). Бүгд EPSG:32647-д хадгалагдана.

| Buffer | Ашиглах зорилго | Layer нэр |
| --- | --- | --- |
| 500 м | Remote sensing clip хийхэд | license_buffer_500m_EPSG32647_v01 |
| 1 км | Sentinel, ASTER, KOMPSAT subset хийхэд | license_buffer_1km_EPSG32647_v01 |
| 5 км | Ойролцоох илрэл, хагарал, геологи шалгах | license_buffer_5km_EPSG32647_v01 |
| 10 км | Геохими, шлих, региональ структур шалгах | license_buffer_10km_EPSG32647_v01 |
| 20 км | CMCS, металлогений контекст шалгах | license_buffer_20km_EPSG32647_v01 |

## Алхам 6. Raster CRS / metadata QA/QC (DEM, KOMPSAT, Sentinel, ASTER, basemap)
Raster файл бүрийн CRS, pixel size, band count, extent, NoData-г шалгаж бүртгэнэ. License boundary-тэй давхцаж байгаа эсэх, reproject шаардлагатай эсэхийг тэмдэглэнэ.
- DEM, hillshade, slope raster-уудын CRS, resolution, extent, NoData шалгах.
- KOMPSAT PAN/MS файлуудыг metadata (.txt), RPC (.rpc), ephemeris (.eph)-тэй тулгаж bundle бүрэн эсэхийг шалгах.
- Sentinel-2 (T46 tile — UTM46N байж болзошгүй), ASTER HDF, Google basemap-ийн CRS шалгах.
- EPSG:32647-аас өөр CRS-тэй raster-уудыг Reprojected_EPSG32647 folder-т тэмдэглэх (хөрвүүлэлтийг Phase 2-д гүйцэтгэнэ).
- Scene extent index болон DEM extent index layer үүсгэх.

Анхаар: ASTER HDF (№73) import алдаа гарч болзошгүй — compatibility шалгах. Sentinel болон зарим basemap UTM46N (EPSG:32646)-д ирсэн тул EPSG:32647 руу reproject хийх эсэхийг тэмдэглэнэ.
## Алхам 7. Scan map georeference (тэргүүлэх дараалал)
QGIS Georeferencer ашиглан scan зургуудыг координатад тааруулна. Тэргүүлэх дараалал:

| № | Зураг | Масштаб | Гаралт |
| --- | --- | --- | --- |
| 1 | Detailed geology map (Namalzakh L47-74-A) | 1:50,000 | detailed_geology_50k_georef_EPSG32647_v01.tif |
| 2 | Mineral occurrence / source materials map | 1:50,000 | mineral_occurrence_50k_georef_EPSG32647_v01.tif |
| 3 | Regional geology / stream sediment / heavy mineral | 1:200,000 | regional_geology_200k_georef_EPSG32647_v01.tif |
| 4 | Regional metallogenic map (L47-B Talshand) | 1:500,000 | regional_metallogenic_500k_georef_EPSG32647_v01.tif |

Georeference дараалал:
- Зураг дээрх координатын grid эсвэл танигдах цэгүүдээс GCP (Ground Control Point) сонгох.
- Transformation: эхлээд Polynomial 1, шаардлагатай бол Thin Plate Spline ашиглах.
- Target CRS: EPSG:32647. Output GeoTIFF үүсгэх.
- GCP хүснэгтийг GCP_Tables-д, RMSE/residual тайланг Georeference_Residual_Reports-д хадгалах.
- RMSE өндөр (масштабт тохирохгүй) бол Low_Confidence_Georef-т тэмдэглэж confidence-г бууруулах.

## Алхам 8. Master GIS Database (GeoPackage) угсрах
Шалгагдсан, хөрвүүлэгдсэн бүх layer-ийг нэг GeoPackage-д нэгтгэнэ. Layer group-ийн логик нь Windows folder болон QGIS group-тэй нийцэх ёстой.
05_Master_GIS_Database/
├─ 01_Rasters    (georeferenced scan, DEM, basemap extent index)
├─ 02_Vectors    (license boundary, buffers, occurrence points, anomaly polygons)
├─ 03_Metadata   (source file, CRS, projection date, data source)
└─ 04_QAQC       (CRS check log, overlay screenshots, alignment notes)
Угсрах дараалал:
- Raster layer нэмэх (Layer → Add Raster Layer) — georeferenced scan, DEM деривативын extent.
- Vector / point layer нэмэх (GPKG, CSV, XLSX) — alias, field name тохируулах, editable болгох.
- Шаардлагатай attribute талбарт constraint тавих (Sample ID, Lithology, Mineralization).
- CRS ба alignment шалгах: бүх layer EPSG:32647 эсэх, overlay-аар spatial alignment баталгаажуулах (license boundary + regional map + DEM).
- Layer → Export → Save As → GeoPackage: XV-023222_Buduunkhad_Master_GIS_Database.gpkg.
- Layer group-уудыг Raster / Vector (Points, Polygons, Lines) / QAQC болгон зохион байгуулах.
- Style (.qml) файлуудыг Styles_QML-д хадгалах.
- QGIS project-ийг .qgz форматаар хадгалах; бүх subfolder-ийг backup .zip болгох.

## Алхам 9. QA/QC ба итгэлцлийн зэрэглэл (confidence ranking)
Layer, raster, scan бүрд итгэлцлийн зэрэглэл өгч, data gap register гаргана.

| Зэрэглэл | Тайлбар |
| --- | --- |
| High | Native CRS тодорхой, georeference нарийвчлалтай (бага RMSE), metadata бүрэн. |
| Medium | CRS/metadata шалгагдсан боловч зарим тодруулга шаардлагатай. |
| Low | Georeference хийгдсэн ч RMSE өндөр, эсвэл source баталгаажаагүй scan. |
| Needs verification | Нээгдэхгүй, эсвэл CRS/source тодорхойгүй; нэмэлт шалгалт шаардлагатай. |

QA/QC хийх зүйлс:
- Бүх layer EPSG:32647 эсэхийг шалгах.
- License boundary, regional map, DEM-ийг overlay хийж spatial alignment баталгаажуулах.
- Overlay screenshot болон alignment note-ийг 04_QAQC-д хадгалах.
- QGIS Print Layout ашиглан visual QA/QC report бэлдэх.
- Дутуу өгөгдөл, тулгарсан асуудлыг Data Gap Register-т бүртгэх.

# 5. Ажлын бодит дараалал — эхний 5 өдөр

| Өдөр | Хийх ажил | Гарах үр дүн |
| --- | --- | --- |
| Өдөр 1 | Raw folder хамгаалах, working copy үүсгэх, file inventory эхлүүлэх (нэр, өргөтгөл, хэмжээ, type, sidecar, open status). | Phase1_File_Inventory.xlsx |
| Өдөр 2 | QGIS project (EPSG:32647); license boundary import ба GeoPackage руу хөрвүүлэх; 500м–20км buffer; Master GeoPackage + QGIS project үүсгэх. | Master_GIS_Database.gpkg; Master_QGIS_Project.qgz; boundary + 5 buffer layer |
| Өдөр 3 | DEM, hillshade, slope шалгах; KOMPSAT PAN/MS-ийг metadata/RPC/EPH-тэй тулгах; Sentinel/ASTER/basemap CRS; extent index үүсгэх. | Raster_CRS_QAQC_Log.xlsx; scene & DEM extent index |
| Өдөр 4 | Scan map georeference (1:50k → 1:200k → 1:500k); GCP table, RMSE/residual report; confidence оноох. | Georeferenced .tif-үүд; Georeference_QAQC_Log.xlsx |
| Өдөр 5 | Бүх өгөгдөлд confidence; data gap register; Phase 2-д бэлэн dataset list; desktop study summary; Master GIS index map PDF. | Data_Confidence_Ranking.xlsx; Data_Gap_Register.xlsx; Index_Map.pdf; Desktop_Study_Summary.docx |

# 6. Нэршлийн стандарт
Бүх output layer, raster, Excel, PDF-г нэг стандарт нэршлээр нэрлэнэ:
XV023222_Buduunkhad_<Theme>_<Description>_<Scale_or_Resolution>_<CRS>_v01
Жишээ:
XV023222_Buduunkhad_LicenseBoundary_L23222_EPSG32647_v01
XV023222_Buduunkhad_RegionalGeology_200K_Georef_EPSG32647_v01
XV023222_Buduunkhad_DetailedGeology_50K_Georef_EPSG32647_v01
XV023222_Buduunkhad_MineralOccurrences_Points_EPSG32647_v01
XV023222_Buduunkhad_StreamSediment_AnomalyPolygons_EPSG32647_v01
XV023222_Buduunkhad_ALOS_DEM_12p5m_EPSG32647_v01
XV023222_Buduunkhad_KOMPSAT2_PAN_MetadataCheck_v01

# 7. Folder бүрийн “дууссан” шалгуур

| Folder / сэдэв | Дууссан гэж үзэх нөхцөл |
| --- | --- |
| License boundary | Boundary EPSG:32647 болсон, 5 buffer үүссэн. |
| Regional geology 1:200K | Scan georeference хийгдсэн, confidence өгсөн. |
| Detailed geology 1:50K | Зураг georeference, lithology/fault/contact digitize эхэлсэн. |
| Mineral occurrences | Occurrence хүснэгт GIS point layer болсон. |
| Regional metallogeny 1:500K | Зураг context layer болсон. |
| Geochem / heavy mineral | Stream/heavy mineral map georeference, anomaly polygon эхэлсэн. |
| Metallogeny / prospectivity | Historical prospect polygon digitize болсон. |
| Field observation / routes | Observation point, route line GIS layer болсон. |
| Remote sensing imagery | Raster QA/QC, metadata, CRS status бүртгэгдсэн. |
| DEM / terrain | DEM/hillshade/slope CRS, extent, NoData шалгагдсан. |
| Tectonic / terrane | Terrane context layer, confidence flag бэлэн болсон. |

# 8. Phase 1-ийн эцсийн бүтээгдэхүүн (deliverables)
- XV-023222_Buduunkhad_Master_GIS_Database.gpkg — нэгдсэн GeoPackage.
- XV-023222_Buduunkhad_Master_QGIS_Project.qgz — Master QGIS project.
- XV-023222_Buduunkhad_Phase1_File_Inventory.xlsx — бүх файлын бүртгэл.
- XV-023222_Buduunkhad_CRS_Georeference_QAQC_Log.xlsx — CRS ба georeference QA/QC.
- XV-023222_Buduunkhad_Data_Confidence_Ranking.xlsx — итгэлцлийн зэрэглэл.
- XV-023222_Buduunkhad_Data_Gap_Register.xlsx — дутуу өгөгдлийн бүртгэл.
- XV-023222_Buduunkhad_Phase1_Master_GIS_Index_Map.pdf — индекс зураг.
- XV-023222_Buduunkhad_Phase1_Desktop_Study_Summary.docx — desktop study дүгнэлт.

## Phase 1-ийн логик урсгал
Raw evidence folders
      ↓
Working copy  →  File inventory  →  CRS check  →  Georeference check
      ↓
Master GeoPackage  →  Master QGIS Project  →  Confidence ranking
      ↓
Phase 2 (Remote Sensing)  +  Phase 3 (Geological Synthesis)

Decision gate: Master GIS суурь EPSG:32647-д бүрэн нэгтгэгдэж, бүх өгөгдөл confidence-тэй бүртгэгдэж, QA/QC log бэлэн болсон тохиолдолд Phase 2 руу шилжинэ.
