<!-- source: Phase_3_Geological_Metallogenic_and_CMCS_Synthesis_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

Доорхыг 03. Phase 3 — Geological, Metallogenic and CMCS Synthesis хэсэгт “илүү тодруулсан аргачлал” болгон шууд нэмж/орлуулж болно. Одоо байгаа баримтад Phase 3 нь №1-8, №53-72 input-ийг голчлон ашиглаж, 03A дэд workflow нь №47-78 болон №9-46 support output-уудыг deposit model-д туслах evidence болгон татах логиктой байна.
03. Phase 3 — Geological, Metallogenic and CMCS Synthesis: Дэлгэрүүлсэн аргачлал
03.1 Зорилго
Phase 3-ийн зорилго нь Бүдүүн хад / XV-023222 / L23222 талбайн геологийн суурь, структур, интрузив/contact, ашигт малтмалын илрэл, эрдэсжсэн цэг, хэтийн төлөвтэй хэсэг, металлогений бүс, CMCS/MRPAM орд-илрэлийн context-ийг нэг Master GIS орчинд нэгтгэж, дараагийн Phase 4 prospect ranking болон Phase 10 final target ranking-д ашиглах geological evidence base үүсгэх явдал юм.
Энэ шат нь орд батлах шат биш. Phase 3-аас гарах бүх output нь “historical/contextual/preliminary support evidence” бөгөөд хээрийн шалгалт, дээжлэлт, лабораторийн шинжилгээ, structural validation хийгдэх хүртэл decision-grade evidence гэж үзэхгүй.
03.2 Ашиглах үндсэн input
Phase 3-д дараах raw input-уудыг шууд ашиглана:

| Input № | Агуулга | Phase 3-д ашиглах зорилго |
| --- | --- | --- |
| №1-7 | Tectonic / terrane context зураг, тайлбар | Lake island arc terrane, Ulaanshand Zone, Nuur Accretionary Megazone context тодорхойлох |
| №8 | License boundary KMZ | Overlay, clipping, buffer, CMCS/MRPAM search boundary |
| №53-56 | 1:200k болон 1:50k geological map + legend | Геологийн нэгж, lithology, contact, fault, intrusive, vein, alteration digitize хийх |
| №57-58 | Mineral resources map + legend | Региональ илрэл, anomaly, ore field context digitize хийх |
| №59-61 | Mineral distribution / metallogenic scheme | Ore district, ore node, metallogenic trend, ore formation context |
| №62-65 | Prospectivity assessment, source materials map + legend | Б-3 Толь хяр, Г-1 зэрэг prospectivity zone, route, observation, sample, trench/pit/source material digitize хийх |
| №66-68 | Gold occurrence description, mineralized point register/table | Илрэл, эрдэсжсэн цэгийн координат, агуулга, commodity, lithology, structure-г occurrence database болгох |
| №69-72 | Regional metallogenic map/report | 1:500k metallogenic belt, ore formation, commodity association, regional context |

Phase 3-ийн 03A deposit model дэд workflow-д Phase 2-оос гарсан Sentinel/ASTER/KOMPSAT/DEM derivative output-уудыг зөвхөн support evidence байдлаар ашиглана. Remote sensing, DEM, KOMPSAT, ASTER output нь хүдэржилтийн баталгаа биш.

03.3 Ажиллах folder structure
03_Phase_3_Geological_Metallogenic_and_CMCS_Synthesis/
├── 01_Input_Working_Copy
├── 02_Tectonic_Terrane_Context
├── 03_Regional_Metallogenic_1M500K
├── 04_Regional_Geology_Mineral_1M200K
├── 05_Local_Geology_Occurrence_1M50K
├── 06_Source_Materials_and_Prospectivity
├── 07_Occurrence_Register_and_Coordinate_QAQC
├── 08_CMCS_MRPAM_Buffer_Check_5km_10km_20km
├── 09_Geological_Evidence_Layers_GPKG
├── 10_Preliminary_Deposit_Model_03A
├── 11_Evidence_Scoring_and_DataGap
└── 12_Phase3_QAQC_and_Handover

