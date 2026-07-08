<!-- source: Matrice400_ZenmuseL3_Universal_Flight_Planning_Template.docx (converted from Word; canonical form for LLM ingestion) -->

DJI MATRICE 400 + ZENMUSE L3 LiDAR
НИСЛЭГ ТӨЛӨВЛӨХ УНИВЕРСАЛ АЖЛЫН АРГАЧЛАЛ / TEMPLATE
Ямар ч га хэмжээтэй хайгуул, уул уурхай, геодези, топографийн талбайд тохируулан ашиглах загвар

| Мэдээлэл | Нөхөх утга |
| --- | --- |
| Баримтын төрөл | Ажлын аргачлалын template |
| Төсөл / талбай | [[PROJECT_NAME]] / [[FIELD_NAME]] |
| Лиценз / талбайн дугаар | [[LICENSE_NO]] |
| Талбайн хэмжээ | [[AREA_HA]] га = [[AREA_KM2]] км² |
| Байршил | [[AIMAG_SUM_LOCATION]] |
| Тоног төхөөрөмж | DJI Matrice 400, Zenmuse L3, D-RTK 3, eSurvey E600 GNSS |
| Зориулалт | LiDAR point cloud, RGB orthophoto, DEM/DTM/DSM, hillshade, slope, contour, геологийн тайлал |
| Бэлтгэсэн огноо | [[YYYY-MM-DD]] |


| Template ашиглах заавар [[...]] тэмдэглэгээтэй бүх хэсгийг тухайн талбайн бодит мэдээллээр сольж бөглөнө. Хүснэгт дэх параметрүүд нь эхний санал бөгөөд DJI Pilot 2 дээр mission preview, battery estimate, terrain, салхи, RTK нөхцөлөөр талбай дээр баталгаажуулна. |
| --- |

# 1. Ажлын зорилго ба хэрэглэх хүрээ
Энэхүү template нь DJI Matrice 400 дрон болон DJI Zenmuse L3 LiDAR камер ашиглан ямар ч хэмжээтэй талбайд LiDAR болон RGB зураглалын нислэгийг төлөвлөх, гүйцэтгэх, QC хийх, дата архивлах нэгдсэн аргачлал юм.
- Лиценз, хайгуулын талбай, уурхайн талбай, карьер, зам/коридор, prospect хэсэгт тохируулан ашиглаж болно.
- Талбайн хэмжээ [[AREA_HA]] га-аас үл хамааран block size болон mission тоог доорх томъёогоор тооцно.
- Үндсэн бүтээгдэхүүн: LAS/LAZ point cloud, classified point cloud, DSM, DTM, DEM, RGB orthophoto, hillshade, slope, contour, QA/QC report.
# 2. Төслийн үндсэн мэдээлэл бөглөх маягт

| Үзүүлэлт | Нөхөх утга |
| --- | --- |
| Төсөл / талбайн нэр | [[PROJECT_NAME]] |
| Лиценз / талбайн дугаар | [[LICENSE_NO]] |
| Талбайн хэмжээ, га | [[AREA_HA]] |
| Талбайн хэмжээ, км² | [[AREA_HA]] / 100 = [[AREA_KM2]] |
| Талбайн урт тэнхлэгийн чиглэл | [[LONG_AXIS_BEARING]] градус |
| Дундаж/их налуу | [[MEAN_SLOPE_DEG]] / [[MAX_SLOPE_DEG]] |
| Рельефийн үнэлгээ | Тэгш / дунд зэргийн / огцом / уул-жалга ихтэй |
| GNSS тулгуур цэг | [[CONTROL_POINTS]] |
| Base station төрөл | D-RTK 3 / NTRIP / CORS / local GNSS base |

# 3. Оролтын өгөгдөл бэлтгэх

| Өгөгдөл | Формат | Ашиглалт |
| --- | --- | --- |
| Лиценз / талбайн хил | KMZ/KML/SHP/DWG | Boundary үүсгэх, buffer гаргах |
| DEM / DSM | GeoTIFF / raster | Terrain Follow, өндөр зөрүү, саад шалгах |
| Hillshade / slope | GeoTIFF | Рельеф, жалга, хяр, огцом налуу үнэлэх |
| Өмнөх зураглал | Sentinel/ALOS/ортозураг | Prospect, lithology, access planning |
| Геодезийн цэгүүд | CSV/SHP/KML/RINEX | RTK/PPK тулгуур, checkpoint |
| Зам, суурин, шугам сүлжээ | SHP/DWG/KML | Аюулгүй ажиллагаа, launch point сонгох |


