<!-- source: XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v9_25km_Clickable_TOC_PageNumbers.docx (converted from Word; canonical form for LLM ingestion) -->

XV-023222 / L23222 Buduunkhad Exploration Workflow Methodology v8 Phase 3 25 km Buffer and TOC
78 raw input files + QGIS + SNAP 13.0.0 + ASTER workflow + KOMPSAT-2 + ALOS-PALSAR + DJI Matrice 400 + Zenmuse L2/L3/P1 + Olympus Vanta M + Bruker Titan S1 + pXRF + target ranking workflow


| Талбар | Утга |
| --- | --- |
| Project area | Buduunkhad / XV-023222 / L23222 |
| Standard CRS | WGS 84 / UTM Zone 47N, EPSG:32647 |
| Document type | Methodology / workflow guide. Бодит боловсруулалтын үр дүн, нөөцийн тооцоо, final target баталгаа биш. |
| Source basis | XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v1.docx дахь 78 raw input file register, CRS, project identity, equipment/software logic. |
| Style reference | BuduunKhad_Namalzakh_29RawInputs_SNAP_ASTER_Drone_XRF_Methodology.docx-ийн phase format, folder tree, QA/QC, input/output template-ийн бичлэгийн хэв маяг. 29 input file list-ийг хуулж оруулаагүй. |
| Main principle | Raw data-г өөрчлөхгүй хадгалж, зөвхөн processing copy дээр ажиллана; sidecar metadata файлуудыг parent raster/image-тэй хамт хадгална. |
| v3 нэмэлт | Historical Scanned Maps QGIS Vectorization Workflow v02 Detailed аргачлалыг Phase 1-ийн дэд аргачлал / Appendix E хэлбэрээр нэмэв. |
| v4 нэмэлт | Preliminary Deposit Model Preparation Methodology-г Appendix биш, үндсэн workflow-ийн 03_Phase_3 дотор 03A дэд workflow болгон нэгтгэв; Phase 4 preliminary prospect ranking болон Phase 10 final target ranking руу handover холбоос нэмэв. |
| v5 нэмэлт | Phase бүрийн Input files хэсгийг ерөнхий evidence group-ээр биш, яг ашиглах raw input file № болон filename-аар заасан. Мөн 1A Explicit Input File Assignment Matrix нэмэж, raw input -> primary phase -> methodology action холбоосыг бүрэн тодорхойлов. |

Анхааруулга: Satellite, ASTER, KOMPSAT-2, DEM, Drone/LiDAR болон pXRF output нь хүдэржилтийн баталгаа биш. Эдгээр нь target generation, field validation, sampling prioritization-д ашиглах support evidence юм. Эцсийн confidence нь хээрийн шалгалт, лабораторийн шинжилгээ, structural/geological evidence, шаардлагатай бол trench/geophysics/scout drilling-аар баталгаажна.

# Table of Contents / Гарчгийн жагсаалт
Click a section title to jump directly to that section. Page numbers are based on the rendered document layout.
Section / Гарчиг	Page / Хуудас
0. Methodology scope and governing principles	7
1. Enhanced 78 raw input file register	7
1A. Explicit raw input assignment by workflow phase	13
1A.1 Phase-level input control summary	13
1A.2 File-by-file input assignment matrix	14
1A.3 Mandatory rule for every phase	17
1B. Phase-wise exact raw input file processing and output matrix — v6 update	18
1B.1 Phase тус бүрийн raw input file assignment summary	18
1B.2 Detailed 78 raw input file → software → processing → output matrix	18
Phase 1 inputs: boundary, full metadata audit and Master GIS setup	18
Phase 2 inputs: DEM, ALOS-PALSAR, KOMPSAT-2, ASTER, Sentinel and basemap processing	19
Phase 3 / 03A inputs: tectonic, geology, mineral occurrence, prospectivity and metallogenic synthesis	25
Phase 6 and Phase 8 field/historical geochemistry inputs	28
1B.3 Required source-traceability fields for every output	29
v6 implementation note	30
2. Integrated 00-99 phase workflow	32
00. Raw Files Archive	32
Processing folder structure	32
Step-by-step methodology	33
QA/QC check	33
Expected outputs	33
Decision gate / next phase condition	33
01. Phase 1 — Data Audit and Master GIS Setup	33
Processing folder structure	33
Step-by-step methodology	33
QA/QC check	33
Expected outputs	33
Decision gate / next phase condition	33
02. Phase 2 — Remote Sensing Preprocessing	35
Processing folder structure	35
Step-by-step methodology	35
QA/QC check	35
Expected outputs	35
Decision gate / next phase condition	36
03. Phase 3 — Geological, Metallogenic and CMCS Synthesis	36
Purpose and scope	36
03.1 Phase 3 input control	36
03.2 Working folder structure	37
03.3 Pre-start readiness check	38
03.4 Step-by-step methodology	38
Step 7 — CMCS/MRPAM 5 km / 10 km / 20 km / 25 km contextual check	39
Step 7A — 25 km near-occurrence coverage buffer for all nearby mineral occurrences	40
QGIS method for 25 km buffer creation	40
Recommended buffer interpretation hierarchy	40
Additional expected outputs from Step 7A	40
Step 8 — Integrate all Phase 3 evidence into one GeoPackage	40
03.5 Expected output package	41
03.6 Mandatory GeoPackage layer schema	42
03.7 QA/QC checklist	42
03.8 Decision gate and handover to Phase 4 / Phase 10	43
03.9 Phase 3 completion criteria	43
03A. Preliminary Deposit Model Preparation — Phase 3 доторх дэд workflow	44
03A.1 Зорилго ба гарах баримт бичиг	44
03A.2 Ашиглах input evidence	44
03A.3 Ажлын үндсэн дараалал	45
Алхам 1 — Evidence layer-үүдийг Master GIS дээр нэгтгэх	45
Алхам 2 — Historical map-уудаас ордын төрлийн evidence ялгах	45
Алхам 3 — Deposit model candidate-уудыг тодорхойлох	45
Алхам 4 — Supporting evidence / missing evidence / validation work хүснэгт гаргах	45
Алхам 5 — Evidence weight ашиглаж preliminary ranking хийх	45
03A.4 Deposit model candidate screening	45
03A.5 Evidence weight ба preliminary ranking	46
03A.6 XV-023222_Buduunkhad_Preliminary_Deposit_Model.docx санал болгох бүтэц	47
03A.7 Богино ажлын checklist	47
03A.8 Phase 3 QA/QC notes for deposit model preparation	47
03A.9 Handover from Phase 3 to Phase 4 and Phase 10	47
04. Phase 4 — Preliminary Prospect Delineation and Ranking	48
Processing folder structure	48
Step-by-step methodology	48
QA/QC check	48
Expected outputs	49
Decision gate / next phase condition	49
05. Phase 5 — DJI Matrice 400 Drone LiDAR Photogrammetry Survey	49
Processing folder structure	49
Step-by-step methodology	49
QA/QC check	50
Expected outputs	50
Decision gate / next phase condition	50
06. Phase 6 — Recon Mapping and Portable XRF Field Screening	50
Processing folder structure	50
Step-by-step methodology	51
QA/QC check	51
Expected outputs	51
Decision gate / next phase condition	51
07. Phase 7 — Rock Chip, Channel and Verification Sampling	51
Processing folder structure	51
Step-by-step methodology	51
QA/QC check	51
Expected outputs	51
Decision gate / next phase condition	51
08. Phase 8 — Orientation Soil, Stream Sediment and Heavy Mineral Check	52
Processing folder structure	53
Step-by-step methodology	53
QA/QC check	53
Expected outputs	53
Decision gate / next phase condition	53
09. Phase 9 — Systematic Soil Grid and Laboratory QA/QC	53
Processing folder structure	53
Step-by-step methodology	53
QA/QC check	53
Expected outputs	53
Decision gate / next phase condition	53
10. Phase 10 — Integrated Interpretation and Final Target Ranking	55
Processing folder structure	55
Step-by-step methodology	55
QA/QC check	55
Expected outputs	55
Decision gate / next phase condition	56
11. Phase 11 — Follow-up Trench, Geophysics and Scout Drill Planning	56
Processing folder structure	56
Step-by-step methodology	56
QA/QC check	56
Expected outputs	57
Decision gate / next phase condition	57
99. Final Deliverables	57
Processing folder structure	57
Step-by-step methodology	57
QA/QC check	57
Expected outputs	57
Decision gate / next phase condition	57
3. Remote sensing special subworkflows	58
4. Deposit model candidate screening table	58
5. Preliminary and final target ranking matrix	59
6. Portable XRF QA/QC and register schema	59
7. Sampling methodology and QA/QC insertion	60
8. Final target description sheet schema	60
Appendix E — Historical Scanned Maps QGIS Vectorization Workflow v02 Detailed	61
Агуулгын товч жагсаалт	61
1. Зорилго ба хамрах хүрээ	61
2. Reference document-тэй нийцүүлэх зарчим	61
3. Ажил гүйцэтгэх ерөнхий sequence	61
4. Input scanned map inventory	61
4.1 Inventory-д заавал нэмэх metadata баганууд	67
5. Map-to-legend linkage ба symbol dictionary	67
5.1 Symbol dictionary үүсгэх алхам	68
6. Folder structure ба file governance	68
7. QGIS project setup	69
8. Georeferencing workflow	70
8.1 GCP сонгох эх сурвалжийн эрэмбэ	70
8.2 QGIS Georeferencer дээр хийх алхам	71
8.3 DMS coordinate-г decimal degree болгох дүрэм	71
9. Raster QA/QC ба confidence	72
9.1 Georeferenced raster output naming	72
10. Vectorization strategy by map type	73
11. Master GeoPackage design	74
11.1 GeoPackage үүсгэх QGIS алхам	74
12. Field schema ба domain/lookup	75
12.1 Common source traceability fields	75
12.2 Standard domain values	75
13. Layer-specific schema	76
13.x Layer: geology_units_polygons	76
13.x Layer: structures_faults_lines	76
13.x Layer: mineral_occurrences_points	76
13.x Layer: heavy_mineral_anomaly_polygons	77
13.x Layer: stream_sediment_anomaly_polygons	77
13.x Layer: prospectivity_target_zones_polygons	77
13.x Layer: source_material_observation_points	78
13.x Layer: source_material_route_lines	78
13.x Layer: metallogenic_zones_polygons	78
14. QGIS digitizing SOP	78
15. Layer бүрийн нарийвчилсан SOP	79
15.1 Geological unit polygons	79
15.2 Structures/faults/lineaments	79
15.3 Mineral occurrence points	79
15.4 Heavy mineral layers	79
15.5 Stream sediment polyelement layers	80
15.6 Source materials layers	80
15.7 Prospectivity target zones	80
15.8 Metallogenic context	80
16. Excel register workbook	80
16.1 GCP table sheet schema	81
17. QA/QC checklist	81
18. Confidence ranking logic	82
19. Data gap register	82
20. Cross-map integration	84
21. Handover package ба acceptance criteria	84
22. Final workflow diagram	85
23. Appendices	85
Appendix A - Feature ID naming standard	85
Appendix B - QGIS Field Calculator expressions	86
Appendix C - QField package preparation note	86
Appendix D - Чанарын хяналтын анхааруулга	86
Critical QA/QC Notes	86
Methodology Limitation	87

# 0. Methodology scope and governing principles
- Энэхүү v2 Enhanced аргачлал нь Бүдүүн хад / XV-023222 / L23222 хайгуулын талбайн 78 raw input файлыг professional exploration workflow болгон үе шаттай хэрэгжүүлэх заавар юм.
- Энэ баримт бичиг нь бодит processing result, нөөц/баялгийн тооцоо, эсвэл эцсийн өрөмдлөгийн баталсан target биш. Зөвхөн өгөгдөл боловсруулах, шалгах, талбайд баталгаажуулах, дараагийн шийдвэр гаргах аргачлал юм.
- 78 input file register-ийг хадгалж, файл бүрийг spatial status, limitation, processing action, expected output-тэй холбож шинэчилсэн.
- 29RawInputs аргачлалын input list-ийг ашиглаагүй; зөвхөн формат, QA/QC-ийн бичлэгийн түвшин, folder/output template-ийн бүтэц авсан.

| Core principle | Implementation rule |
| --- | --- |
| Raw preservation | 00_Raw_Files_Archive дотор original file read-only хадгална. Rename хийх шаардлагатай бол standardized name register-д бичиж, raw file-г overwrite хийхгүй. |
| Processing copy | Бүх боловсруулалтыг 01-11 phase-ийн Input/Working/Processing хавтасны copy дээр хийнэ. |
| CRS control | Final deliverables EPSG:32647; native CRS/source CRS-г metadata-д хадгална. |
| Evidence hierarchy | Remote sensing/pXRF/drone = support evidence; lab assay + field geology + structural control = decision evidence. |
| Decision gates | Phase бүрийн төгсгөлд QA/QC болон go/no-go шалгуураар дараагийн шат руу шилжинэ. |

# 1. Enhanced 78 raw input file register
Доорх хүснэгт нь v1 баримт бичигт байгаа 78 input file-ийн жагсаалтыг хадгалж, хэрэгжүүлэхэд шаардлагатай spatial status, workflow phase, limitation, required processing action, expected output багануудыг нэмсэн register юм. Sidecar файлууд (.tfw, .aux.xml, .ovr, .rpc, .eph, .txt metadata) нь parent raster/image-ээс салгахгүй хадгалагдана.

| № | Evidence group | Raw input filename | File type | Spatial status / CRS status | Exploration use | Workflow phase | Confidence / limitation | Required processing action | Expected output |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 01_Tectonic_Terrane_KMZ | Geological and Tectonic Characteristics of the Lake Terrane, Mongolia.png | Зураг/скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Англи эх текст: Lake Terrane-ийн геологи, тектоникийн шинж | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Master inventory and confidence ranking entry |
| 2 | 01_Tectonic_Terrane_KMZ | Mongolia_Tectonic_Terrane_Map_Project_Area_Lake_Island_Arc_Terrane.jpg | Зураг/скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Монголын террейний зураг: төслийн талбай Lake island arc terrane-тэй давхцах байдал | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Master inventory and confidence ranking entry |
| 3 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Central_Mongolian_Massif_and_Daagandel_Tectonic_Zone_Page11.jpg | Зураг/скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | МУГЗ-500 тайлбар, хуудас 11: Даагандэлийн бүс ба Төв Монголын массив | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Master inventory and confidence ranking entry |
| 4 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part1_Page08.jpg | Зураг/скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | МУГЗ-500 тайлбар, хуудас 8: Бодонч-Цээлийн бүс, Нуурын Атриат мегабүс | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Master inventory and confidence ranking entry |
| 5 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part2_Page09.jpg | Зураг/скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | МУГЗ-500 тайлбар, хуудас 9: Хурайн, Баатархайрханы, Улааншандын бүс | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Master inventory and confidence ranking entry |
| 6 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part3_Page10.jpg | Зураг/скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | МУГЗ-500 тайлбар, хуудас 10: Ханхөхийн ба Хантайширийн бүс | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Master inventory and confidence ranking entry |
| 7 | 01_Tectonic_Terrane_KMZ | Regional_Tectonic_Subdivision_Map_of_Mongolia_Tumurtogoo_2017_Buduunkhad_Project_in_Ulaanshand_Zone.jpg | Зураг/скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Монголын тектоник дүүрэгчлэлийн зураг: Бүдүүн хад төслийн талбай Улааншандын бүсэд | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Master inventory and confidence ranking entry |
| 8 | 01_Tectonic_Terrane_KMZ | MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz | KMZ / KML polygon | Spatial polygon/vector; WGS84 байх магадлалтай. QGIS дээр EPSG:4326 -> EPSG:32647 хөрвүүлж баталгаажуулна. | L23222 / Buduunhhad тусгай зөвшөөрлийн хил, WGS84 координатын олон өнцөгт | 01_Phase_1_Data_Audit_and_Master_GIS_Setup | Medium/High after CRS, metadata, coordinate and content QA/QC. | Extract coordinates/attributes, clean register, link with GIS layers. | license_boundary layer in Master_GIS_Database.gpkg |
| 9 | 02_DEM_ALOS_ASTERGDEM | ASTER-GDEM-v3_N45E096_DEM_1arcsec_WGS84_v01_raw.tif | Үндсэн raster өгөгдөл | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | Үндсэн raster өгөгдөл | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 10 | 02_DEM_ALOS_ASTERGDEM | ASTER-GDEM-v3_N45E096_NumObservations_1arcsec_WGS84_v01_raw.tif | Үндсэн raster өгөгдөл | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | Үндсэн raster өгөгдөл | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 11 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tfw | World file: pixel хэмжээ, байрлал, north-up georeference | Raster sidecar world file; parent raster-тай хамт хадгална, дангаар spatial layer биш. | World file: pixel хэмжээ, байрлал, north-up georeference | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 12 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif | Үндсэн raster өгөгдөл | GeoTIFF/raster; UTM47N/EPSG:32647 гэж нэрэнд дурдсан боловч CRS, pixel size, extent, NoData-г шалгана. | Үндсэн raster өгөгдөл | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 13 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.aux.xml | Auxiliary metadata: histogram/statistics ба GIS sidecar мэдээлэл | GIS sidecar/overview metadata; parent raster-ийн statistics, pyramid, display support. Parent file-тай хамт хадгална. | Auxiliary metadata: histogram/statistics ба GIS sidecar мэдээлэл | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 14 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.ovr | Overview/pyramid: хурдан харуулахад ашиглагдах багасгасан raster | GIS sidecar/overview metadata; parent raster-ийн statistics, pyramid, display support. Parent file-тай хамт хадгална. | Overview/pyramid: хурдан харуулахад ашиглагдах багасгасан raster | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 15 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tfw | World file: pixel хэмжээ, байрлал, north-up georeference | Raster sidecar world file; parent raster-тай хамт хадгална, дангаар spatial layer биш. | World file: pixel хэмжээ, байрлал, north-up georeference | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 16 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif | Үндсэн raster өгөгдөл | GeoTIFF/raster; UTM47N/EPSG:32647 гэж нэрэнд дурдсан боловч CRS, pixel size, extent, NoData-г шалгана. | Үндсэн raster өгөгдөл | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 17 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif.aux.xml | Auxiliary metadata: histogram/statistics ба GIS sidecar мэдээлэл | GIS sidecar/overview metadata; parent raster-ийн statistics, pyramid, display support. Parent file-тай хамт хадгална. | Auxiliary metadata: histogram/statistics ба GIS sidecar мэдээлэл | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 18 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif.ovr | Overview/pyramid: хурдан харуулахад ашиглагдах багасгасан raster | GIS sidecar/overview metadata; parent raster-ийн statistics, pyramid, display support. Parent file-тай хамт хадгална. | Overview/pyramid: хурдан харуулахад ашиглагдах багасгасан raster | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 19 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tfw | World file: pixel хэмжээ, байрлал, north-up georeference | Raster sidecar world file; parent raster-тай хамт хадгална, дангаар spatial layer биш. | World file: pixel хэмжээ, байрлал, north-up georeference | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 20 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif | Үндсэн raster өгөгдөл | GeoTIFF/raster; UTM47N/EPSG:32647 гэж нэрэнд дурдсан боловч CRS, pixel size, extent, NoData-г шалгана. | Үндсэн raster өгөгдөл | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 21 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif.aux.xml | Auxiliary metadata: histogram/statistics ба GIS sidecar мэдээлэл | GIS sidecar/overview metadata; parent raster-ийн statistics, pyramid, display support. Parent file-тай хамт хадгална. | Auxiliary metadata: histogram/statistics ба GIS sidecar мэдээлэл | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 22 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif.ovr | Overview/pyramid: хурдан харуулахад ашиглагдах багасгасан raster | GIS sidecar/overview metadata; parent raster-ийн statistics, pyramid, display support. Parent file-тай хамт хадгална. | Overview/pyramid: хурдан харуулахад ашиглагдах багасгасан raster | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | DEM QC, projection check, hillshade/slope/aspect/drainage/terrain derivative. | Terrain derivatives: hillshade, slope, drainage, access/safety layers |
| 23 | 03_KOMPSAT2_MSC_L1G | KOMPSAT EULA Form_3.1.pdf | Лицензийн нөхцөл / End User License Agreement | Text/table scanned or office document; coordinate extraction, table cleaning, source confidence log шаардлагатай. | Data provenance, license compliance, тайлангийн хавсралт, хөрөнгө оруулагч/зөвлөх/төрийн байгууллагад эх үүсвэр тайлбарлахад хадгална. | 02_Phase_2_Remote_Sensing_Preprocessing | Needs verification. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 24 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.tif | Panchromatic буюу PAN band raster зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Суурь зураг, lineament interpretation, зам/шурф/ухаш/эвдрэл/ил гарш ялгах, field route planning, pan-sharpening хийхэд хамгийн чухал үндсэн raster файл. | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 25 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.txt | PAN metadata text file | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Тайлангийн Data Source хэсэг, GIS projection/GSD шалгалт, raw data register, QA/QC verification-д ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 26 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.rpc | PAN RPC файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Orthorectification, DEM ашигласан terrain correction, PAN 1 m зургийг газрын бодит байрлалд нарийвчлалтай тохируулахад ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 27 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.eph | PAN ephemeris/orbit файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Геометр боловсруулалтын туслах файл; энгийн GIS дээр шууд нээх шаардлагагүй боловч raw bundle-д хадгална. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 28 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.tif | Multispectral Green band raster | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | True color composite-ийн Green component, Red/Blue/NIR band-уудтай хамт RGB/false color composite, гадаргын өнгөний ялгаа, ус/ургамал/ил гаршийн ялгаралд ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 29 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.txt | Green band metadata | Spatial/metadata status тодруулах шаардлагатай; Data Audit phase-д шалгана. | Band stacking хийхэд band order шалгах, тайлангийн metadata, QA/QC register-д ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 30 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.rpc | Green band RPC файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Green band orthorectification, бусад MS band болон PAN band-тай spatial alignment хийхэд ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 31 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.eph | Green band ephemeris/orbit файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | RPC-based геометр засвар, processing audit-д хэрэгтэй; tif/txt/rpc/eph дөрвийг хамтад хадгална. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 32 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.tif | Multispectral Blue band raster | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | True color composite-ийн Blue component, ус/сүүдэр/atmospheric haze/цайвар гадаргын ялгаа, ил гарш ба хөрсний өнгөний ялгааг бусад band-тай харьцуулан тайлна. | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 33 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.txt | Blue band metadata | Spatial/metadata status тодруулах шаардлагатай; Data Audit phase-д шалгана. | Blue band source verification, band stacking, тайлангийн хавсралт, data register-д ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 34 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.rpc | Blue band RPC файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Blue band orthorectification, DEM-тэй relief correction, band-to-band alignment хийхэд ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 35 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.eph | Blue band ephemeris/orbit файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Advanced geometric processing болон audit trail-д хадгална; шууд зураглал хийх файл биш. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 36 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.tif | Multispectral NIR band raster | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | False color composite, vegetation mask, Red band-тай NDVI, ил гарш/ургамлаар хучигдсан хэсэг, drainage pattern, аллювийн ялгаа харахад ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 37 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.txt | NIR band metadata | Spatial/metadata status тодруулах шаардлагатай; Data Audit phase-д шалгана. | NIR band-ийг зөв таних, NDVI/false color/vegetation mask workflow-д source verification хийхэд ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 38 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.rpc | NIR band RPC файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | NIR band orthorectification, бусад band-уудтай давхцуулах, pan-sharpening өмнөх geometry consistency шалгахад хэрэглэнэ. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 39 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.eph | NIR band ephemeris/orbit файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Advanced geometric processing, audit trail-д хадгална; шууд interpretation хийх файл биш. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 40 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.tif | Multispectral Red band raster | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | True color composite-ийн Red component, NIR-тэй NDVI, хөрс/ил гарш/ferric эсвэл iron-stained гадаргын өнгөний ялгааг ажиглахад ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 41 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.txt | Red band metadata | Spatial/metadata status тодруулах шаардлагатай; Data Audit phase-д шалгана. | Red band source verification, NDVI/true color/false color composite хийхэд band identity баталгаажуулах, QA/QC register-д ашиглана. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 42 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.rpc | Red band RPC файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Red band orthorectification, NIR/Green/Blue/PAN band-уудтай spatial alignment, DEM ашигласан terrain correction-д хэрэгтэй. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 43 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.eph | Red band ephemeris/orbit файл | Sensor/geometric/metadata sidecar; KOMPSAT PAN/MS orthorectification ба audit-д parent raster-тай хамт хадгална. | Геометр боловсруулалтын туслах өгөгдөл; raw data бүртгэлд хадгална. | 02_Phase_2_Remote_Sensing_Preprocessing | Support file; parent data-гүй дангаар ашиглахгүй. Parent raster/image-тэй хамт хадгалах бол High support value. | KOMPSAT bundle-ийн parent PAN/MS file-тэй хамт archive; metadata/RPC audit-д холбох. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 44 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_br.jpg | Browse image / preview зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Scene coverage зөв эсэхийг хурдан шалгах, data register/catalog thumbnail, тайлангийн internal preview-д ашиглана. Analysis хийх үндсэн зураг биш. | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 45 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_br.jgw | Browse image world file | Raster sidecar world file; parent raster-тай хамт хадгална, дангаар spatial layer биш. | br.jpg-г ArcGIS/QGIS дээр ойролцоогоор зөв байрлалтай нээх, lightweight preview overlay хийхэд ашиглана. Дангаараа зураг биш. | 02_Phase_2_Remote_Sensing_Preprocessing | Needs verification. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 46 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_tn.jpg | Thumbnail image | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Data inventory, thumbnail preview, тайлангийн хавсралтад ашиглаж болно. Geospatial analysis, pixel value analysis хийхэд ашиглахгүй. | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | PAN/MS import, band identity check, RPC alignment, orthorectification, pan-sharpen/visual products. | KOMPSAT orthobasemap / NDVI / lineament-outcrop interpretation support |
| 47 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_1-200000_v01_raw-scan.jpg | Зураг / шлихийн сорьцлолтын үр дүн | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Шлихийн сорьц, ёроолын сорьц, ашигт малтмалын/индикатор минералын тархалтын контур, элемент-минералын тэмдэглэгээ. | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Georeference/digitize anomaly contours, drainage catchment analysis, field follow-up planning. | stream_sediment_anomaly and heavy_mineral_anomaly GIS layers; follow-up plan |
| 48 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | Таних тэмдэг / шлихийн зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Шлих, ёроолын сорьцын тэмдэг, минералуудын нэршил, агуулгын ангилал, контурын тайлбар. | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Georeference/digitize anomaly contours, drainage catchment analysis, field follow-up planning. | stream_sediment_anomaly and heavy_mineral_anomaly GIS layers; follow-up plan |
| 49 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | Таних тэмдэг / ёроолын сорьц | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Ёроолын сорьцын агуулга, сарнилын урсгал, сав газрын контур, дээжлэлт хийсэн судлаачдын жагсаалт. | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Georeference/digitize anomaly contours, drainage catchment analysis, field follow-up planning. | stream_sediment_anomaly and heavy_mineral_anomaly GIS layers; follow-up plan |
| 50 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Polyelement_1-200000_v01_raw-scan.jpg | Зураг / ёроолын сорьцын полиметалл үр дүн | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Cu, Pb, Zn, Ag, As, Bi, W, Sn, Mo, Mn, Ba, F зэрэг олон элементийн сарнилын хүрээ ба урсгалын зураглал. | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Georeference/digitize anomaly contours, drainage catchment analysis, field follow-up planning. | stream_sediment_anomaly and heavy_mineral_anomaly GIS layers; follow-up plan |
| 51 | 04_HeavyMineral_StreamSediment_Field | 2011_MN_Namalzakh_L47-74-A_FieldRouteNotebook_Routes14-15_Obs1076-1090_1-50000_v01_raw-scan.pdf | PDF / хээрийн маршрутын дэвтэр | Text/table scanned or office document; coordinate extraction, table cleaning, source confidence log шаардлагатай. | Маршрут 14, 15; ажиглалтын цэг 1076-1090; гар зураг, координат, чулуулгийн гарш, судал, структурын тэмдэглэл. | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Georeference/digitize anomaly contours, drainage catchment analysis, field follow-up planning. | stream_sediment_anomaly and heavy_mineral_anomaly GIS layers; follow-up plan |
| 52 | 04_HeavyMineral_StreamSediment_Field | XV023222_Buduunkhad_Report7255_FieldObservation_StationDescription_Table_WGS84_LegacyRaw_v01.pdf | PDF / ажиглалтын цэгийн хүснэгт | Text/table scanned or office document; coordinate extraction, table cleaning, source confidence log шаардлагатай. | Ажиглалтын цэгүүдийн координат, чулуулаг, структур, эрдэсжилтийн товч тайлбар. | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | Needs verification. | Georeference/digitize anomaly contours, drainage catchment analysis, field follow-up planning. | stream_sediment_anomaly and heavy_mineral_anomaly GIS layers; follow-up plan |
| 53 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_1-200000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Региональ геологийн суурь зураг | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 54 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_Legend_1-200000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Региональ геологийн зурагт ашигласан стратиграфи, интрузив, структур, литологийн тайлбар | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 55 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_1-50000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Нарийвчилсан геологи, литологи, хагарал, зүсэлт | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 56 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_Legend_1-50000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Нарийвчилсан стратиграфи, интрузив, судал, хувирлын тэмдэглэгээ | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 57 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_1-200000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Региональ ашигт малтмалын илрэл, геохимийн гажил, хүдрийн талбай | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 58 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_Legend_1-200000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Ашигт малтмал, элемент, илрэл, гажлын тэмдэглэгээ | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 59 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MineralDistributionPatternMap_1-100000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Металлогенийн бүс, хүдрийн дүүрэг, зангилаа, талбайн харилцан байрлал | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 60 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_MineralOccurrenceMap_1-50000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Au-Cu, Cu, Mo, As, Zn зэрэг илрэл ба геологийн суурьтай давхцуулсан зураг | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 61 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MetallogenicSchemeAndMetallogenogram_1-400000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Хүдрийн формац, нас, металлогенийн бүс ба элементүүдийн холбоо | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 62 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessment_ReportExcerpt_B3-TolKhar_v01_raw-photo.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Б-2, Б-3, Б-4 талбайн тайлбар, талбайн хэмжээ, илрэл, хэтийн төлөв | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 63 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessmentMap_1-50000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Б-3 Толь хяр, Г-1 зэрэг хэтийн төлөвтэй хэсгийг ялгасан зураг | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 64 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_1-50000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Маршрут, ажиглалтын цэг, сорьц, суваг, шурф, зүсэлтийн байрлал | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 65 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_Legend_1-50000_v01_raw-scan.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Ажиглалтын цэг, маршрут, сорьц, шурф, суваг, тэмдэглэгээ | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 66 | 05_Geology_Mineral_Prospectivity | 2013_MN_L47-XIX_GoldOccurrenceDescriptions_XIX-74-A_4186_v01_raw.docx | DOCX текст | Text/table scanned or office document; coordinate extraction, table cleaning, source confidence log шаардлагатай. | XIX-74-A-1, A-2, A-3 алтны илрэлийн координат, агуулга, геологийн нөхцөл | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/High after CRS, metadata, coordinate and content QA/QC. | Extract coordinates/attributes, clean register, link with GIS layers. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 67 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MineralOccurrenceAndMineralizedPointRegister_7255_v01_raw-scan.pdf | PDF скан, 14 хуудас | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Илрэл, эрдэсжсэн цэг, гар зураг, хүснэгт, P3 тайлбар | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 68 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_MineralizedPointRegister_7255_v01_raw-table.xlsx | XLSX хүснэгт | Text/table scanned or office document; coordinate extraction, table cleaning, source confidence log шаардлагатай. | Цэгийн дугаар, координат, чулуулаг, агуулга, эрдэсжилт, төрөл, дээж | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/High after CRS, metadata, coordinate and content QA/QC. | Extract coordinates/attributes, clean register, link with GIS layers. | Geology/mineral occurrence/prospectivity layers and occurrence database |
| 69 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_Legend_RawScan_2020_v01.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Металлогений зургийн таних тэмдэг, ашигт малтмалын төрөл, орд-илрэлийн тэмдэглэгээ, судалгааны ажлын тэмдэглэгээ | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Metallogenic context map/report and deposit model screening table |
| 70 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_RawScan_2020_v01.jpg | JPG зураг | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Монгол улсын 1:500,000-ны металлогений зураг, L-47-B (Тал шанд) хавтгай | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Metallogenic context map/report and deposit model screening table |
| 71 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book01_ProjectBook13_1M500K_RawScan_2021_v01.pdf | PDF скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Монгол орны 1:500,000-ны масштабын металлогений зураг, тайлбар бичиг. Ном-1, төслийн номын дугаар-13 | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Metallogenic context map/report and deposit model screening table |
| 72 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book04_ProjectBook16_1M500K_RawScan_2021_v01.pdf | PDF скан | Scanned/non-native image; georeference status unknown. Map grid/GCP ашиглан QA/QC хийх шаардлагатай. | Монгол орны 1:500,000-ны масштабын металлогений зураг, тайлбар бичиг. Ном-4, төслийн номын дугаар-16 | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis | Medium/Low until georeferenced and source checked; scale/residual/confidence flag шаардлагатай. | Scan QA/QC, georeference if map, digitize key evidence, attribute coding, confidence flag. | Metallogenic context map/report and deposit model screening table |
| 73 | 07_Basemap_Sentinel2_ASTER | 2005-09-05_MN_ASTER-L1B_MultispectralImagery_00409052005043503_v01_raw.hdf | HDF4 | ASTER HDF raw product; direct GIS layer биш. ASTER workflow v5 дагуу import/band extraction шаардлагатай. | error | 02_Phase_2_Remote_Sensing_Preprocessing | Needs verification; HDF import алдаа/compatibility шалгана. Raw product өөрчлөхгүй. | ASTER HDF import, band extraction, UTM47 grid, index/score/class/mask workflow. | ASTER raw score, class map, final binary support mask, QA/QC log |
| 74 | 07_Basemap_Sentinel2_ASTER | 2025-05-28_MN_T46TGS_GeoreferencedSatelliteRaster_v01_raw.tif | GTiff | GeoTIFF/raster; UTM46N/T46 tile байж болзошгүй. EPSG:32647 стандарт руу reproject хийх эсэхийг шалгана. | ok | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | Remote sensing QA/QC, subset/reproject, derive composites/indices, export EPSG:32647. | Sentinel/ASTER/basemap derivative GeoTIFF and remote sensing QA/QC report |
| 75 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif | GTiff | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | ok | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | Remote sensing QA/QC, subset/reproject, derive composites/indices, export EPSG:32647. | Sentinel/ASTER/basemap derivative GeoTIFF and remote sensing QA/QC report |
| 76 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif | GTiff | GeoTIFF/raster; CRS/resolution/extent/NoData/band count шалгана. | ok | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | Remote sensing QA/QC, subset/reproject, derive composites/indices, export EPSG:32647. | Sentinel/ASTER/basemap derivative GeoTIFF and remote sensing QA/QC report |
| 77 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_GeologicalInterpretation_RGB_B12-B08-B03_10m_UTM46N_ReceivedRaw_v01.tif | GTiff | GeoTIFF/raster; UTM46N/T46 tile байж болзошгүй. EPSG:32647 стандарт руу reproject хийх эсэхийг шалгана. | ok | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | Remote sensing QA/QC, subset/reproject, derive composites/indices, export EPSG:32647. | Sentinel/ASTER/basemap derivative GeoTIFF and remote sensing QA/QC report |
| 78 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_LithologyIndex_B11B12_B08B11_B04B03_10m_UTM46N_ReceivedRaw_v01.tif | GTiff | GeoTIFF/raster; UTM46N/T46 tile байж болзошгүй. EPSG:32647 стандарт руу reproject хийх эсэхийг шалгана. | ok | 02_Phase_2_Remote_Sensing_Preprocessing | Medium/High after CRS, metadata, coordinate and content QA/QC. | Remote sensing QA/QC, subset/reproject, derive composites/indices, export EPSG:32647. | Sentinel/ASTER/basemap derivative GeoTIFF and remote sensing QA/QC report |


