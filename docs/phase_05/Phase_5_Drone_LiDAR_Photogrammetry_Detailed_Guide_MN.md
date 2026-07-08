<!-- source: Phase_5_Drone_LiDAR_Photogrammetry_Detailed_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

Phase 5 — DJI Matrice 400 Drone LiDAR Photogrammetry Survey
Дэлгэрэнгүй ажлын заавар
Энэ DOCX файл нь энэ чатад өгөгдсөн зураг/даалгавар болон түүнд үндэслэн боловсруулсан Phase 5 ажлын дэлгэрэнгүй зааврыг нэгтгэн багтаав.
# 1. Чатад ирүүлсэн эх зураг

# 2. Эх зураг дахь ажлын товч агуулга

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Priority prospect дээр orthomosaic/LiDAR/terrain/structure field planning base авах. |
| Input files | Phase 4 A/B prospect polygons plus direct planning support raw inputs №8 license boundary, №9–22 DEM/slope/hillshade, №24–46 KOMPSAT basemap/lineament support, №75–78 high-resolution/Sentinel/basemap rasters. Exact filename list is in Section 1A. |
| Software / equipment | 4 x DJI Matrice 400, Zenmuse P1, Zenmuse L2, Zenmuse L3, GNSS/RTK/PPK, processing software. |

# 3. Processing folder structure
05_Phase_5_DJI_Matrice_400_Drone_LiDAR_Photogrammetry_Survey/
├── 01_Flight_Block_Design
├── 02_GCP_Checkpoint_RTK_PPK
├── 03_Zenmuse_P1_Photogrammetry
├── 04_Zenmuse_L2_LiDAR
├── 05_Zenmuse_L3_Detailed_LiDAR
├── 06_Raw_Backup_Flight_Log
├── 07_Processing_Orthomosaic_PointCloud_DTM_DSM
└── 08_Drone_QAQC_Interpretation
# 4. Step-by-step methodology
- 4 ширхэг DJI Matrice 400-r parallel survey team болгон ашиглана: P1 orthomosaic, L2 terrain/structure, L3 detailed LiDAR, 4-р дрон backup/parallel block.
- Flight block design: target boundary + buffer, terrain/slope/access, take-off/landing/emergency area, no-fly/safety restriction.
- GCP/checkpoint, RTK/PPK, overlap, flight altitude, wind/weather/sun angle, battery rotation, raw backup, flight log бүртгэнэ.
- Zenmuse P1: high-resolution orthomosaic, oblique photo, outcrop mapping base.
- Zenmuse L2: DTM/DSM, terrain, drainage, slope, structural lineament.
- Zenmuse L3: detailed LiDAR, micro-topography, fault/contact/vein corridor.
- Output-уудыг field traverse, sample point, trench/drill pad planning-д ашиглана.
# 5. QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| GCP/checkpoint accuracy reviewed | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Flight log complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Overlap/altitude/weather recorded | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Raw photo/LiDAR backed up | Recorded in phase QA/QC log; reviewer/date/decision required. |
| DTM/DSM/orthomosaic checked | Recorded in phase QA/QC log; reviewer/date/decision required. |

# 6. Expected outputs
- XV-023222_Buduunkhad_Drone_Flight_Plan.pdf
- XV-023222_Buduunkhad_Drone_Orthomosaic_P1.tif
- XV-023222_Buduunkhad_Drone_LiDAR_PointCloud.laz
- XV-023222_Buduunkhad_Drone_DTM_DSM.tif
- XV-023222_Buduunkhad_Drone_Structure_Outcrop_Interpretation.gpkg
# 7. Decision gate / next phase condition
- Orthomosaic/LiDAR products meet mapping scale and field planning requirements.