03.4 Алхамчилсан аргачлал
Алхам 1 — Phase 1/2 output-уудыг шалгаж авах
Phase 3 эхлэхээс өмнө дараах зүйлс бэлэн эсэхийг шалгана:

| Шалгах зүйл | Шаардлага |
| --- | --- |
| Master QGIS project | EPSG:32647 CRS-тэй, missing layer байхгүй |
| License boundary | №8-аас үүссэн EPSG:32647 GeoPackage layer |
| Georeference QA/QC log | Scan map бүрийн GCP, residual, scale, confidence бүртгэгдсэн |
| Phase 2 remote sensing output | Sentinel/ASTER/KOMPSAT/DEM support layer-үүд EPSG:32647-д бэлэн |
| Data confidence ranking | High / Medium / Low / Needs verification үнэлгээтэй |

Phase 1-д scan map бүрийн georeference residual, GCP count, map scale, reviewer/date/decision-г бүртгэх ёстой гэж баримтад заасан тул Phase 3 нь энэ QA/QC бүртгэл дээр тулгуурлана.
Алхам 2 — Tectonic / terrane context нэгтгэх
№1-7 input-ийг тус бүрээр шалгаж, дараах register үүсгэнэ:
Output:
XV023222_Buduunkhad_Tectonic_Terrane_Context_Register_v01.xlsx
Register-ийн баганууд:

| Field | Тайлбар |
| --- | --- |
| source_raw_input_no | №1-7 |
| source_raw_filename | Exact filename |
| terrane_zone_name | Lake Terrane / Ulaanshand Zone / Nuur Accretionary Megazone гэх мэт |
| evidence_type | map / explanatory text / regional tectonic interpretation |
| relevance_to_project | project boundary-тэй ямар context-ээр холбогдох |
| source_scale | мэдэгдэж байвал |
| confidence | High / Medium / Low / Needs verification |
| limitation | scanned, non-native, georeference unknown гэх мэт |
| use_in_deposit_model | ямар candidate model-д context болох |

Энэ шатанд terrane map-уудыг local ore target boundary мэт ашиглахгүй. Зөвхөн regional geological setting, tectonic affinity, deposit model screening context болгон ашиглана.
Алхам 3 — 1:500,000 regional metallogenic context боловсруулах
№69-72 input-ийг ашиглана.
Хийх ажил:
№69 legend scan-аас ore formation, commodity, symbol dictionary гаргана.
№70 metallogenic map-ийг georeference хийж, license boundary + 20 km buffer-тэй overlay хийнэ.
№71-72 report PDF-ээс project area-тэй холбоотой metallogenic belt, ore formation, commodity association, regional occurrence мэдээллийг evidence register-д оруулна.
1:500k scale-ийн хязгаарлалтыг заавал тэмдэглэнэ.
Output:
XV023222_Buduunkhad_L47B_RegionalMetallogenic_Legend_Dictionary_v01.xlsx
XV023222_Buduunkhad_2020_L47B_Talshand_RegionalMetallogenicMap_1-500K_Georeferenced_EPSG32647_v01.tif
metallogenic_zones_polygons_EPSG32647_v01.gpkg
XV023222_Buduunkhad_RegionalMetallogenic_Context_Map_v01.pdf
XV023222_Buduunkhad_RegionalMetallogenic_Evidence_Register_v01.xlsx
Алхам 4 — 1:200,000 regional geology/mineral resources боловсруулах
№53-54 болон №57-58 input-ийг ашиглана.
Хийх ажил:
№53 geological map-ийг georeference хийнэ.
№54 legend scan-аас lithology, age, intrusive, fault, contact, symbol dictionary гаргана.
Геологийн нэгжүүдийг polygon layer болгон digitize хийнэ.
Fault, structure, intrusive contact-уудыг line layer болгон digitize хийнэ.
№57 mineral resources map-ийг georeference хийж, ore field, occurrence, anomaly, mineralized zone-уудыг point/polygon layer болгоно.
№58 legend-аас commodity болон occurrence type lookup table үүсгэнэ.
Output:
XV023222_Buduunkhad_1987_L47-XIX_GeologicalMap_1-200K_Georeferenced_EPSG32647_v01.tif
geology_units_200k_polygons_EPSG32647_v01.gpkg
structures_faults_200k_lines_EPSG32647_v01.gpkg
XV023222_Buduunkhad_1987_L47-XIX_MineralResourcesMap_1-200K_Georeferenced_EPSG32647_v01.tif
regional_mineral_occurrences_points_EPSG32647_v01.gpkg
regional_mineralized_zones_polygons_EPSG32647_v01.gpkg
Алхам 5 — 1:50,000 local geology, occurrence, prospectivity боловсруулах
№55-68 input нь Phase 3-ийн хамгийн чухал local-scale evidence болно.
Хийх ажил:

| Input | Хийх ажил |
| --- | --- |
| №55 | 1:50k geology map georeference, lithology/contact/fault/vein/alteration digitize |
| №56 | Legend dictionary: stratigraphy, lithology, intrusive, alteration, vein type |
| №60 | Au-Cu, Cu, Mo, As, Zn occurrence points digitize |
| №63 | Б-3 Толь хяр, Г-1 зэрэг prospectivity polygons digitize |
| №64 | Route, observation, sample, trench/pit, section line digitize |
| №65 | Source material symbol/domain dictionary |
| №66 | Gold occurrence description-аас coordinate, grade, lithology, structure extract |
| №67 | Mineral occurrence/mineralized point PDF register extract |
| №68 | XLSX mineralized point table clean, coordinate validation, GIS point layer үүсгэх |

Output:
XV023222_Buduunkhad_2013_L47-74-A_GeologicalMap_1-50K_Georeferenced_EPSG32647_v01.tif
geology_units_50k_polygons_EPSG32647_v01.gpkg
structures_faults_50k_lines_EPSG32647_v01.gpkg
intrusive_contacts_lines_EPSG32647_v01.gpkg
dyke_vein_lines_EPSG32647_v01.gpkg
mineral_occurrences_points_EPSG32647_v01.gpkg
prospectivity_target_zones_polygons_EPSG32647_v01.gpkg
source_material_observation_points_EPSG32647_v01.gpkg
source_material_route_lines_EPSG32647_v01.gpkg
source_material_trench_pit_points_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Mineral_Occurrences_Register_v01.xlsx
Алхам 6 — Coordinate болон attribute QA/QC хийх
№66, №67, №68-аас гарсан occurrence/mineralized point data-г хооронд нь тулгана.
Шалгах зүйл:

| QA/QC item | Тайлбар |
| --- | --- |
| Coordinate format | WGS84 lat/long, UTM, local grid эсэх |
| CRS conversion | EPSG:4326 → EPSG:32647 зөв хөрвүүлсэн эсэх |
| Duplicate point | Ижил нэр, ижил координат, ойролцоо давхцал |
| Commodity consistency | Au, Cu, Mo, As, Zn, Pb, W, Sn, Bi гэх мэт нэг мөр кодчилох |
| Map-register match | №60 map дээрх occurrence №68 table-тэй таарч байгаа эсэх |
| Confidence flag | map-derived / table-derived / text-derived / uncertain |
| Validation status | Historical only гэж тэмдэглэх |