| Evidence group | File count | Primary workflow use |
| --- | --- | --- |
| 01_Tectonic_Terrane_KMZ | 8 | Terrane, tectonic setting, license boundary and regional concept. |
| 02_DEM_ALOS_ASTERGDEM | 14 | Terrain, slope, drainage, access, safety and lineament support. |
| 03_KOMPSAT2_MSC_L1G | 24 | High-resolution visual basemap, PAN/MS, lineament/outcrop/access interpretation. |
| 04_HeavyMineral_StreamSediment_Field | 6 | Historical geochemical anomaly, drainage follow-up and orientation sampling. |
| 05_Geology_Mineral_Prospectivity | 16 | Detailed/regional geology, occurrences, prospectivity and occurrence database. |
| 06_Regional_Metallogenic_L47B | 4 | 1:500,000 metallogenic context and deposit model screening. |
| 07_Basemap_Sentinel2_ASTER | 6 | Sentinel/ASTER/basemap remote sensing support layers. |

# 1A. Explicit raw input assignment by workflow phase
Purpose: Энэ хэсэг нь 78 raw input file бүрийг яг аль workflow phase-ийн input болохыг, filename-ээр нь, аргачлалын хэрэглээтэй нь холбож заана. Phase дотор “Input files” гэж ерөнхий бичихгүй; доорх № болон filename-ийг ашиглана. Raw data-г өөрчлөхгүй, зөвхөн working copy дээр боловсруулна.
## 1A.1 Phase-level input control summary

| Workflow phase | Exact direct raw input № | How to apply | Handover note |
| --- | --- | --- | --- |
| 00 Raw Files Archive | №1-78 | Бүх raw file болон sidecar файлыг read-only archive-д бүртгэж checksum үүсгэнэ. | All later phases use working copies only. |
| 01 Data Audit and Master GIS Setup | №1-78 | Файл бүрийн metadata, CRS/spatial status, sidecar, scan quality, processing copy status, confidence-г шалгана. | Master inventory + Master GIS schema. |
| 02 Remote Sensing Preprocessing | №9-46, №73-78 | DEM, KOMPSAT, ASTER, Sentinel/basemaps-ийг QA/QC, orthorectify/reproject/subset/derive products болгоно. | Support evidence only; ore proof биш. |
| 03 Geological, Metallogenic and CMCS Synthesis | №1-8, №53-72 | Tectonic, geology, occurrence, prospectivity, source material, metallogenic context-ийг нэгтгэнэ. | Deposit model and geological evidence layers. |
| 03A Preliminary Deposit Model Preparation | №1-8, №47-78, №9-46 as support | Ордын candidate model бүрт exact source evidence ашиглан supporting/missing/validation хүснэгт гаргана. | Phase 4 scoring and Phase 10 final target model-fit. |
| 04 Preliminary Prospect Delineation and Ranking | Traceable basis №1-78 + Phase 1-3 outputs | Evidence overlay, 100-point score, A/B/C/D ranking; dominant_deposit_model талбар нэмнэ. | A/B prospects to drone/recon. |
| 05 Drone/LiDAR/Photogrammetry | №8, №9-22, №24-46, №75-78 + Phase 4 outputs | Flight block, terrain/access/safety/basemap/lineament support. | Drone outputs to Phase 6-10. |
| 06 Recon Mapping and pXRF | №8, №9-22, №55-56, №60, №63-68, №75-78 + Phase 4/5 outputs | Field validation, lithology/alteration/mineralization/pXRF forms and traverse planning. | Validated field evidence to Phase 7. |
| 07 Rock Chip/Channel Sampling | №52, №55-56, №60, №63-68, №9-22, №75-78 + Phase 6 outputs | Sample candidate selection, lab submission, QA/QC insertion, assay import template. | Lab evidence to Phase 10. |
| 08 Orientation Soil/Stream/Heavy Mineral | №47-52, №9-22, №53-56, №60, №63-64, №68 | Historical drainage/heavy mineral/geochemical evidence, orientation survey design. | Validated method to Phase 9. |
| 09 Systematic Soil Grid | №8, №9-22, №47-52, №55, №60, №63-64, №68, №75-78 + Phase 8 outputs | Grid design, soil collection, lab QA/QC, soil anomaly map. | Assay anomalies to Phase 10. |
| 10 Integrated Interpretation and Final Target Ranking | Full traceable source basis №1-78 + validated phase outputs | All evidence, field/lab QA/QC, model-fit re-score, final target sheets. | Final A/B targets to Phase 11. |
| 11 Follow-up Trench/Geophysics/Scout Drill | №8, №9-22, №55, №60, №63-64, №68, №75-78 + Phase 10 outputs | Trench/IP/magnetic/scout drill collar planning, HSE/access/budget check. | Only if minimum criteria met. |
| 99 Final Deliverables | №1-78 traceability + all phase outputs | Final package, GIS, reports, QA/QC, limitations, source references. | Ready for technical/management review. |

## 1A.2 File-by-file input assignment matrix
Энэ matrix-д raw input file бүрийг primary workflow phase-тэй холбов. Secondary phase-үүдэд ашиглах үед тухайн phase-ийн “Input files” мөр болон Phase-level summary-д заасан №-өөр татаж хэрэглэнэ.

| № | Evidence group | Exact raw input filename | Primary input phase | Methodology action |
| --- | --- | --- | --- | --- |
| 1 | 01_Tectonic_Terrane_KMZ | Geological and Tectonic Characteristics of the Lake Terrane, Mongolia.png | 03 | Lake Terrane tectonic/geological context; use as regional concept evidence only after source and scan QA/QC. |
| 2 | 01_Tectonic_Terrane_KMZ | Mongolia_Tectonic_Terrane_Map_Project_Area_Lake_Island_Arc_Terrane.jpg | 03 | Terrane overlay; supports Lake island arc terrane context and deposit model screening. |
| 3 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Central_Mongolian_Massif_and_Daagandel_Tectonic_Zone_Page11.jpg | 03 | Regional tectonic explanation; extract narrative evidence and confidence/source note. |
| 4 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part1_Page08.jpg | 03 | Nuur accretionary megazone context; use for regional geological setting. |
| 5 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part2_Page09.jpg | 03 | Khurai/Baatarkhairkhan/Ulaanshand zone context; supports model screening. |
| 6 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part3_Page10.jpg | 03 | Khankhukhi/Khantayshir regional context; source note and limitation flag required. |
| 7 | 01_Tectonic_Terrane_KMZ | Regional_Tectonic_Subdivision_Map_of_Mongolia_Tumurtogoo_2017_Buduunkhad_Project_in_Ulaanshand_Zone.jpg | 03 | Ulaanshand Zone tectonic subdivision context for deposit model candidate screening. |
| 8 | 01_Tectonic_Terrane_KMZ | MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz | 01 | Primary license boundary; import to GeoPackage, reproject EPSG:32647, use for all clipping/buffer/QA. |
| 9 | 02_DEM_ALOS_ASTERGDEM | ASTER-GDEM-v3_N45E096_DEM_1arcsec_WGS84_v01_raw.tif | 02 | DEM terrain base; derive hillshade/slope/aspect/drainage and use for access/safety/lineament support. |
| 10 | 02_DEM_ALOS_ASTERGDEM | ASTER-GDEM-v3_N45E096_NumObservations_1arcsec_WGS84_v01_raw.tif | 02 | ASTER GDEM observation-count QA layer; evaluate DEM reliability/artefacts. |
| 11 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tfw | 02 | World file sidecar for ALOS-PALSAR DEM; keep with parent raster, do not use alone. |
| 12 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif | 02 | High-resolution terrain DEM; produce DTM derivatives, drainage, slope and lineament support. |
| 13 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.aux.xml | 02 | Auxiliary metadata/statistics sidecar for ALOS DEM; preserve with parent raster. |
| 14 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.ovr | 02 | Overview/pyramid sidecar for ALOS DEM; preserve with parent raster. |
| 15 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tfw | 02 | World file sidecar for hillshade; keep with parent raster. |
| 16 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif | 02 | Hillshade support layer; use for structural/terrain interpretation and field/drone planning. |
| 17 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif.aux.xml | 02 | Auxiliary metadata/statistics sidecar for hillshade; preserve with parent raster. |
| 18 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif.ovr | 02 | Overview/pyramid sidecar for hillshade; preserve with parent raster. |
| 19 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tfw | 02 | World file sidecar for slope raster; keep with parent raster. |
| 20 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif | 02 | Slope degree raster; use for access, safety, drainage and drone/trench/drill workability. |
| 21 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif.aux.xml | 02 | Auxiliary metadata/statistics sidecar for slope raster; preserve with parent raster. |
| 22 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif.ovr | 02 | Overview/pyramid sidecar for slope raster; preserve with parent raster. |
| 23 | 03_KOMPSAT2_MSC_L1G | KOMPSAT EULA Form_3.1.pdf | 02 | License/provenance evidence; store in data source and compliance register. |
| 24 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.tif | 02 | KOMPSAT PAN raster; orthorectify/pansharpen, use for lineament, outcrop, access and basemap. |
| 25 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.txt | 02 | PAN metadata; use for source verification, GSD/projection audit, processing register. |
| 26 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.rpc | 02 | PAN RPC sidecar; required for orthorectification/terrain correction. |


| № | Evidence group | Exact raw input filename | Primary input phase | Methodology action |
| --- | --- | --- | --- | --- |
| 27 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.eph | 02 | PAN ephemeris/orbit sidecar; preserve with PAN bundle for geometric audit. |
| 28 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.tif | 02 | KOMPSAT Green band; stack with MS bands for true/false color and pan-sharpened products. |
| 29 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.txt | 02 | Green band metadata; verify band identity and processing parameters. |
| 30 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.rpc | 02 | Green band RPC sidecar; use for MS orthorectification/alignment. |
| 31 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.eph | 02 | Green band ephemeris/orbit sidecar; preserve with MS bundle. |
| 32 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.tif | 02 | KOMPSAT Blue band; stack with MS bands for composites and basemap. |
| 33 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.txt | 02 | Blue band metadata; verify source and band identity. |
| 34 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.rpc | 02 | Blue band RPC sidecar; use for MS orthorectification/alignment. |
| 35 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.eph | 02 | Blue band ephemeris/orbit sidecar; preserve with MS bundle. |
| 36 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.tif | 02 | KOMPSAT NIR band; derive NDVI/vegetation mask and false color support. |
| 37 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.txt | 02 | NIR band metadata; verify source and band identity. |
| 38 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.rpc | 02 | NIR band RPC sidecar; use for MS orthorectification/alignment. |
| 39 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.eph | 02 | NIR band ephemeris/orbit sidecar; preserve with MS bundle. |
| 40 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.tif | 02 | KOMPSAT Red band; stack for RGB/NDVI/false color support. |
| 41 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.txt | 02 | Red band metadata; verify source and band identity. |
| 42 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.rpc | 02 | Red band RPC sidecar; use for MS orthorectification/alignment. |
| 43 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.eph | 02 | Red band ephemeris/orbit sidecar; preserve with MS bundle. |
| 44 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_br.jpg | 02 | KOMPSAT browse image; use for scene coverage preview only, not analysis-grade raster. |
| 45 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_br.jgw | 02 | Browse image world file; keep with br.jpg for lightweight overlay only. |
| 46 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_tn.jpg | 02 | Thumbnail preview; use for inventory/catalog only. |
| 47 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_1-200000_v01_raw-scan.jpg | 08 | Heavy mineral sampling result map; georeference/digitize indicator minerals/anomaly polygons and drainage follow-up. |
| 48 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | 08 | Heavy mineral legend; build symbol dictionary and indicator mineral domain values. |
| 49 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | 08 | Stream sediment legend; build element/anomaly/contour domain values. |
| 50 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Polyelement_1-200000_v01_raw-scan.jpg | 08 | Stream sediment polyelement map; digitize Cu-Pb-Zn-Ag-As-Bi-W-Sn-Mo-Mn-Ba-F anomaly layers. |
| 51 | 04_HeavyMineral_StreamSediment_Field | 2011_MN_Namalzakh_L47-74-A_FieldRouteNotebook_Routes14-15_Obs1076-1090_1-50000_v01_raw-scan.pdf | 08 | Field route notebook; extract observation routes/points, compare with geology and sampling plans. |
| 52 | 04_HeavyMineral_StreamSediment_Field | XV023222_Buduunkhad_Report7255_FieldObservation_StationDescription_Table_WGS84_LegacyRaw_v01.pdf | 08 | Field observation station table; extract coordinates/lithology/mineralization into validation register. |


| № | Evidence group | Exact raw input filename | Primary input phase | Methodology action |
| --- | --- | --- | --- | --- |
| 53 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_1-200000_v01_raw-scan.jpg | 03 | Regional geology map; georeference and digitize regional geology/structure for context. |
| 54 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_Legend_1-200000_v01_raw-scan.jpg | 03 | Regional geology legend; build lithology/age/intrusion/structure lookup. |
| 55 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_1-50000_v01_raw-scan.jpg | 03 | Detailed geology map; primary local geology/structure/contact/section vectorization source. |
| 56 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_Legend_1-50000_v01_raw-scan.jpg | 03 | Detailed geology legend; build stratigraphy, intrusive, vein and alteration domains. |
| 57 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_1-200000_v01_raw-scan.jpg | 03 | Regional mineral resources map; digitize occurrence/resource/anomaly context. |
| 58 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_Legend_1-200000_v01_raw-scan.jpg | 03 | Mineral resources legend; build commodity/occurrence/anomaly symbol dictionary. |
| 59 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MineralDistributionPatternMap_1-100000_v01_raw-scan.jpg | 03 | Mineral distribution pattern map; ore district/node/metallogenic area context. |
| 60 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_MineralOccurrenceMap_1-50000_v01_raw-scan.jpg | 03 | Detailed mineral occurrence map; primary Au-Cu/Cu/Mo/As/Zn occurrence vectorization source. |
| 61 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MetallogenicSchemeAndMetallogenogram_1-400000_v01_raw-scan.jpg | 03 | Metallogenic scheme/metallogenogram; ore formation and regional metallogenic context. |
| 62 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessment_ReportExcerpt_B3-TolKhar_v01_raw-photo.jpg | 03 | Prospectivity report excerpt; extract B-2/B-3/B-4 narrative evidence and data gaps. |
| 63 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessmentMap_1-50000_v01_raw-scan.jpg | 03 | Prospectivity assessment map; digitize B-3 Tol Khar/G-1 and priority areas. |
| 64 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_1-50000_v01_raw-scan.jpg | 03 | Source materials map; digitize routes, stations, samples, trenches, pits and sections. |
| 65 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_Legend_1-50000_v01_raw-scan.jpg | 03 | Source materials legend; build route/observation/sample/work-type domains. |
| 66 | 05_Geology_Mineral_Prospectivity | 2013_MN_L47-XIX_GoldOccurrenceDescriptions_XIX-74-A_4186_v01_raw.docx | 03 | Gold occurrence descriptions; extract Au occurrence coordinates, grades and geological descriptions. |
| 67 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MineralOccurrenceAndMineralizedPointRegister_7255_v01_raw-scan.pdf | 03 | Mineral occurrence/mineralized point register; extract/cross-check occurrence attributes and P3 notes. |
| 68 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_MineralizedPointRegister_7255_v01_raw-table.xlsx | 03 | Mineralized point table; import cleaned coordinates/attributes to occurrence database. |
| 69 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_Legend_RawScan_2020_v01.jpg | 03 | Regional metallogenic legend; build belt/ore-formation/commodity domain values. |
| 70 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_RawScan_2020_v01.jpg | 03 | 1:500k metallogenic map; use as regional metallogenic context only. |
| 71 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book01_ProjectBook13_1M500K_RawScan_2021_v01.pdf | 03 | Metallogenic report book 01; extract text evidence for ore formation and regional context. |
| 72 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book04_ProjectBook16_1M500K_RawScan_2021_v01.pdf | 03 | Metallogenic report book 04; extract text evidence for ore formation and regional context. |
| 73 | 07_Basemap_Sentinel2_ASTER | 2005-09-05_MN_ASTER-L1B_MultispectralImagery_00409052005043503_v01_raw.hdf | 02 | ASTER HDF raw product; import/extract bands and derive alteration/lithology indices. |
| 74 | 07_Basemap_Sentinel2_ASTER | 2025-05-28_MN_T46TGS_GeoreferencedSatelliteRaster_v01_raw.tif | 02 | Received satellite raster; QA/QC CRS/extent, subset/reproject and derive support products. |
| 75 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif | 02 | Google Maps RGB basemap; QA/QC/reproject for field planning and visual reference. |
| 76 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif | 02 | High-resolution surface basemap; reproject/clip for access, outcrop and field planning support. |
| 77 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_GeologicalInterpretation_RGB_B12-B08-B03_10m_UTM46N_ReceivedRaw_v01.tif | 02 | Sentinel-2 geology composite; reproject to EPSG:32647 and use as lithology/alteration support. |
| 78 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_LithologyIndex_B11B12_B08B11_B04B03_10m_UTM46N_ReceivedRaw_v01.tif | 02 | Sentinel-2 lithology index product; reproject and use as support evidence only. |

## 1A.3 Mandatory rule for every phase
- Phase бүрийн аргачлалд input-ийг “geology files” эсвэл “remote sensing files” гэж дангаар бичихгүй; Section 1A.2 дахь raw input № болон exact filename-ийг заавал ашиглана.
- Output layer/report/table бүрт source_input_no, source_raw_filename, source_group, source_phase, processing_version, confidence, limitation талбар/мөр хадгална.
- Historical scanned map-derived evidence нь validation_status = Historical only байхаас field/lab confirmed evidence-тэй холигдохгүй.
- Remote sensing, DEM, KOMPSAT, Sentinel, ASTER, drone/LiDAR, pXRF output нь хүдэржилтийн баталгаа биш; support evidence гэж тэмдэглэнэ.

# 1B. Phase-wise exact raw input file processing and output matrix — v6 update
Зорилго. Энэ v6 нэмэлт нь 78 raw input file бүрийг аль phase-д ашиглах, яг ямар нэртэй input файл болох, ямар software/program-аар ямар боловсруулалт хийх, ямар нэртэй output file гаргахыг нэг бүрчлэн заана. Raw file-г overwrite хийхгүй; бүх ажил processing copy дээр хийгдэнэ. Output filename нь standard deliverable naming бөгөөд бодит боловсруулалтын үед version дугаарыг v01/v02... гэж өсгөнө.
## 1B.1 Phase тус бүрийн raw input file assignment summary

| Workflow phase | Raw input file numbers | Main software/program | Main output package |
| --- | --- | --- | --- |
| 00_Raw_Files_Archive | 1-78 | File system, checksum utility, Excel | Master inventory, checksum register, source data README |
| 01_Phase_1_Data_Audit_and_Master_GIS_Setup | 1-78 metadata; primary spatial boundary input №8; all raster/scan/doc sidecar QA | QGIS, GDAL/OGR, Excel | Master_GIS_Database.gpkg; Master_QGIS_Project.qgz; CRS/Georef QAQC Log; Data Confidence Ranking |
| 02_Phase_2_Remote_Sensing_Preprocessing | 9-46, 73-78 | SNAP 13.0.0, QGIS, GDAL, ILWIS 3.6.8, Global Mapper | Processed DEM/Sentinel/ASTER/KOMPSAT outputs, QAQC logs, remote sensing support layers |
| 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | 1-7, 53-72 plus outputs from Phase 1/2 and boundary №8 | QGIS, QGIS Georeferencer, Excel/Word evidence registers | Geological evidence layers, metallogenic context, occurrence database, Preliminary Deposit Model.docx |
| 04_Phase_4_Preliminary_Prospect_Delineation_and_Ranking | Derived from raw №1-8, 47-78 and Phase 2/3 outputs | QGIS, Excel scoring matrix | Prospect polygons, ranking table, Go/No-Go desktop matrix |
| 05_Phase_5_DJI_Matrice_400_Drone_LiDAR_Photogrammetry_Survey | Derived A/B prospect outputs from Phase 4; DEM/access from №9-22 and basemap №75-78 | DJI Matrice 400, Zenmuse P1/L2/L3, processing software, QGIS | Drone flight plan, orthomosaic, LiDAR point cloud, DTM/DSM, interpretation layers |
| 06_Phase_6_Recon_Mapping_and_Portable_XRF_Field_Screening | Field planning from №51, №52, №60, №63, №64 and Phase 4/5 outputs | QField/QGIS, Olympus Vanta M, Bruker Titan S1 | Recon traverse, field observations, pXRF register and QAQC report |
| 07_Phase_7_Rock_Chip_Channel_and_Verification_Sampling | Field-confirmed targets derived from №55, №60, №63, №64, №66-68 and Phase 6 outputs | QField/QGIS, GPS/GNSS, lab submission templates | Rock chip/channel register, lab submission, assay import template |
| 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | 47-52 plus target/geology outputs from №55, №60, №63, №64 | QGIS, DEM drainage tools, pXRF, lab workflow | Orientation soil plan, stream/heavy mineral follow-up plan |
| 09_Phase_9_Systematic_Soil_Grid_and_Laboratory_QAQC | Derived from Phase 8; geologic/target controls from №55, №60, №63, №64 | QGIS grid design, pXRF, laboratory assay | Soil grid plan, sample points, QAQC report, soil assay results |
| 10_Phase_10_Integrated_Interpretation_and_Final_Target_Ranking | All validated raw-derived outputs from №1-78 plus lab/field/drone results | QGIS, Excel/statistical validation, Word report | Integrated interpretation report, final target polygons, target description sheets |
| 11_Phase_11_Follow_Up_Trench_Geophysics_and_Scout_Drill_Planning | Final A/B targets; DEM/access from №9-22; geology/structure from №53-68; RS from №73-78 | QGIS, trench/geophysics/drilling planning templates | Follow-up work plan, trench/geophysics lines, scout drilling proposal, collar table |

