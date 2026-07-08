<!-- source: Phase_4_Preliminary_Prospect_Delineation_and_Ranking_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

# 04-р үе шатны ажлын дэлгэрэнгүй заавар
Preliminary Prospect Delineation and Ranking
Энэхүү баримт бичиг нь “04. Phase 4 — Preliminary Prospect Delineation and Ranking” ажлыг бодитоор гүйцэтгэх дэлгэрэнгүй аргачлал, folder structure, QGIS болон scoring spreadsheet-ийн шаардлага, QA/QC шалгалт, expected output болон decision gate-ийг бүрэн тусгасан заавар юм.

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Desktop evidence-үүдийг 100 онооны scoring matrix-аар preliminary prospect болгох. |
| Input files | Input files: Phase 1–3 processed outputs + source raw inputs №1–78 as traceable evidence basis. Key direct evidence sources: №47–52 geochemistry/field observations, №53–68 geology/occurrence/prospectivity/source materials, №69–72 metallogenic context, №9–46 and №73–78 terrain/remote sensing support, №8 license boundary. |
| Software / equipment | QGIS, scoring spreadsheet, prospect register. |

# 1. Ажлын зорилго
Энэ ажлын зорилго нь хайгуулын өмнөх үе шатуудаас боловсруулсан геологи, структур, эрдэсжилт, геохими, remote sensing, DEM terrain, field observation болон CMCS/лицензийн мэдээллийг нэгтгэж дараах үр дүнг гаргах явдал юм.
- Боломжит prospect polygon-уудыг зурж тогтоох;
- Prospect бүрт нотлох баримтын давхаргуудыг холбох;
- 100 онооны scoring matrix ашиглан үнэлгээ хийх;
- Prospect бүрийг A/B/C/D ангилалд оруулах;
- Дараагийн шатанд drone survey, reconnaissance mapping, эсвэл data gap нөхөх ажлыг санал болгох;
- Go / No-Go шийдвэрийн үндэслэл гаргах.
# 2. Ашиглах үндсэн input файлууд
## 2.1 Phase 1–3-аас гарсан боловсруулсан output
Үүнд дараах боловсруулсан үр дүн, spatial layer болон тайлбар материалууд орно.
- Геологийн нэгтгэсэн зураглал;
- Литологи, структур, fault, shear zone, contact zone;
- Alteration / mineralization indication;
- Remote sensing interpretation;
- DEM terrain analysis;
- Deposit model preparation;
- Existing occurrence / mineral showing мэдээлэл;
- Field observation point;
- Stream sediment / heavy mineral / geochemical anomaly;
- License boundary болон access нөхцөл.
## 2.2 Source raw input evidence
Зурагт дурдсан evidence эх сурвалжуудыг prospect polygon бүртэй traceable байдлаар холбож өгөх шаардлагатай.
- №1–78: traceable evidence basis;
- №47–52: geochemistry / field observations;
- №53–68: geology / occurrence / prospectivity source materials;
- №69–72: metallogenic context;
- №9–46 болон №73–78: terrain / remote sensing support;
- №8: license boundary.
# 3. Ажлын folder structure
Phase 4-ийн бүх файлыг дараах бүтэцтэй хадгална.
04_Phase_4_Preliminary_Prospect_Delineation_and_Ranking/
├── 01_Evidence_Overlay/
├── 02_Prospect_Polygon_Delineation/
├── 03_Scoring_Matrix/
├── 04_Confidence_DataGap_NextAction/
└── 05_A_B_C_D_Field_Priority/
## Folder бүрийн зориулалт
### 01_Evidence_Overlay
Бүх нотлох давхаргуудыг нэг QGIS project-д давхарлаж харуулах folder.
- Evidence overlay QGIS project;
- Geology layer;
- Occurrence layer;
- Geochemistry anomaly layer;
- Stream / heavy mineral layer;
- ASTER / Sentinel interpretation;
- KOMPSAT lineament / outcrop interpretation;
- DEM terrain layer;
- CMCS context;
- License boundary.
### 02_Prospect_Polygon_Delineation
Prospect polygon зурсан үндсэн spatial dataset-ууд хадгалагдана.
- Prospect polygon geopackage;
- Polygon drawing version history;
- Prospect boundary notes;
- Draft target areas;
- Final preliminary prospect polygons.
### 03_Scoring_Matrix
100 онооны үнэлгээний spreadsheet хадгалагдана.
- Prospect бүрийн оноо;
- Evidence category score;
- Confidence score;
- Data gap;
- Ranking;
- A/B/C/D ангилал;
- Reviewer note;
- Decision log.
### 04_Confidence_DataGap_NextAction
Prospect бүрийн итгэлцүүр, дутуу мэдээлэл, дараагийн хийх ажлын санал хадгалагдана.
- Confidence flag;
- Missing evidence;
- Recommended validation work;
- Drone survey requirement;
- Recon mapping requirement;
- Sampling requirement;
- Access / safety note.
### 05_A_B_C_D_Field_Priority
Эцсийн эрэмбэлсэн prospect жагсаалт болон field priority map хадгална.
- A priority prospect;
- B priority prospect;
- C retained with data gap;
- D low priority / no-go;
- Field campaign planning map;
- Go / No-Go decision matrix.
# 4. Програм, хэрэгсэл
## 4.1 QGIS
QGIS дээр дараах ажлуудыг гүйцэтгэнэ.
- Evidence layer-үүдийг overlay хийх;
- Prospect polygon зурах;
- Атрибут хүснэгт үүсгэх;
- Score-ийг spatial layer-тэй холбох;
- Ranking map гаргах;
- Layout map экспортлох.
## 4.2 Excel / Google Sheets
Spreadsheet дээр дараах ажлуудыг гүйцэтгэнэ.
- 100 онооны scoring matrix боловсруулах;
- Prospect бүрийн оноо бодох;
- A/B/C/D ангилал автоматаар гаргах;
- Data gap болон next action бүртгэх;
- QA/QC log хөтлөх.
## 4.3 Prospect register
Prospect бүрийн үндсэн бүртгэлийг хөтөлнө.