| CRS шалгах дүрэм KMZ/KML нь ихэвчлэн WGS84 EPSG:4326 байна. Боловсруулалт болон талбайн хэмжилтэд тухайн longitude-д тохирох UTM zone-ийг сонгоно. Бүх raster/vector давхаргыг QGIS дээр давхардуулж, байршлын зөрүүгүй эсэхийг шалгасны дараа DJI Pilot 2-д импортолно. |
| --- |

# 4. Талбайн хэмжээгээр block болон mission тооцох арга
Талбайн хэмжээ ямар ч байсан нислэгийг нэг mission-д багтаах гэж оролдохгүй. Нэг block нь battery reserve, RTK холбоо, terrain-following, turn distance, дата хэмжээ, processing ачааллыг тооцсон практик хэмжээтэй байна.

| Алхам | Тооцоо | Томъёо / тайлбар |
| --- | --- | --- |
| 1 | Талбайг км² болгох | AREA_KM2 = AREA_HA / 100 |
| 2 | Нэг block-ийн зорилтот хэмжээг сонгох | TARGET_BLOCK_HA = доорх хүснэгтээс сонгоно |
| 3 | Эхний block тоо | BLOCK_COUNT = CEILING(AREA_HA / TARGET_BLOCK_HA) |
| 4 | Terrain correction | Рельеф огцом бол block_count +10–30% нэмэгдүүлнэ |
| 5 | Mission count | Block бүрийн Pilot 2 battery estimate-г шалгаж, нэг block олон mission байж болно |


| Ажлын төрөл | Өндөр AGL | Хурд | Front/Side overlap | Зорилтот block хэмжээ | Ашиглах нөхцөл |
| --- | --- | --- | --- | --- | --- |
| Том талбайн хурдан бүрхэлт | 300–500 м | 10–15 м/с | 60–70 / 30–40 | 800–1,200 га/block | Ерөнхий DEM/DSM, эхний шат |
| Ерөнхий хайгуулын production | 250–300 м | 8–12 м/с, нөхцөл сайн бол 15 м/с | 70 / 40–50 | 500–800 га/block | LiDAR + RGB + DTM/DSM |
| Нарийвчилсан prospect | 120–200 м | 6–8 м/с | 80 / 60 | 100–300 га/block | Хагарал, судал, ил гарц |
| Маш нарийвчилсан геодези | 80–150 м | 5–8 м/с | 80 / 60–70 | 50–150 га/block | Өндөр нарийвчлалтай хэсэг |

# 5. Buffer ба block overlap сонгох арга

| Төрөл | Minimum | Recommended | Тайлбар |
| --- | --- | --- | --- |
| Ерөнхий boundary buffer | 100 м | 150 м | Лицензийн хил дээр дата тасрахгүй байх |
| Огцом рельеф, жалга, хадан гарц | 150 м | 200 м | Scan edge, terrain-following алдааны нөөц |
| Block-to-block overlap | 100 м | 150–200 м | Strip alignment, block merge, QC |
| Prospect detail block overlap | 150 м | 200 м+ | Нарийвчилсан хэсгийн захын чанар хамгаалах |

# 6. Нислэгийн чиглэл сонгох арга
- Урт нарийн талбайд flight line-ийг талбайн урт тэнхлэгтэй параллель тавина.
- Block бүрийн урт тэнхлэгийн bearing-ийг QGIS/AutoCAD дээр тодорхойлж [[HEADING_DEG]] гэж оруулна.
- Эргэлтийн тоо их байвал heading-ийг 90° эргүүлж battery estimate-ийг дахин шалгана.
- Жалга, нуруу, геологийн структур тодорхой чиглэлтэй бол үндсэн чиглэлтэй ойролцоо эсвэл cross-line нэмнэ.
# 7. Flight parameter сонгох decision matrix