## 1B.2 Detailed 78 raw input file → software → processing → output matrix
### Phase 1 inputs: boundary, full metadata audit and Master GIS setup

| № | Evidence group | Exact raw input filename | Primary workflow phase | Software / program | Processing action | Expected output filename(s) |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | 01_Tectonic_Terrane_KMZ | MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz | 01_Phase_1_Data_Audit_and_Master_GIS_Setup | QGIS, GDAL/OGR, GeoPackage | KMZ/KML polygon import; CRS шалгах; EPSG:4326-аас EPSG:32647 руу export; topology/area/perimeter QA/QC; master project-ийн үндсэн boundary layer болгоно. | XV023222_Buduunkhad_L23222_LicenseBoundary_EPSG32647_v01.gpkg; XV023222_Buduunkhad_LicenseBoundary_QAQC_Register.xlsx; XV023222_Buduunkhad_Project_Buffer_500m_1km_5km_10km_20km_25km_EPSG32647.gpkg |

### Phase 2 inputs: DEM, ALOS-PALSAR, KOMPSAT-2, ASTER, Sentinel and basemap processing

| № | Evidence group | Exact raw input filename | Primary workflow phase | Software / program | Processing action | Expected output filename(s) |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | 02_DEM_ALOS_ASTERGDEM | ASTER-GDEM-v3_N45E096_DEM_1arcsec_WGS84_v01_raw.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, Global Mapper | DEM CRS/resolution/NoData/extent шалгах; license+buffer subset; EPSG:32647 reproject; hillshade/slope/aspect/contour/drainage derivative гаргана. | XV023222_Buduunkhad_ASTERGDEM_DEM_EPSG32647_v01.tif; XV023222_Buduunkhad_ASTERGDEM_Hillshade_Slope_Aspect_Drainage_EPSG32647_v01.gpkg/tif; XV023222_Buduunkhad_DEM_QAQC_Log.xlsx |
| 10 | 02_DEM_ALOS_ASTERGDEM | ASTER-GDEM-v3_N45E096_NumObservations_1arcsec_WGS84_v01_raw.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | ASTER GDEM observation-count raster-г DEM quality mask болгон шалгах; low reliability pixel flag; DEM QA/QC-д холбох. | XV023222_Buduunkhad_ASTERGDEM_NumObservations_QA_Mask_EPSG32647_v01.tif; XV023222_Buduunkhad_DEM_Quality_Assessment.xlsx |
| 11 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tfw | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, Global Mapper | Parent DEM-тэй хамтад нь bundle болгон хадгална; CRS/pixel size/extent/NoData шалгаж EPSG:32647 DEM derivative-ийн үндсэн эх болгон ашиглана. | XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif; XV023222_Buduunkhad_ALOS_PALSAR_Terrain_Derivatives_EPSG32647_v01.gpkg/tif; sidecar_bundle_QAQC entry (world file) |
| 12 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, Global Mapper | ALOS-PALSAR 12.5 m DEM-ийг CRS/pixel/extent шалгаж subset/reproject; terrain derivative, drainage, access/safety, drone/trench planning-д ашиглана. | XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif; XV023222_Buduunkhad_ALOS_PALSAR_Terrain_Derivatives_EPSG32647_v01.gpkg/tif; sidecar_bundle_QAQC entry (12.5 m DEM raster) |
| 13 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.aux.xml | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, Global Mapper | Parent DEM-тэй хамтад нь bundle болгон хадгална; CRS/pixel size/extent/NoData шалгаж EPSG:32647 DEM derivative-ийн үндсэн эх болгон ашиглана. | XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif; XV023222_Buduunkhad_ALOS_PALSAR_Terrain_Derivatives_EPSG32647_v01.gpkg/tif; sidecar_bundle_QAQC entry (aux/statistics sidecar) |
| 14 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_DEM_12p5m_UTM47N_Raw_v01.tif.ovr | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, Global Mapper | Parent DEM-тэй хамтад нь bundle болгон хадгална; CRS/pixel size/extent/NoData шалгаж EPSG:32647 DEM derivative-ийн үндсэн эх болгон ашиглана. | XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif; XV023222_Buduunkhad_ALOS_PALSAR_Terrain_Derivatives_EPSG32647_v01.gpkg/tif; sidecar_bundle_QAQC entry (overview pyramid sidecar) |
| 15 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tfw | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_hillshade_world_file_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 16 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_hillshade_raster_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 17 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif.aux.xml | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_hillshade_aux_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 18 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_Hillshade_12p5m_UTM47N_Derived_v01.tif.ovr | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_hillshade_overview_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 19 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tfw | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_slope_world_file_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 20 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_slope_raster_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 21 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif.aux.xml | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_slope_aux_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 22 | 02_DEM_ALOS_ASTERGDEM | XV023222_Buduunkhad_ALOS-PALSAR_SlopeDeg_12p5m_UTM47N_Derived_v01.tif.ovr | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | Derived raster/sidecar QA; parent raster-тэй хамт bundle audit; EPSG:32647 alignment шалгах; terrain/access/lineament interpretation-д reference layer болгоно. | XV023222_Buduunkhad_ALOS_PALSAR_slope_overview_QAQC_EPSG32647_v01.tif/register; XV023222_Buduunkhad_Terrain_Derivatives_Index.xlsx |
| 23 | 03_KOMPSAT2_MSC_L1G | KOMPSAT EULA Form_3.1.pdf | 00_Raw_Files_Archive / 02_Phase_2_Remote_Sensing_Preprocessing | PDF reader, Word/Excel register | Data license/provenance бүртгэл; usage restriction, source note, acquisition info-г Source Data README-д оруулна. | XV023222_Buduunkhad_KOMPSAT2_Data_License_Provenance_Register.xlsx; XV023222_Buduunkhad_Source_Data_Readme.docx |
| 24 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | PAN raster: PAN orthorectification, terrain correction, pan-sharpen base, high-resolution lineament/outcrop/access interpretation; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 25 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.txt | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | PAN metadata: PAN metadata extraction: acquisition, GSD, projection/source details; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 26 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.rpc | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | PAN RPC: RPC terrain correction/orthorectification support; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 27 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344PN00_1G.eph | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | PAN ephemeris: orbit/geometry support archive; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 28 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Green band: MS band alignment and RGB composite component; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 29 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.txt | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Green metadata: band metadata extraction; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 30 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.rpc | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Green RPC: MS orthorectification support; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 31 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M1N00G_1G.eph | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Green ephemeris: orbit/geometry support archive; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 32 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Blue band: MS band alignment and RGB component; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 33 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.txt | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Blue metadata: band metadata extraction; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 34 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.rpc | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Blue RPC: MS orthorectification support; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 35 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M2N00B_1G.eph | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Blue ephemeris: orbit/geometry support archive; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 36 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | NIR band: false color/NDVI/vegetation mask component; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 37 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.txt | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | NIR metadata: band metadata extraction; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 38 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.rpc | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | NIR RPC: MS orthorectification support; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 39 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M3N00N_1G.eph | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | NIR ephemeris: orbit/geometry support archive; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 40 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Red band: RGB/NDVI component, iron-stained surface visual interpretation; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 41 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.txt | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Red metadata: band metadata extraction; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 42 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.rpc | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Red RPC: MS orthorectification support; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 43 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344M4N00R_1G.eph | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | Red ephemeris: orbit/geometry support archive; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 44 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_br.jpg | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | browse image: coverage preview/catalog thumbnail only; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 45 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_br.jgw | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | browse world file: browse georeference sidecar support; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 46 | 03_KOMPSAT2_MSC_L1G | MSC_111127030410_28454_08621344N00_1G_tn.jpg | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, ILWIS 3.6.8, RPC/orthorectification workflow | thumbnail: inventory thumbnail only; PAN/MS bundle alignment, RPC/EPH/TXT metadata audit, orthorectification, band stack, true/false color and NDVI support products. | XV023222_Buduunkhad_KOMPSAT2_PAN_MS_Orthorectified_Bundle_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap_EPSG32647_v01.tif; XV023222_Buduunkhad_KOMPSAT2_NDVI_Lineament_Outcrop_Interpretation_EPSG32647_v01.gpkg; XV023222_Buduunkhad_KOMPSAT2_QAQC_Register.xlsx |
| 73 | 07_Basemap_Sentinel2_ASTER | 2005-09-05_MN_ASTER-L1B_MultispectralImagery_00409052005043503_v01_raw.hdf | 02_Phase_2_Remote_Sensing_Preprocessing | SNAP 13.0.0, ILWIS/ASTER workflow v5, QGIS/GDAL | ASTER HDF import; VNIR/SWIR/TIR band extraction where available; projection to UTM47/EPSG32647; alteration/lithology indices; score/class/binary mask separation. | XV023222_Buduunkhad_ASTER_BandStack_EPSG32647_v01.tif; XV023222_Buduunkhad_ASTER_score_porphyry_alteration_raw_v01.tif; XV023222_Buduunkhad_ASTER_porphyry_potential_class_v01.tif; XV023222_Buduunkhad_ASTER_porphyry_final_target_binary_mask_v01.tif; ASTER_QAQC_Log.xlsx |
| 74 | 07_Basemap_Sentinel2_ASTER | 2025-05-28_MN_T46TGS_GeoreferencedSatelliteRaster_v01_raw.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL, SNAP if source L1C/L2A needed | CRS/extent/band check; subset/reproject to EPSG:32647; base satellite raster QA; derivative composite support. | XV023222_Buduunkhad_20250528_T46TGS_GeoreferencedSatelliteRaster_EPSG32647_v01.tif; RemoteSensing_QAQC_Register.xlsx |
| 75 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | WGS84 basemap CRS check; reproject to EPSG:32647; visual reference layer for field route/access/outcrop interpretation. | XV023222_Buduunkhad_GoogleMaps_Basemap_RGB_2p4m_EPSG32647_v01.tif; Basemap_Overlay_QAQC_Log.xlsx |
| 76 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif | 02_Phase_2_Remote_Sensing_Preprocessing | QGIS, GDAL | EPSG:3857 high-resolution basemap reproject; tile/clip to license+buffer; use for detailed outcrop/disturbance/access interpretation. | XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_v01.tif; HighRes_Basemap_QAQC_Log.xlsx |
| 77 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_GeologicalInterpretation_RGB_B12-B08-B03_10m_UTM46N_ReceivedRaw_v01.tif | 02_Phase_2_Remote_Sensing_Preprocessing | SNAP 13.0.0, QGIS, GDAL | Sentinel-2 geology RGB B12-B08-B03 status check; UTM46N to EPSG32647 reproject; subset; lithology/structure visual interpretation support. | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_GeologicalInterpretation_RGB_B12-B08-B03_10m_EPSG32647_v01.tif; Sentinel2_Geology_RGB_QAQC_Log.xlsx |
| 78 | 07_Basemap_Sentinel2_ASTER | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_LithologyIndex_B11B12_B08B11_B04B03_10m_UTM46N_ReceivedRaw_v01.tif | 02_Phase_2_Remote_Sensing_Preprocessing | SNAP 13.0.0, QGIS, GDAL | Sentinel-2 lithology index raster QA; UTM46N to EPSG32647; mask/noise check; geology/alteration support layer, ore proof биш. | XV023222_Buduunkhad_Sentinel2_T46TGS_20250528_LithologyIndex_B11B12_B08B11_B04B03_10m_EPSG32647_v01.tif; Sentinel2_LithologyIndex_QAQC_Log.xlsx |

### Phase 3 / 03A inputs: tectonic, geology, mineral occurrence, prospectivity and metallogenic synthesis

| № | Evidence group | Exact raw input filename | Primary workflow phase | Software / program | Processing action | Expected output filename(s) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 01_Tectonic_Terrane_KMZ | Geological and Tectonic Characteristics of the Lake Terrane, Mongolia.png | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS Layout, Excel/Word evidence register | Lake Terrane-ийн геологи/тектоникийн context зураг/эх мэдээлэл-ийг source confidence-тэй бүртгэж, шаардлагатай бол georeference/overlay хийж terrane/metallogenic context болгон digitize/attribute coding хийнэ. | XV023222_Buduunkhad_Tectonic_Terrane_Context_Register.xlsx; XV023222_Buduunkhad_Tectonic_Terrane_Context_Map_EPSG32647.pdf; XV023222_Buduunkhad_Tectonic_Context_Layers.gpkg |
| 2 | 01_Tectonic_Terrane_KMZ | Mongolia_Tectonic_Terrane_Map_Project_Area_Lake_Island_Arc_Terrane.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS Layout, Excel/Word evidence register | төслийн талбай Lake island-arc terrane-тэй холбогдох regional context-ийг source confidence-тэй бүртгэж, шаардлагатай бол georeference/overlay хийж terrane/metallogenic context болгон digitize/attribute coding хийнэ. | XV023222_Buduunkhad_Tectonic_Terrane_Context_Register.xlsx; XV023222_Buduunkhad_Tectonic_Terrane_Context_Map_EPSG32647.pdf; XV023222_Buduunkhad_Tectonic_Context_Layers.gpkg |
| 3 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Central_Mongolian_Massif_and_Daagandel_Tectonic_Zone_Page11.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS Layout, Excel/Word evidence register | Даагандэлийн бүс ба Төв Монголын массивын тайлбар-ийг source confidence-тэй бүртгэж, шаардлагатай бол georeference/overlay хийж terrane/metallogenic context болгон digitize/attribute coding хийнэ. | XV023222_Buduunkhad_Tectonic_Terrane_Context_Register.xlsx; XV023222_Buduunkhad_Tectonic_Terrane_Context_Map_EPSG32647.pdf; XV023222_Buduunkhad_Tectonic_Context_Layers.gpkg |
| 4 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part1_Page08.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS Layout, Excel/Word evidence register | Нуурын аккрецийн мегабүсийн тайлбар-ийг source confidence-тэй бүртгэж, шаардлагатай бол georeference/overlay хийж terrane/metallogenic context болгон digitize/attribute coding хийнэ. | XV023222_Buduunkhad_Tectonic_Terrane_Context_Register.xlsx; XV023222_Buduunkhad_Tectonic_Terrane_Context_Map_EPSG32647.pdf; XV023222_Buduunkhad_Tectonic_Context_Layers.gpkg |
| 5 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part2_Page09.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS Layout, Excel/Word evidence register | Хурайн/Баатархайрхан/Улааншандын бүсийн тайлбар-ийг source confidence-тэй бүртгэж, шаардлагатай бол georeference/overlay хийж terrane/metallogenic context болгон digitize/attribute coding хийнэ. | XV023222_Buduunkhad_Tectonic_Terrane_Context_Register.xlsx; XV023222_Buduunkhad_Tectonic_Terrane_Context_Map_EPSG32647.pdf; XV023222_Buduunkhad_Tectonic_Context_Layers.gpkg |
| 6 | 01_Tectonic_Terrane_KMZ | MUGZ500_Geomed2013_Explanatory_Text_Nuur_Accretionary_Megazone_Part3_Page10.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS Layout, Excel/Word evidence register | Ханхөхий/Хантайширийн бүсийн тайлбар-ийг source confidence-тэй бүртгэж, шаардлагатай бол georeference/overlay хийж terrane/metallogenic context болгон digitize/attribute coding хийнэ. | XV023222_Buduunkhad_Tectonic_Terrane_Context_Register.xlsx; XV023222_Buduunkhad_Tectonic_Terrane_Context_Map_EPSG32647.pdf; XV023222_Buduunkhad_Tectonic_Context_Layers.gpkg |
| 7 | 01_Tectonic_Terrane_KMZ | Regional_Tectonic_Subdivision_Map_of_Mongolia_Tumurtogoo_2017_Buduunkhad_Project_in_Ulaanshand_Zone.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS Layout, Excel/Word evidence register | Улааншандын бүсийн regional tectonic context-ийг source confidence-тэй бүртгэж, шаардлагатай бол georeference/overlay хийж terrane/metallogenic context болгон digitize/attribute coding хийнэ. | XV023222_Buduunkhad_Tectonic_Terrane_Context_Register.xlsx; XV023222_Buduunkhad_Tectonic_Terrane_Context_Map_EPSG32647.pdf; XV023222_Buduunkhad_Tectonic_Context_Layers.gpkg |
| 53 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_1-200000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference; regional geology unit/fault/intrusive/contact vectorization; scale flag = regional. | XV023222_Buduunkhad_1987_L47-XIX_GeologicalMap_1-200K_Georeferenced_EPSG32647_v01.tif; geology_units_200k_polygons/structures_faults_lines_EPSG32647_v01.gpkg |
| 54 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_Legend_1-200000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS/Image viewer, Excel lookup | Regional geology legend dictionary; lithology/age/intrusive/structure domain values. | XV023222_Buduunkhad_1987_GeologicalMap_Legend_Symbol_Dictionary_v01.xlsx |
| 55 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_1-50000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference; detailed lithology, intrusive, contact, fault, vein, alteration/section digitizing; target-scale geology layer. | XV023222_Buduunkhad_2013_L47-74-A_GeologicalMap_1-50K_Georeferenced_EPSG32647_v01.tif; geology_units_50k_polygons/structures_faults_lines/intrusive_contacts_lines/dyke_vein_lines_EPSG32647_v01.gpkg |
| 56 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_Legend_1-50000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS/Image viewer, Excel lookup | Detailed geology legend dictionary; stratigraphic_unit, vein_type, alteration, lithology domains. | XV023222_Buduunkhad_2013_GeologicalMap_Legend_Symbol_Dictionary_v01.xlsx |
| 57 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_1-200000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference; regional occurrence/resource/anomaly/ore field digitizing; commodity coding. | XV023222_Buduunkhad_1987_L47-XIX_MineralResourcesMap_1-200K_Georeferenced_EPSG32647_v01.tif; mineral_occurrences_points/mineralized_zones_polygons/ore_field_prospect_polygons_EPSG32647_v01.gpkg |
| 58 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_Legend_1-200000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS/Image viewer, Excel lookup | Mineral resources legend dictionary; commodity, occurrence type, ore field type domains. | XV023222_Buduunkhad_1987_MineralResources_Legend_Symbol_Dictionary_v01.xlsx |
| 59 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MineralDistributionPatternMap_1-100000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference; ore district/node/mineral distribution context digitizing; Phase 3 deposit model context. | XV023222_Buduunkhad_2013_L47-73-74_MineralDistributionPatternMap_1-100K_Georeferenced_EPSG32647_v01.tif; ore_district_node_context_EPSG32647_v01.gpkg |
| 60 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_MineralOccurrenceMap_1-50000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference; Au-Cu/Cu/Mo/As/Zn occurrence points and target features digitizing; relation to geology/source materials. | XV023222_Buduunkhad_2013_L47-74-A_MineralOccurrenceMap_1-50K_Georeferenced_EPSG32647_v01.tif; mineral_occurrences_points_EPSG32647_v01.gpkg; XV023222_Buduunkhad_Mineral_Occurrences_Register.xlsx |
| 61 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MetallogenicSchemeAndMetallogenogram_1-400000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Regional metallogenic scheme georeference/context digitizing; ore formation and age/element relation register. | XV023222_Buduunkhad_2013_MetallogenicSchemeMetallogenogram_1-400K_Georeferenced_EPSG32647_v01.tif; metallogenic_context_layers_EPSG32647_v01.gpkg |
| 62 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessment_ReportExcerpt_B3-TolKhar_v01_raw-photo.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | Image/PDF viewer, Word/Excel evidence register | Report excerpt transcription/summary; B-2/B-3/B-4 area evidence, limitation, recommended follow-up coding. | XV023222_Buduunkhad_2013_Prospectivity_ReportExcerpt_Evidence_Register_v01.xlsx; report_evidence_summary_for_Preliminary_Deposit_Model.docx |
| 63 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessmentMap_1-50000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference; Б-3 Толь хяр, Г-1 and other prospectivity polygons digitizing; priority and evidence_basis attributes. | XV023222_Buduunkhad_2013_L47-74-A_ProspectivityAssessmentMap_1-50K_Georeferenced_EPSG32647_v01.tif; prospectivity_target_zones_polygons_EPSG32647_v01.gpkg; XV023222_Buduunkhad_Prospectivity_Target_Register.xlsx |
| 64 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_1-50000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference; route, observation, sample, trench/pit/shaft/channel, section line digitizing for QField/field validation. | XV023222_Buduunkhad_2013_L47-74-A_SourceMaterialsMap_1-50K_Georeferenced_EPSG32647_v01.tif; source_material_observation_points/source_material_route_lines/source_material_trench_pit_points_EPSG32647_v01.gpkg |
| 65 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_Legend_1-50000_v01_raw-scan.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS/Image viewer, Excel lookup | Source materials legend dictionary; observation_type, sample_type, work_type domains; QField form lookup. | XV023222_Buduunkhad_SourceMaterials_Legend_Symbol_Dictionary_v01.xlsx; QField_Lookups_Domains.xlsx |
| 66 | 05_Geology_Mineral_Prospectivity | 2013_MN_L47-XIX_GoldOccurrenceDescriptions_XIX-74-A_4186_v01_raw.docx | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | Microsoft Word/LibreOffice, Excel, QGIS | Gold occurrence descriptions extraction; coordinates/grade/lithology/structure; occurrence register and model evidence coding. | XV023222_Buduunkhad_4186_GoldOccurrence_Descriptions_Extracted_Register_v01.xlsx; XV023222_Buduunkhad_4186_GoldOccurrence_Points_EPSG32647_v01.gpkg; preliminary_deposit_model_evidence_table.xlsx |
| 67 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MineralOccurrenceAndMineralizedPointRegister_7255_v01_raw-scan.pdf | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | PDF reader, Excel, QGIS | PDF register extraction; occurrence/mineralized point attributes; coordinate validation and cross-reference with map 60/68. | XV023222_Buduunkhad_7255_MineralOccurrence_MineralizedPoint_Register_Extracted_v01.xlsx; XV023222_Buduunkhad_7255_MineralizedPoint_Layers_EPSG32647_v01.gpkg; extraction_QAQC_log.xlsx |
| 68 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_MineralizedPointRegister_7255_v01_raw-table.xlsx | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | Excel/LibreOffice Calc, QGIS | XLSX table cleaning; coordinate conversion; element/commodity standardization; GIS point layer and deposit model evidence. | XV023222_Buduunkhad_7255_MineralizedPoint_Clean_Register_v01.xlsx; XV023222_Buduunkhad_7255_MineralizedPoint_Points_EPSG32647_v01.gpkg; XV023222_Buduunkhad_Occurrence_CrossReference_7255_4186.xlsx |
| 69 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_Legend_RawScan_2020_v01.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS/Image viewer, Excel lookup | 1:500k metallogenic legend symbol dictionary; ore formation/commodity/metallogenic unit domains. | XV023222_Buduunkhad_L47B_RegionalMetallogenic_Legend_Dictionary_v01.xlsx |
| 70 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_RawScan_2020_v01.jpg | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | QGIS Georeferencer, QGIS digitizing | Georeference/context overlay; metallogenic belt/zone/ore district/node digitizing; context_only flag. | XV023222_Buduunkhad_2020_L47B_Talshand_RegionalMetallogenicMap_1-500K_Georeferenced_EPSG32647_v01.tif; metallogenic_zones_polygons_EPSG32647_v01.gpkg; regional_metallogenic_context_map.pdf |
| 71 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book01_ProjectBook13_1M500K_RawScan_2021_v01.pdf | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | PDF reader, Word/Excel evidence register | Regional report text/table extraction; ore formation/metallogenic context notes for deposit model. | XV023222_Buduunkhad_RegionalMetallogenic_Report_Book01_Evidence_Register_v01.xlsx; metallogenic_context_summary.docx |
| 72 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book04_ProjectBook16_1M500K_RawScan_2021_v01.pdf | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 03A | PDF reader, Word/Excel evidence register | Regional report text/table extraction; cross-reference with map 70/71; context evidence and limitations. | XV023222_Buduunkhad_RegionalMetallogenic_Report_Book04_Evidence_Register_v01.xlsx; metallogenic_context_cross_reference.xlsx |

### Phase 6 and Phase 8 field/historical geochemistry inputs

| № | Evidence group | Exact raw input filename | Primary workflow phase | Software / program | Processing action | Expected output filename(s) |
| --- | --- | --- | --- | --- | --- | --- |
| 47 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_1-200000_v01_raw-scan.jpg | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | QGIS Georeferencer, QGIS digitizing, DEM drainage analysis | Georeference; heavy mineral sample/anomaly/indicator contour digitizing; DEM drainage catchment overlay; upstream source check planning. | XV023222_Buduunkhad_1987_L47-XIX_HeavyMineralSamplingResultsMap_1-200K_Georeferenced_EPSG32647_v01.tif; XV023222_Buduunkhad_HeavyMineral_Anomaly_Layers_EPSG32647_v01.gpkg; XV023222_Buduunkhad_HeavyMineral_FollowUp_Plan.xlsx/pdf |
| 48 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | QGIS/Image viewer, Excel lookup table | Legend symbol dictionary үүсгэх; mineral_indicator/anomaly_class/sample_symbol domain values; main map digitizing attribute control. | XV023222_Buduunkhad_HeavyMineral_Symbol_Dictionary_v01.xlsx; QGIS lookup/domain table in gpkg |
| 49 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | QGIS/Image viewer, Excel lookup table | Stream sediment legend dictionary; element suite/anomaly level/contour type domain; map interpretation QA. | XV023222_Buduunkhad_StreamSediment_Symbol_Dictionary_v01.xlsx; QGIS lookup/domain table in gpkg |
| 50 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Polyelement_1-200000_v01_raw-scan.jpg | 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check | QGIS Georeferencer, QGIS digitizing, DEM drainage analysis | Georeference; Cu-Pb-Zn-Ag-As-Bi-W-Sn-Mo-Mn-Ba-F anomaly contour/vector digitizing; drainage source direction and orientation sampling plan. | XV023222_Buduunkhad_1987_L47-XIX_StreamSedimentPolyelementMap_1-200K_Georeferenced_EPSG32647_v01.tif; XV023222_Buduunkhad_StreamSediment_Anomaly_Layers_EPSG32647_v01.gpkg; XV023222_Buduunkhad_StreamSediment_FollowUp_Plan.xlsx/pdf |
| 51 | 04_HeavyMineral_StreamSediment_Field | 2011_MN_Namalzakh_L47-74-A_FieldRouteNotebook_Routes14-15_Obs1076-1090_1-50000_v01_raw-scan.pdf | 06_Phase_6_Recon_Mapping_and_Portable_XRF_Field_Screening / 08_Phase_8 | PDF reader, QGIS, Excel register | Route 14-15 and observations 1076-1090 extraction; coordinates/route/sketch/observation attributes; QField recon and sampling planning. | XV023222_Buduunkhad_2011_FieldRouteNotebook_Routes14-15_Observation_Register_v01.xlsx; XV023222_Buduunkhad_Field_Route_Observation_Layers_EPSG32647_v01.gpkg; XV023222_Buduunkhad_QField_Recon_Input_Package_v01 |
| 52 | 04_HeavyMineral_StreamSediment_Field | XV023222_Buduunkhad_Report7255_FieldObservation_StationDescription_Table_WGS84_LegacyRaw_v01.pdf | 06_Phase_6_Recon_Mapping_and_Portable_XRF_Field_Screening / 03_Phase_3 | PDF reader, Excel, QGIS | Station description table extraction; WGS84 coordinates validation; lithology/structure/mineralization attribute coding; Master GIS observation layer. | XV023222_Buduunkhad_Report7255_FieldObservation_Station_Register_v01.xlsx; XV023222_Buduunkhad_Report7255_FieldObservation_Points_EPSG32647_v01.gpkg; XV023222_Buduunkhad_FieldObservation_QAQC_Log.xlsx |

Тайлбар. Phase 4-11 нь raw file-г шууд дахин боловсруулахаас илүүтэй Phase 1-3/03A болон Phase 8-аас гарсан QA/QC хийгдсэн derivative output-уудыг ашиглана. Гэсэн ч тэдгээр derivative output бүрийн эх raw input №-г дээрх matrix-д хадгалсан тул final target sheet, sample register, drill plan бүрт source_raw_input_no/source_file/source_phase талбаруудыг заавал үлдээнэ.
## 1B.3 Required source-traceability fields for every output