| Талбар | Тайлбар |
| --- | --- |
| Prospect_ID | Жишээ: PR-01, PR-02 |
| Prospect_Name | Талбайн нэр |
| License_No | Лицензийн дугаар |
| Area_ha | Талбайн хэмжээ |
| Dominant_Deposit_Model | Гол deposit model |
| Model_Confidence | High / Medium / Low |
| Evidence_Score | Нотлох мэдээллийн оноо |
| Total_Score | Нийт 100 оноо |
| Class | A / B / C / D |
| Data_Gap | Дутуу мэдээлэл |
| Next_Action | Drone / Recon / Sampling / Hold |
| Access_Risk | Low / Medium / High |
| Safety_Risk | Low / Medium / High |
| Reviewer | Хянасан хүн |
| Decision_Date | Шийдвэрийн огноо |

# 5. Алхамчилсан ажлын аргачлал
## Алхам 1. Phase 1–3 output-уудыг шалгах
Юуны өмнө Phase 1, Phase 2, Phase 3-аас гарсан бүх output бүрэн байгаа эсэхийг шалгана.
Шалгах зүйлс:
- Геологийн layer бүрэн эсэх;
- Occurrence / mineral showing dataset байгаа эсэх;
- Geochemistry anomaly dataset байгаа эсэх;
- Remote sensing interpretation layer байгаа эсэх;
- DEM terrain result байгаа эсэх;
- Deposit model preparation output байгаа эсэх;
- License boundary зөв эсэх;
- Coordinate reference system нэг стандартад байгаа эсэх;
- Файлын нэршил project naming convention-тэй нийцэж байгаа эсэх.
Хэрэв CRS өөр байвал бүх spatial layer-ийг нэг CRS-д хөрвүүлнэ. Жишээ нь Mongolia-д ихэвчлэн UTM zone-based projection ашиглаж болно.
## Алхам 2. Evidence overlay үүсгэх
QGIS дээр шинэ project үүсгээд дараах layer-үүдийг нэг дор оруулна.
Давхарлах layer-үүд:
- License boundary;
- Geological units;
- Fault / structure / lineament;
- Known mineral occurrence;
- Geochemical anomaly;
- Stream sediment result;
- Heavy mineral result;
- Alteration / ASTER;
- Sentinel interpretation;
- KOMPSAT lineament / outcrop;
- DEM slope / ridge / drainage;
- Access road / track;
- Field observation point;
- CMCS / regional metallogenic context.
Энэ overlay-ийн зорилго нь нэг газар дээр олон төрлийн эерэг нотолгоо давхцаж байгаа хэсгүүдийг илрүүлэх юм.
## Алхам 3. Evidence давхцлын бүсүүдийг тодорхойлох
QGIS дээр дараах асуултаар талбайг шинжилнэ.
- Геохимийн anomaly нь fault эсвэл contact zone-той давхцаж байна уу?
- Known occurrence-тэй ойролцоо байна уу?
- ASTER alteration signature илэрч байна уу?
- DEM terrain нь structural control-той нийцэж байна уу?
- Remote sensing lineament нь geological structure-тэй давхцаж байна уу?
- Stream / heavy mineral result тухайн drainage basin-д эерэг байна уу?
- Field observation point дээр mineralization, alteration, vein, gossan, quartz zone тэмдэглэгдсэн үү?
- Deposit model-той нийцэх geological setting байна уу?
- Access болон safety condition field work хийх боломжтой юу?
Эдгээр асуултын хариултаар preliminary prospect candidate area-уудыг сонгоно.
## Алхам 4. Prospect polygon зурах
Evidence давхцсан хэсгүүд дээр prospect polygon зурна.
### Polygon зурах үндсэн зарчим
Prospect polygon нь дараах шаардлагыг хангана.
- Геологийн хувьд утгатай байх;
- Нэг deposit model эсвэл нэг structural trend-тэй холбоотой байх;
- Evidence concentration бүхий хэсгийг хамрах;
- Хэт том, ерөнхий boundary биш байх;
- Хэт жижиг, ганц point-д тулгуурласан биш байх;
- Field validation хийх боломжтой хэмжээтэй байх;
- Лицензийн boundary дотор байх;
- Access болон terrain нөхцөлтэй уялдах.
### Polygon зурахад анхаарах зүйл
Prospect boundary-г дараах шалтгаанаар тогтооно.
- Fault / shear zone дагасан trend;
- Lithological contact;
- Alteration zone;
- Geochemical anomaly envelope;
- Occurrence cluster;
- Drainage catchment;
- Remote sensing lineament;
- Terrain expression;
- Outcrop distribution.
Polygon бүрт заавал Prospect_ID өгнө.
Жишээ:
PR-01
PR-02
PR-03
PR-04
## Алхам 5. Prospect polygon attribute table үүсгэх
QGIS-ийн polygon layer дээр дараах attribute талбаруудыг үүсгэнэ.