# 8. Phase 5 — дэлгэрэнгүй ажлын заавар
## 8.1 Ажлын зорилго
Энэ ажлаар Buduunkhad талбайн Phase 4 A/B prospect polygon болон тэргүүлэх хайгуулын бүсүүд дээр дроны фотограмметр, LiDAR хэмжилт хийж дараах үндсэн бүтээгдэхүүнийг гаргана.
- Өндөр нарийвчлалтай orthomosaic зураг
- LiDAR point cloud
- DSM — Digital Surface Model
- DTM — Digital Terrain Model
- Налуу, рельеф, fault/contact/vein corridor илрүүлэх terrain base
- Outcrop, structure, access route, sample/trench/drill planning base
- QGIS дээр ашиглах georeferenced raster/vector output
Энэ ажлын үр дүн нь талбайн геологийн зураглалын нарийвчлалыг нэмэгдүүлж, газар дээр очих маршрутыг оновчлох, дээж авах цэг, суваг малталт, өрөмдлөгийн цэгийн төлөвлөлтийг дэмжинэ.
## 8.2 Ашиглах үндсэн input data
### 8.2.1 License boundary
Ашиглах файл: №8 license boundary.
Хэрэглэх зорилго: Тусгай зөвшөөрлийн хил хязгаарыг тодорхойлж, дроны нислэг зөвхөн зөвшөөрөгдсөн талбай дотор эсвэл ажлын төлөвлөгөөнд туссан бүсэд явагдах нөхцөлийг хангана.
- License polygon зөв байрлалтай эсэх
- Coordinate reference system зөв эсэх
- Талбайн хил гадна нислэг хийх эрсдэл байгаа эсэх
- Phase 4 A/B prospect polygon-ууд license boundary дотор байгаа эсэх
### 8.2.2 DEM, slope, hillshade data
Ашиглах файлууд: №9–22 DEM / slope / hillshade.
Хэрэглэх зорилго: Нислэгийн өндөр, рельефийн огцом өөрчлөлт, хөндий, уулын хажуу, өндөрлөг, жалга, cliff/outcrop бүсүүдийг урьдчилан тодорхойлно.
- Хамгийн өндөр болон нам цэг
- Налуу ихтэй бүсүүд
- Дроны холбоо тасрах боломжтой уулын ар, жалга, хөндий
- Нислэгийн өндөр terrain following хийх шаардлагатай эсэх
- Safe take-off / landing point сонгох боломжтой байршил
### 8.2.3 KOMPSAT basemap / lineament / geological interpretation data
Ашиглах файлууд: №24–46 KOMPSAT basemap / lineament support.
Хэрэглэх зорилго: Өмнөх хиймэл дагуулын зураг, lineament, alteration, structure interpretation дээр үндэслэн LiDAR болон photogrammetry survey хийх priority бүсийг тодорхойлно.
- Fault / fracture / lineament corridor
- Alteration zone
- Outcrop exposure
- Drainage-controlled structure
- Өмнөх Phase 4 target polygon-той давхцал
- Geological contact zone
### 8.2.4 Geological map / regional mineral occurrence support
Хэрэв боломжтой бол CMCS / MRPAM эх сурвалжаас тухайн талбай орчмын geological map, mineral occurrence, deposit, showing, old working, geochemical anomaly зэргийг давхарлаж шалгана.
Хэрэглэх зорилго: Дроны нислэгийн priority block-уудыг ойролцоох орд, илрэл, геологийн нэгж, структурын үргэлжлэлтэй уялдуулан эрэмбэлэх.
## 8.3 Ажлын баг ба тоног төхөөрөмж

| Баг | Үүрэг | Ашиглах мэдрэгч |
| --- | --- | --- |
| Team 1 | Orthomosaic / high-resolution photo | Zenmuse P1 |
| Team 2 | Terrain / structure LiDAR | Zenmuse L2 |
| Team 3 | Detailed LiDAR / micro-topography | Zenmuse L3 |
| Team 4 | Backup / parallel block / safety support | P1, L2 эсвэл L3 шаардлагаар |