| Output field | Required value | Purpose |
| --- | --- | --- |
| source_raw_input_no | 1-78 дугаар | Output бүрийг аль raw input-оос үүссэнтэй audit trail-аар холбох |
| source_raw_filename | Exact raw filename | Файлын нэр өөрчлөгдөх/холилдох эрсдэлийг хаах |
| processing_phase | 00/01/02/03/03A/04... | Аль workflow шатанд боловсруулсан болохыг тодруулах |
| processing_software | QGIS / SNAP / GDAL / Excel / QField / etc. | Дахин боловсруулахад reproducibility хангах |
| processing_action | Georeference / reproject / digitize / extract / score / QAQC | Юу хийснийг тодорхой бичих |
| output_filename | Standardized output file name | Deliverable package-д нэг мөр нэршилтэй хадгалах |
| qaqc_status | Draft / Checked / Approved / Rejected | Decision-grade биш output-г буруу ашиглахаас хамгаалах |
| validation_status | Historical only / Field checked / Sampled / Lab confirmed | Historical evidence ба баталгаажсан evidence-г салгах |

# v6 implementation note
Энэ v6 хувилбар нь 78 raw input file бүрийг phase-wise байдлаар exact filename, software, processing action, expected output filename-тай холбосон тул цаашид QGIS/Excel/QField/Drone/Lab workflow-д source-traceability хадгалахад ашиглана. Бүх output нь preliminary/support evidence бөгөөд field validation, laboratory assay, QA/QC review хийгдэх хүртэл mineralization proof эсвэл resource/reserve estimate биш.

# 2. Integrated 00-99 phase workflow
00_Raw_Files_Archive
  -> 01_Phase_1_Data_Audit_and_Master_GIS_Setup
  -> 02_Phase_2_Remote_Sensing_Preprocessing
  -> 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis
  -> 04_Phase_4_Preliminary_Prospect_Delineation_and_Ranking
  -> 05_Phase_5_DJI_Matrice_400_Drone_LiDAR_Photogrammetry_Survey
  -> 06_Phase_6_Recon_Mapping_and_Portable_XRF_Field_Screening
  -> 07_Phase_7_Rock_Chip_Channel_and_Verification_Sampling
  -> 08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check
  -> 09_Phase_9_Systematic_Soil_Grid_and_Laboratory_QAQC
  -> 10_Phase_10_Integrated_Interpretation_and_Final_Target_Ranking
  -> 11_Phase_11_Follow_Up_Trench_Geophysics_and_Scout_Drill_Planning
  -> 99_Final_Deliverables
# 00. Raw Files Archive

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Raw data-г өөрчлөхгүй архивлах, integrity/metadata/source хяналт тогтоох. |
| Input files | Direct raw input files: №1-78 бүх raw input file. Яг filename, evidence group, primary phase, methodology action-ийг Section 1A-д бүрэн заасан. Sidecar files (.tfw, .aux.xml, .ovr, .rpc, .eph, .txt) parent raster/image-ээс салгахгүй. |
| Software / equipment | File system, checksum utility, inventory workbook. |

## Processing folder structure
00_Raw_Files_Archive/
├── 01_Tectonic_Terrane_KMZ
├── 02_DEM_ALOS_ASTERGDEM
├── 03_KOMPSAT2_MSC_L1G
├── 04_HeavyMineral_StreamSediment_Field
├── 05_Geology_Mineral_Prospectivity
├── 06_Regional_Metallogenic_L47B
└── 07_Basemap_Sentinel2_ASTER
## Step-by-step methodology
- 78 raw input файлыг evidence group-ийн дагуу raw archive хавтас руу байршуулна.
- Original filename, standardized filename, file type, source note, owner/responsible person, read status, processing copy status бүртгэнэ.
- SHA-256 checksum үүсгэж integrity log-д бичнэ.
- Sidecar файлуудыг parent file-аас салгахгүй: .tfw/.aux.xml/.ovr/.rpc/.eph/.txt metadata нь тухайн raster/image bundle-ийн хэсэг.
- Raw file дээр rename/overwrite/clip/reproject хийхгүй; working copy-г дараагийн phase-д хуулна.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Checksum match | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Raw overwrite хийгдээгүй | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Sidecar completeness | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Source note and owner registered | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_78Input_Master_Inventory.xlsx
- XV-023222_Buduunkhad_Raw_Data_Integrity_Log.xlsx
- XV-023222_Buduunkhad_Source_Data_Readme.docx
- SHA-256_Checksum_Register.csv
## Decision gate / next phase condition
- All files archived, checksum complete, processing copies available.
# 01. Phase 1 — Data Audit and Master GIS Setup

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | 78 input file-ийг GIS-ready болгох, EPSG:32647 master database үүсгэх. |
| Input files | Direct raw input files: №1-78 бүх raw input file. Үүнээс №8 license boundary нь master boundary layer; №9-78 raster/scan/table/PDF/DOCX бүрийн metadata, CRS, sidecar, confidence, working-copy status шалгана. Section 1A-г primary input checklist болгон ашиглана. |
| Software / equipment | QGIS, GeoPackage, spreadsheet register. |

## Processing folder structure
01_Phase_1_Data_Audit_and_Master_GIS_Setup/
├── 01_File_Inventory
├── 02_Metadata_Check
├── 03_CRS_Check
├── 04_Raster_Scan_Georeference_QAQC
├── 05_KMZ_KML_to_GPKG
├── 06_Master_GeoPackage_Schema
├── 07_Data_Confidence_Ranking
└── 08_Master_QGIS_Project_Setup
## Step-by-step methodology
- QGIS project үүсгэнэ: XV-023222_Buduunkhad_Master_QGIS_Project.qgz.
- Project CRS-г WGS 84 / UTM Zone 47N, EPSG:32647 болгож тохируулна.
- MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz-г import хийж GeoPackage layer болгон хадгална.
- Raster бүрийн CRS, resolution, extent, NoData, band count, pixel alignment, sidecar availability-г шалгана.
- Scan map бүрт georeference QA/QC: GCP count, residual, map scale, grid/tick consistency, reviewer/date/decision бүртгэнэ.
- Master GeoPackage schema үүсгэнэ: license_boundary, geology_units_polygon, faults_structures_line, intrusive_contacts_line, mineral_occurrences_point, stream_sediment_anomaly_polygon, heavy_mineral_anomaly_polygon, lineament_interpretation_line, preliminary_prospect_polygon, target_polygon, field_observation_point, sample_point, pXRF_reading_table.
- Data confidence ranking: High / Medium / Low / Needs verification өгнө.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| EPSG:32647 project CRS | Recorded in phase QA/QC log; reviewer/date/decision required. |
| KMZ boundary topology valid | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Raster CRS/resolution/extent/nodata/band count checked | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Scan georeference residual and confidence logged | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Master GPKG schema created | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Master_GIS_Database.gpkg
- XV-023222_Buduunkhad_Master_QGIS_Project.qgz
- XV-023222_Buduunkhad_CRS_Georeference_QAQC_Log.xlsx
- XV-023222_Buduunkhad_Data_Confidence_Ranking.xlsx
## Decision gate / next phase condition
- Master GIS project opens without missing layers; critical data confidence recorded.
Нэмэлт дэд аргачлал: Historical scanned map файлуудыг QGIS дээр inventory -> georeference -> vector digitizing -> register -> QA/QC -> confidence ranking -> Master GIS handover дарааллаар боловсруулах нарийвчилсан SOP-ийг энэ баримт бичгийн Appendix E хэсэгт бүрэн оруулав. Энэ дэд аргачлал нь Phase 1 Data Audit, Phase 3 Geological/Metallogenic Synthesis, Phase 4 Prospect Ranking, Phase 6 Recon Mapping, Phase 7 Sampling, Phase 8/9 Soil/Stream/Heavy Mineral planning-д шууд handover хийх зориулалттай.
# 02. Phase 2 — Remote Sensing Preprocessing

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Sentinel, ASTER, KOMPSAT, DEM өгөгдлийг QA/QC-тэй interpretation-ready support layer болгох. |
| Input files | Direct raw input files: №9-22 DEM/ALOS/ASTERGDEM; №23-46 KOMPSAT-2 PAN/MS/RPC/EPH/metadata/browse; №73 ASTER HDF; №74-78 Sentinel/Google/basemap rasters. Exact filename бүрийг Section 1A болон Section 1 register-ээс авна. |
| Software / equipment | SNAP 13.0.0, ASTER workflow v5/ILWIS, ILWIS 3.6.8 or QGIS, Global Mapper 24.0/QGIS. |

## Processing folder structure
02_Phase_2_Remote_Sensing_Preprocessing/
├── 01_Sentinel2_SNAP13
├── 02_ASTER_Workflow_v5
├── 03_KOMPSAT2_ILWIS368_QGIS
├── 04_ALOS_ASTERGDEM_GlobalMapper_QGIS
├── 05_RemoteSensing_QAQC
└── 06_Export_EPSG32647
## Step-by-step methodology
- Sentinel-2 raw/received raster status шалгана; L1C бол SNAP 13.0.0 Sen2Cor ашиглан L2A болгоно; received derivative бол metadata-г бүртгэнэ.
- Subset: license boundary + 500 m эсвэл 1 km buffer.
- Resample: all relevant bands to 10 m grid; pixel alignment шалгана.
- Cloud/shadow/snow/water/vegetation mask үүсгэж alteration/lithology interpretation-д noise орохоос сэргийлнэ.
- Sentinel RGB/index: Natural RGB, SWIR-NIR-Red, geology composite, lithology ratio/index, NDVI, NDWI, iron oxide, ferric, clay/SWIR, ferrous, brightness index.
- ASTER workflow v5: HDF import, band extraction, UTM47 project grid, b*_project band-аас index тооцох; haze/edge filter-ийг ratio calculation-д ашиглахгүй.
- ASTER outputs тусад нь хадгална: raw Float32 score, 1/2/3 class, 0/1 binary mask.
- KOMPSAT-2: PAN/MS, RPC, EPH, TXT metadata-г хамт хадгалж orthorectification/band alignment/pan-sharpen/NDVI/lineament-outcrop basemap гаргана.
- ALOS-PALSAR/ASTER GDEM: hillshade, slope, aspect, contour, drainage, watershed, terrain ruggedness, curvature, access/safety derivatives гаргана.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Cloud/shadow/vegetation mask applied where relevant | Recorded in phase QA/QC log; reviewer/date/decision required. |
| ASTER raw score/class/binary mask separated | Recorded in phase QA/QC log; reviewer/date/decision required. |
| KOMPSAT PAN/MS alignment checked | Recorded in phase QA/QC log; reviewer/date/decision required. |
| DEM derivatives visually and spatially checked | Recorded in phase QA/QC log; reviewer/date/decision required. |
| No remote sensing output treated as ore proof | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Sentinel2_Processed_Products.tif/gpkg
- XV-023222_Buduunkhad_ASTER_score_porphyry_alteration_raw_v1.tif
- XV-023222_Buduunkhad_ASTER_porphyry_potential_class_v1.tif
- XV-023222_Buduunkhad_ASTER_porphyry_final_target_binary_mask_v1.tif
- XV-023222_Buduunkhad_KOMPSAT2_Pansharpened_Orthobasemap.tif
- XV-023222_Buduunkhad_Terrain_Derivatives.gpkg
- XV-023222_Buduunkhad_RemoteSensing_QAQC_Report.docx
## Decision gate / next phase condition
- Remote sensing derivatives passed QA/QC and are ready as support evidence only.
# 03. Phase 3 — Geological, Metallogenic and CMCS Synthesis
### Purpose and scope
Энэ өргөтгөсөн Phase 3 аргачлал нь Бүдүүн хад / XV-023222 / L23222 талбайн tectonic, geology, mineral occurrence, prospectivity, source material, metallogenic context болон CMCS/MRPAM орд-илрэлийн мэдээллийг нэг Master GIS evidence base болгон нэгтгэх нарийвчилсан SOP юм.
Phase 3 нь хүдэржилт батлах, нөөц/баялаг тогтоох шат биш. Энэ шатны бүх output нь Historical only / Contextual support / Preliminary interpretation статустай байна. Field validation, laboratory assay, structural/geological confirmation болон шаардлагатай бол trench/geophysics/scout drilling хийгдэх хүртэл decision-grade evidence гэж үзэхгүй.
### 03.1 Phase 3 input control
Phase 3-д input-ийг “geology files” гэх мэт ерөнхий нэрээр бичихгүй. Доорх raw input № болон exact filename-ийг output бүрийн source traceability талбарт заавал хадгална.

| Raw input № | Exact input group / file use | Phase 3 use | Mandatory limitation flag |
| --- | --- | --- | --- |
| №1-7 | Tectonic / terrane context images and explanatory pages | Lake Terrane, Ulaanshand Zone, Nuur Accretionary Megazone and regional tectonic setting | Regional context only; not local target proof |
| №8 | MN_BuduunKhad_L23222_LicenseBoundary_WGS84_v01_raw.kmz | Overlay, clipping, 5 km / 10 km / 20 km / 25 km buffer and CMCS/MRPAM search boundary | Boundary topology and CRS must be checked |
| №53-56 | 1:200k and 1:50k geological map and legends | Lithology, stratigraphy, intrusive/contact, fault, vein, alteration and structural control | Scale limitation and georeference residual required |
| №57-58 | Mineral resources map and legend | Regional occurrence, ore field, anomaly and commodity context | Regional evidence only |
| №59-61 | Mineral distribution pattern, metallogenic scheme and metallogenogram | Ore district/node, ore formation, age and commodity association | Context layer; not target boundary |
| №62-65 | Prospectivity assessment, prospectivity map, source material map and legends | B-3 Tol Khar, G-1 and other prospectivity zones; routes, stations, samples, trenches/pits/sections | Historical only until field checked |
| №66-68 | Gold occurrence description, mineral occurrence/mineralized point register and XLSX table | Occurrence database, coordinate validation, commodity/lithology/structure attributes | Coordinate confidence and duplicate check required |
| №69-72 | Regional metallogenic map, legend and report books | 1:500k metallogenic belt, ore formation, regional commodity context | Cannot be used as local ore proof |
| Phase 2 outputs | Sentinel / ASTER / KOMPSAT / DEM derivative products | Alteration, lithology contrast, lineament, exposure, drainage and access support | Support evidence only; ore proof биш |

### 03.2 Working folder structure
03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis/
├── 01_Input_Working_Copy
├── 02_Tectonic_Terrane_Context
├── 03_Regional_Metallogenic_1M500K
├── 04_Regional_Geology_Mineral_1M200K
├── 05_Local_Geology_Occurrence_1M50K
├── 06_Source_Materials_and_Prospectivity
├── 07_Occurrence_Register_and_Coordinate_QAQC
├── 08_CMCS_MRPAM_Buffer_Check_5km_10km_20km_25km
├── 09_Geological_Evidence_Layers_GPKG
├── 10_Preliminary_Deposit_Model_03A
├── 11_Evidence_Scoring_and_DataGap
└── 12_Phase3_QAQC_and_Handover
### 03.3 Pre-start readiness check

| Readiness item | Acceptance requirement | Output / register to check |
| --- | --- | --- |
| Master QGIS project | Project CRS = WGS 84 / UTM Zone 47N, EPSG:32647; no critical missing layers | XV-023222_Buduunkhad_Master_QGIS_Project.qgz |
| License boundary | №8 boundary imported, topology checked, area/perimeter recorded, EPSG:32647 version available | LicenseBoundary_EPSG32647.gpkg and QA/QC register |
| Scan georeference QA/QC | GCP count, residual, map scale, grid/tick consistency and reviewer/date/decision recorded | CRS_Georeference_QAQC_Log.xlsx |
| Remote sensing support outputs | Sentinel/ASTER/KOMPSAT/DEM products are clipped/reprojected and marked support evidence only | RemoteSensing_QAQC_Report.docx |
| Data confidence ranking | Each raw and derived input has High / Medium / Low / Needs verification status | Data_Confidence_Ranking.xlsx |

### 03.4 Step-by-step methodology
#### Step 1 — Create Phase 3 working copy and source traceability register
1. Copy Phase 3 raw inputs №1-7, №53-72 and boundary №8 from 00_Raw_Files_Archive to 03/01_Input_Working_Copy. Do not edit the raw archive.
2. Create a Phase3_Source_Traceability_Register with source_raw_input_no, source_raw_filename, source_group, processing_phase, processing_software, processing_action, confidence, limitation, validation_status and output_filename.
3. Set validation_status = Historical only for all scanned historical map-derived layers until field/lab confirmation is available.
#### Step 2 — Build tectonic and terrane context package from №1-7
1. Register Lake Terrane, Lake island arc terrane, Ulaanshand Zone, Nuur Accretionary Megazone and related regional tectonic context.
2. If a map has recognizable grid/ticks, georeference in QGIS; otherwise record as non-spatial narrative context.
3. Digitize only defensible regional polygons/lines and mark them as context_only = Yes.
#### Step 3 — Process 1:500,000 regional metallogenic context from №69-72
1. Create ore formation / commodity / metallogenic belt symbol dictionary from №69.
2. Georeference №70 where possible; overlay with license boundary and 5 km / 10 km / 20 km buffers.
3. Extract relevant ore formation and regional context notes from №71-72 and cross-reference them with the georeferenced map.
4. Record source_scale = 1:500,000 and limitation = Regional context only.
#### Step 4 — Process 1:200,000 regional geology and mineral resources from №53-58
1. Georeference №53 geological map and digitize regional geology units, faults/structures, intrusive/contact lines and major lithological packages.
2. Create lithology/age/intrusive/structure lookup tables from №54.
3. Georeference №57 mineral resources map and digitize mineral occurrence, mineralized zone, ore field/prospect and anomaly features.
4. Create commodity/occurrence/anomaly symbol dictionary from №58.
#### Step 5 — Process 1:50,000 local geology, occurrence and prospectivity from №55-65
1. Georeference №55 and digitize local geology units, detailed structures, faults, contacts, veins/dykes, alteration and section lines.
2. Use №56 to build stratigraphic_unit, lithology, intrusive, alteration, vein_type and structure domain values.
3. Georeference №60 and digitize Au-Cu, Cu, Mo, As, Zn and related occurrence points/features.
4. Georeference №63 and digitize B-3 Tol Khar, G-1 and other prospectivity target polygons with evidence_basis and priority attributes.
5. Georeference №64 and digitize route lines, observation points, sample points, trench/pit/shaft/channel and section features; use №65 as domain dictionary.
#### Step 6 — Extract and QA/QC occurrence registers from №66-68
1. Extract coordinates, grades, commodities, lithology, structure, alteration and notes from №66.
2. Extract and clean scanned PDF table/register content from №67; link occurrences to source pages where possible.
3. Clean XLSX fields from №68; standardize element and commodity names; convert coordinates to EPSG:32647.
4. Cross-check map-derived occurrence points from №60 against text/table-derived points from №66-68; flag duplicates and uncertain coordinates.
## Step 7 — CMCS/MRPAM 5 km / 10 km / 20 km / 25 km contextual check
1. Create 5 km, 10 km, 20 km and 25 km buffers from the checked license boundary. Use 25 km as the all-near-occurrence coverage buffer when 20 km does not include the full BH_near_min_occurrences dataset.
2. Query or compile nearest deposits, occurrences, mineralized points, commodity, deposit type, direction and distance from CMCS/MRPAM or equivalent official register.
3. Create CMCS_Nearest_Deposit_Register and map. Add limitation: Context only — not proof of mineralization inside license.
## Step 7A — 25 km near-occurrence coverage buffer for all nearby mineral occurrences
Rationale. During the spatial check of the BH_near_min_occurrences point layer, the 20 km buffer did not include all near-occurrence points, while the 25 km buffer included the full nearby occurrence dataset. Therefore, the 25 km buffer shall be retained as an additional coverage buffer for regional occurrence context analysis.
Important limitation. The 25 km buffer is not a mineralization proof boundary and must not be treated as evidence that mineralization occurs inside the XV-023222 / L23222 license. It is only a regional context and occurrence-coverage tool for screening analogue mineral systems, commodity associations, metallogenic setting, and follow-up prioritization.
### QGIS method for 25 km buffer creation
- Use the checked license boundary layer in EPSG:32647. Do not create a metric buffer from EPSG:4326 latitude/longitude geometry.
- Run Vector -> Geoprocessing Tools -> Buffer.
- Input layer: license_boundary_EPSG32647.
- Distance: 25000 meters; Segments: 30; Dissolve result: checked.
- Save output as XV023222_Buduunkhad_L23222_Buffer_25km_EPSG32647.gpkg with layer name license_boundary_buffer_25km.
- Use Select by Location to confirm that BH_near_min_occurrences points intersect or are within license_boundary_buffer_25km.
- Export selected points as BH_near_mineral_occurrences_within_25km_EPSG32647.gpkg and retain source_raw_input_no/source_raw_filename or occurrence register references where available.
### Recommended buffer interpretation hierarchy
- 5 km buffer: immediate license-margin context and high-priority near-boundary check.
- 10 km buffer: local exploration context and short-range analogue occurrence check.
- 20 km buffer: standard regional context check used for CMCS/MRPAM nearest deposits and occurrences.
- 25 km buffer: all-near-occurrence coverage buffer for this dataset because it captures all nearby mineral occurrence points that were not fully covered by the 20 km buffer.
### Additional expected outputs from Step 7A
- XV023222_Buduunkhad_L23222_Buffer_25km_EPSG32647.gpkg
- BH_near_mineral_occurrences_within_25km_EPSG32647.gpkg
- XV023222_Buduunkhad_25km_Near_Occurrence_Coverage_Check_Register_v01.xlsx
- XV023222_Buduunkhad_25km_Near_Occurrence_Context_Map_v01.pdf
## Step 8 — Integrate all Phase 3 evidence into one GeoPackage
1. Merge cleaned layers into XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg.
2. Every layer must carry source_raw_input_no, source_raw_filename, source_scale, evidence_type, validation_status, confidence and limitation.
3. Apply consistent symbology and layer naming so Phase 4 and Phase 10 can use the package without re-processing raw scans.
#### Step 9 — Prepare Preliminary Deposit Model handover to 03A
1. Summarize host geology, intrusive/contact, structure, occurrence, geochemistry, metallogenic context and remote sensing support by candidate model.
2. Prepare supporting_evidence / missing_evidence / recommended_validation_work table for Au-Cu hydrothermal vein, intrusion-related Cu-Au-Mo, skarn/contact metasomatic, polymetallic vein, VMS possibility and heavy mineral/placer indicator.
3. Calculate preliminary evidence score and data-gap priority using the 100-point model matrix in 03A.
#### Step 10 — Prepare Phase 3 QA/QC and handover package
1. Review georeference residuals, scale limitations, coordinate confidence, duplicate occurrences, CMCS limitation and support-evidence flags.
2. Export final Phase 3 maps, registers, GPKG and QA/QC log.
3. Handover to Phase 4 only after source traceability and validation_status fields are complete.
### 03.5 Expected output package

| Output file / layer | Purpose | Required source-traceability fields |
| --- | --- | --- |
| XV023222_Buduunkhad_Tectonic_Terrane_Context_Register_v01.xlsx | Terrane / tectonic narrative and source confidence register | source_raw_input_no, source_raw_filename, confidence, limitation |
| XV023222_Buduunkhad_Tectonic_Context_Layers_v01.gpkg | Regional terrane and tectonic context layers | context_only, source_scale, validation_status |
| XV023222_Buduunkhad_RegionalMetallogenic_Context_Map_v01.pdf | 1:500k metallogenic context layout | source_raw_input_no, source_scale, limitation |
| XV023222_Buduunkhad_RegionalMetallogenic_Evidence_Register_v01.xlsx | Metallogenic report/map extracted evidence | report_book, page_ref, evidence_summary, limitation |
| geology_units_200k_polygons_EPSG32647_v01.gpkg | Regional geology units | source_scale, lithology_code, confidence |
| geology_units_50k_polygons_EPSG32647_v01.gpkg | Local target-scale geology units | source_scale, stratigraphic_unit, lithology, confidence |
| faults_structures_50k_lines_EPSG32647_v01.gpkg | Local structural control layer | structure_type, confidence, limitation |
| mineral_occurrences_points_EPSG32647_v01.gpkg | Historical occurrence and mineralized point layer | commodity, occurrence_type, validation_status |
| prospectivity_target_zones_polygons_EPSG32647_v01.gpkg | B-3 Tol Khar / G-1 / other prospectivity zones | priority, evidence_basis, limitation |
| source_material_observation_points_EPSG32647_v01.gpkg | Routes, observations, samples, trenches/pits and source material features | work_type, observation_type, sample_type |
| XV023222_Buduunkhad_CMCS_Nearest_Deposit_Register_v01.xlsx | Nearest deposit / occurrence contextual register | distance_km, direction, context_only |
| XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg | Single integrated Phase 3 evidence package | all mandatory traceability fields |
| XV023222_Buduunkhad_Preliminary_Deposit_Model_v01.docx | 03A conceptual deposit model document | source evidence references and data-gap table |
| XV023222_Buduunkhad_Phase3_QAQC_Log_v01.xlsx | QA/QC decision record | reviewer, review_date, qaqc_status, decision |

### 03.6 Mandatory GeoPackage layer schema

| Field name | Required content | Why it is required |
| --- | --- | --- |
| source_raw_input_no | 1-78 input number | Links each output back to original raw data |
| source_raw_filename | Exact raw filename | Prevents loss of file provenance |
| source_group | Evidence group name | Allows filtering by data family |
| processing_phase | 03 or 03A | Shows where the layer/table was created |
| processing_software | QGIS / Excel / Word / PDF reader / etc. | Reproducibility |
| source_scale | 1:50k / 1:200k / 1:500k / text / table / unknown | Prevents overinterpretation of regional data |
| evidence_type | geology / structure / occurrence / metallogenic / prospectivity / CMCS context | Supports scoring and filtering |
| validation_status | Historical only / Field checked / Sampled / Lab confirmed | Separates historical evidence from confirmed evidence |
| confidence | High / Medium / Low / Needs verification | Controls decision confidence |
| limitation | Scale, scan, georef, coordinate or context limitation | Avoids misuse as direct proof |
| qaqc_status | Draft / Checked / Approved / Rejected | Controls release status |
| processing_version | v01 / v02 / ... | Version control |

### 03.7 QA/QC checklist

| QA/QC item | Acceptance criterion | Pass / fail consequence |
| --- | --- | --- |
| Raw preservation | No raw file overwritten; all work done on processing copy | Fail = stop and restore from archive |
| CRS control | All spatial deliverables exported or displayed in EPSG:32647; native CRS retained in metadata | Fail = reproject/metadata correction |
| Georeference quality | GCP count, residual, scale and grid consistency recorded for each scanned map | Fail = confidence lowered or map not used for spatial decision |
| Scale limitation | 1:500k / 1:200k / 1:50k evidence not mixed without source_scale field | Fail = scoring not allowed |
| Occurrence coordinate validation | №60, №66, №67 and №68 cross-checked; duplicate/uncertain points flagged | Fail = occurrence layer remains Draft |
| CMCS/MRPAM limitation | Marked context_only and not used as direct proof inside license | Fail = report/map correction required |
| Remote sensing limitation | Sentinel/ASTER/KOMPSAT/DEM marked support evidence only | Fail = interpretation note correction required |
| Historical evidence separation | Historical scanned map vectors use validation_status = Historical only | Fail = Phase 4 handover blocked |
| Deposit model table | Supporting, missing and validation work fields completed for each candidate model | Fail = 03A incomplete |
| Handover readiness | GPKG, registers, maps and QA/QC log complete | Fail = no Phase 4 handover |

### 03.8 Decision gate and handover to Phase 4 / Phase 10
Phase 3 is complete only when the geological evidence package can be used by Phase 4 without returning to raw scans, and when every derived layer/table/report can be traced back to exact raw input numbers and filenames.

| Handover item | Used in Phase 4 | Updated in Phase 10 |
| --- | --- | --- |
| Geological_Evidence_Layers.gpkg | Evidence overlay and prospect polygon delineation | Final integrated interpretation and target sheets |
| Occurrence and mineralized point database | Known occurrence score and field validation priority | Re-scored after field/lab confirmation |
| Metallogenic context register/map | Regional model-fit support | Context remains support unless validated locally |
| CMCS nearest deposit register | Context and analogue comparison | Not upgraded to proof unless local evidence confirms |
| Preliminary Deposit Model.docx and score matrix | dominant_deposit_model, model_confidence and validation_priority fields | Model-fit confidence updated with field/lab results |
| Phase3_QAQC_Log.xlsx | Go / Conditional Go / Hold control | Audit trail for final decision |