| Field name | Type | Тайлбар |
| --- | --- | --- |
| Prospect_ID | Text | PR-01 гэх мэт |
| Prospect_Name | Text | Prospect нэр |
| Area_ha | Decimal | Га талбай |
| License_No | Text | Лицензийн дугаар |
| Dominant_Model | Text | Гол deposit model |
| Model_Confidence | Text | High / Medium / Low |
| Geo_Evidence | Integer | Геологийн оноо |
| Geochem_Evidence | Integer | Геохимийн оноо |
| Occurrence_Evidence | Integer | Occurrence оноо |
| RS_Evidence | Integer | Remote sensing оноо |
| Terrain_Evidence | Integer | DEM/terrain оноо |
| Access_Score | Integer | Access score |
| Safety_Risk | Text | Low / Medium / High |
| Data_Gap | Text | Дутуу мэдээлэл |
| Next_Action | Text | Drone / Recon / Sampling |
| Total_Score | Integer | Нийт оноо |
| Class | Text | A / B / C / D |
| Reviewer | Text | Хянасан хүн |
| Decision | Text | Go / Hold / No-Go |

# 6. 100 онооны scoring matrix боловсруулах
Prospect бүрийг нийт 100 оноогоор үнэлнэ. Доорх жишиг матрицыг ашиглаж болно.
## 6.1 Санал болгож буй scoring structure