| Ажил | Өндөр | Хурд | Overlap | Scan mode | Pulse rate | Returns | Тайлбар |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage 1: нийт талбай | 250–300 м | 8–12 м/с; сайн нөхцөлд 15 м/с | 70/40–50 | Non-Repetitive | 350 kHz | 8 | RGB ON, RTK FIX |
| Stage 2: prospect | 150–200 м | 6–8 м/с | 80/60 | Star-Shaped | 350 kHz эсвэл тохиромжтой preset | 8–16 | Cross-line заавал |
| Stage 3: маш нарийвчилсан | 80–150 м | 5–8 м/с | 80/60–70 | Star-Shaped | terrain/чанараас хамаарна | 8–16 | GCP/checkpoint нягт |
| Coverage priority | 300–500 м | 10–15 м/с | 60–70/30–40 | Non-Repetitive | 100/350 kHz нөхцөлөөс хамаарна | 4–8 | Рельеф тогтвортой үед |

# 8. Terrain Follow ашиглах шалгуур

| Рельефийн нөхцөл | Terrain Follow | Заавар |
| --- | --- | --- |
| Тэгш, өндөр зөрүү бага | Optional | AGL тогтвортой бол шаардлагагүй байж болно |
| Өндөр зөрүү 50 м-ээс дээш | Ашиглана | DEM чанар шалгаж, safe altitude тохируулна |
| Уул, жалга, огцом налуу | Заавал | 3D preview хийж мөргөх эрсдэл шалгана |
| DEM чанар муу, no-data их | Болгоомжтой | DEM засварлаж эсвэл conservative өндөр сонгоно |

# 9. RTK / PPK / GNSS аргачлал
- Ойролцоох баталгаатай хатуу цэгүүдийг [[CONTROL_POINTS]] гэж тодорхойлно.
- eSurvey E600 GNSS ашиглан base point, checkpoint, шаардлагатай бол GCP хэмжинэ.
- D-RTK 3-ийг тэнгэр нээлттэй, металл/машин/цахилгаан шугамаас хол байрлуулна.
- Нислэг эхлэхээс өмнө RTK FIX, antenna height, base coordinate, GNSS raw logging-ийг шалгана.
- Survey-grade ажилд D-RTK 3 raw data, drone GNSS/IMU/LiDAR raw data, eSurvey RINEX, CORS/MONPOS RINEX backup хадгална.
# 10. Газрын хяналтын цэгийн тоо ба байрлал

| Талбайн хэмжээ | Check point санал | Байрлуулах зарчим |
| --- | --- | --- |
| 1 км² хүртэл | 5–8 | 4 булан + төв + өндөр/нам дор хэсэг |
| 1–5 км² | 8–15 | Ирмэг, төв, рельефийн өөрчлөлтөөр тараана |
| 5–10 км² | 15–25 | Block залгаа хэсэгт заавал байрлуулна |
| 10 км² дээш | Block бүрт 5-аас доошгүй | Нийт талбайд жигд тархалттай, overlap хэсгүүдийг хамруулна |

# 11. DJI Pilot 2 mission үүсгэх дараалал
- QGIS/AutoCAD дээр boundary, buffer, block overlap-ийг баталгаажуулна.
- Block бүрийг KMZ/KML/SHP хэлбэрээр экспортлоно.
- DJI Pilot 2 → LiDAR Mapping mission үүсгэнэ.
- Boundary импортлоод altitude, speed, overlap, heading, scan mode, returns, RGB тохируулна.
- Terrain Follow хэрэгтэй бол DEM/terrain data оруулж 3D preview шалгана.
- Mission preview дээр turn distance, line direction, battery estimate, RTH altitude шалгана.
- Battery reserve 20–25%-иас бага үлдэхээр байвал block-ийг жижигрүүлнэ.
- Mission нэрийг стандарт форматаар хадгална.
# 12. Нэршил ба folder structure
Mission болон raw data folder-ийг бүх төсөлд нэг форматаар нэрлэнэ.

| Төрөл | Формат / тайлбар |
| --- | --- |
| Folder format | YYYYMMDD_DRN-[[DRONE_CODE]]_BLK-001_L3_M001_Raw |
| Жишээ | 20260610_DRN-M400_BLK-001_L3_M001_Raw |
| BLK-001 | Block дугаар |
| M001 | Тухайн block-ийн mission/flight дугаар |