### 03.9 Phase 3 completion criteria
- №1-8 and №53-72 have been processed, registered or explicitly marked not usable with limitation.
- All georeferenced scanned map outputs have GCP/residual/scale/confidence records.
- Occurrence and mineralized point coordinates from map, table and text sources have been cross-checked.
- CMCS/MRPAM 5 km, 10 km, 20 km and 25 km contextual/coverage register is complete and clearly marked context only. The 25 km buffer is specifically retained to capture all nearby occurrence points in the BH_near_min_occurrences dataset.
- Preliminary Deposit Model evidence table is ready for 03A and Phase 4 scoring.
- Every output contains source_raw_input_no, source_raw_filename, processing_phase, confidence, limitation and validation_status.
- Phase 4 A/B/C/D preliminary ranking can start without reprocessing raw Phase 3 input files.
# 03A. Preliminary Deposit Model Preparation — Phase 3 доторх дэд workflow
Энэ хэсэг нь XV-023222_Buduunkhad_Preliminary_Deposit_Model.docx файлыг бэлтгэх аргачлалыг үндсэн workflow-ийн Phase 3 дотор байрлуулсан болно. Энэ нь Appendix биш; Phase 3-ийн Geological, Metallogenic and CMCS Synthesis ажлын заавал хийх дэд ажил бөгөөд Phase 4 preliminary prospect ranking, Phase 10 final target ranking руу шууд handover хийнэ.
Энэхүү дэд workflow нь ордын төрлийн урьдчилсан концепцийн загвар гаргах аргачлал юм. Satellite, ASTER, KOMPSAT-2, DEM, Drone/LiDAR болон pXRF output нь хүдэржилтийн баталгаа биш; эдгээр нь target generation, field validation, sampling prioritization-д ашиглах support evidence. Эцсийн confidence нь хээрийн шалгалт, дээжлэлт, лабораторийн шинжилгээ, structural/geological evidence, шаардлагатай бол trench/geophysics/scout drilling-аар баталгаажна.
## 03A.1 Зорилго ба гарах баримт бичиг
XV-023222_Buduunkhad_Preliminary_Deposit_Model.docx нь Бүдүүн хад талбайд боломжит ордын төрлүүдийг урьдчилсан байдлаар ялгаж, ямар evidence дээр үндэслэж байгаа, ямар evidence дутуу байгаа, дараагийн ямар field/lab validation хийх шаардлагатайг тодорхойлох концепцийн загварын баримт бичиг байна.
Энэ файлыг таамгаар бичихгүй. 78 input workflow-ийн Phase 3 — Geological, Metallogenic and CMCS Synthesis шатны үр дүнд, Phase 1-ийн Master GIS database болон historical scanned map vectorization output дээр тулгуурлан гаргана.

| Талбар | Утга |
| --- | --- |
| Project area | Buduunkhad / XV-023222 / L23222 |
| Standard CRS | WGS 84 / UTM Zone 47N, EPSG:32647 |
| Document to be prepared | XV-023222_Buduunkhad_Preliminary_Deposit_Model.docx |
| Document type | Preliminary conceptual deposit model methodology; final resource/reserve estimate биш |
| Source workflow basis | 78 Inputs v3/v4 Enhanced workflow + Historical Scanned Maps QGIS Vectorization v02 Detailed |
| Workflow location | 03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis / 07_Preliminary_Deposit_Model_Preparation |

## 03A.2 Ашиглах input evidence

| Input evidence | Ашиглах мэдээлэл | Deposit model-д өгөх үүрэг |
| --- | --- | --- |
| Геологийн суурь зураг | 1:50,000, 1:200,000 geology map, legend, lithology, intrusive, structure, fault, vein, alteration. | Host rock, intrusive contact, structural control, local/regional geology. |
| Ашигт малтмалын илрэл, эрдэсжсэн цэг | Mineral occurrence map, mineral resources map, 7255 register, 4186 gold occurrence description, mineralized point table. | Au, Cu, Mo, As, Zn, Pb, W, Sn, Bi element association болон historical occurrence evidence. |
| Металлогений зураг, тайлан | 1:500,000 metallogenic map, L47B regional metallogenic report, metallogenic scheme/metallogenogram. | Metallogenic belt, ore formation, ore district/node context. Local target boundary биш. |
| Historical scanned map vector output | Georeferenced raster, geology, structure, occurrence, stream sediment, heavy mineral, prospectivity target vector layers. | Historical evidence database. validation_status = Historical only гэж хадгална. |
| Remote sensing support | Sentinel, ASTER, KOMPSAT, DEM, ALOS-PALSAR derivative layers. | Alteration, lithology, lineament, terrain, drainage, exposure support. Ore proof биш. |

## 03A.3 Ажлын үндсэн дараалал
### Алхам 1 — Evidence layer-үүдийг Master GIS дээр нэгтгэх
QGIS дээр license_boundary, geology_units_50k/200k, structures_faults_lines, intrusive_contacts_lines, mineral_occurrences_points, mineralized_zones, stream_sediment_anomaly, heavy_mineral_anomaly, prospectivity_target_zones, metallogenic_zones, Sentinel/ASTER/KOMPSAT/DEM support layer-үүдийг EPSG:32647 CRS-тэй нэг project-д давхарлана.
### Алхам 2 — Historical map-уудаас ордын төрлийн evidence ялгах
Historical scanned map vectorization workflow-ийн дагуу map type бүрээс host geology, structure, occurrence, geochemical anomaly, heavy mineral, prospectivity zone, metallogenic context ялгана. Historical vector data-г field/lab confirmed data-тай холихгүй.
### Алхам 3 — Deposit model candidate-уудыг тодорхойлох
Au-Cu hydrothermal vein, intrusion-related Cu-Au-Mo, skarn/contact metasomatic, polymetallic vein, VMS-type sulphide possibility, heavy mineral/placer indicator гэсэн candidate model бүрийг тусад нь шалгана.
### Алхам 4 — Supporting evidence / missing evidence / validation work хүснэгт гаргах
Ордын төрөл бүр дээр одоо байгаа evidence, дутуу evidence, баталгаажуулах ажлыг хүснэгтээр үнэлнэ.
### Алхам 5 — Evidence weight ашиглаж preliminary ranking хийх
Deposit model тус бүрт 100 онооны matrix-ээр оноо өгч High priority model / Moderate priority model / Low conceptual model / Insufficient evidence гэж ангилна.

| Map type | Deposit model-д авах мэдээлэл |
| --- | --- |
| Geological map | Host rock, intrusive contact, volcanic/intrusive package, structure. |
| Mineral occurrence map | Au-Cu, Cu, Mo, As, Zn зэрэг илрэл. |
| Mineral resources map | Regional occurrence, ore field, anomaly. |
| Stream sediment map | Cu-Pb-Zn-Ag-As-Bi-W-Sn-Mo-Mn-Ba-F anomaly. |
| Heavy mineral map | Au, W, Sn, Ti, Cr, magnetite зэрэг indicator. |
| Prospectivity map | Б-3 Толь хяр, Г-1 зэрэг хэтийн төлөвтэй хэсэг. |
| Metallogenic map | Ore formation, metallogenic belt, ore district context. |

## 03A.4 Deposit model candidate screening

| Candidate deposit model | Юуг шалгах вэ? | Дутуу evidence / эрсдэл | Recommended validation work |
| --- | --- | --- | --- |
| Au-Cu hydrothermal vein | Quartz vein, pyrite, chalcopyrite, malachite, Au-Cu-Ag-As-Bi, shear/fault corridor, lineament intersection. | Au pXRF unreliable; судлын continuity, width, grade тодорхойгүй байж болно. | Recon mapping, rock chip/channel, lab Au fire assay + multi-element, LiDAR/structural mapping. |
| Intrusion-related Cu-Au-Mo | Diorite/granodiorite/gabbrodiorite contact, Cu-Mo-Bi-As, stockwork/quartz veinlets, ASTER/Sentinel alteration support. | Porphyry-style alteration zoning and sulphide system not confirmed. | ASTER validation, intrusive phase mapping, soil grid, IP/magnetic, trench/channel. |
| Skarn/contact metasomatic Cu-Au-W-Bi | Intrusive-carbonate contact, epidote/garnet/magnetite/skarn minerals, W-Bi-Cu-Au association. | Carbonate host and skarn mineral assemblage unclear. | Detailed contact mapping, pXRF W/Bi/Cu screening, petrography, magnetic/IP support. |
| Polymetallic vein | Pb-Zn-Cu-Ag-As association, vein/shear structures, gossan/iron oxide, historical occurrence overlap. | Depth continuity and grade continuity unknown. | Rock chip/channel, soil grid, structural mapping, lab Pb-Zn-Ag multi-element. |
| VMS-type sulphide possibility | Volcanic-sedimentary package, Cu-Zn-Pb-Ba-Fe-Mn, stratiform sulphide or gossan, regional arc/oceanic context. | Stratigraphic control and massive sulphide textures not confirmed. | Detailed stratigraphic mapping, geochemistry, IP, magnetic, targeted trenching. |
| Heavy mineral / placer indicator | Historical shlich/heavy mineral anomaly, drainage concentration, Au/W/Sn/Ti/Cr indicators. | Source may be transported/secondary; bedrock source not proven. | Drainage follow-up, upstream sampling, heavy mineral panning, geomorphology and bedrock checking. |

## 03A.5 Evidence weight ба preliminary ranking

| Шалгуур | Оноо | Тайлбар |
| --- | --- | --- |
| Favorable geology / host lithology | 20 | Host rock, intrusive/contact, volcanic-sedimentary or carbonate contact setting. |
| Intrusive/contact/structure control | 15 | Fault, shear, vein trend, lineament intersection, intrusive contact. |
| Known mineral occurrence | 15 | Historical Au-Cu/Cu/Mo/Pb-Zn/W-Sn occurrence or mineralized point. |
| Historical geochemistry / shlich / stream sediment | 15 | Cu-Au-Ag-Mo-Bi-As-Pb-Zn-W-Sn anomaly overlap, drainage source consistency. |
| Metallogenic context | 10 | Relevant metallogenic belt, ore formation, ore district/node context. |
| ASTER/Sentinel alteration support | 10 | Clay/sericite/silica/ferric/chlorite/carbonate indicators and lithology contrast. |
| Field mapping / pXRF support | 10 | Malachite, pyrite, epidote, quartz vein, elevated Cu/Pb/Zn/As/Mo/W/Sn; Au pXRF not decision-grade. |
| Access / workability | 5 | Field access, slope, drone/sampling/trenching feasibility. |
| Нийт | 100 | Deposit model тус бүрээр оноо өгнө. |


| Confidence class | Score range | Meaning |
| --- | --- | --- |
| High priority model | >=70 | Олон evidence давхцаж байгаа, field/lab follow-up priority. |
| Moderate priority model | 50-69 | Боломжтой боловч нэмэлт field/lab validation шаардлагатай. |
| Low / conceptual model | 30-49 | Contextual эсвэл дутуу evidence ихтэй. |
| Insufficient evidence | <30 | Одоогийн өгөгдлөөр deposit model гэж дэмжихэд хангалтгүй. |


| Rank | Deposit model | Preliminary confidence | Why |
| --- | --- | --- | --- |
| 1 | Au-Cu hydrothermal vein | High / Moderate | Quartz vein, Au-Cu occurrence, structure support байвал өндөр оноо авна. |
| 2 | Intrusion-related Cu-Au-Mo | Moderate | Intrusive contact + Cu-Mo-Bi-As possibility + alteration support шалгана. |
| 3 | Skarn/contact metasomatic | Moderate / Low | Contact evidence байгаа ч carbonate/skarn mineral баталгаажуулах шаардлагатай. |
| 4 | Polymetallic vein | Moderate / Low | Pb-Zn-Cu-Ag-As association байгаа эсэхийг field/lab-аар шалгана. |
| 5 | VMS possibility | Conceptual | Regional volcanic context байж болох ч direct stratiform sulphide evidence дутуу. |
| 6 | Heavy mineral / placer | Contextual | Drainage/shlich evidence байж болох ч bedrock source тодорхойгүй. |

## 03A.6 XV-023222_Buduunkhad_Preliminary_Deposit_Model.docx санал болгох бүтэц
- Title page: XV-023222 / L23222 Buduunkhad Preliminary Deposit Model; subtitle: Geological, Metallogenic, Historical Geochemistry, Remote Sensing and Occurrence Evidence-Based Conceptual Deposit Model.
- Methodology note: Final resource model биш, preliminary conceptual model гэдгийг тайлбарлана.
- Input data basis: 78 raw input-ийн аль evidence group-ээс ямар мэдээлэл авсныг хүснэгтээр оруулна.
- Regional geological setting: Ulaanshand Zone, Nuur Accretionary Megazone, Lake island-arc terrane context.
- Local geology and structural control: 1:50k, 1:200k geology, intrusive, fault, contact, vein, alteration.
- Mineral occurrence and geochemical evidence: Au-Cu, Cu, Mo, As, Zn, Pb, W, Sn, Bi, stream sediment, heavy mineral evidence.
- Remote sensing and terrain support: Sentinel, ASTER, KOMPSAT, ALOS/DEM support; ore proof биш гэдгийг заавал тэмдэглэнэ.
- Deposit model candidate screening: 6 candidate model-ийг supporting evidence / missing evidence / recommended validation work хүснэгтээр үнэлнэ.
- Preliminary model ranking: Хамгийн боломжтой ордын төрлийг evidence score-оор эрэмбэлнэ.
- Recommended validation work: Historical map QA/QC, recon mapping, pXRF, sampling, orientation soil, drainage follow-up, lab assay, IP/magnetic/trench/scout drilling.
## 03A.7 Богино ажлын checklist
- 78 input-ийн геологи, илрэл, геохими, металлогени, remote sensing evidence-г Master GIS-д нэгтгэнэ.
- Historical scanned map-уудыг georeference + vectorize хийж confidence ranking өгнө.
- Ордын боломжит төрлүүдийг Au-Cu vein, intrusion-related Cu-Au-Mo, skarn, polymetallic vein, VMS, placer/heavy mineral гэж ангилна.
- Төрөл бүрээр байгаа evidence, дутуу evidence, баталгаажуулах ажлыг хүснэгтээр үнэлнэ.
- Хамгийн боломжтой ордын төрлийг preliminary ranking-ээр гаргана.
- Энэ нь final дүгнэлт биш, field validation + lab assay дараа шинэчлэгдэх conceptual model гэж тэмдэглэнэ.
## 03A.8 Phase 3 QA/QC notes for deposit model preparation
- Raw data-г засварлахгүй; processing copy дээр ажиллана.
- Final deliverables-ийн CRS нь EPSG:32647; native/raw CRS-г metadata-д хадгална.
- Historical scanned map-derived vector data нь validation_status = Historical only гэж хадгалагдана.
- Regional 1:400k/1:500k metallogenic layer-ийг local target boundary мэт ашиглахгүй.
- ASTER final binary mask, Sentinel alteration ratio, KOMPSAT visual lineament, drone interpretation нь хүдэржилтийн баталгаа биш.
- pXRF нь lab assay-г орлохгүй; Au-ийн pXRF response-ийг decision-grade гэж үзэхгүй.
- CMCS/MRPAM nearest deposit нь contextual evidence бөгөөд тухайн license дотор хүдэржилт байгаа эсэхийг шууд батлахгүй.
- Final target confidence нь хээрийн шалгалт, дээжлэлт, laboratory assay, structural/geological evidence, шаардлагатай бол trench/geophysics/scout drilling-аар баталгаажна.
Methodology guide only — not mineralization proof or resource estimate
## 03A.9 Handover from Phase 3 to Phase 4 and Phase 10
03A дэд workflow-ийн үр дүн нь Phase 4-ийн Preliminary Prospect Delineation and Ranking-д deposit model evidence score, missing evidence, validation priority хэлбэрээр орно. Мөн Phase 10-д final target ranking хийх үед field/lab result-аар шинэчлэгдсэн conceptual model болгон дахин шалгана.

| Handover item | Phase 4-д ашиглах байдал | Phase 10-д ашиглах байдал |
| --- | --- | --- |
| Deposit model candidate table | Prospect polygon бүрийн model-fit шалгуур болно. | Final target sheet-д model-fit confidence болгон шинэчилнэ. |
| Evidence weight score | Preliminary A/B/C/D ranking-ийн geology/model component болно. | Assay/field validation-аар re-score хийнэ. |
| Missing evidence / risk | Field validation, drone, recon, sampling priority гаргана. | Go/Conditional Go/No-Go decision-д data gap/risk болно. |
| Recommended validation work | Phase 5-9 ажлын дараалал, sample plan, orientation survey-г чиглүүлнэ. | Trench/geophysics/scout drilling criteria-д шилжинэ. |

# 04. Phase 4 — Preliminary Prospect Delineation and Ranking

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Desktop evidence-үүдийг 100 онооны scoring matrix-аар preliminary prospect болгох. |
| Input files | Input files: Phase 1-3 processed outputs + source raw inputs №1-78 as traceable evidence basis. Key direct evidence sources: №47-52 geochemistry/field observations, №53-68 geology/occurrence/prospectivity/source materials, №69-72 metallogenic context, №9-46 and №73-78 terrain/remote sensing support, №8 license boundary. |
| Software / equipment | QGIS, scoring spreadsheet, prospect register. |

## Processing folder structure
04_Phase_4_Preliminary_Prospect_Delineation_and_Ranking/
├── 01_Evidence_Overlay
├── 02_Prospect_Polygon_Delineation
├── 03_Scoring_Matrix
├── 04_Confidence_DataGap_NextAction
└── 05_A_B_C_D_Field_Priority
## Step-by-step methodology
- Evidence overlay үүсгэнэ: geology + occurrence + stream/heavy mineral + ASTER/Sentinel + KOMPSAT lineament/outcrop + DEM terrain + CMCS context.
- Prospect polygon бүрт evidence score, confidence flag, limitation/data gap, field access, safety risk, next action бүртгэнэ.
- A/B/C/D preliminary target class олгоно: A >=75, B=55-74, C=35-54, D<35.
- Field-ready A/B prospect-уудыг drone survey болон recon mapping-д шилжүүлнэ.
Phase 3-ийн 03A Preliminary Deposit Model Preparation-аас гарсан deposit model score, missing evidence, recommended validation work-ийг prospect scoring matrix-д заавал холбож оруулна. Prospect polygon бүрт dominant_deposit_model, model_confidence, missing_model_evidence, validation_priority талбар нэмнэ.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| 100-point matrix calculated | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Confidence/data gap/next action fields filled | Recorded in phase QA/QC log; reviewer/date/decision required. |
| A/B/C/D class reviewed | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Field access and safety checked | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Preliminary_Prospect_Ranking_Map.pdf
- XV-023222_Buduunkhad_Prospect_Polygons.gpkg
- XV-023222_Buduunkhad_Prospect_Ranking_Table.xlsx
- XV-023222_Buduunkhad_Go_NoGo_Desktop_Decision_Matrix.xlsx
## Decision gate / next phase condition
- A/B prospects selected for drone and recon; C/D retained with data gaps.
# 05. Phase 5 — DJI Matrice 400 Drone LiDAR Photogrammetry Survey

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Priority prospect дээр orthomosaic/LiDAR/terrain/structure field planning base авах. |
| Input files | Input files: Phase 4 A/B prospect polygons plus direct planning support raw inputs №8 license boundary, №9-22 DEM/slope/hillshade, №24-46 KOMPSAT basemap/lineament support, №75-78 high-resolution/Sentinel/basemap rasters. Exact filename list is in Section 1A. |
| Software / equipment | 4 x DJI Matrice 400, Zenmuse P1, Zenmuse L2, Zenmuse L3, GNSS/RTK/PPK, processing software. |

## Processing folder structure
05_Phase_5_DJI_Matrice_400_Drone_LiDAR_Photogrammetry_Survey/
├── 01_Flight_Block_Design
├── 02_GCP_Checkpoint_RTK_PPK
├── 03_Zenmuse_P1_Photogrammetry
├── 04_Zenmuse_L2_LiDAR
├── 05_Zenmuse_L3_Detailed_LiDAR
├── 06_Raw_Backup_Flight_Log
├── 07_Processing_Orthomosaic_PointCloud_DTM_DSM
└── 08_Drone_QAQC_Interpretation
## Step-by-step methodology
- 4 ширхэг DJI Matrice 400-г parallel survey team болгон ашиглана: P1 orthomosaic, L2 terrain/structure, L3 detailed LiDAR, 4-р дрон backup/parallel block.
- Flight block design: target boundary + buffer, terrain/slope/access, take-off/landing/emergency area, no-fly/safety restriction.
- GCP/checkpoint, RTK/PPK, overlap, flight altitude, wind/weather/sun angle, battery rotation, raw backup, flight log бүртгэнэ.
- Zenmuse P1: high-resolution orthomosaic, oblique photo, outcrop mapping base.
- Zenmuse L2: DTM/DSM, terrain, drainage, slope, structural lineament.
- Zenmuse L3: detailed LiDAR, micro-topography, fault/contact/vein corridor.
- Output-уудыг field traverse, sample point, trench/drill pad planning-д ашиглана.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| GCP/checkpoint accuracy reviewed | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Flight log complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Overlap/altitude/weather recorded | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Raw photo/LiDAR backed up | Recorded in phase QA/QC log; reviewer/date/decision required. |
| DTM/DSM/orthomosaic checked | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Drone_Flight_Plan.pdf
- XV-023222_Buduunkhad_Drone_Orthomosaic_P1.tif
- XV-023222_Buduunkhad_Drone_LiDAR_PointCloud.laz
- XV-023222_Buduunkhad_Drone_DTM_DSM.tif
- XV-023222_Buduunkhad_Drone_Structure_Outcrop_Interpretation.gpkg
## Decision gate / next phase condition
- Orthomosaic/LiDAR products meet mapping scale and field planning requirements.
# 06. Phase 6 — Recon Mapping and Portable XRF Field Screening

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Priority target-ийг газар дээр шалгаж pXRF vectoring хийх. |
| Input files | Input files: Phase 4 target polygons + Phase 5 drone outputs + direct validation support raw inputs №55-56 detailed geology/legend, №60 mineral occurrence map, №63 prospectivity map, №64-65 source materials map/legend, №66-68 occurrence/register files, №9-22 terrain, №75-78 basemaps, №8 boundary. |
| Software / equipment | QField/QGIS forms, Olympus Vanta M, Bruker Titan S1, GPS/GNSS, camera. |

## Processing folder structure
06_Phase_6_Recon_Mapping_and_Portable_XRF_Field_Screening/
├── 01_Traverse_Planning
├── 02_Field_Mapping_Forms
├── 03_pXRF_VantaM_Primary
├── 04_pXRF_TitanS1_Duplicate_Check
├── 05_pXRF_QAQC_CRM_Blank_Duplicate
├── 06_Field_Database
└── 07_Recon_Report
## Step-by-step methodology
- A/B targets дээр traverse төлөвлөж lithology, alteration, mineralization, vein, structure, weathering, exposure, access, safety бүртгэнэ.
- Olympus Vanta M-г primary screening, Bruker Titan S1-г duplicate/cross-check байдлаар ашиглана.
- Өдөр бүр warm-up, calibration check, CRM, blank, duplicate, check sample уншуулна.
- pXRF бүртгэлд sample ID, GPS coordinate, lithology, alteration, mineralization, instrument model/serial, operator, mode, reading time, moisture/surface condition, Cu/Pb/Zn/As/Mo/W/Sn/Mn/Fe/S зэрэг element орно.
- Au-ийн pXRF response-ийг decision-grade evidence гэж үзэхгүй; lab assay шаардлагатай.
- pXRF-lab correlation sheet-д element бүрээр reliability flag өгнө.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| CRM/blank/duplicate/check sample daily | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Vanta M vs Titan S1 duplicate comparison | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Au not used as pXRF decision-grade | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Moisture/surface condition recorded | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Recon_Traverse_Lines.gpkg
- XV-023222_Buduunkhad_Field_Observation_Points.gpkg
- XV-023222_Buduunkhad_pXRF_Field_Screening_Register.xlsx
- XV-023222_Buduunkhad_pXRF_QAQC_Report.docx
- XV-023222_Buduunkhad_Recon_Mapping_Report.docx
## Decision gate / next phase condition
- Field evidence and pXRF vectoring justify sampling or downgrade target.
# 07. Phase 7 — Rock Chip, Channel and Verification Sampling

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Field-confirmed mineralization/alteration/structure дээр лабораторийн дээж авах. |
| Input files | Input files: Phase 6 recon/pXRF outputs + direct historical evidence raw inputs №52 field observation table, №55-56 detailed geology/legend, №60 mineral occurrence map, №63 prospectivity map, №64-65 source materials map/legend, №66-68 occurrence/register files, №9-22 terrain and №75-78 basemaps. |
| Software / equipment | Field sampling kit, GPS/GNSS, pXRF support, sample bags/tags, chain-of-custody forms. |

## Processing folder structure
07_Phase_7_Rock_Chip_Channel_and_Verification_Sampling/
├── 01_Sample_Planning
├── 02_RockChip_Channel_Float_Registers
├── 03_QAQC_Insertion
├── 04_Chain_of_Custody
├── 05_Lab_Submission
└── 06_Assay_Import_Preparation
## Step-by-step methodology
- Recon/pXRF-ээр баталгаажсан quartz vein, gossan, malachite/sulphide, intrusive contact, shear/fault, altered lithology дээр дээж авна.
- Sample type: representative rock chip, selective rock chip, float, channel, verification sample.
- Sample ID convention: BUD-RC-001, BUD-CH-001, BUD-SOIL-001, BUD-STR-001, BUD-HM-001, BUD-QC-STD-001, BUD-QC-BLK-001, BUD-QC-DUP-001.
- Sample register: coordinate, photo, drone tile, pXRF reading, lithology, alteration, mineralization, structure, width/strike/dip, sample mass, collector, date/time.
- QA/QC: CRM/standard, blank, duplicate, field duplicate, lab duplicate, pulp duplicate; chain-of-custody ба lab submission template заавал бүрдүүлнэ.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Sample ID unique | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Coordinates/photo/chain-of-custody complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| QA/QC insertion complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Lab submission consistent with register | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Rock_Chip_Sampling_Plan.pdf
- XV-023222_Buduunkhad_Rock_Chip_Sample_Register.xlsx
- XV-023222_Buduunkhad_Rock_Chip_QAQC_Plan.xlsx
- XV-023222_Buduunkhad_Lab_Submission_RockChip.xlsx
- XV-023222_Buduunkhad_Assay_Import_Template.xlsx
## Decision gate / next phase condition
- Lab submission complete and QA/QC inserted; assay import template ready.
# 08. Phase 8 — Orientation Soil, Stream Sediment and Heavy Mineral Check

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Systematic grid өмнө soil/drainage response аргачлал баталгаажуулах. |
| Input files | Direct raw input files: №47 HeavyMineralSamplingResultsMap, №48 HeavyMineral legend, №49 StreamSediment legend, №50 StreamSediment Polyelement map, №51 field route notebook, №52 field observation table; support inputs №9-22 DEM/drainage, №53-56 geology, №60 occurrence map, №63-64 prospectivity/source materials, №68 mineralized point table. |
| Software / equipment | Soil auger/shovel/sieve, GPS, pXRF, lab submission workflow. |

## Processing folder structure
08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check/
├── 01_Orientation_Line_Design
├── 02_Depth_Horizon_Mesh_Test
├── 03_pXRF_Lab_Comparison
├── 04_StreamSediment_FollowUp
├── 05_HeavyMineral_FollowUp
└── 06_Recommended_Systematic_Method
## Step-by-step methodology
- Systematic grid шууд эхлүүлэхгүй; эхлээд orientation survey хийж horizon/depth/mesh/spacing response баталгаажуулна.
- Depth test: 20 cm, 40 cm, 60-80 cm. Horizon: A/B/C/residual/transported.
- Mesh/fraction test, soil texture, carbonate, clay, slope position, drainage/alluvial influence тэмдэглэнэ.
- pXRF + lab comparison-аар ямар element suite, horizon, depth, spacing илүү anomaly өгч байгааг тодорхойлно.
- Historical stream sediment/heavy mineral map-тай drainage catchment analysis хийж upstream source direction болон follow-up point төлөвлөнө.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Depth/horizon/mesh comparison complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Transported vs residual flag | Recorded in phase QA/QC log; reviewer/date/decision required. |
| pXRF-lab comparison done | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Drainage source logic documented | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Orientation_Soil_Survey_Plan.pdf
- XV-023222_Buduunkhad_Orientation_Soil_Sample_Register.xlsx
- XV-023222_Buduunkhad_Orientation_Soil_pXRF_Lab_Comparison.xlsx
- XV-023222_Buduunkhad_StreamSediment_FollowUp_Plan.pdf
- XV-023222_Buduunkhad_HeavyMineral_FollowUp_Plan.pdf
## Decision gate / next phase condition
- Best horizon/depth/mesh/spacing confirmed before systematic grid.
# 09. Phase 9 — Systematic Soil Grid and Laboratory QA/QC

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Validated method-оор systematic soil geochemical coverage хийх. |
| Input files | Input files: Phase 8 orientation results + direct planning support raw inputs №8 boundary, №9-22 DEM/slope/drainage, №47-52 historical drainage/heavy mineral/field evidence, №55/60/63/64/68 local geology-occurrence-source evidence, №75-78 basemaps/Sentinel support. Exact filenames in Section 1A. |
| Software / equipment | QGIS grid design, field collection tools, pXRF, laboratory assay. |