| Үнэлгээний бүлэг | Дээд оноо | Тайлбар |
| --- | --- | --- |
| Geological setting | 20 | Литологи, contact, structure, alteration |
| Mineral occurrence evidence | 15 | Known occurrence, showing, field observation |
| Geochemical evidence | 20 | Stream, soil, rock, heavy mineral anomaly |
| Remote sensing evidence | 15 | ASTER, Sentinel, KOMPSAT indication |
| Structural / lineament control | 10 | Fault, shear, fold, lineament density |
| Deposit model fit | 10 | Phase 3 deposit model-той нийцэл |
| Access / field practicality | 5 | Зам, terrain, logistics |
| Confidence / data completeness | 5 | Evidence-ийн бүрэн байдал |
| Нийт | 100 |  |

## 6.2 Geological setting score — 20 оноо

| Нөхцөл | Оноо |
| --- | --- |
| Favorable lithology + structure + alteration бүгд илэрсэн | 17–20 |
| Favorable lithology + structure байгаа, alteration сул | 13–16 |
| Зөвхөн favorable lithology эсвэл structure байгаа | 8–12 |
| Геологийн үндэслэл сул | 1–7 |
| Нотлох мэдээлэл байхгүй | 0 |

## 6.3 Mineral occurrence evidence — 15 оноо

| Нөхцөл | Оноо |
| --- | --- |
| Prospect дотор known mineral occurrence / showing байгаа | 12–15 |
| Prospect-той шууд ойролцоо occurrence байгаа | 8–11 |
| Regional occurrence trend-тэй холбоотой | 4–7 |
| Occurrence evidence сул | 1–3 |
| Байхгүй | 0 |

## 6.4 Geochemical evidence — 20 оноо

| Нөхцөл | Оноо |
| --- | --- |
| Олон element anomaly + coherent spatial pattern | 17–20 |
| Нэгээс дээш sample type дээр anomaly батлагдсан | 13–16 |
| Нэг төрлийн geochemical anomaly байгаа | 8–12 |
| Сул эсвэл isolated anomaly | 1–7 |
| Байхгүй | 0 |

## 6.5 Remote sensing evidence — 15 оноо

| Нөхцөл | Оноо |
| --- | --- |
| ASTER/Sentinel alteration + KOMPSAT lineament/outcrop давхцсан | 12–15 |
| Хоёр remote sensing evidence давхцсан | 8–11 |
| Нэг төрлийн RS evidence байгаа | 4–7 |
| Сул indication | 1–3 |
| Байхгүй | 0 |

## 6.6 Structural / lineament control — 10 оноо

| Нөхцөл | Оноо |
| --- | --- |
| Major structure, intersection, fault corridor дээр байрласан | 8–10 |
| Structure-тэй тодорхой холбоотой | 5–7 |
| Regional trend-тэй сул холбоотой | 2–4 |
| Structural evidence байхгүй | 0–1 |

## 6.7 Deposit model fit — 10 оноо
Phase 3-ийн Deposit Model Preparation-аас гарсан model score-ийг энд заавал холбож оруулна.

| Нөхцөл | Оноо |
| --- | --- |
| Deposit model-той маш сайн нийцсэн | 8–10 |
| Дунд зэрэг нийцсэн | 5–7 |
| Сул нийцсэн | 2–4 |
| Нийцэл тодорхойгүй | 0–1 |

Prospect бүрт дараах талбаруудыг нэмнэ:
- dominant_deposit_model
- model_confidence
- missing_model_evidence
- validation_priority
## 6.8 Access / field practicality — 5 оноо

| Нөхцөл | Оноо |
| --- | --- |
| Хялбар хүрэх боломжтой, field validation хийхэд тохиромжтой | 5 |
| Дунд зэргийн access | 3–4 |
| Хүнд access, terrain risk өндөр | 1–2 |
| Field access боломжгүй эсвэл аюултай | 0 |

## 6.9 Confidence / data completeness — 5 оноо

| Нөхцөл | Оноо |
| --- | --- |
| Олон төрлийн evidence бүрэн, traceable | 5 |
| Ихэнх evidence байгаа боловч minor gap байна | 3–4 |
| Гол evidence дутуу | 1–2 |
| Маш их data gap байна | 0 |