[[PROJECT_NAME]]_L3_Mapping/
├── 00_Admin/
├── 01_Input_Data/
│   ├── Boundary_KMZ_SHP_DWG/
│   ├── DEM_Hillshade_Slope/
│   └── Previous_Exploration_Data/
├── 02_Flight_Planning/
│   ├── QGIS_Project/
│   ├── AutoCAD_DWG/
│   ├── DJI_Pilot2_Missions/
│   └── Block_Boundaries/
├── 03_Raw_Data/
│   ├── L3_Raw/
│   ├── RGB_Raw/
│   ├── GNSS_IMU_Raw/
│   └── Flight_Logs/
├── 04_GNSS_RTK_PPK/
├── 05_DJI_Terra_Processing/
├── 06_Outputs/
│   ├── LAS_LAZ/
│   ├── Classified_PointCloud/
│   ├── DSM_DTM_DEM/
│   ├── Orthophoto/
│   ├── Hillshade_Slope_Contour/
│   └── GIS_Interpretation/
└── 07_QA_QC_Report/

## 13. Нислэгийн өмнөх checklist

| № | ✓ | Шалгах зүйл | Тайлбар |
| --- | --- | --- | --- |
| 1 | ☐ | Boundary зөв, buffer орсон, block overlap хангалттай эсэх |  |
| 2 | ☐ | CRS / UTM zone / өндрийн систем зөв эсэх |  |
| 3 | ☐ | DEM/Terrain Follow data no-data, spike, shift алдаагүй эсэх |  |
| 4 | ☐ | Launch point болон emergency landing area аюулгүй эсэх |  |
| 5 | ☐ | RTH altitude рельеф, саадаас хангалттай өндөр эсэх |  |
| 6 | ☐ | D-RTK 3 base coordinate, antenna height зөв эсэх |  |
| 7 | ☐ | RTK FIX, satellite тоо, GNSS signal тогтвортой эсэх |  |
| 8 | ☐ | L3 sensor, gimbal, IMU status хэвийн эсэх |  |
| 9 | ☐ | CFexpress card сул зай хангалттай эсэх |  |
| 10 | ☐ | Battery set, propeller, firmware, weather, wind шалгасан эсэх |  |

## 14. Нислэгийн явцын checklist

| № | ✓ | Шалгах зүйл | Тайлбар |
| --- | --- | --- | --- |
| 1 | ☐ | Mission нэр, block дугаар, parameter зөв эсэхийг баталгаажуулах |  |
| 2 | ☐ | RTK FIX тасалдахгүй байгаа эсэхийг хянах |  |
| 3 | ☐ | LiDAR recording болон RGB capture идэвхтэй эсэхийг шалгах |  |
| 4 | ☐ | Battery reserve 20–25%-иас доош оруулахгүй байх |  |
| 5 | ☐ | Салхи, dust, bird, vehicle, хүн/малын хөдөлгөөнд хяналт тавих |  |
| 6 | ☐ | Mission дууссаны дараа raw data бүрэн бичигдсэн эсэхийг шалгах |  |

# 15. Field log маягт

| Огноо | Block | Mission | Sensor | Өндөр | Хурд | Overlap | RTK | Battery | Тайлбар |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [[YYYYMMDD]] | BLK-001 | M001 | L3 | [[ALT]] м | [[SPEED]] м/с | [[70/50]] | FIX | B01/B02 | Хэвийн |
| [[YYYYMMDD]] | BLK-001 | M002 | L3 | [[ALT]] м | [[SPEED]] м/с | [[70/50]] | FIX/FLOAT | B03/B04 | Тайлбар |
| [[YYYYMMDD]] | BLK-002 | M001 | L3 | [[ALT]] м | [[SPEED]] м/с | [[70/50]] | FIX | B05/B06 | Terrain follow |

# 16. Боловсруулалтын дараах QA/QC