## Processing folder structure
09_Phase_9_Systematic_Soil_Grid_and_Laboratory_QAQC/
├── 01_Grid_Design_200x50_100x25_50x25_25x10
├── 02_Field_Collection
├── 03_pXRF_Screening
├── 04_Lab_Submission_QAQC
├── 05_Assay_Validation
└── 06_Soil_Anomaly_Map
## Step-by-step methodology
- Orientation result-оор grid spacing сонгоно: Recon 200 m x 50 m, Target 100 m x 25 m, Infill 50 m x 25 m, Vein detail 25 m x 10 m.
- Grid orientation нь geological strike, structural trend, drainage/slope-д нийцсэн байна.
- pXRF realtime screening ашиглаж field vectoring хийж болох боловч final map lab assay дээр үндэслэнэ.
- QA/QC insertion schedule: CRM, blank, duplicate, field duplicate, lab repeat, pulp duplicate.
- Assay validation: unit conversion, detection limit, duplicate/CRM/blank performance, outlier check.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Grid spacing justified by orientation results | Recorded in phase QA/QC log; reviewer/date/decision required. |
| QA/QC performance acceptable | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Assay unit/detection limit validated | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Anomaly continuity checked | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Systematic_Soil_Grid_Plan.pdf
- XV-023222_Buduunkhad_Soil_Sample_Points.gpkg
- XV-023222_Buduunkhad_Soil_Sample_Register.xlsx
- XV-023222_Buduunkhad_Soil_QAQC_Report.docx
- XV-023222_Buduunkhad_Soil_Assay_Results.xlsx
## Decision gate / next phase condition
- Validated geochemical anomaly supports final target ranking.
# 10. Phase 10 — Integrated Interpretation and Final Target Ranking

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Бүх evidence, assay QA/QC, remote/drone/field data-г final target decision болгон нэгтгэх. |
| Input files | Input files: All validated phase outputs + full traceable raw evidence basis №1-78. Final target sheets must reference exact source raw input filenames from Section 1A/Section 1, not only generic evidence group names. |
| Software / equipment | QGIS, spreadsheet/statistical validation, report templates. |

## Processing folder structure
10_Phase_10_Integrated_Interpretation_and_Final_Target_Ranking/
├── 01_Assay_Validation
├── 02_Evidence_Integration
├── 03_Target_Scoring
├── 04_Target_Description_Sheets
├── 05_Go_NoGo_Decision
└── 06_Final_Target_GIS_Map_Report
## Step-by-step methodology
- Geology, metallogeny, mineral occurrence, stream sediment, heavy mineral, Sentinel, ASTER, KOMPSAT, ALOS DEM, drone, LiDAR, field mapping, pXRF, rock chip/channel assay, soil assay, CMCS context-ийг нэгтгэнэ.
- Assay validation: unit conversion, detection limits, duplicate check, CRM/blank performance, pXRF-lab correlation, outlier check.
- ASTER/Sentinel support layers-ийг field/lab evidence-тэй давхарлаж зөвхөн validation-supported target polygon болгон засварлана.
- Final target description sheet бүрт target ID, location, evidence summary, geology, structure, alteration, geochemistry, remote sensing, drone/LiDAR, sampling result, confidence, risk/data gap, recommended follow-up, Go/No-Go decision бичнэ.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| All evidence layers version-controlled | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Assay QA/QC passed | Recorded in phase QA/QC log; reviewer/date/decision required. |
| pXRF-lab correlation documented | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Target sheets complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Go/No-Go decision recorded | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Integrated_Interpretation_Report.docx
- XV-023222_Buduunkhad_Integrated_Geology_Geochemistry_Alteration_Map.pdf
- XV-023222_Buduunkhad_Final_Target_Polygons.gpkg
- XV-023222_Buduunkhad_Final_Target_Ranking_Table.xlsx
- XV-023222_Buduunkhad_Target_Description_Sheets.docx
## Decision gate / next phase condition
- Final A/B targets have sufficient evidence for trench/geophysics/scout drill planning.
# 11. Phase 11 — Follow-up Trench, Geophysics and Scout Drill Planning

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Final A/B target дээр trench, geophysics, scout drilling төлөвлөх. |
| Input files | Input files: Phase 10 final A/B targets + direct planning support raw inputs №8 boundary, №9-22 DEM/slope/hillshade, №55 detailed geology, №60 occurrence map, №63 prospectivity map, №64 source materials map, №68 mineralized point table, №75-78 basemap/Sentinel rasters. |
| Software / equipment | QGIS, trench/geophysics planning tools, drilling design spreadsheet, HSE/budget templates. |

## Processing folder structure
11_Phase_11_Follow_Up_Trench_Geophysics_and_Scout_Drill_Planning/
├── 01_Trench_Channel_Planning
├── 02_IP_Resistivity_Planning
├── 03_Magnetic_Survey_Planning
├── 04_Infill_Soil_Planning
├── 05_Scout_Drill_Collar_Design
├── 06_HSE_Environment_Rehabilitation
└── 07_Budget_Permit_Schedule
## Step-by-step methodology
- Trench/channel хийх нөхцөл: surface mineralization + lab/pXRF response + accessible slope + geometry trace.
- IP/resistivity хийх нөхцөл: disseminated sulphide/chargeability target эсвэл covered anomaly; line orientation нь structure/geology-г огтлох.
- Magnetic survey хийх нөхцөл: intrusive/mafic/contact/structure ялгах шаардлагатай үед.
- Infill soil хийх нөхцөл: open-ended soil anomaly, low spacing confidence, transported cover uncertainty.
- Scout drilling minimum criteria: confirmed surface mineralization, lab assay support, structure confirmed, favorable geology/contact, target geometry estimated, access/HSE possible, trench/geophysics recommended or completed.
- Drill collar table: collar ID, Easting/Northing, RL, azimuth, dip, depth, target, section line, access, pad, water, HSE, rehabilitation, budget.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Minimum scout drill criteria met | Recorded in phase QA/QC log; reviewer/date/decision required. |
| HSE/access/rehabilitation reviewed | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Drill collar geometry justified | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Budget/permit/schedule template completed | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_Follow_Up_Work_Plan.pdf
- XV-023222_Buduunkhad_Proposed_Trench_Locations.gpkg
- XV-023222_Buduunkhad_Proposed_IP_Magnetic_Lines.gpkg
- XV-023222_Buduunkhad_Scout_Drilling_Proposal.docx
- XV-023222_Buduunkhad_Drill_Collar_Table.xlsx
## Decision gate / next phase condition
- Scout drilling proceeds only if minimum criteria and HSE/access/permit conditions are met.
# 99. Final Deliverables

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Бүх output-ийг стандарт folder package болгон бүрдүүлэх. |
| Input files | Input files: All phase outputs and QA/QC logs, with source traceability back to raw input files №1-78. Final package must include the exact raw input filename reference from Section 1A for every evidence layer/report/table/map. |
| Software / equipment | QGIS, Office, PDF export, archive/checksum tools. |

## Processing folder structure
99_Final_Deliverables/
├── 01_Reports
├── 02_GIS_GPKG_QGIS_QField
├── 03_Remote_Sensing_Products
├── 04_Drone_LiDAR_Orthomosaic_PointCloud
├── 05_Field_Forms_and_pXRF_Registers
├── 06_Assay_and_QAQC_Tables
├── 07_Target_Ranking_and_Decision_Matrix
├── 08_Follow_Up_Work_Plans
└── 09_Final_Report_Package
## Step-by-step methodology
- All reports, GIS, remote sensing, drone/LiDAR, field forms, assay/QAQC, target ranking, follow-up work plans and final report package-г зохион байгуулж өгнө.
- Final deliverables EPSG:32647 standard CRS-тэй байна; raw/native CRS болон metadata-г хадгална.
- Deliverable бүрт source, processing date, operator/reviewer, QA/QC status, limitation note бичнэ.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Folder structure complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Files named consistently | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Metadata and limitations included | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Final QA/QC notes included | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- Final report package, GIS package, remote sensing products, drone/LiDAR products, field forms, assay/QAQC tables, target ranking and follow-up plans.
## Decision gate / next phase condition
- Final package is internally consistent, QA/QC reviewed and ready for management/technical review.
# 3. Remote sensing special subworkflows

| Subworkflow | Key method | Important limitation |
| --- | --- | --- |
| Sentinel-2 SNAP 13.0.0 | Raw/received status check; L1C -> Sen2Cor L2A; subset boundary + 500 m/1 km; 10 m resample; cloud/shadow/vegetation mask; Natural RGB, SWIR-NIR-Red, geology composite, lithology ratio/index, NDVI, NDWI, iron oxide, ferric, clay/SWIR, ferrous, brightness index; export GeoTIFF EPSG:32647. | Sentinel output нь field validation support бөгөөд хүдэржилтийн баталгаа биш. |
| ASTER workflow v5 | HDF import/band extraction; UTM47 project grid; b*_project band-аас alteration/lithology index тооцох; haze/edge filter зөвхөн visual; lithology composite -> favorable polygon -> raster -> normalized score; save score_porphyry_alteration_raw_v1.tif, porphyry_potential_class_v1.tif, porphyry_final_target_binary_mask_v1.tif. | Raw score=Float32 continuous; class=1/2/3; mask=0/1. Binary mask нь хүдэржилтийн баталгаа биш. |
| KOMPSAT-2 | PAN/MS band, RPC, EPH, TXT metadata bundle; PAN/MS alignment; orthorectification; true color, false color, NDVI, pan-sharpened basemap, lineament/outcrop/access interpretation. | SWIR байхгүй тул clay/sericite/carbonate alteration-ийг дангаар батлахгүй. |
| ALOS-PALSAR / ASTER GDEM / DEM | Hillshade, slope, aspect, contour, drainage, watershed, ruggedness, curvature; drone flight, access, trench/drill pad, safety, lineament support. | DEM derivative нь structural support; field confirmation шаардлагатай. |

# 4. Deposit model candidate screening table

| Deposit model candidate | Supporting evidence to look for | Missing evidence / risk | Recommended validation work |
| --- | --- | --- | --- |
| Au-Cu hydrothermal vein | Quartz vein, pyrite/chalcopyrite/malachite, Au-Cu-Ag-As-Bi, shear/fault corridor, lineament intersection. | Au pXRF unreliable; vein continuity/width/grade may be unknown. | Recon mapping, rock chip/channel, lab Au fire assay + multi-element, LiDAR/structural mapping. |
| Intrusion-related Cu-Au-Mo | Diorite/granodiorite/gabbrodiorite contact, Cu-Mo-Bi-As, stockwork/quartz veinlets, ASTER/Sentinel alteration support. | Porphyry-style alteration zoning and sulphide system not confirmed. | ASTER validation, mapping of intrusive phases, soil grid, IP/magnetic, trench/channel. |
| Skarn/contact metasomatic Cu-Au-W-Bi | Intrusive-carbonate contact, garnet/epidote/magnetite/skarn minerals, W-Bi-Cu-Au association. | Carbonate/contact continuity and skarn mineral assemblage may be unclear. | Detailed contact mapping, pXRF W/Bi/Cu screening, petrography, magnetic/IP support. |
| Polymetallic vein | Pb-Zn-Cu-Ag-As association, vein/shear structures, gossan/iron oxide, historical occurrence overlap. | Depth continuity and grade continuity unknown. | Rock chip/channel, soil grid, structure mapping, lab Pb-Zn-Ag multi-element. |
| VMS-type sulphide possibility | Volcanic-sedimentary package, Cu-Zn-Pb-Ba-Fe-Mn, stratiform sulphide or gossan, regional arc/oceanic context. | Stratigraphic control and massive sulphide textures not confirmed. | Detailed stratigraphic mapping, geochemistry, IP, magnetic, targeted trenching. |
| Heavy mineral / placer indicator | Historical shlich/heavy mineral anomaly, drainage concentration, Au/W/Sn/Ti/Cr indicators. | Source may be transported/secondary; bedrock source not proven. | Drainage follow-up, upstream sampling, heavy mineral panning, geomorphology and bedrock checking. |

# 5. Preliminary and final target ranking matrix

| Evidence | Weight | High score criterion | Required attribute fields |
| --- | --- | --- | --- |
| Geology / lithology / intrusive contact | 20 | Favorable host, intrusive contact, skarn/contact, volcanic/intrusive package, mapped mineralized zone. | score_geology, confidence, data_gap, next_action |
| Historical geochemistry / shlich / stream sediment | 15 | Cu-Au-Ag-Mo-Bi-As-Pb-Zn-W-Sn anomaly overlap and drainage source consistency. | score_historical_geochem, source_scale, limitation |
| ASTER / Sentinel alteration and lithology | 15 | Clay/sericite/silica/ferric/chlorite/carbonate indicators and lithology index overlap. | score_rs, rs_product, mask_flag |
| Structure / lineament / intersection | 15 | Fault/shear/vein trend, lineament intersection, contact-parallel structures. | score_structure, trend, intersection_type |
| Field mapping and pXRF response | 15 | Malachite, pyrite, epidote, quartz vein, gossan, elevated Cu/Pb/Zn/As/Mo/W/Sn. | score_field_pxrf, instrument, qa_status |
| Drone LiDAR / photogrammetry evidence | 8 | Outcrop exposure, vein trace, trench/pit evidence, micro-topography, access confirmation. | score_drone, orthomosaic_id, lidar_id |
| CMCS nearest deposit / metallogenic context | 7 | Relevant Au-Cu/Cu-polymetallic/skarn/VMS occurrence within 5/10/20 km context. | score_cmcs, buffer_km, context_only_flag |
| Access / safety / workability | 5 | Field access possible, slope moderate, drone/sampling/trenching feasible. | score_access, hse_risk, route_status |


| Target class | Score range | Meaning | Action |
| --- | --- | --- | --- |
| A | >=75 | Field/lab follow-up priority with multiple evidence types. | Drone/recon/sampling/trench/geophysics planning. |
| B | 55-74 | Promising but additional mapping/sampling needed. | Drone/recon + targeted sampling; update confidence. |
| C | 35-54 | Data gap or low confidence. | Limited check, additional desktop/field validation. |
| D | <35 | Archive/monitor unless new evidence emerges. | No immediate field cost except opportunistic check. |

# 6. Portable XRF QA/QC and register schema

| Daily pXRF step | Olympus Vanta M / Bruker Titan S1 procedure | Record field |
| --- | --- | --- |
| Warm-up | Instrument manufacturer recommended warm-up; battery/mode/profile check. | instrument_model, serial_no, operator, date_time |
| Calibration/check sample | Daily start/end check; known reference material comparison. | crm_id, expected_value, measured_value, pass_fail |
| Blank | Contamination check between high-grade or dusty samples. | blank_id, measured_elements, pass_fail |
| Duplicate/cross-check | 10-15% duplicate reading or critical station repeat; Vanta M vs Titan S1 comparison. | duplicate_id, parent_sample_id, instrument_pair |
| Reading conditions | Surface prep, moisture, grain size, weathering, measurement window and time. | moisture, surface_condition, reading_time_sec, mode |
| Element suite | Cu, Pb, Zn, As, Mo, W, Sn, Mn, Fe, S and relevant pathfinders. Au not decision-grade. | element_ppm_pct fields, reliability_flag |

# 7. Sampling methodology and QA/QC insertion

| Sample type | When to use | Sample ID convention | Critical note |
| --- | --- | --- | --- |
| Representative rock chip | Alteration zone/host rock characterization. | BUD-RC-001 | Avoid only high-grade visible pieces unless coded as selective. |
| Selective rock chip | Visible sulphide/malachite/quartz vein/mineralized float. | BUD-RC-001 | Clearly flag selective bias. |
| Float sample | Mineralized float where outcrop is limited. | BUD-RC-001 / BUD-FLT-001 optional | Do not use as in-situ proof unless source traced. |
| Channel sample | Vein/zone width measurable and safe to cut across. | BUD-CH-001 | Record width, orientation, recovery, continuity. |
| Orientation soil | Before systematic grid to test response. | BUD-SOIL-001 | Depth/horizon/mesh/fraction required. |
| Stream sediment follow-up | Historical drainage anomaly source checking. | BUD-STR-001 | Use catchment logic and upstream/downstream control. |
| Heavy mineral follow-up | Shlich/heavy mineral anomaly verification. | BUD-HM-001 | Record panning/concentrate method and geomorphic setting. |
| QA/QC standard | Certified reference material insertion. | BUD-QC-STD-001 | CRM suitable for expected element suite. |
| QA/QC blank | Contamination monitoring. | BUD-QC-BLK-001 | Insert after high-grade or regular interval. |
| QA/QC duplicate | Field/lab precision check. | BUD-QC-DUP-001 | Blind duplicate preferred. |

# 8. Final target description sheet schema

| Field | Required content |
| --- | --- |
| target_id | Unique ID, e.g., BUD-TGT-A01. |
| location | Easting/Northing EPSG:32647, license relation, access route. |
| evidence_summary | Concise multi-evidence summary with source layers. |
| geology | Host lithology, intrusive/contact relation, map confidence. |
| structure | Fault/shear/vein trend, intersection, LiDAR/field confirmation. |
| alteration | ASTER/Sentinel support, field alteration, confidence. |
| geochemistry | pXRF/lab/soil/stream/heavy mineral values and QA/QC status. |
| remote_sensing_support | Sentinel/ASTER/KOMPSAT/DEM product IDs and limitation. |
| drone_lidar_support | Orthomosaic tile, LiDAR DTM/DSM/lineament/outcrop evidence. |
| sampling_result | Rock chip/channel/soil assay summary and QA/QC performance. |
| confidence | High/Medium/Low with reason. |
| risk_data_gap | Missing evidence and uncertainty. |
| recommended_follow_up | Mapping, sampling, trench, IP, magnetic, scout drilling. |
| go_no_go_decision | Go / Conditional Go / No-Go with reviewer/date. |

# Appendix E — Historical Scanned Maps QGIS Vectorization Workflow v02 Detailed
Энэ appendix нь XV023222_Buduunkhad_HistoricalScannedMaps_QGIS_Vectorization_Workflow_MN_v02_Detailed.docx баримт бичгийн аргачлалыг үндсэн 78Inputs v2 Enhanced workflow-д нэмсэн хэсэг юм. Historical scan-derived vector evidence нь field/lab confirmed evidence биш бөгөөд confidence flag, data gap, scale-use limitation-тайгаар ашиглагдана.
XV-023222 / Buduunkhad / L23222
Historical Scanned Maps to Georeferenced Raster and Vector GIS Evidence Database Workflow
QGIS / GeoPackage / QA-QC / Confidence Ranking аргачлал - v02 Detailed
Энэ хувилбар нь v01 аргачлалыг илүү дэлгэрүүлж, QGIS дээр хийх бодит алхам, layer schema, Excel register sheet, QA/QC шалгуур, confidence scoring, data gap, handover acceptance criteria-г нэг бүрчлэн оруулсан audit-ready ажлын заавар юм.

| Талбар | Утга |
| --- | --- |
| Project | XV-023222 / Buduunkhad / L23222 |
| Workflow title | Historical Scanned Map to Georeferenced Raster and Vector GIS Evidence Database Workflow |
| Scope | 1987-2021 historical scanned geology, geochemistry, heavy mineral, stream sediment, mineral resources, metallogenic, prospectivity and source material maps |
| Standard CRS | WGS 84 / UTM Zone 47N, EPSG:32647 |
| Software | QGIS, GeoPackage, Excel register, QA/QC workbook |
| Workflow status | Raw Scan -> Inventory -> Georeference -> Vector Digitizing -> Register -> QA/QC -> Confidence Ranking -> Master GIS Handover |
| Version | v02 Detailed |
| Prepared date | 2026-05-26 |

# Агуулгын товч жагсаалт
- 1. Зорилго ба хамрах хүрээ
- 2. Reference document-тэй нийцүүлэх зарчим
- 3. Ажил гүйцэтгэх ерөнхий sequence
- 4. Input scanned map inventory
- 5. Map-to-legend linkage ба symbol dictionary
- 6. Folder structure ба file governance
- 7. QGIS project setup
- 8. Georeferencing workflow
- 9. Raster QA/QC ба confidence
- 10. Vectorization strategy by map type
- 11. Master GeoPackage design
- 12. Field schema ба domain/lookup
- 13. QGIS digitizing SOP
- 14. Layer бүрийн нарийвчилсан SOP
- 15. Excel register workbook
- 16. QA/QC checklist
- 17. Confidence ranking logic
- 18. Data gap register
- 19. Cross-map integration
- 20. Handover package ба acceptance criteria
- 21. Final workflow diagram
- 22. Appendices
# 1. Зорилго ба хамрах хүрээ
Энэхүү аргачлал нь Бүдүүн хад / XV-023222 / L23222 төслийн бүх historical scanned map файлыг QGIS дээр бүртгэх, georeference хийх, vector GIS layer болгон боловсруулах, Excel/GeoPackage register үүсгэх, QA/QC болон confidence ranking хийж Master GIS database-д audit-ready байдлаар нэгтгэх зорилготой.
Энэ нь ганц ашигт малтмалын зураг боловсруулах workflow биш. 1987 оны 1:200,000 шлих, ёроолын сорьц, геологи, ашигт малтмалын зураг; 2013 оны 1:50,000 геологи, ашигт малтмал, хэтийн төлөв, эх материалын зураг; 1:100,000-1:500,000 металлогени болон regional metallogenic report scan/pdf файлуудыг нэгэн зэрэг хамарна.
Raw scan-derived vector data нь historical interpretation evidence бөгөөд field/lab confirmed evidence биш. Field validation, pXRF screening, rock chip/soil sampling, laboratory assay-аар баталгаажихаас өмнө decision-grade evidence гэж ашиглахгүй.
1:50,000 зураг нь target-scale interpretation болон QField field validation-д илүү өндөр ач холбогдолтой. 1:100,000-1:500,000 зураг нь regional context, drainage/geochemical dispersion, metallogenic framework, structural trend, target screening-д ашиглагдана.
Бүх final spatial output EPSG:32647-д хадгалагдана. Native/raw CRS, source scale, GCP, georeference confidence, digitizing confidence-г metadata/register-д заавал хадгална. Raw archive файлыг засварлахгүй. Processing зөвхөн working copy дээр хийгдэнэ.

| Хамрах зүйл | Энэ workflow-д хийх ажил | Хязгаарлалт |
| --- | --- | --- |
| Raw scan JPG/PDF | Inventory, working copy, map type classification, legend linkage | Raw file дээр overwrite хийхгүй |
| Main map | Georeference, GeoTIFF, vector digitizing | Map scale-ийн хязгаарыг хадгална |
| Legend scan | Symbol dictionary, domain/lookup table, interpretation rule | Ихэвчлэн georeference хийхгүй |
| Vector evidence | Point/line/polygon layer, source traceability, QA/QC | Historical only гэсэн validation_status хадгална |
| Register/QAQC | Excel workbook, confidence ranking, data gap register | Хоосон field-тэй output handover хийхгүй |

# 2. Reference document-тэй нийцүүлэх зарчим

| Reference | Энэ workflow-д тусгах шаардлага | v02-д нэмсэн дэлгэрүүлэлт |
| --- | --- | --- |
| Overall 78-input exploration workflow | 78 raw input evidence group-ийг Phase 1 Data Audit and Master GIS Setup-тэй уялдуулах; EPSG:32647 CRS; raw data-г өөрчлөхгүй; Master GIS database; Phase 3/4/6/7/8/9 handover. | 21 scan map-ыг evidence group, map family, priority, handover use-ээр ангилсан. |
| Phase 1 - Data Audit and Master GIS Setup | File inventory, metadata register, sidecar check, CRS check, georeference audit, GCP table, residual report, Master GeoPackage, Master QGIS project, QA/QC log, confidence ranking, data gap register. | GCP table schema, residual acceptance, raster/vector confidence score, data gap fields, acceptance criteria-г дэлгэрүүлсэн. |
| 2013 MineralOccurrenceMap QGIS workflow | Raw scan -> GeoTIFF -> vector digitizing -> register -> QA/QC гэсэн логикийг бүх scanned map family-д өргөтгөх. | Ганц occurrence point биш: geology, structure, geochemistry anomaly, heavy mineral, source material, prospectivity, metallogenic context layer-үүдийг нэмсэн. |

# 3. Ажил гүйцэтгэх ерөнхий sequence
- Raw archive-г read-only гэж үзэж, бүх scan map-ыг evidence group-ээр шалгана.
- 01_Input_Working_Copy руу файлуудыг хуулж, filename, size, extension, checksum, source note бүртгэнэ.
- Map Inventory болон Map-to-Legend Linkage register үүсгэнэ.
- QGIS project-ийг EPSG:32647 CRS-тэй үүсгэж, license boundary болон buffer layer-уудыг reference болгон load хийнэ.
- Main map бүрийн georeference priority тогтоож, GCP сонголтын төлөвлөгөө гаргана.
- QGIS Georeferencer дээр map бүрийг GeoTIFF болгож, GCP table, residual report, screenshot/check map хадгална.
- Georeferenced raster бүрт CRS, extent, RMSE/residual, grid alignment, license/basemap/DEM overlay шалгаж raster confidence өгнө.
- Map type бүрийн digitizing rule болон legend-based symbol dictionary-г баталгаажуулна.
- GeoPackage layer-үүдийг үүсгэж, common source traceability fields + layer-specific fields нэмнэ.
- Vector digitizing хийж, QGIS form tab, domain/lookup, required field constraints тохируулна.
- Topology, geometry validity, duplicate, NULL, ID uniqueness, scale-use flag, historical/confirmed separation QA/QC шалгана.
- Excel register workbook export хийж, confidence ranking болон data gap register бөглөнө.
- Cross-map integration хийж, evidence давхцал/зөрүү/шийдвэрийн нөлөөллийг бүртгэнэ.
- Master QGIS project, Master GeoPackage, QA/QC workbook, README, handover checklist багцалж дараагийн phase-д шилжүүлнэ.

| Stage | Input | Main action | Output | QA gate |
| --- | --- | --- | --- | --- |
| S1 Inventory | Raw scan files | Register + checksum + working copy | Map Inventory | All files accounted |
| S2 Legend linkage | Main map + legend | Symbol/domain mapping | Legend linkage register | Legend status assigned |
| S3 Georeference | Working raster | GCP + transformation + GeoTIFF | GeoTIFF EPSG:32647 | Residual + overlay checked |
| S4 Vectorization | GeoTIFF + legend | Digitize by map type | GeoPackage layers | Geometry/attribute QA passed |
| S5 Register | Vector layers | Export and enrich attributes | Excel workbook | Required sheets complete |
| S6 Integration | All evidence layers | Cross-map overlay | Confidence/data gap/handover | Acceptance criteria passed |

# 4. Input scanned map inventory
Доорх 21 файлыг нэг Map Inventory-д бүртгэж, main map, legend, report excerpt, regional context гэсэн холбоосоор удирдана. Файл бүрийн raw path, working copy path, checksum, open status, georeference status, output status-г workbook-д нэмэлт баганаар хадгална.