Үндсэн тоног төхөөрөмж:
- 4 × DJI Matrice 400 drone
- Zenmuse P1 camera
- Zenmuse L2 LiDAR
- Zenmuse L3 LiDAR
- GNSS RTK base / rover
- PPK processing support
- GCP marker
- Checkpoint marker
- Spare batteries
- Charging station
- Field laptop
- External SSD / HDD backup
- Flight planning software
- Photogrammetry processing software
- LiDAR processing software
- QGIS / GIS processing software
- Field QA/QC log sheet
## 8.4 Folder тус бүрийн зориулалт

| Folder | Зориулалт |
| --- | --- |
| 01_Flight_Block_Design | Нислэгийн block design, flight plan, priority area, no-fly/safety restriction map. |
| 02_GCP_Checkpoint_RTK_PPK | GCP, checkpoint, RTK/PPK raw болон processed data. |
| 03_Zenmuse_P1_Photogrammetry | P1 raw photo, oblique photo, metadata, mission folder. |
| 04_Zenmuse_L2_LiDAR | L2 LiDAR raw data, trajectory, IMU/GNSS data. |
| 05_Zenmuse_L3_Detailed_LiDAR | L3 detailed LiDAR survey data. |
| 06_Raw_Backup_Flight_Log | Raw backup, battery log, weather log, flight log. |
| 07_Processing_Orthomosaic_PointCloud_DTM_DSM | Processed final болон intermediate output. |
| 08_Drone_QAQC_Interpretation | QA/QC шалгалт, interpretation, final planning layer. |

## 8.5 Ажлын ерөнхий дараалал
Input data бэлтгэх
→ QGIS дээр flight block design хийх
→ GCP / checkpoint төлөвлөх
→ RTK/PPK base setup хийх
→ Field safety check хийх
→ P1 orthomosaic нислэг хийх
→ L2 terrain / structure LiDAR нислэг хийх
→ L3 detailed LiDAR нислэг хийх
→ Raw data backup хийх
→ Photogrammetry processing хийх
→ LiDAR processing хийх
→ DTM / DSM / orthomosaic гаргах
→ QA/QC шалгах
→ QGIS interpretation хийх
→ дараагийн phase-ийн field planning layer гаргах
## 8.6 Алхам 1. Input data-г QGIS-д бэлтгэх
QGIS дээр шинэ project үүсгэнэ. Санал болгох project CRS: WGS 84 / UTM Zone 47N, EPSG:32647. Хэрэв тухайн талбай өөр zone-д байвал license boundary болон өмнөх бүх raw data-ийн CRS-ийг шалгаж нэг CRS-д нэгтгэнэ.
QGIS-д оруулах layer-ууд:
- License boundary
- Phase 4 A/B prospect polygons
- DEM
- Slope
- Hillshade
- KOMPSAT basemap
- Lineament interpretation
- Geological contact layer
- Alteration layer
- Existing road / access route
- Drainage / stream layer
- Previous sample points
- Mineral occurrence / showing / deposit points
- Proposed traverse / trench / drill planning layer

| Шалгах зүйл | Хүлээн авах нөхцөл |
| --- | --- |
| CRS | Бүх layer нэг CRS-д зөв давхцсан байх |
| Boundary | License polygon зөв байрлалтай байх |
| DEM | NoData, gap, shift байхгүй байх |
| Hillshade | Рельеф зөв харагдах |
| Phase 4 polygon | Target polygon зөв давхцах |
| Access route | Field access боломжтой байх |
| Structure layer | Lineament/target zone-той логик уялдаатай байх |

## 8.7 Алхам 2. Survey priority area тодорхойлох

| Priority | Тайлбар | Нислэгийн шаардлага |
| --- | --- | --- |
| Priority 1 | Phase 4 A/B target, alteration, structure, mineral occurrence давхцсан бүс | P1 + L2 + L3 detailed |
| Priority 2 | Strong lineament/contact zone, outcrop exposure сайтай бүс | P1 + L2 |
| Priority 3 | Access/traverse planning шаардлагатай terrain zone | P1 эсвэл L2 |
| Priority 4 | Background/reference area | Зөвхөн шаардлагатай бол P1 |