# 7. A/B/C/D ангиллын дүрэм
Нийт оноог дараах байдлаар ангилна.

| Ангилал | Оноо | Тайлбар | Дараагийн арга хэмжээ |
| --- | --- | --- | --- |
| A | ≥75 | Өндөр ач холбогдолтой prospect | Drone survey + recon mapping + sampling |
| B | 55–74 | Дунд-өндөр ач холбогдолтой | Recon mapping + selective sampling |
| C | 35–54 | Data gap ихтэй, хадгалж ажиглах | Нэмэлт мэдээлэл цуглуулах |
| D | <35 | Бага ач холбогдолтой | No-Go эсвэл low priority archive |

# 8. Confidence flag, data gap, next action бөглөх
Prospect polygon бүр дээр оноо өгөхөөс гадна дараах гурван зүйлийг заавал бөглөнө.
## 8.1 Confidence flag

| Flag | Тайлбар |
| --- | --- |
| High | Олон эх сурвалжийн evidence давхцсан |
| Medium | Зарим evidence байгаа боловч баталгаажуулалт хэрэгтэй |
| Low | Evidence сул, data gap өндөр |

## 8.2 Data gap
Жишээ data gap:
- Геохимийн sample density хангалтгүй;
- Field observation point байхгүй;
- Alteration interpretation баталгаажаагүй;
- Occurrence мэдээлэл хуучин;
- Deposit model evidence дутуу;
- Access road тодорхойгүй;
- DEM terrain risk шалгаагүй;
- License boundary overlap шалгах шаардлагатай.
## 8.3 Next action
Жишээ next action:
- Drone survey;
- Reconnaissance mapping;
- Rock chip sampling;
- Stream sediment infill sampling;
- Soil sampling;
- Ground truthing of alteration;
- Structural traverse;
- Access route inspection;
- No immediate action.
# 9. QA/QC шалгалт
Phase 4-ийн QA/QC нь зөвхөн map харах биш, scoring болон decision process зөв эсэхийг шалгах зорилготой.
## QA/QC checklist

| QA/QC item | Шалгах зүйл |
| --- | --- |
| 100-point matrix calculated | Prospect бүрийн оноо бүрэн бодогдсон эсэх |
| Confidence / data gap / next action filled | Дутуу талбар үлдээгүй эсэх |
| A/B/C/D class reviewed | Ангилал оноотой нийцэж байгаа эсэх |
| Field access and safety checked | Field ажил хийх боломж, эрсдэл шалгасан эсэх |
| Deposit model score linked | Phase 3 deposit model score орсон эсэх |
| Evidence traceability checked | Prospect бүр ямар эх сурвалжаар дэмжигдсэн нь тодорхой эсэх |
| Reviewer / date / decision recorded | Хэн, хэзээ, ямар шийдвэр гаргасан нь бүртгэгдсэн эсэх |

QA/QC бүрийг phase QA/QC log-д бүртгэнэ.
# 10. Expected outputs
Эцэст нь дараах output файлуудыг гаргана.
XV-023222_Buduunkhad_Preliminary_Prospect_Ranking_Map.pdf
XV-023222_Buduunkhad_Prospect_Polygons.gpkg
XV-023222_Buduunkhad_Prospect_Ranking_Table.xlsx
XV-023222_Buduunkhad_Go_NoGo_Desktop_Decision_Matrix.xlsx
## Output бүрийн агуулга
### 10.1 Preliminary Prospect Ranking Map PDF
Энэ зурагт дараах зүйлс орно.
- License boundary;
- Prospect polygon;
- A/B/C/D color-coded ангилал;
- Key evidence layer;
- Major structure;
- Occurrence;
- Geochemical anomaly;
- Remote sensing evidence;
- Access route;
- North arrow, scale bar, legend;
- Coordinate grid;
- Data source note;
- Reviewer/date.
### 10.2 Prospect Polygons GPKG
GeoPackage файлд дараах зүйлс орно.
- Prospect polygon geometry;
- Prospect_ID;
- Total_Score;
- Class;
- Dominant_Model;
- Confidence;
- Data_Gap;
- Next_Action;
- QA/QC status.
### 10.3 Prospect Ranking Table XLSX
Excel хүснэгтэд дараах зүйлс орно.
- Prospect бүрийн scoring;
- Evidence category оноо;
- Нийт оноо;
- A/B/C/D ангилал;
- Data gap;
- Next action;
- Reviewer decision.
### 10.4 Go / No-Go Desktop Decision Matrix XLSX
Энэ файл нь удирдлагын шийдвэр гаргах зориулалттай.