Output:
XV023222_Buduunkhad_Occurrence_CrossReference_7255_4186_v01.xlsx
XV023222_Buduunkhad_Occurrence_Coordinate_QAQC_Log_v01.xlsx
XV023222_Buduunkhad_Validated_Historical_Occurrence_Points_EPSG32647_v01.gpkg
Алхам 7 — CMCS/MRPAM 5 km, 10 km, 20 km buffer check хийх
№8 license boundary-аас 5 km, 10 km, 20 km buffer үүсгээд CMCS/MRPAM nearest deposit/occurrence мэдээллийг тусад нь register болгоно. Одоо байгаа баримтад CMCS evidence нь зөвхөн contextual support бөгөөд тухайн license дотор хүдэржилт байгааг батлахгүй гэж тэмдэглэх шаардлагатай.
Хийх ажил:
License boundary-аас 5 km, 10 km, 20 km buffer polygon үүсгэнэ.
CMCS/MRPAM-ээс deposit, occurrence, mineralized point, commodity, deposit type, distance, direction мэдээлэл авна.
Buffer доторх болон ойролцоох илрэлүүдийг distance/rank-аар ангилна.
“Context only — not proof of mineralization inside license” гэсэн limitation талбар оруулна.
Output:
XV023222_Buduunkhad_CMCS_MRPAM_Buffer_5km_10km_20km_EPSG32647_v01.gpkg
XV023222_Buduunkhad_CMCS_Nearest_Deposit_Register_v01.xlsx
XV023222_Buduunkhad_CMCS_Context_Map_v01.pdf
Алхам 8 — Geological evidence layer-үүдийг нэг Master GPKG-д нэгтгэх
Phase 3-ийн бүх vector output-ийг нэг GeoPackage-д нэгтгэнэ.
Output file:
XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg
GeoPackage дотор байх layer-үүд:
license_boundary
buffer_5km_10km_20km
tectonic_terrane_context_polygon
metallogenic_zones_polygon
ore_district_node_context_polygon
geology_units_200k_polygon
geology_units_50k_polygon
faults_structures_line
intrusive_contacts_line
dyke_vein_line
mineral_occurrences_point
mineralized_points_point
prospectivity_target_zones_polygon
source_material_observation_point
source_material_route_line
source_material_trench_pit_point
cmcs_nearest_occurrences_point
Layer бүрт дараах mandatory field байна:

| Field | Тайлбар |
| --- | --- |
| source_raw_input_no | 1-78 дугаар |
| source_raw_filename | exact raw filename |
| source_group | evidence group |
| processing_phase | 03 эсвэл 03A |
| source_scale | 1:50k / 1:200k / 1:500k |
| geometry_type | point / line / polygon |
| evidence_type | geology / structure / occurrence / metallogenic / prospectivity |
| validation_status | Historical only / Field checked / Sampled / Lab confirmed |
| confidence | High / Medium / Low / Needs verification |
| limitation | scale, scan, georef, coordinate uncertainty |
| processing_version | v01, v02 гэх мэт |
| reviewer | шалгасан хүн |
| review_date | огноо |

Алхам 9 — 03A Preliminary Deposit Model Preparation хийх
03A нь Phase 3-ийн заавал хийх дэд workflow байна. Энэ шатанд Au-Cu hydrothermal vein, intrusion-related Cu-Au-Mo, skarn/contact metasomatic, polymetallic vein, VMS possibility, heavy mineral/placer indicator гэсэн candidate model бүрийг тусад нь үнэлнэ. Одоо байгаа баримтад эдгээр candidate model-ийг supporting evidence, missing evidence, validation work хүснэгтээр үнэлэхээр заасан байна.
Deposit model evidence table:

| Deposit model | Supporting evidence | Missing evidence | Validation work | Preliminary confidence |
| --- | --- | --- | --- | --- |
| Au-Cu hydrothermal vein | quartz vein, Au-Cu occurrence, fault/shear, As-Bi support | vein continuity, width, lab Au grade | recon mapping, rock chip/channel, Au fire assay | High / Moderate / Low |
| Intrusion-related Cu-Au-Mo | intrusive contact, Cu-Mo-Bi-As, stockwork/alteration support | alteration zoning, sulphide confirmation | ASTER validation, soil grid, IP/magnetic | Moderate |
| Skarn/contact metasomatic | intrusive-carbonate contact, W-Bi-Cu, magnetite/skarn minerals | carbonate host, garnet/epidote confirmation | contact mapping, petrography, pXRF W/Bi/Cu | Moderate / Low |
| Polymetallic vein | Pb-Zn-Cu-Ag-As, vein/shear, gossan | grade and continuity | rock chip/channel, soil grid | Moderate / Low |
| VMS possibility | volcanic-sedimentary context, Cu-Zn-Pb-Ba-Fe-Mn | stratiform sulphide texture | stratigraphic mapping, IP, magnetic | Conceptual |
| Heavy mineral / placer | drainage/shlich anomaly, Au/W/Sn indicator | bedrock source | upstream sampling, panning, geomorphology | Contextual |