QGIS дээр Drone_Survey_Priority_Blocks нэртэй polygon layer үүсгэнэ.

| Field name | Type | Тайлбар |
| --- | --- | --- |
| block_id | Text | Жишээ: DRN-BLK-001 |
| priority | Integer | 1, 2, 3, 4 |
| target_type | Text | Porphyry, epithermal, skarn, vein, structure гэх мэт |
| reason | Text | Яагаад сонгосон үндэслэл |
| sensor | Text | P1, L2, L3 |
| area_ha | Decimal | Талбайн хэмжээ |
| planned_date | Date | Нислэгийн төлөвлөсөн огноо |
| status | Text | planned / flown / processed / checked |

## 8.8 Алхам 3. Flight block design хийх
- Нэг block нь нэг дроны нэг mission-д багтах хэмжээтэй байх
- Battery хүрэлцэхүйц байх
- Terrain огцом өөрчлөгдвөл block-ийг жижиглэх
- Нэг block дотор flight altitude хэт их өөрчлөгдөхгүй байх
- Adjacent block хооронд overlap үлдээх
- Priority 1 block-ийг хамгийн түрүүнд нисгэх
### 8.8.1 P1 photogrammetry flight parameter

| Parameter | Санал болгох утга |
| --- | --- |
| Flight type | Grid / double grid |
| Front overlap | 80–85% |
| Side overlap | 70–80% |
| Oblique photo | Outcrop/structure zone дээр авах |
| GSD | Төслийн шаардлагаас хамааран 2–5 cm/pixel |
| Flight altitude | Terrain болон GSD-ээс хамаарна |
| Speed | Зураг blur үүсгэхгүй хэмжээнд |
| Camera mode | Manual эсвэл fixed exposure |
| White balance | Fixed |
| RTK/PPK | Асаалттай |

Өндөр уул, огцом налуу, жалга бүхий талбайд terrain follow ашиглах шаардлагатай.
### 8.8.2 L2 LiDAR flight parameter

| Parameter | Санал болгох утга |
| --- | --- |
| Flight type | Parallel line / corridor / block |
| Strip overlap | 30–50% буюу түүнээс дээш |
| Flight altitude | Terrain complexity-ээс хамаарна |
| Scan mode | Repetitive / non-repetitive шаардлагаар |
| Return mode | Multiple return боломжтой бол ашиглах |
| GNSS/IMU | RTK/PPK заавал |
| Calibration line | Mission эхэнд болон төгсгөлд хийх |

### 8.8.3 L3 detailed LiDAR flight parameter
Zenmuse L3-ийг fault corridor, contact zone, quartz vein corridor, outcrop-rich ridge, proposed trench line, proposed drill pad area, small-scale micro-topography шаардлагатай бүсэд ашиглана.

| Parameter | Санал болгох утга |
| --- | --- |
| Flight type | Detailed block / corridor |
| Overlap | Өндөр overlap |
| Altitude | Бага өндөр, өндөр нарийвчлал |
| Speed | Удаан, тогтвортой |
| GNSS/IMU | RTK/PPK заавал |
| Output focus | Micro-topography / structure / access planning |

## 8.9 Алхам 4. GCP болон checkpoint төлөвлөх
GCP нь orthomosaic болон LiDAR product-ийн байрлалын нарийвчлалыг баталгаажуулахад ашиглагдана.
- Нислэгийн block-ийн булан бүрт
- Block-ийн төв хэсэгт
- Өндөрлөг болон нам хэсэгт аль алинд нь
- Terrain огцом өөрчлөгдөх бүсэд
- Нислэгийн block хоорондын давхцлын бүсэд
- Зам, талбай, ил харагдах тогтвортой гадарга дээр
- Ус, хөдөлгөөнт хөрс, сул хайрга, сүүдэртэй газар тавихгүй
Checkpoint нь processing-д ашиглахгүй, зөвхөн accuracy шалгахад ашиглана. Жишээ харьцаа: GCP 70%, Checkpoint 30%.