| Map_ID | Evidence group | Raw filename | Year | Sheet | Scale | Map type | Legend | Expected output | Priority | Main use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BK-SCAN-001 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Heavy mineral sampling results map | BK-SCAN-002 | GeoTIFF + heavy mineral sample/anomaly layers | P2 | Шлихийн сорьц, indicator mineral, тархалтын contour |
| BK-SCAN-002 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_HeavyMineralSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Heavy mineral legend | BK-SCAN-001 | Symbol dictionary / lookup | P2 | Шлих/индикатор минералын таних тэмдэг |
| BK-SCAN-003 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Legend_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Stream sediment legend | BK-SCAN-004 | Symbol dictionary / lookup | P2 | Ёроолын сорьц, сарнилын урсгал, contour |
| BK-SCAN-004 | 04_HeavyMineral_StreamSediment_Field | 1987_MN_L47-XIX_StreamSedimentSamplingResultsMap_Polyelement_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Stream sediment polyelement map | BK-SCAN-003 | GeoTIFF + anomaly polygon/contour layers | P2 | Cu Pb Zn Ag As Bi W Sn Mo Mn Ba F anomaly |
| BK-SCAN-005 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Regional geological map | BK-SCAN-006 | GeoTIFF + regional geology/structure layers | P2 | Региональ геологи, lithology, structure |
| BK-SCAN-006 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_GeologicalMap_Legend_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Regional geological legend | BK-SCAN-005 | Symbol dictionary / lookup | P2 | Stratigraphy, intrusion, structure, lithology |
| BK-SCAN-007 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Mineral resources map | BK-SCAN-008 | GeoTIFF + occurrence/resource layers | P2 | Региональ илрэл, гажил, хүдрийн талбай |
| BK-SCAN-008 | 05_Geology_Mineral_Prospectivity | 1987_MN_L47-XIX_MineralResourcesMap_Legend_1-200000_v01_raw-scan.jpg | 1987 | L47-XIX | 1:200,000 | Mineral resources legend | BK-SCAN-007 | Symbol dictionary / lookup | P2 | Ашигт малтмал, элемент, илрэл, гажлын тэмдэглэгээ |
| BK-SCAN-009 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_1-50000_v01_raw-scan.jpg | 2013 | L47-74-A | 1:50,000 | Detailed geological map | BK-SCAN-010 | GeoTIFF + detailed geology/structure layers | P1 | Нарийвчилсан геологи, lithology, fault, section |
| BK-SCAN-010 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_GeologicalMap_Legend_1-50000_v01_raw-scan.jpg | 2013 | L47-74-A | 1:50,000 | Detailed geological legend | BK-SCAN-009 | Symbol dictionary / lookup | P1 | Stratigraphy, intrusive, vein, alteration |
| BK-SCAN-011 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_MineralOccurrenceMap_1-50000_v01_raw-scan.jpg | 2013 | L47-74-A | 1:50,000 | Mineral occurrence map | BK-SCAN-010/BK-SCAN-015 | GeoTIFF + mineral occurrence/target layers | P1 | Au-Cu Cu Mo As Zn илрэл + геологийн суурь |
| BK-SCAN-012 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessment_ReportExcerpt_B3-TolKhar_v01_raw-photo.jpg | 2013 | L47-74-A | Report/photo | Prospectivity report excerpt | BK-SCAN-013 | Text evidence register | P1 | Б-2/B-3/B-4 талбайн тайлбар |
| BK-SCAN-013 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_ProspectivityAssessmentMap_1-50000_v01_raw-scan.jpg | 2013 | L47-74-A | 1:50,000 | Prospectivity assessment map | BK-SCAN-012 | GeoTIFF + prospectivity polygons | P1 | Б-3 Толь хяр, Г-1 хэтийн төлөвтэй хэсэг |
| BK-SCAN-014 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_1-50000_v01_raw-scan.jpg | 2013 | L47-74-A | 1:50,000 | Source materials map | BK-SCAN-015 | GeoTIFF + routes/obs/sample/trench layers | P1 | Маршрут, ажиглалт, сорьц, суваг, шурф, зүсэлт |
| BK-SCAN-015 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-74-A_SourceMaterialsMap_Legend_1-50000_v01_raw-scan.jpg | 2013 | L47-74-A | 1:50,000 | Source materials legend | BK-SCAN-014 | Symbol dictionary / lookup | P1 | Ажиглалтын цэг, маршрут, сорьц, шурф, суваг |
| BK-SCAN-016 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MineralDistributionPatternMap_1-100000_v01_raw-scan.jpg | 2013 | L47-73-74 | 1:100,000 | Mineral distribution pattern map | None | GeoTIFF + ore district/node context | P3 | Металлогенийн бүс, хүдрийн дүүрэг, зангилаа |
| BK-SCAN-017 | 05_Geology_Mineral_Prospectivity | 2013_MN_Namalzakh_L47-73-74_MetallogenicSchemeAndMetallogenogram_1-400000_v01_raw-scan.jpg | 2013 | L47-73-74 | 1:400,000 | Metallogenic scheme/metallogenogram | None | GeoTIFF + metallogenic context | P3 | Хүдрийн формац, нас, металлогенийн бүс |
| BK-SCAN-018 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_Legend_RawScan_2020_v01.jpg | 2020 | L47B Talshand | 1:500,000 | Regional metallogenic legend | BK-SCAN-019 | Symbol dictionary / lookup | P4 | Металлогений таних тэмдэг |
| BK-SCAN-019 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_L47B_Talshand_1M500K_RawScan_2020_v01.jpg | 2020 | L47B Talshand | 1:500,000 | Regional metallogenic map | BK-SCAN-018 | GeoTIFF + regional metallogenic zones | P4 | Монгол улсын 1:500k металлогени |
| BK-SCAN-020 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book01_ProjectBook13_1M500K_RawScan_2021_v01.pdf | 2021 | Regional | 1:500,000 | Metallogenic report book 01 | BK-SCAN-019 | Report evidence register | P4 | Тайлангийн текст, тайлбар |
| BK-SCAN-021 | 06_Regional_Metallogenic_L47B | Regional_MetallogenicMap_Report_Book04_ProjectBook16_1M500K_RawScan_2021_v01.pdf | 2021 | Regional | 1:500,000 | Metallogenic report book 04 | BK-SCAN-019 | Report evidence register | P4 | Тайлангийн текст, тайлбар |

## 4.1 Inventory-д заавал нэмэх metadata баганууд

| Багана | Төрөл | Заавал эсэх | Тайлбар / domain |
| --- | --- | --- | --- |
| raw_path | Text | Yes | 00_Raw_Files_Archive доторх эх файл |
| working_copy_path | Text | Yes | 01_Input_Working_Copy доторх боловсруулалтын хуулбар |
| file_size_mb | Decimal | Yes | Хэмжээг audit-д хадгална |
| checksum_sha256 | Text | Recommended | Raw vs working copy integrity шалгах |
| open_status | Text | Yes | Opens / Error / Needs conversion |
| scan_quality | Text | Yes | Good / Fair / Poor |
| has_coordinate_grid | Text | Yes | Yes / No / Partial / Unknown |
| georef_required | Text | Yes | Yes / No / Context only |
| georef_status | Text | Yes | Not started / In progress / Completed / Failed / Needs verification |
| vectorization_status | Text | Yes | Not started / Draft / Checked / Approved / Not applicable |
| handover_status | Text | Yes | Ready / Use with caution / Hold / Exclude |

# 5. Map-to-legend linkage ба symbol dictionary
Main map болон legend файлыг салгаж хадгалах боловч digitizing rule, attribute domain, symbol dictionary үүсгэхэд хооронд нь заавал холбож бүртгэнэ. Legend файлыг тусад нь georeference хийх шаардлагагүй, харин map symbol тайлах evidence болгон бүртгэнэ.

| Main map | Legend / report support | Digitizing rule | Domain / lookup үүсгэх зүйл |
| --- | --- | --- | --- |
| 1987 HeavyMineralSamplingResultsMap | 1987 HeavyMineralSamplingResultsMap_Legend | Шлих, indicator mineral, contour, sample symbol domain үүсгэнэ. | mineral_indicator, anomaly_class, sample_symbol |
| 1987 StreamSedimentSamplingResultsMap_Polyelement | 1987 StreamSedimentSamplingResultsMap_Legend | Element suite, anomaly contour, drainage dispersion symbol domain үүсгэнэ. | element_suite, anomaly_level, contour_type |
| 1987 GeologicalMap | 1987 GeologicalMap_Legend | Geological unit, age, lithology, intrusive, structure symbol domain үүсгэнэ. | map_symbol, lithology, age, intrusive_type |
| 1987 MineralResourcesMap | 1987 MineralResourcesMap_Legend | Commodity, occurrence type, anomaly, ore field symbol domain үүсгэнэ. | commodity, occurrence_type, ore_field_type |
| 2013 GeologicalMap | 2013 GeologicalMap_Legend | Detailed lithology, fault, vein, alteration, section symbol domain үүсгэнэ. | stratigraphic_unit, vein_type, alteration |
| 2013 MineralOccurrenceMap | 2013 GeologicalMap/SourceMaterials legend болон map label | Au-Cu, Cu, Mo, As, Zn occurrence point and target zone digitizing rule үүсгэнэ. | commodity_group, target_style |
| 2013 SourceMaterialsMap | 2013 SourceMaterialsMap_Legend | Route, station, sample, trench/pit/shaft/channel/section symbol domain үүсгэнэ. | observation_type, sample_type, work_type |
| Regional MetallogenicMap L47B | Regional MetallogenicMap_L47B_Legend + Book01/Book04 | Metallogenic belt, ore district, commodity group, regional occurrence context rule үүсгэнэ. | metallogenic_unit, ore_formation, scale_context |

## 5.1 Symbol dictionary үүсгэх алхам
- Legend scan-ыг QGIS эсвэл image viewer дээр нээгээд symbol бүрийг screenshot/zoom түвшинд шалгана.
- Symbol_Code, Symbol_Image_Ref, Mongolian_Name, English_Name, Geometry_Type, Default_Layer, Attribute_Field, Domain_Value, Notes гэсэн баганатай dictionary sheet үүсгэнэ.
- Main map дээрх тэмдэглэгээ legend-тэй тохирч байгаа эсэхийг 10-20 жишээ feature дээр туршиж баталгаажуулна.
- Тодорхойгүй тэмдэглэгээ бүрт attribute_confidence = Low/Unknown, data_gap_type = Unclear legend гэж тэмдэглэнэ.
- QGIS layer form дээр dropdown domain болгон ашиглах lookup list үүсгэнэ.

| Symbol dictionary багана | Жишээ | Тайлбар |
| --- | --- | --- |
| symbol_code | HM-MAG-01 | Дотоод код |
| symbol_name_mn | Магнетит агуулсан шлих | Legend-ээс уншсан нэр |
| symbol_name_en | Magnetite heavy mineral indicator | Тайлан/олон улсын нэршил |
| geometry_type | Point / Line / Polygon | Digitize хийх геометр |
| target_layer | heavy_mineral_sample_points | QGIS layer |
| domain_field | mineral_indicator | Атрибут талбар |
| domain_value | Magnetite | Нэг мөр стандарт утга |
| confidence_default | Medium | Тэмдэглэгээний тод байдал |
| notes | Legend scan unclear | Тайлбар |

# 6. Folder structure ба file governance
Дараах бүтэц нь Phase 1 Data Audit and Master GIS Setup дотор ажиллахад тохиромжтой. Raw archive-г өөрчлөхгүй; энэ бүтэц нь working copy болон output-д зориулагдана.
01_Phase_1_Data_Audit_and_Master_GIS_Setup/
  00_Admin_and_Method/
  01_Input_Working_Copy/
    01_HeavyMineral_StreamSediment_1987/
    02_Geology_MineralResources_1987/
    03_Geology_MineralOccurrence_Prospectivity_2013/
    04_Metallogenic_Regional_2013_2021/
  02_Inventory_and_Metadata/
  03_CRS_Check/
  04_Georeference_Check/
    01_GCP_Tables/
    02_Georeferenced_Rasters/
    03_Residual_Reports/
    04_Georeference_Screenshots/
    05_Low_Confidence_Georef/
  05_Vector_Digitized/
    01_Geology_Polygons/
    02_Structures_Faults_Lines/
    03_Mineral_Occurrences_Points/
    04_Geochemistry_Anomaly_Polygons/
    05_HeavyMineral_StreamSediment_Layers/
    06_Source_Materials_Points_Lines/
    07_Prospectivity_Target_Zones/
    08_Metallogenic_Context/
  06_Register_Metadata/
  07_QGIS_Project/
  08_QAQC_and_Confidence/
  09_Handover_Package/

| Governance rule | Зорилго | Хэрэгжүүлэх арга |
| --- | --- | --- |
| Raw read-only | Эх өгөгдөл эвдрэхээс хамгаалах | Raw archive дээр бичих эрхгүй, processing зөвхөн copy дээр |
| Checksum | Файл солигдсон эсэхийг хянах | SHA-256 raw ба working copy-д хадгалах |
| Versioning | Дахин боловсруулалтыг ялгах | v01, v02, v03; draft файлыг _DRAFT гэж тэмдэглэх |
| Sidecar grouping | Raster metadata алдагдахаас сэргийлэх | .aux.xml, .ovr, .tfw, .jgw, .rpc, .eph файлыг хамт хадгалах |
| Change log | Audit trail үүсгэх | Action_Log.xlsx: date/operator/action/input/output/status |

# 7. QGIS project setup
- QGIS -> Project -> New сонгоно.
- Project -> Properties -> CRS хэсгээс WGS 84 / UTM Zone 47N, EPSG:32647 сонгоно.
- Distance unit = meters; Area unit = square kilometers/hectares; Ellipsoid = WGS84 тохируулна.
- Project-г 07_QGIS_Project хавтаст XV023222_Buduunkhad_HistoricalScannedMaps_Vectorization_QGIS_EPSG32647_v02.qgz нэрээр хадгална.
- GeoPackage connection үүсгэж Master GeoPackage-г Browser Panel-д холбоно.
- Layer group structure-г доорх байдлаар үүсгэнэ.
- Project Properties -> General дээр project title, author/team, path relative тохиргоог шалгана.
- Project Properties -> Data Sources дээр Automatically create transaction groups шаардлагатай бол идэвхжүүлнэ.
- QGIS snapping болон topology editing тохиргоог vector digitizing эхлэхээс өмнө тохируулна.
Layer group structure:
01_Source_Raw_and_Georef_Raster
02_Admin_Boundary_and_Buffer
03_Geology
04_Mineral_Occurrence
05_HeavyMineral_StreamSediment
06_Source_Materials
07_Prospectivity_Targets
08_Metallogenic_Context
09_QAQC_Confidence
10_Handover

| QGIS setting | Recommended value | Тайлбар |
| --- | --- | --- |
| Project CRS | EPSG:32647 | Final output CRS |
| On-the-fly reprojection | Enabled | Native layer display хийхэд |
| Snapping type | Vertex and segment | Line/polygon digitizing-д |
| Snapping tolerance | 5-10 pixels / scale dependent | Scale-аас хамааруулж тохируулна |
| Topological editing | Enabled for line/polygon | Overlap/sliver багасгана |
| Avoid overlap | Enabled for same polygon layers | Geology/target zone polygon-д |
| Default encoding | UTF-8 | Монгол/кирилл attribute алдагдахгүй |
| Project paths | Relative | Handover package зөөвөрлөхөд |

# 8. Georeferencing workflow
Legend scan файлыг гол төлөв georeference хийхгүй. Main map scan-уудыг georeference хийж GeoTIFF болгосны дараа legend scan-ыг symbol dictionary, lookup/domain, attribute coding хийхэд ашиглана.
## 8.1 GCP сонгох эх сурвалжийн эрэмбэ

| Эрэмбэ | Control source | Ашиглах нөхцөл | Confidence impact |
| --- | --- | --- | --- |
| 1 | Coordinate grid intersection | Зураг дээр coordinate grid тод, огтлолцол сайн харагдаж байвал хамгийн түрүүнд сонгоно. | High |
| 2 | Map frame corner coordinate / labelled tick | Булан/захын coordinate тодорхой үед. | High |
| 3 | Map sheet boundary | L47-XIX, L47-74-A sheet boundary coordinates баталгаатай үед. | Medium-High |
| 4 | License boundary corner / known control point | Тусгай зөвшөөрлийн хил эсвэл баталгаатай vector boundary давхцаж байвал. | Medium |
| 5 | Stable topographic feature | Голын уулзвар, замын огтлолцол, ridge/valley гэх мэт. | Medium-Low |
| 6 | Visual matching only | Grid/coordinate байхгүй үед зөвхөн context map-д. | Low / Needs verification |

## 8.2 QGIS Georeferencer дээр хийх алхам
- Raster -> Georeferencer нээнэ.
- Open Raster сонгож working copy JPG/PDF raster-г нээнэ. PDF бол шаардлагатай бол өмнө нь 300-600 dpi TIFF/PNG болгон хөрвүүлнэ.
- Settings -> Transformation Settings нээгээд Target CRS = EPSG:32647 сонгоно.
- Output raster нэрийг 04_Georeference_Check/02_Georeferenced_Rasters хавтаст naming standard-аар өгнө.
- Load in QGIS when done сонголтыг идэвхжүүлнэ.
- Compression = LZW; creation options-д TILED=YES, COMPRESS=LZW гэж боломжтой бол өгнө.
- GCP цэгүүдийг бүх талбайд жигд тархааж оруулна. Зөвхөн 4 булангаар хязгаарлахгүй.
- Coordinate оруулахдаа эх coordinate нь longitude/latitude бол decimal degree болгож оруулаад QGIS transform ашиглана эсвэл UTM координатаар шууд оруулна.
- Transformation-г эхлээд Polynomial 1 ашиглаж туршина. Residual их, scan distortion local байвал Thin Plate Spline туршиж, confidence note бичнэ.
- Georeferencing ажиллуулсны дараа GeoTIFF layer properties -> Source дээр CRS, extent, pixel size, path шалгана.
- GeoTIFF-г license boundary, DEM hillshade, basemap, өмнө georeferenced raster-тай давхарлаж overlay QA хийнэ.
- GCP table-г CSV/XLSX болгон хадгалж, residual report screenshot болон QGIS map screenshot хадгална.

| Scale | Minimum / preferred GCP | Transformation | Use rule | Confidence анхааруулга |
| --- | --- | --- | --- | --- |
| 1:50,000 | Minimum 6; preferred 8-12 | Polynomial 1 / Helmert / TPS only if needed | Target-scale digitizing-д ашиглана | GCP муу бол occurrence/target vector confidence буурна |
| 1:100,000 | 6-10 | Polynomial 1 | Ore district / mineral distribution context | Local target geometry гэж хэтрүүлж ашиглахгүй |
| 1:200,000 | 6-10 | Polynomial 1 | Regional geology/geochemistry/drainage evidence | Field validation before decision-grade use |
| 1:400,000-1:500,000 | 4-8 | Polynomial 1 | Metallogenic context only | Context evidence; local target boundary биш |

## 8.3 DMS coordinate-г decimal degree болгох дүрэм
Зарим scan map дээр coordinate нь 96°30′E, 46°00′N гэх мэт DMS хэлбэртэй байдаг. Decimal degree = degree + minute/60 + second/3600. East/North эерэг, West/South сөрөг тэмдэгтэй байна.

| DMS | Decimal degree | Тайлбар |
| --- | --- | --- |
| 96°30′00″E | 96.500000 | 96 + 30/60 |
| 45°50′00″N | 45.833333 | 45 + 50/60 |
| 96°45′00″E | 96.750000 | 96 + 45/60 |
| 46°00′00″N | 46.000000 | 46 + 0/60 |

# 9. Raster QA/QC ба confidence

| QA/QC item | QGIS дээр шалгах арга | Pass criteria | Fail / action |
| --- | --- | --- | --- |
| CRS | Layer Properties -> Source | EPSG:32647 | Wrong CRS бол reproject/georef дахин |
| Extent | Layer Properties -> Information + map canvas | License/buffer/map sheet-тэй logical overlap | Outside extent бол GCP/check coordinate |
| GCP count | Georeferencer GCP table | Scale-specific minimum хангагдсан | GCP нэмэх |
| Residual/RMSE | GCP residual table | Outlier багатай, grid alignment зөв | Outlier GCP-г шалгах/хасах |
| Grid alignment | Coordinate grid/tick давхцал | Булан болон дунд grid сайн таарсан | Transformation/GCP дахин |
| Visual distortion | Raster rotation/stretch | Уншигдахуйц, суналт хэтрээгүй | TPS/scan crop дахин |
| Raster completeness | Canvas display / overview | Зураг тасалдаагүй, эргээгүй | Export/render setting шалгах |
| Metadata | Inventory + properties | Source file, scale, year, map sheet бүртгэгдсэн | Metadata register бөглөх |


| Raster confidence | Шалгуур | Use status |
| --- | --- | --- |
| High | 8+ well-distributed GCP; grid/coordinate сайн; residual acceptable; license/topographic overlay сайн; scan quality good | Target-scale digitizing болон Phase 4 ranking-д ашиглаж болно |
| Medium | 4-8 GCP; minor distortion; overlay logical; зарим grid/scan issue байна | Overlay/interpretation-д болгоомжтой ашиглана |
| Low | GCP цөөн; grid тодорхойгүй; regional scale; visual match давамгайлсан | Context evidence; local target boundary болгохгүй |
| Needs verification | CRS/georef эргэлзээтэй; residual өндөр; feature location conflict | Vector digitizing хийхээс өмнө дахин шалгана |

## 9.1 Georeferenced raster output naming

| Raster theme | Output filename |
| --- | --- |
| 1987 Heavy mineral | XV023222_Buduunkhad_1987_L47-XIX_HeavyMineralSamplingResultsMap_1-200K_Georeferenced_EPSG32647_v02.tif |
| 1987 Stream sediment | XV023222_Buduunkhad_1987_L47-XIX_StreamSedimentPolyelementMap_1-200K_Georeferenced_EPSG32647_v02.tif |
| 1987 Geology | XV023222_Buduunkhad_1987_L47-XIX_GeologicalMap_1-200K_Georeferenced_EPSG32647_v02.tif |
| 1987 Mineral resources | XV023222_Buduunkhad_1987_L47-XIX_MineralResourcesMap_1-200K_Georeferenced_EPSG32647_v02.tif |
| 2013 Detailed geology | XV023222_Buduunkhad_2013_L47-74-A_GeologicalMap_1-50K_Georeferenced_EPSG32647_v02.tif |
| 2013 Mineral occurrence | XV023222_Buduunkhad_2013_L47-74-A_MineralOccurrenceMap_1-50K_Georeferenced_EPSG32647_v02.tif |
| 2013 Prospectivity | XV023222_Buduunkhad_2013_L47-74-A_ProspectivityAssessmentMap_1-50K_Georeferenced_EPSG32647_v02.tif |
| 2013 Source materials | XV023222_Buduunkhad_2013_L47-74-A_SourceMaterialsMap_1-50K_Georeferenced_EPSG32647_v02.tif |
| 2013 Mineral distribution | XV023222_Buduunkhad_2013_L47-73-74_MineralDistributionPatternMap_1-100K_Georeferenced_EPSG32647_v02.tif |
| 2013 Metallogenic scheme | XV023222_Buduunkhad_2013_L47-73-74_MetallogenicSchemeMetallogenogram_1-400K_Georeferenced_EPSG32647_v02.tif |
| 2020 Regional metallogenic | XV023222_Buduunkhad_2020_L47B_Talshand_RegionalMetallogenicMap_1-500K_Georeferenced_EPSG32647_v02.tif |

# 10. Vectorization strategy by map type

| Map type | Vector output | Use limit | Primary QA/QC |
| --- | --- | --- | --- |
| Geological maps | geology_units_50k_polygons, geology_units_200k_polygons, structures_faults_lines, intrusive_contacts_lines, dyke_vein_lines, alteration_zones_polygons | 1:50k = local evidence; 1:200k = regional evidence | Polygon topology, boundary match, symbol domain |
| Mineral occurrence / mineral resources maps | mineral_occurrences_points, mineralized_zones_polygons, ore_field_prospect_polygons, occurrence_labels, commodity groups | Historical map-derived evidence; field/lab confirmed гэж нэрлэхгүй | Point placement, commodity spelling, duplicate/cross-ref |
| Heavy mineral sampling maps | heavy_mineral_sample_points, heavy_mineral_anomaly_polygons, indicator_mineral_distribution_polygons, drainage_interpretation_lines | Drainage/source direction interpretation requires DEM/drainage check | Contour closure, drainage relation, indicator mineral domain |
| Stream sediment polyelement maps | stream_sediment_sample_points, stream_sediment_anomaly_polygons, geochemical_anomaly_contours_lines, drainage_anomaly_trend_lines | Multi-element suite field заавал бөглөнө | Element suite, anomaly class, drainage consistency |
| Prospectivity assessment maps | prospectivity_target_zones_polygons, priority_areas, named_prospects, recommended_followup_zones | Prospect polygon = historical interpretation; ranking-д confidence-тэй хэрэглэнэ | Target ID, evidence basis, priority consistency |
| Source materials maps | source_material_observation_points, source_material_route_lines, sample_points, trench_pit_shaft_channel_points, section_lines | QField validation, field route planning-д шууд хэрэгтэй | Route connectivity, station/sample ID, source symbol |
| Metallogenic maps | metallogenic_zones_polygons, ore_district_node_polygons, regional_structure_lines, regional_occurrence_context_points | Context only; local target boundary биш | Scale flag, use_limit, regional label |

# 11. Master GeoPackage design
Нэг Master GeoPackage үүсгэнэ: XV023222_Buduunkhad_HistoricalScannedMaps_Vectorized_MasterGIS_EPSG32647_v02.gpkg. Layer бүрийн CRS EPSG:32647 байна. Layer name lowercase_snake_case байна.

| No | Layer name | Geometry | Purpose |
| --- | --- | --- | --- |
| 01 | scan_map_index_polygons | Polygon | Georeferenced map extent, map ID, raster confidence |
| 02 | georeference_gcp_points | Point | GCP coordinate, residual, control source |
| 03 | geology_units_50k_polygons | Polygon | 2013 detailed geology units |
| 04 | geology_units_200k_polygons | Polygon | 1987 regional geology units |
| 05 | structures_faults_lines | LineString | Faults, inferred faults, lineaments |
| 06 | intrusive_contacts_lines | LineString | Intrusive/contact boundaries |
| 07 | dyke_vein_lines | LineString | Dyke, vein, quartz vein, section lines |
| 08 | alteration_zones_polygons | Polygon | Alteration zones if shown |
| 09 | mineral_occurrences_points | Point | Mineral occurrence/resource points |
| 10 | mineralized_zones_polygons | Polygon | Mineralized zones / ore fields |
| 11 | ore_field_prospect_polygons | Polygon | Ore field/prospect areas |
| 12 | heavy_mineral_sample_points | Point | Heavy mineral sample points if shown |
| 13 | heavy_mineral_anomaly_polygons | Polygon | Indicator mineral/anomaly polygons |
| 14 | stream_sediment_sample_points | Point | Stream sediment sample points if shown |
| 15 | stream_sediment_anomaly_polygons | Polygon | Polyelement anomaly polygons |
| 16 | geochemical_anomaly_contours_lines | LineString | Anomaly contour/dispersion lines |
| 17 | prospectivity_target_zones_polygons | Polygon | Prospectivity / priority target zones |
| 18 | source_material_observation_points | Point | Observation stations |
| 19 | source_material_route_lines | LineString | Field route lines |
| 20 | source_material_trench_pit_points | Point | Trench/pit/shaft/channel points |
| 21 | metallogenic_zones_polygons | Polygon | Regional metallogenic belt/zone polygons |
| 22 | regional_occurrence_context_points | Point | Regional occurrence points if shown |
| 23 | source_cross_reference | No geometry / table | Feature relationships across maps |
| 24 | data_confidence_ranking_spatial | Point/Polygon/Table | Spatial confidence features |
| 25 | data_gap_register_spatial | Point/Polygon/Table | Spatial data gaps |

## 11.1 GeoPackage үүсгэх QGIS алхам
- Browser Panel -> GeoPackage -> Create Database эсвэл Layer -> Create Layer -> New GeoPackage Layer сонгоно.
- Database path: 05_Vector_Digitized/XV023222_Buduunkhad_HistoricalScannedMaps_Vectorized_MasterGIS_EPSG32647_v02.gpkg гэж өгнө.
- Эхний layer-ийг үүсгэсний дараа дараагийн layer-үүдийг ижил database-д Add layer to existing database байдлаар нэмнэ.
- Geometry type, CRS EPSG:32647, attribute fields-ийг schema-ийн дагуу үүсгэнэ.
- Layer бүрт fid/geometry auto field-г user form дээр нууж, feature_id, source_map_id, confidence fields-ийг required болгоно.
- Layer style QML файлыг 05_Master_GIS_Database/Styles_QML хавтаст хадгалж version-той нэрлэнэ.
# 12. Field schema ба domain/lookup
## 12.1 Common source traceability fields

| Field | Type | Required | Purpose / domain |
| --- | --- | --- | --- |
| feature_id | Text | Yes | Unique feature ID, e.g. BUD-MIN-0001 |
| source_map_id | Text | Yes | BK-SCAN-xxx |
| source_file | Text | Yes | Raw filename |
| source_year | Integer | Yes | 1987/2013/2020/2021 |
| map_sheet | Text | Yes | L47-XIX / L47-74-A / L47B |
| map_scale | Text | Yes | 1:50,000 etc. |
| map_type | Text | Yes | Geology / mineral / heavy mineral / stream sediment |
| digitized_from_raster | Text | Yes | Georeferenced GeoTIFF filename |
| legend_file | Text | Recommended | Related legend file |
| original_symbol | Text | Recommended | Symbol as shown on map |
| original_label | Text | Recommended | Label/number on map |
| digitized_by | Text | Yes | Operator name |
| digitized_date | Date | Yes | Date of digitizing |
| geometry_source | Text | Yes | Domain: digitized/interpreted/approximate |
| geom_confidence | Text | Yes | High/Medium/Low/Needs verification |
| attribute_confidence | Text | Yes | High/Medium/Low/Unknown |
| overall_confidence | Text | Yes | High/Medium/Low/Needs verification |
| qaqc_status | Text | Yes | Draft/Checked/Approved/Rejected |
| validation_status | Text | Yes | Historical only/Field checked/Sampled/Lab confirmed/Not found/Not applicable |
| recommended_followup | Text | Recommended | Field check/Rock chip/Soil grid/No action/Data gap |
| comment | Text | No | Free text |