| QC үзүүлэлт | Шалгах зүйл |
| --- | --- |
| Trajectory quality | RTK/PPK тасарсан эсэх, GNSS/IMU continuity |
| Coverage check | Boundary + buffer бүрэн бүрхэгдсэн эсэх, gap байгаа эсэх |
| Strip alignment | Зэрэгцээ flight line хооронд өндөр/хэвтээ зөрүү |
| Cross-line error | Перпендикуляр cross-line дээрх зөрүү |
| Point density | Талбайн бүх хэсэгт хангалттай нягт эсэх |
| Ground classification | Ground/non-ground ялгалт зөв эсэх |
| Checkpoint accuracy | ΔX, ΔY, ΔZ, horizontal/vertical RMSE |
| Orthophoto QC | Blur, seamline, gap, distortion |
| DTM/DSM QC | Spike, hole, no-data, block edge mismatch |

# 17. Дахин нисэх шийдвэр гаргах нөхцөл
- RTK FLOAT/LOSS удаан үргэлжилсэн эсвэл trajectory discontinuity гарсан.
- LiDAR recording тасарсан, raw data incomplete болсон.
- RGB image missing, blur, exposure problem ихтэй гарсан.
- Boundary/buffer coverage дутсан эсвэл block хооронд gap гарсан.
- Strip alignment / cross-line error хүлцлээс давсан.
- Point density шаардлага хангахгүй, ялангуяа зах, жалга, хадан гарц дээр сул гарсан.
# 18. Тухайн талбайд нөхөж баталгаажуулах final setup

| Параметр | Final утга |
| --- | --- |
| Талбайн нэр | [[FIELD_NAME]] |
| Нийт талбай | [[AREA_HA]] га / [[AREA_KM2]] км² |
| Сонгосон ажлын төрөл | Stage 1 / Stage 2 / Stage 3 / Coverage priority |
| Block тоо | [[BLOCK_COUNT]] |
| Mission тоо | [[MISSION_COUNT]] |
| Altitude | [[ALTITUDE_AGL]] м AGL |
| Speed | [[SPEED_MS]] м/с |
| Overlap | [[FRONT_OVERLAP]] / [[SIDE_OVERLAP]] |
| Heading | [[HEADING_DEG]]° |
| Scan mode | [[SCAN_MODE]] |
| Pulse / returns | [[PULSE_RATE]] / [[RETURNS]] |
| RTK / PPK | [[RTK_SOURCE]] + [[PPK_BACKUP]] |
| Buffer | [[BUFFER_M]] м |
| Block overlap | [[BLOCK_OVERLAP_M]] м |

# 19. Template-ийн товч дүгнэлт
Энэхүү template-ийг ашиглахдаа талбайн га хэмжээгээр block тоо, өндөр, хурд, overlap, scan mode, buffer, checkpoint тоог сонгож тохируулна. Ямар ч хэмжээтэй талбайд нийт зарчим ижил: эхлээд boundary/CRS/terrain шалгах, дараа нь block хуваах, Pilot 2 дээр battery болон 3D preview баталгаажуулах, RTK/PPK workflow-ийг бүрэн хадгалах, эцэст нь QA/QC-ээр хүлээн авах эсэхийг шийдвэрлэх.

| Нөхөх үндсэн хувьсагчид [[PROJECT_NAME]], [[FIELD_NAME]], [[LICENSE_NO]], [[AREA_HA]], [[AREA_KM2]], [[BLOCK_COUNT]], [[MISSION_COUNT]], [[ALTITUDE_AGL]], [[SPEED_MS]], [[FRONT_OVERLAP]], [[SIDE_OVERLAP]], [[SCAN_MODE]], [[BUFFER_M]], [[BLOCK_OVERLAP_M]], [[CONTROL_POINTS]], [[RTK_SOURCE]], [[YYYY-MM-DD]] |
| --- |

# Хавсралт A. Жишээ тооцоо

| Жишээ | Тайлбар |
| --- | --- |
| [[AREA_HA]] = 3,800 га | AREA_KM2 = 3,800 / 100 = 38 км² |
| Production target block = 700 га/block | BLOCK_COUNT = CEILING(3,800 / 700) = 6 block |
| Coverage target block = 1,000 га/block | BLOCK_COUNT = CEILING(3,800 / 1,000) = 4 block |
| Decision | Чанар чухал бол 5–6 block; хурдан бүрхэлт бол 4 block, гэхдээ battery preview заавал шалгана |