| Field | Тайлбар |
| --- | --- |
| point_id | GCP-001, GCP-002 гэх мэт |
| type | GCP эсвэл Checkpoint |
| easting | UTM X |
| northing | UTM Y |
| elevation | Z |
| CRS | EPSG:32647 |
| measured_by | Хэмжсэн хүн |
| instrument | RTK / PPK / GNSS |
| date_time | Хэмжсэн огноо, цаг |
| photo_id | Талбайн зураг |
| description | Газрын нөхцөл |
| quality | good / moderate / poor |

## 8.10 Алхам 5. Field safety болон flight readiness check
Нислэг бүрийн өмнө weather check, drone pre-flight check, mission check, RTK/PPK status check болон safety briefing заавал хийнэ.

| Шалгах зүйл | Тайлбар |
| --- | --- |
| Weather | Салхи, бороо/цас, манан, үүлшил, нарны өнцөг, температур, тоосжилт, үзэгдэх орчин |
| Propeller | Гэмтэл, сулрал байхгүй |
| Battery | Цэнэг, температур хэвийн |
| Sensor | P1/L2/L3 зөв суусан |
| Gimbal | Түгжээ, calibration хэвийн |
| SD/SSD | Хоосон зай хангалттай |
| RTK | Fix авсан эсэх |
| Compass/IMU | Calibration болон ажиллагаа хэвийн эсэх |
| Mission file | Зөв block сонгосон эсэх |
| RTH altitude | Terrain-ээс өндөр, аюулгүй эсэх |
| Take-off point | Саадгүй, тэгш, аюулгүй эсэх |

## 8.11 Алхам 6. Нислэг гүйцэтгэх
- Take-off / landing point-ийг газар дээр баталгаажуулна.
- Weather log бөглөнө.
- Battery log бөглөнө.
- RTK/PPK status шалгана.
- Mission file зөв эсэхийг шалгана.
- Drone home point зөв орсон эсэхийг шалгана.
- Observer болон pilot хооронд radio/phone холбоо шалгана.
- Нислэгийг эхлүүлнэ.
- Нислэгийн явцад drone altitude, battery, GNSS, wind warning, image capture / LiDAR recording status-г хянана.
- Нислэг дууссаны дараа data recording бүрэн хадгалагдсан эсэхийг шалгана.

| Drone | Үүрэг | Тайлбар |
| --- | --- | --- |
| Drone 1 | P1 orthomosaic | Priority block-уудын image base |
| Drone 2 | L2 LiDAR | Terrain / structure base |
| Drone 3 | L3 detailed LiDAR | Нарийвчилсан fault/contact/outcrop zone |
| Drone 4 | Backup / second block | Battery rotation, нөхөх нислэг, emergency support |


| Flight log field | Тайлбар |
| --- | --- |
| mission_id | DRN-P1-001 гэх мэт |
| block_id | DRN-BLK-001 |
| drone_id | Drone serial / team |
| sensor | P1 / L2 / L3 |
| pilot | Нисгэгч |
| observer | Ажиглагч |
| start_time | Эхэлсэн цаг |
| end_time | Дууссан цаг |
| battery_id | Battery дугаар |
| weather | Салхи, үүлшил, температур |
| RTK_status | Fixed / Float / None |
| overlap | Төлөвлөсөн overlap |
| altitude | Нислэгийн өндөр |
| issue | Асуудал гарсан эсэх |
| data_status | complete / incomplete / repeat required |