| Prospect | Score | Class | Confidence | Key evidence | Data gap | Next action | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PR-01 | 82 | A | High | Geo + geochem + RS | Minor | Drone + recon | Go |
| PR-02 | 63 | B | Medium | Geo + structure | Geochem gap | Recon | Go |
| PR-03 | 44 | C | Low | RS only | Field gap | Data infill | Hold |
| PR-04 | 28 | D | Low | Weak | Major gap | None | No-Go |

# 11. Field priority decision
Эцсийн шийдвэрийг дараах байдлаар гаргана.
## A ангилал
A prospect нь хамгийн түрүүнд шалгах талбай.
Шаардлагатай ажил:
- Drone survey;
- Recon mapping;
- Rock chip sampling;
- Structural mapping;
- Ground truthing;
- Detailed field photo log.
## B ангилал
B prospect нь боломжийн талбай боловч A-аас бага priority.
Шаардлагатай ажил:
- Recon mapping;
- Selective sampling;
- Access шалгалт;
- Data gap нөхөх.
## C ангилал
C prospect нь шууд field campaign-д оруулахгүй байж болно. Гэхдээ хадгалж, data gap нөхсөний дараа дахин үнэлнэ.
Шаардлагатай ажил:
- Remote review;
- Additional sampling design;
- Evidence re-check;
- Deposit model reassessment.
## D ангилал
D prospect нь одоогоор бага ач холбогдолтой.
Шийдвэр:
- No-Go;
- Archive;
- Дараагийн шатанд оруулахгүй;
- Зөвхөн шинэ evidence гарвал дахин нээж үнэлнэ.
# 12. Ажлын чанарын үндсэн зарчим
Энэ үе шатанд хамгийн чухал зарчим нь оноо бүр evidence-тэй холбогдсон байх юм.
Буруу арга:
PR-01 = 85 оноо
Учир нь сайн харагдаж байна.
Зөв арга:
PR-01 = 85 оноо
Учир нь:
- Favorable lithology + fault intersection байна;
- Stream geochemical anomaly давхцсан;
- ASTER alteration signature илэрсэн;
- Known occurrence 500 м дотор байна;
- Phase 3 deposit model score өндөр;
- Access боломжтой.
Өөрөөр хэлбэл prospect ranking нь зөвхөн мэргэжлийн таамаг биш, харин traceable evidence-based decision байх ёстой.
# 13. Гүйцэтгэх дарааллын товч workflow
1. Phase 1–3 output шалгах
2. Бүх spatial layer-ийг QGIS-д нэг CRS-д оруулах
3. Evidence overlay project үүсгэх
4. Evidence давхцлын бүсүүдийг тодорхойлох
5. Prospect polygon зурах
6. Polygon attribute table бөглөх
7. Phase 3 deposit model score холбох
8. 100 онооны scoring matrix бөглөх
9. Total score тооцох
10. A/B/C/D ангилал гаргах
11. Confidence flag, data gap, next action бөглөх
12. Field access болон safety risk шалгах
13. QA/QC review хийх
14. Prospect ranking map экспортлох
15. Prospect ranking table болон Go/No-Go matrix гаргах
16. A/B prospect-уудыг дараагийн field work-д санал болгох
# 14. Эцсийн decision gate
Phase 4 дуусахад дараах шийдвэр гарсан байх ёстой.
A/B prospects → drone survey болон reconnaissance mapping-д шилжинэ.
C/D prospects → data gap-тайгаар хадгална эсвэл low priority/no-go болгоно.
Ингэснээр Phase 5 буюу field validation / drone / reconnaissance ажилд зөвхөн хамгийн өндөр үндэслэлтэй prospect-уудыг сонгон оруулах боломжтой болно.