Output:
XV023222_Buduunkhad_Preliminary_Deposit_Model_v01.docx
preliminary_deposit_model_evidence_table_v01.xlsx
deposit_model_candidate_score_matrix_v01.xlsx
Алхам 10 — Evidence weight scoring хийх
Deposit model бүрийг 100 оноогоор preliminary score өгнө.

| Шалгуур | Оноо |
| --- | --- |
| Favorable geology / host lithology | 20 |
| Intrusive/contact/structure control | 15 |
| Known mineral occurrence | 15 |
| Historical geochemistry / shlich / stream sediment | 15 |
| Metallogenic context | 10 |
| ASTER/Sentinel alteration support | 10 |
| Field mapping / pXRF support | 10 |
| Access / workability | 5 |
| Нийт | 100 |

Confidence class:

| Оноо | Ангилал |
| --- | --- |
| ≥70 | High priority model |
| 50-69 | Moderate priority model |
| 30-49 | Low / conceptual model |
| <30 | Insufficient evidence |

Алхам 11 — Phase 3 QA/QC хийх

| QA/QC item | Acceptance criteria |
| --- | --- |
| Map scale limitation recorded | 1:50k, 1:200k, 1:500k ялгаж тэмдэглэсэн |
| Georeference confidence recorded | GCP count, residual, reviewer/date/decision бүртгэсэн |
| Occurrence coordinate validated | map/table/text source хооронд тулгасан |
| CMCS not used as proof | context only limitation бичсэн |
| Remote sensing not used as ore proof | support evidence гэж тэмдэглэсэн |
| Historical vector not mixed with confirmed data | validation_status = Historical only |
| Deposit model evidence/missing evidence table complete | model бүрээр бөглөсөн |
| Output source traceability complete | source_raw_input_no, filename, phase, confidence бүрэн |

Алхам 12 — Phase 4 ба Phase 10 руу handover хийх
Phase 3-ийн output нь Phase 4-ийн prospect ranking-д шууд орно. Phase 4 дээр prospect polygon бүрт dominant_deposit_model, model_confidence, missing_model_evidence, validation_priority талбар нэмэх ёстой гэж баримтад заасан байна.
Handover package:
XV023222_Buduunkhad_Geological_Evidence_Layers_v01.gpkg
XV023222_Buduunkhad_CMCS_Nearest_Deposit_Register_v01.xlsx
XV023222_Buduunkhad_Regional_Metallogenic_Context_Map_v01.pdf
XV023222_Buduunkhad_Preliminary_Deposit_Model_v01.docx
deposit_model_candidate_score_matrix_v01.xlsx
XV023222_Buduunkhad_Phase3_QAQC_Log_v01.xlsx
XV023222_Buduunkhad_Phase3_DataGap_and_Validation_Priority_v01.xlsx
Decision gate
Phase 3 дууссан гэж үзэх нөхцөл:
№1-8, №53-72 input-уудын геологи, структур, илрэл, prospectivity, metallogenic context Master GIS-д орсон байх.
Occurrence/mineralized point coordinate QA/QC хийгдсэн байх.
CMCS/MRPAM 5 km, 10 km, 20 km buffer register бэлэн байх.
Preliminary Deposit Model.docx болон score matrix бэлэн байх.
Бүх historical evidence validation_status = Historical only гэж тэмдэглэгдсэн байх.
Phase 4 рүү шилжүүлэх A/B/C prospect ranking-д хэрэглэх geological evidence package бэлэн байх.