## 8.12 Алхам 7. Raw data backup хийх
Нислэг бүрийн дараа raw data-г шууд backup хийнэ. 1 дэх хувь: Field laptop; 2 дахь хувь: External SSD; 3 дахь хувь: Office / cloud backup боломжтой бол.
2026-06-05_DRN-BLK-001_P1_Mission001_Raw/
2026-06-05_DRN-BLK-001_L2_Mission001_Raw/
2026-06-05_DRN-BLK-002_L3_Mission001_Raw/
- Файлын тоо raw SD card болон backup folder дээр ижил эсэх
- Файлын хэмжээ 0 KB биш эсэх
- Metadata файл хамт хуулсан эсэх
- LiDAR trajectory / GNSS / IMU файл хамт байгаа эсэх
- Flight log mission ID-тэй folder нэр таарч байгаа эсэх
## 8.13 Алхам 8. Photogrammetry processing хийх
Zenmuse P1 raw photo-г ашиглан orthomosaic боловсруулна.
Оруулах data: P1 raw photos, photo metadata, RTK/PPK trajectory, GCP coordinates, checkpoint coordinates, camera calibration data, flight log.
- Project үүсгэх
- Raw photos import хийх
- Coordinate system тохируулах
- Camera position import хийх
- Photo alignment хийх
- Tie point үүсгэх
- GCP marker оруулах
- GCP adjustment хийх
- Checkpoint residual шалгах
- Dense point cloud үүсгэх
- DSM үүсгэх
- Orthomosaic үүсгэх
- Export GeoTIFF хийх
- Processing report гаргах

| QA/QC item | Хүлээн авах нөхцөл |
| --- | --- |
| Coverage | Нислэгийн block бүрэн бүрхсэн |
| Blur | Зураг сарниагүй |
| Seamline | Хэт эвдрэлгүй |
| Shadow | Геологийн тайлбар хийхэд саад болохгүй |
| GCP residual | Төслийн шаардлагад нийцсэн |
| Checkpoint error | Хүлээн зөвшөөрөх хэмжээнд |
| CRS | EPSG:32647 эсвэл төслийн CRS зөв |
| Pixel size | Төлөвлөсөн GSD-тэй нийцсэн |

## 8.14 Алхам 9. LiDAR processing хийх
L2 болон L3 LiDAR data-г боловсруулж point cloud, DTM, DSM гаргана.
Оруулах data: Raw LiDAR scan, trajectory data, GNSS/IMU data, RTK/PPK correction, GCP/checkpoint, flight log, calibration line data.
- Raw LiDAR mission import хийх
- Trajectory processing хийх
- RTK/PPK correction хийх
- Strip alignment хийх
- Point cloud үүсгэх
- Noise removal хийх
- Ground classification хийх
- Non-ground classification хийх
- LAS/LAZ export хийх
- DTM үүсгэх
- DSM үүсгэх
- Slope / hillshade derivative гаргах
- Checkpoint accuracy шалгах
- Processing report гаргах

| Class | Тайлбар |
| --- | --- |
| Ground | Газрын гадарга |
| Low vegetation | Нам ургамал |
| Medium vegetation | Дунд ургамал |
| High vegetation | Өндөр ургамал |
| Rock outcrop | Ил гарсан чулуулгийн гадарга, боломжтой бол |
| Noise | Алдаатай цэг |
| Water / shadow gap | Мэдээлэл муутай бүс |