## 12.2 Standard domain values

| Field | Allowed values | Тайлбар |
| --- | --- | --- |
| geom_confidence | High; Medium; Low; Needs verification | Geometry/source position confidence |
| attribute_confidence | High; Medium; Low; Unknown | Legend/label/attribute confidence |
| overall_confidence | High; Medium; Low; Needs verification | Combined confidence |
| qaqc_status | Draft; Checked; Approved; Rejected | QA/QC workflow status |
| validation_status | Historical only; Field checked; Sampled; Lab confirmed; Not found; Not applicable | Field/lab verification status |
| geometry_source | Digitized from georeferenced historical scan; Derived from map symbol; Interpreted from contour; Approximate from regional map | Source geometry origin |
| scale_context | Local target-scale; Regional evidence; Metallogenic context; Report context | Map scale use limitation |
| use_limit | Can support target ranking; Use with caution; Context only; Do not use until verified | Use status |

# 13. Layer-specific schema
## 13.x Layer: geology_units_polygons

| Field name | Type | Required |
| --- | --- | --- |
| unit_id | Text | Yes |
| map_symbol | Text | Yes |
| lithology | Text | Yes |
| age | Text | Recommended |
| stratigraphic_unit | Text | Recommended |
| intrusive_type | Text | Optional |
| alteration | Text | Optional |
| description | Text | Optional |
| source_scale | Text | Yes |
| confidence | Text | Yes |
| comment | Text | No |

## 13.x Layer: structures_faults_lines

| Field name | Type | Required |
| --- | --- | --- |
| struct_id | Text | Yes |
| struct_type | Text | Yes |
| certainty | Text | Yes |
| trend | Text | Recommended |
| relation_to_mineralization | Text | Recommended |
| relation_to_intrusion | Text | Recommended |
| relation_to_geochemistry | Text | Recommended |
| source_symbol | Text | Recommended |
| confidence | Text | Yes |
| comment | Text | No |

## 13.x Layer: mineral_occurrences_points

| Field name | Type | Required |
| --- | --- | --- |
| occ_id | Text | Yes |
| map_no | Text | Recommended |
| occ_name | Text | Optional |
| commodity_raw | Text | Yes |
| commodity_1 | Text | Recommended |
| commodity_2 | Text | Optional |
| commodity_group | Text | Recommended |
| occurrence_type | Text | Recommended |
| mineralization | Text | Optional |
| lithology | Text | Optional |
| structure_relation | Text | Optional |
| target_style | Text | Optional |
| recommended_followup | Text | Recommended |
| confidence | Text | Yes |
| comment | Text | No |

## 13.x Layer: heavy_mineral_anomaly_polygons

| Field name | Type | Required |
| --- | --- | --- |
| anomaly_id | Text | Yes |
| mineral_indicator | Text | Yes |
| anomaly_class | Text | Recommended |
| source_material | Text | Recommended |
| drainage_relation | Text | Recommended |
| interpreted_source_direction | Text | Optional |
| confidence | Text | Yes |
| recommended_followup | Text | Recommended |
| comment | Text | No |

## 13.x Layer: stream_sediment_anomaly_polygons

| Field name | Type | Required |
| --- | --- | --- |
| anomaly_id | Text | Yes |
| element_suite | Text | Yes |
| dominant_element | Text | Recommended |
| associated_elements | Text | Recommended |
| anomaly_level | Text | Recommended |
| drainage_basin | Text | Optional |
| possible_source_area | Text | Optional |
| confidence | Text | Yes |
| recommended_followup | Text | Recommended |
| comment | Text | No |

## 13.x Layer: prospectivity_target_zones_polygons

| Field name | Type | Required |
| --- | --- | --- |
| target_id | Text | Yes |
| target_name | Text | Recommended |
| prospect_class | Text | Recommended |
| evidence_basis | Text | Yes |
| dominant_commodity | Text | Recommended |
| associated_commodities | Text | Optional |
| geology_control | Text | Recommended |
| structure_control | Text | Recommended |
| geochem_support | Text | Recommended |
| historical_work_support | Text | Recommended |
| priority | Text | Yes |
| data_gap | Text | Optional |
| recommended_next_work | Text | Recommended |
| confidence | Text | Yes |
| comment | Text | No |

## 13.x Layer: source_material_observation_points

| Field name | Type | Required |
| --- | --- | --- |
| obs_id | Text | Yes |
| route_id | Text | Recommended |
| station_no | Text | Recommended |
| observation_type | Text | Yes |
| lithology | Text | Optional |
| mineralization | Text | Optional |
| sample_reference | Text | Optional |
| trench_pit_reference | Text | Optional |
| confidence | Text | Yes |
| comment | Text | No |

## 13.x Layer: source_material_route_lines

| Field name | Type | Required |
| --- | --- | --- |
| route_id | Text | Yes |
| route_no | Text | Recommended |
| source_year | Integer | Yes |
| observer | Text | Optional |
| route_type | Text | Recommended |
| related_observations | Text | Optional |
| confidence | Text | Yes |
| comment | Text | No |

## 13.x Layer: metallogenic_zones_polygons

| Field name | Type | Required |
| --- | --- | --- |
| zone_id | Text | Yes |
| zone_name | Text | Recommended |
| metallogenic_unit | Text | Recommended |
| ore_formation | Text | Recommended |
| commodity_group | Text | Recommended |
| scale_context | Text | Yes |
| relation_to_license | Text | Recommended |
| confidence | Text | Yes |
| use_limit | Text | Yes |
| comment | Text | No |

# 14. QGIS digitizing SOP
- GeoTIFF raster layer-ийг 40-60% opacity-тэй болгож, contrast/stretch-ийг уншигдах хэмжээнд тохируулна. Raster-г засварлахгүй.
- Legend dictionary sheet-ийг нээлттэй байлгаж, symbol бүрийг стандарт domain value-тай тулгана.
- Зөв layer сонгосон эсэхээ шалгаж Toggle Editing асаана.
- Feature digitize хийхдээ map symbol-ийн төв, line-ийн гол, polygon boundary-ийн зураг дээрх бодит хүрээг баримтална.
- Feature бүрт feature_id болон source_map_id-г шууд өгнө. Feature ID давхцахгүй байх ёстой.
- original_symbol, original_label талбаруудыг map дээрх байдлаар бичнэ. Тодорхойгүй бол Unknown гэж бичээд data gap үүсгэнэ.
- Confidence-г геометр болон attribute тус бүрээр өгнө. Ерөнхий confidence нь хамгийн сул confidence-оос өндөр байж болохгүй.
- Editing дуусах бүрт Save Layer Edits хийнэ. Өдөр бүрийн төгсгөлд GeoPackage backup үүсгэнэ.
- QA/QC reviewer шалгасны дараа qaqc_status = Checked эсвэл Approved болгож өөрчилнө.

| Scale flag | Digitizing нарийвчлалын зарчим | Prohibited use |
| --- | --- | --- |
| 1:50,000 | Local / target-scale evidence. Илрэл, маршрут, target polygon, geology contact-д ашиглаж болно. | Field/lab баталгаагүй байхад reserve/resource conclusion хийхгүй. |
| 1:100,000 | Ore district / mineral distribution context. Polygon boundary-г ойролцоогоор авна. | Local target boundary мэт ашиглахгүй. |
| 1:200,000 | Regional geology/geochemistry/drainage evidence. Anomaly/structure-г regional support гэж хэрэглэнэ. | Detailed trench/soil grid location-ийг дангаар тогтоохгүй. |
| 1:400,000-1:500,000 | Metallogenic context only. Deposit model, regional belt, report figure-д хэрэглэнэ. | License доторх local target geometry гэж ашиглахгүй. |

# 15. Layer бүрийн нарийвчилсан SOP
## 15.1 Geological unit polygons
2013 1:50k болон 1987 1:200k geological map-аас lithology/stratigraphy нэгжүүдийг digitize хийнэ. Эхлээд major unit boundary, дараа нь intrusive body, alteration zone, dyke/vein separate layer болгон оруулна. Polygon closure, overlap, sliver шалгана. 1:50k layer-ийг geology_units_50k_polygons, 1:200k layer-ийг geology_units_200k_polygons гэж тусгаарлана.
## 15.2 Structures/faults/lineaments
Fault, inferred fault, contact, lineament, shear, fold axis, vein trend зэрэг line feature-ийг structures_faults_lines layer-д оруулна. certainty = Observed/Inferred/Interpreted; trend = NE-SW/NW-SE/N-S/E-W гэх мэт. Илрэл, геохими, intrusive contact-тай хамаарал байвал relation_to_mineralization талбарт тэмдэглэнэ.
## 15.3 Mineral occurrence points
Mineral occurrence symbol-ийн төвд point тавина. commodity_raw-д map дээрх тэмдэглэгээг яг бичнэ; commodity_1/2-д standardized element оруулна. Au-Cu, Cu, Mo, As, Zn зэрэг spelling-ийг lookup-тай тулгана. Map no, label тодорхойгүй бол attribute_confidence = Low/Unknown.
## 15.4 Heavy mineral layers
Individual sample point харагдаж байвал sample point digitize хийнэ. Anomaly/indicator mineral contour харагдаж байвал polygon эсвэл line contour болгон оруулна. DEM/drainage layer-тай давхарлаж interpreted_source_direction-г зөвхөн тайлбарлагдсан үед бөглөнө.
## 15.5 Stream sediment polyelement layers
Polyelement anomaly contour, drainage dispersion, sample point-уудыг тусад нь digitize хийнэ. element_suite field-д Cu Pb Zn Ag As Bi W Sn Mo Mn Ba F зэрэг багцуудыг нэг мөр стандарт бичнэ. Anomaly level тодорхойгүй бол data gap үүсгэнэ.
## 15.6 Source materials layers
Route lines, observation station, sample point, trench/pit/shaft/channel, section line-уудыг тусдаа layer-д оруулна. Field route planning болон QField validation-д хамгийн ашигтай тул route_id, station_no, sample_reference талбарыг аль болох бүрэн бөглөнө.
## 15.7 Prospectivity target zones
Prospectivity map дээрх Б-3 Толь хяр, Г-1 зэрэг target/prospect zone-уудыг polygon хэлбэрээр оруулна. evidence_basis-д occurrence, geology, geochem, historical work support-ыг бичнэ. priority = P1/P2/P3/P4 гэж өгч, regional map-аас авсан polygon бол use_limit = Context only гэж тэмдэглэнэ.
## 15.8 Metallogenic context
1:400k-1:500k regional metallogenic map-аас belt, ore district, node, ore formation polygon/point-ийг context layer болгон оруулна. Энэ layer-ийг Phase 3 concept model болон Phase 4 scoring support-д ашиглах боловч local field target boundary биш.
# 16. Excel register workbook
Нэг QA/QC workbook гаргана: XV023222_Buduunkhad_HistoricalScannedMaps_Vectorization_Register_QAQC_v02.xlsx. Workbook нь GIS layer бүрийн attribute export, GCP, QA/QC, confidence, data gap, handover checklist-ийг нэг дор хадгална.

| Sheet | Purpose |
| --- | --- |
| 00_README | Workbook purpose, version, owner, CRS, definitions |
| 01_Map_Inventory | 21 scan map/report file metadata |
| 02_Map_Legend_Linkage | Main map + legend + symbol dictionary status |
| 03_Georeference_GCP_Table | GCP coordinates, source, residual |
| 04_Georeference_QAQC | Raster QA/QC results and raster confidence |
| 05_Geology_Units_Register | Geology polygon export |
| 06_Structures_Register | Fault/structure/line export |
| 07_Mineral_Occurrences_Register | Occurrence point export |
| 08_HeavyMineral_Register | Heavy mineral point/polygon export |
| 09_StreamSediment_Register | Stream sediment anomaly/sample export |
| 10_Prospectivity_Target_Register | Prospect/target zone export |
| 11_Source_Materials_Register | Route/obs/sample/trench export |
| 12_Metallogenic_Context_Register | Regional metallogenic context export |
| 13_Topology_QAQC | Geometry/topology check log |
| 14_Attribute_QAQC | NULL/domain/ID/spelling check log |
| 15_Confidence_Ranking | Raster/vector confidence scoring |
| 16_Data_Gap_Register | Gap type, impact, action, owner |
| 17_Change_Log | Date/operator/action/input/output/status |
| 18_Handover_Checklist | Final acceptance and phase handover status |
| 19_Source_Cross_Reference | Cross-map evidence relationship table |
| 20_Lookups_Domains | Domain values for QGIS forms |

## 16.1 GCP table sheet schema

| Column | Type | Description |
| --- | --- | --- |
| gcp_id | Text | Map_ID + sequence, e.g. BK-SCAN-009-GCP-001 |
| source_map_id | Text | BK-SCAN-xxx |
| pixel_x | Decimal | Georeferencer pixel x |
| pixel_y | Decimal | Georeferencer pixel y |
| map_x | Decimal | Target CRS Easting or longitude |
| map_y | Decimal | Target CRS Northing or latitude |
| coord_source | Text | Grid intersection / tick / boundary / topographic feature |
| residual_x | Decimal | Residual x |
| residual_y | Decimal | Residual y |
| residual_total | Decimal | Total residual |
| used_in_transform | Text | Yes / No |
| review_note | Text | Outlier or accepted note |

# 17. QA/QC checklist

| QA/QC group | Check item | Pass criteria |
| --- | --- | --- |
| File inventory | Бүх raw file бүртгэгдсэн эсэх | 21 scanned map/report file Map Inventory-д орсон |
| File inventory | Main map ба legend холбоотой эсэх | Map-to-legend linkage register бөглөгдсөн |
| File inventory | Raw file өөрчлөгдөөгүй эсэх | Raw archive checksum / working copy path бүртгэгдсэн |
| CRS / georeference | CRS EPSG:32647 эсэх | Final GeoTIFF/vector layer EPSG:32647 |
| CRS / georeference | GCP хангалттай эсэх | Scale-specific GCP minimum хангагдсан |
| CRS / georeference | Residual error acceptable эсэх | GCP residual report хадгалагдсан, outlier note бичигдсэн |
| CRS / georeference | Overlay check | License boundary / basemap / DEM / other map-тэй logical overlap |
| Geometry | Invalid / empty geometry | QGIS Check validity OK |
| Geometry | Duplicate feature | Duplicate geometry / duplicate ID шалгасан |
| Geometry | Polygon overlap/sliver | Topology check хийсэн |
| Geometry | Point outside map extent/license/buffer | Flag or data gap created |
| Geometry | Line dangle/overshoot/undershoot | Structure/route/contact line-д reviewer check хийсэн |
| Attribute | Required NULL | Required fields бүрэн бөглөгдсөн |
| Attribute | ID uniqueness | feature_id, occ_id, anomaly_id, target_id unique |
| Attribute | Commodity/element spelling | Domain list-тэй нийцсэн |
| Attribute | Source traceability | source_map_id/source_file/digitized_from_raster бүрэн |
| Interpretation | Scale-use flag | Regional map-derived feature local target мэт хэтрүүлээгүй |
| Interpretation | Historical vs confirmed | Historical map-derived data field/lab confirmed data-тай холигдоогүй |
| Handover | Workbook complete | Required sheets бөглөгдсөн |
| Handover | README and change log | Handover note complete |

# 18. Confidence ranking logic
Бүх raster болон vector output-д source quality, scan quality, legend clarity, GCP quality, georeference accuracy, map scale suitability, digitizing clarity, attribute completeness, cross-map consistency, field validation status гэсэн шалгуураар confidence үнэлгээ өгнө. Ерөнхий confidence нь хамгийн сул critical criterion-оос өндөр байж болохгүй.

| Criterion | Score 0 | Score 1 | Score 2 | Weight |
| --- | --- | --- | --- | --- |
| Source quality | Unknown source | Known file but partial metadata | Known source + year + scale + map sheet | 10% |
| Scan quality | Unreadable/poor | Usable with unclear areas | Clear symbols/labels | 10% |
| Legend clarity | Missing | Partial/unclear | Clear linked legend | 10% |
| GCP quality | Insufficient/weak | Minimum met | Well-distributed preferred count | 15% |
| Georeference accuracy | High residual/conflict | Acceptable regional | Good overlay/grid | 15% |
| Map scale suitability | Too regional | Regional/context | Target-scale/local | 10% |
| Digitizing clarity | Approximate | Mostly clear | Clear symbol/boundary | 10% |
| Attribute completeness | Many NULL/unknown | Minor gaps | Complete required fields | 10% |
| Cross-map consistency | Conflict | Not checked/neutral | Supports other evidence | 5% |
| Validation status | Historical only | Field checked/sample pending | Sampled/lab confirmed | 5% |


| Total score | Confidence class | Use status |
| --- | --- | --- |
| >=80 | High | Target ranking-д ашиглаж болно; field validation шаардлагатай хэвээр |
| 60-79 | Medium | Overlay/interpretation-д болгоомжтой ашиглана |
| 40-59 | Low | Context evidence; decision-grade ашиглахгүй |
| <40 or critical fail | Needs verification | Ашиглахаас өмнө дахин шалгах, field/lab/report validation шаардлагатай |

# 19. Data gap register

| Gap type | Impact | Required action | Owner / status field |
| --- | --- | --- | --- |
| Missing legend | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Unclear legend | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Poor scan quality | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Weak coordinate grid | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Insufficient GCP | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| High residual error | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| CRS uncertainty | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Symbol unreadable | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Attribute uncertain | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Feature duplicated across maps | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Conflicting feature location | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Scale too regional for local use | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Field validation required | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Lab confirmation required | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |
| Report text needed to interpret map | Confidence бууруулна / handover-д анхааруулга болно | Review, re-georeference, validate with field/lab/report, or use as context only | gap_owner, due_date, status |


| Data gap register column | Description |
| --- | --- |
| gap_id | Unique ID, e.g. BUD-GAP-001 |
| source_map_id | Related BK-SCAN ID |
| feature_id | Related feature if spatial |
| gap_type | Controlled gap type |
| gap_description | Detailed issue |
| impact_on_use | How it affects use |
| confidence_impact | Decrease / hold / exclude |
| required_action | What to do |
| responsible_person | Owner |
| due_date | Target date |
| status | Open / In progress / Closed / Deferred |
| closure_note | How it was resolved |

# 20. Cross-map integration
Vector evidence-үүдийг нэг map-аас авсан дан мэдээлэл гэж үзэхгүй. Дараах overlay / consistency check-ийг хийж confidence-д нөлөөлүүлнэ.

| Overlay pair | Шалгах зүйл | Confidence impact | QGIS tool / method |
| --- | --- | --- | --- |
| 2013 mineral occurrence points vs 2013 geology | Occurrence нь favorable lithology/contact/structure дээр байгаа эсэх | Match бол confidence өснө; mismatch бол data gap | Join attributes by location, Select by location |
| 2013 prospectivity zones vs mineral occurrence points | Target zone дотор occurrence cluster байгаа эсэх | Давхцалтай бол P1/P2 ranking support | Count points in polygon |
| 2013 source materials routes/observations vs occurrence points | Historic observation/sample/trench point давхцах эсэх | Field validation planning-д шууд ашиглана | Distance to nearest hub / buffer |
| 1987 stream sediment anomalies vs geology | Anomaly drainage favorable lithology/structure-аас эхтэй эсэх | Drainage source confidence нэмэгдэнэ | Overlay + DEM drainage analysis |
| 1987 heavy mineral anomalies vs DEM/drainage/geology | Indicator mineral source direction logical эсэх | Orientation soil/stream sediment planning support | Drainage catchment overlay |
| 1987 mineral resources vs 2013 mineral occurrence | Historical occurrence continuity байгаа эсэх | Cross-source support нэмэгдэнэ | Spatial join + attribute compare |
| 2013 metallogenic scheme vs 2020/2021 regional metallogenic map | Ore formation / belt consistency | Deposit model support | Overlay and narrative register |
| All evidence vs license boundary and buffers | License дотор/гадна/буферийн байрлал | Field work priority болон use limit тогтооно | Clip, intersection, distance |


| Cross-map consistency field | Description |
| --- | --- |
| evidence_id | Feature/evidence ID |
| related_map_1 | First map ID |
| related_map_2 | Second map ID |
| match_type | Overlap / Near / Conflict / Supports / No relation |
| spatial_relationship | Within / intersects / adjacent / upstream / downstream |
| geological_relationship | Contact / same unit / structure controlled / no relation |
| confidence_impact | Increase / Neutral / Decrease / Needs verification |
| required_action | Field check / review legend / re-georef / report check |

# 21. Handover package ба acceptance criteria

| Deliverable | File / folder | Use | Acceptance criteria |
| --- | --- | --- | --- |
| Master QGIS Project | XV023222_Buduunkhad_HistoricalScannedMaps_Vectorization_QGIS_EPSG32647_v02.qgz | Layer overlay, review, map production, QField package preparation | Opens without missing layers; relative paths OK |
| Master GeoPackage | XV023222_Buduunkhad_HistoricalScannedMaps_Vectorized_MasterGIS_EPSG32647_v02.gpkg | All vector evidence layers in EPSG:32647 | All mandatory layers created or documented as N/A |
| Georeferenced GeoTIFF folder | 04_Georeference_Check/02_Georeferenced_Rasters | Base raster for audit and future redigitizing | Priority map GeoTIFF complete + QAQC |
| Excel QA/QC workbook | XV023222_Buduunkhad_HistoricalScannedMaps_Vectorization_Register_QAQC_v02.xlsx | Register, QA/QC, confidence, data gap, change log | Required sheets complete; no missing required fields |
| PDF index maps | Phase1_Master_GIS_Index_Maps.pdf | Review / reporting | License + evidence layers shown |
| README + Change log | README.txt, Change_Log.xlsx | Audit trail and handover note | Version, CRS, source note, limitations documented |


| Handover phase | Required layers | Decision use |
| --- | --- | --- |
| Phase 3 Geological / Metallogenic Synthesis | Geology, structures, metallogenic zones, occurrence context | Concept model, deposit style, regional context |
| Phase 4 Preliminary Prospect Ranking | Occurrence, target zones, geology, geochem anomalies, confidence layers | Evidence scoring, A/B/C/D ranking |
| Phase 6 Recon Mapping and pXRF | QField-ready observation/source materials/target points | Field validation and pXRF route planning |
| Phase 7 Rock Chip Sampling | Mineral occurrences, structures, target zones, source observations | Rock chip candidate locations |
| Phase 8/9 Soil / Stream Sediment Planning | Drainage, heavy mineral, stream sediment anomaly, geology/structure | Orientation survey and systematic grid planning |
| QField field validation package | Approved subset of points/targets/routes + forms | Mobile field verification |

# 22. Final workflow diagram
Raw Scanned Maps + Legends
  -> Working Copy + File Inventory
  -> Map-Legend Linkage Register
  -> CRS / Georeference Status Audit
  -> QGIS Georeferencing + GCP Table
  -> Georeferenced GeoTIFF EPSG:32647
  -> Georeference QA/QC + Raster Confidence Ranking
  -> Vector Digitizing by Map Type
  -> GeoPackage Layers + Source Traceability
  -> Attribute Domain Validation
  -> Topology / Geometry / Attribute QA/QC
  -> Excel Registers + QA/QC Workbook
  -> Cross-Map Evidence Integration
  -> Confidence Ranking + Data Gap Register
  -> Master GIS / QField / Prospect Ranking Handover
# 23. Appendices
## Appendix A - Feature ID naming standard

| Layer | ID prefix | Example |
| --- | --- | --- |
| geology_units_50k_polygons | BUD-GEO50 | BUD-GEO50-0001 |
| geology_units_200k_polygons | BUD-GEO200 | BUD-GEO200-0001 |
| structures_faults_lines | BUD-STR | BUD-STR-0001 |
| mineral_occurrences_points | BUD-MIN | BUD-MIN-0001 |
| heavy_mineral_anomaly_polygons | BUD-HM-AN | BUD-HM-AN-0001 |
| stream_sediment_anomaly_polygons | BUD-SS-AN | BUD-SS-AN-0001 |
| prospectivity_target_zones_polygons | BUD-TGT | BUD-TGT-0001 |
| source_material_observation_points | BUD-OBS | BUD-OBS-0001 |
| source_material_route_lines | BUD-RTE | BUD-RTE-0001 |
| metallogenic_zones_polygons | BUD-MET | BUD-MET-0001 |
| data_gap_register_spatial | BUD-GAP | BUD-GAP-0001 |

## Appendix B - QGIS Field Calculator expressions

| Purpose | Expression | Тайлбар |
| --- | --- | --- |
| UTM Easting | x($geometry) | Point layer-д x_utm |
| UTM Northing | y($geometry) | Point layer-д y_utm |
| Longitude WGS84 | x(transform($geometry, @layer_crs, 'EPSG:4326')) | Point geometry longitude |
| Latitude WGS84 | y(transform($geometry, @layer_crs, 'EPSG:4326')) | Point geometry latitude |
| Polygon area km2 | area($geometry) / 1000000 | Target/geology polygon талбай |
| Line length km | length($geometry) / 1000 | Route/fault/structure length |
| Feature ID example | concat('BUD-MIN-', lpad(@row_number,4,'0')) | Draft ID үүсгэх |

## Appendix C - QField package preparation note
- QField-д зөвхөн Approved эсвэл Checked status-тэй local target-scale layers оруулна.
- Context-only 1:400k/1:500k metallogenic layer-ийг field package-д заавал оруулах шаардлагагүй; шаардлагатай бол non-editable reference layer болгоно.
- Field editable layer-үүд: source_material_observation_points, mineral_occurrences_points_validation_copy, prospectivity_target_zones_polygons_reference, source_material_route_lines_reference.
- Form tab: Source / Geometry / Observation / Mineralization / Confidence / Photo / QAQC.
- fid, system fields, geometry fields-ийг user form дээр hide хийнэ. Required fields-д constraint тавина.
## Appendix D - Чанарын хяналтын анхааруулга
- Historical scanned map-derived vector data нь хүдэржилтийг батлах decision-grade evidence биш.
- Field validation, rock chip sampling, pXRF screening, laboratory assay шаардлагатай.
- Georeferenced scan map-ийн positional accuracy-г confidence flag-гүй ашиглаж болохгүй.
- Regional scale map-аас гарсан polygon/line-г local target boundary мэт ашиглаж болохгүй.
- Raster дээрх map symbol-ийг vector болгохдоо source_file, source_map_id, original_symbol, original_label талбаруудыг заавал бөглөнө.
- Raw scan file-г overwrite хийхгүй. Version update бүрт v02, v03 гэх мэтээр нэмэгдүүлнэ.
# Critical QA/QC Notes
- Raw data-г засварлахгүй; processing copy дээр ажиллана.
- Final deliverables-ийн CRS нь EPSG:32647; native/raw CRS-г metadata-д хадгална.
- .tfw, .aux.xml, .ovr, .rpc, .eph, .txt зэрэг sidecar файлуудыг parent raster/image-тэй хамт хадгална.
- Scan map/georeferenced map-ийн positional accuracy-г residual болон confidence flag-тай хэрэглэнэ.
- ASTER final binary mask, Sentinel alteration ratio, KOMPSAT visual lineament, drone interpretation нь хүдэржилтийн баталгаа биш.
- pXRF нь lab assay-г орлохгүй; Au-ийн pXRF response-ийг decision-grade гэж үзэхгүй.
- CMCS/MRPAM nearest deposit нь contextual evidence бөгөөд тухайн license дотор хүдэржилт байгаа эсэхийг шууд батлахгүй.
- Final target confidence нь хээрийн шалгалт, дээжлэлт, лабораторийн assay, structural/geological evidence, шаардлагатай бол trench/geophysics/scout drilling-аар баталгаажна.
# Methodology Limitation
- Энэ баримт бичиг нь methodology / workflow guide бөгөөд бодит raster processing, vector digitizing, assay interpretation, target grade estimation хийгээгүй.
- 78 raw input file-ийн агуулга, spatial correctness, coordinate accuracy, file integrity нь Phase 1 Data Audit-ээр баталгаажсаны дараа л analysis-ready гэж үзнэ.
- Remote sensing index болон alteration proxy нь surface condition, vegetation, shadow, weathering, sensor limitations, CRS/pixel alignment-аас хамаарч буруу response өгөх боломжтой.
- Historical map scale (1:500,000, 1:200,000, 1:50,000) нь target-scale field decision-д шууд хангалтгүй; field verification шаардлагатай.
- Эцсийн follow-up болон scout drilling decision нь энэ document-ийн workflow-оос гадна permit, land access, HSE, budget, environmental and legal requirements-тай нийцэх ёстой.