## 8.15 Алхам 10. DTM, DSM, slope, hillshade гаргах
DTM нь vegetation, object-ийг хассан газрын гадаргын загвар. DSM нь газрын гадарга дээрх бүх объектыг багтаасан surface model. Slope map-аар огцом налуу, боломжит fault scarp, trench хийхэд хүндрэлтэй бүс, машин техник очих боломжгүй бүс, unstable slope эрсдэлийг үнэлнэ. Hillshade-г structure interpretation-д ашиглана.
- Fault scarp
- Drainage pattern
- Ridge / valley morphology
- Trench planning
- Drill pad planning
- Access road planning
- Linear ridge
- Straight valley
- Offset drainage
- Fault-controlled escarpment
- Vein ridge
- Lithological contact morphology
## 8.16 Алхам 11. QGIS дээр interpretation хийх
Боловсруулсан orthomosaic, DTM, DSM, slope, hillshade-г QGIS-д оруулж геологийн тайлбар хийнэ.
Drone_Interpreted_Lineaments
Drone_Interpreted_Faults
Drone_Interpreted_Contacts
Drone_Interpreted_Outcrops
Drone_Interpreted_Vein_Corridors
Drone_Field_Traverse_Planning
Drone_Sample_Point_Planning
Drone_Trench_Planning
Drone_Drill_Pad_Planning
Lineament interpretation хийхдээ шулуун хөндий, шулуун жалга, ridge alignment, drainage offset, slope break, өнгөний огцом өөрчлөлт, ургамлын шугаман ялгаа, outcrop alignment, quartz vein ridge, structural corridor зэрэг шинжүүдийг ашиглана.
Outcrop interpretation хийхдээ ил гарсан чулуулгийн өнгө, барзгар гадарга, ургамал багатай хэсэг, ridge crest exposure, slope shoulder exposure, drainage incision дээр илэрсэн чулуулаг, хүдрийн бүс байж болох өнгөний өөрчлөлтийг харгалзана.
Vein / alteration corridor ялгахдаа цайвар linear feature, quartz ridge, iron oxide stain, yellow/red/brown alteration tone, fault-contact дагасан өнгөний ялгаа, stream sediment anomaly-той давхцах байдал, өмнөх sample point-той ойр байх зэргийг ашиглана.
## 8.17 Алхам 12. Field traverse, sample, trench, drill planning хийх
Drone interpretation дээр үндэслэн дараагийн талбайн ажлын төлөвлөгөөг гаргана.

| Planning type | Үндсэн шалгуур |
| --- | --- |
| Traverse planning | Priority target, access route, slope safety, outcrop exposure, structure crossing, drainage crossing, sample logistics, vehicle/walking route |
| Sample point planning | Fault/contact intersection, quartz vein exposure, alteration zone, iron oxide stained outcrop, lineament corridor, lithological boundary, stream sediment anomaly, historical mineral occurrence, Phase 4 A/B prospect |
| Trench planning | Target structure-ийг хөндлөн огтлох, налуу хэт огцом биш, техник орох боломжтой, ус/жалга/protected area-аас зайлсхийх, contact/vein/alteration zone-г огтлох, нөхөн сэргээлт хийх боломжтой |
| Drill pad planning | Topography тэгш эсвэл засах боломжтой, target-тэй геометрийн хувьд зөв, access ойр, water/logistics боломжтой, license boundary дотор, environmental restriction-ээс гадуур |

## 8.18 QA/QC шалгалт

| QA/QC item | Шалгах зүйл | Шийдвэр |
| --- | --- | --- |
| GCP/checkpoint accuracy | RTK/PPK coordinate зөв эсэх | accept / remeasure |
| Flight coverage | Block бүрэн ниссэн эсэх | accept / reflown |
| Overlap | Front/side overlap хангалттай эсэх | accept / repeat |
| Weather | Нислэгт нөлөөлсөн эсэх | accept / note / repeat |
| Raw data backup | Давхар backup бүрэн эсэх | accept / backup again |
| Flight log | Бүрэн бөглөгдсөн эсэх | accept / correct |


| Processing QA/QC item | Шалгах зүйл | Хүлээн авах нөхцөл |
| --- | --- | --- |
| Orthomosaic | Shift, blur, gap, seamline | Том алдаа байхгүй |
| Point cloud | Density, strip mismatch, noise | Хүлээн зөвшөөрөх хэмжээнд |
| DTM | Ground classification зөв эсэх | Terrain үнэн зөв |
| DSM | Surface continuity | Gap бага |
| CRS | Coordinate system зөв эсэх | Project CRS-тэй нийцсэн |
| Checkpoint error | Accuracy | Төслийн шаардлага хангасан |
| Metadata | Processing report complete | Бүрэн байх |

## 8.19 Expected outputs
XV-023222_Buduunkhad_Drone_Flight_Plan.pdf
XV-023222_Buduunkhad_Drone_Orthomosaic_P1.tif
XV-023222_Buduunkhad_Drone_LiDAR_PointCloud.laz
XV-023222_Buduunkhad_Drone_DTM_DSM.tif
XV-023222_Buduunkhad_Drone_Structure_Outcrop_Interpretation.gpkg

Нэмэлтээр:
XV-023222_Buduunkhad_Drone_Slope.tif
XV-023222_Buduunkhad_Drone_Hillshade.tif
XV-023222_Buduunkhad_Drone_GCP_Checkpoint_Register.xlsx
XV-023222_Buduunkhad_Drone_Flight_Log_Master.xlsx
XV-023222_Buduunkhad_Drone_QAQC_Report.docx
XV-023222_Buduunkhad_Drone_Field_Planning_Map.pdf
XV-023222_Buduunkhad_Drone_Trench_Drill_Planning.gpkg
## 8.20 Decision gate / дараагийн phase рүү шилжих нөхцөл

| Шалгуур | Нөхцөл |
| --- | --- |
| Orthomosaic | Бүх priority block бүрэн бүрхсэн |
| LiDAR point cloud | Нягтрал, coverage хангалттай |
| DTM/DSM | Геологийн болон terrain planning-д ашиглах боломжтой |
| QA/QC | GCP/checkpoint, overlap, processing report бүрэн |
| Interpretation | Fault, contact, outcrop, vein corridor layer үүссэн |
| Field planning | Traverse, sample, trench/drill planning layer гарсан |
| Backup | Raw болон processed data давхар хадгалагдсан |

## 8.21 Талбай дээр өдөр тутам мөрдөх богино checklist
### Өглөө
- Weather шалгасан
- Drone battery бүрэн
- Sensor зөв суусан
- RTK/PPK ажиллаж байгаа
- Mission file зөв
- GCP/checkpoint төлөвлөгөө бэлэн
- Take-off point шалгасан
- Safety briefing хийсэн
### Нислэгийн үеэр
- Battery status хянасан
- RTK status хянасан
- Sensor recording хянасан
- Wind warning хянасан
- Mission coverage хянасан
- Асуудал гарвал flight log-д тэмдэглэсэн
### Нислэгийн дараа
- Raw data хуулсан
- Backup 2 хувь хийсэн
- Flight log бөглөсөн
- Battery log бөглөсөн
- Weather log бөглөсөн
- Data completeness шалгасан
- Repeat flight шаардлагатай эсэхийг шийдсэн
## 8.22 Хүлээлгэн өгөх final package
Final_Deliverables/
├── 01_Flight_Plan/
│   └── XV-023222_Buduunkhad_Drone_Flight_Plan.pdf
├── 02_Orthomosaic/
│   └── XV-023222_Buduunkhad_Drone_Orthomosaic_P1.tif
├── 03_LiDAR_PointCloud/
│   └── XV-023222_Buduunkhad_Drone_LiDAR_PointCloud.laz
├── 04_DTM_DSM/
│   ├── XV-023222_Buduunkhad_Drone_DTM.tif
│   ├── XV-023222_Buduunkhad_Drone_DSM.tif
│   ├── XV-023222_Buduunkhad_Drone_Slope.tif
│   └── XV-023222_Buduunkhad_Drone_Hillshade.tif
├── 05_GIS_Interpretation/
│   └── XV-023222_Buduunkhad_Drone_Structure_Outcrop_Interpretation.gpkg
├── 06_QAQC/
│   ├── XV-023222_Buduunkhad_Drone_QAQC_Log.xlsx
│   └── XV-023222_Buduunkhad_Drone_Processing_Report.pdf
└── 07_Field_Planning/
    ├── XV-023222_Buduunkhad_Drone_Field_Planning_Map.pdf
    └── XV-023222_Buduunkhad_Drone_Sample_Trench_Drill_Planning.gpkg
# 9. Нэг өгүүлбэрээр дүгнэлт
Энэ Phase 5 ажил нь дроны өндөр нарийвчлалтай зураглал ба LiDAR data ашиглан Phase 4 target-уудыг газар дээр шалгах, сорьцлолт хийх, trench болон drill planning хийхэд зориулсан нарийвчилсан topographic–structural base map бэлтгэх үе шат юм.
