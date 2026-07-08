<!-- source: Phase_9_Systematic_Soil_Grid_Laboratory_QAQC_Detailed_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

09. Phase 9 — Systematic Soil Grid and Laboratory QA/QC
Системтэй хөрсний торлолын дээжлэлт, лабораторийн шинжилгээ, QA/QC баталгаажуулалт хийх дэлгэрэнгүй ажлын заавар

# 1. Ажлын зорилго
Phase 9-ийн үндсэн зорилго нь өмнөх шатны хайгуулын мэдээлэлд үндэслэн сонгогдсон сонирхолтой талбайнуудад хөрсний системтэй торлолын дээжлэлт хийж, лабораторийн шинжилгээгээр геохимийн аномалийг баталгаажуулах юм. Энэ үе шатны үр дүн нь дараагийн trench, geophysics, drilling target сонгох техникийн үндэслэл болно.
Энэ ажлын төгсгөлд хөрсний геохимийн баталгаажсан аномалийн зураг, QA/QC тайлан, лабораторийн баталгаажсан үр дүн, sample point database, final target ranking update бэлэн болсон байна.
- Cu, Au, Ag, Pb, Zn, Mo, As, Sb зэрэг элементүүдийн хөрсөн дэх тархалтыг тодорхойлох;
- Өмнөх фазуудаар таамагласан хүдэржилтийн бүс геохимийн аномали үүсгэж байгаа эсэхийг шалгах;
- Порфир, эпитермаль, судлын, скарн, полиметалл төрлийн боломжит хүдэржилтийн геохимийн илэрхийллийг таних;
- Дараагийн шатанд суваг малталт, trench, IP/resistivity, drilling хийх эсэх шийдвэрийг гаргах;
- Target ranking буюу зорилтот бүсүүдийг ач холбогдлоор нь шинэчлэн эрэмбэлэх.
# 2. Methodology summary / эх мэдээллийн товч бүртгэл

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Validated method-gap systematic soil geochemical coverage хийх. Өмнөх orientation result, target ranking, geological/structural interpretation болон field evidence-д үндэслэн хөрсний торлол төлөвлөж лабораторийн QA/QC баталгаажуулалт хийнэ. |
| Input files | Phase 8 orientation results + direct planning support raw inputs №8 boundary, №9–22 DEM/slope/drainage, №47–52 historical drainage/heavy mineral/field evidence, №55/60/63/64/68 local geology-occurrence-source evidence, №75–78 basemaps/Sentinel support. Exact filenames in Section 1A. |
| Software / equipment | QGIS grid design, field collection tools, pXRF, laboratory assay. |

# 3. Processing folder structure
Ажлын бүх файлыг дараах бүтэцтэй хадгална. Фолдерын нэршил, дэс дарааллыг өөрчлөхгүй байх нь өгөгдлийн мөрдөх чадвар, QA/QC audit trail-д чухал.
09_Phase_9_Systematic_Soil_Grid_and_Laboratory_QAQC/
├── 01_Grid_Design_200x50_100x25_50x25_25x10
├── 02_Field_Collection
├── 03_pXRF_Screening
├── 04_Lab_Submission_QAQC
├── 05_Assay_Validation
└── 06_Soil_Anomaly_Map
## 3.1 Folder тус бүрийн зориулалт

| Folder | Зориулалт |
| --- | --- |
| 01_Grid_Design_200x50_100x25_50x25_25x10 | Хөрсний дээж авах торлолын загвар, sample point layer, traverse line, grid spacing decision, orientation result хадгална. |
| 02_Field_Collection | Талбайн дээжлэлт, sample register, GPS point, field photo, lithology/soil description, duplicate location зэрэг мэдээллийг хадгална. |
| 03_pXRF_Screening | pXRF-ийн урьдчилсан хэмжилт, field screening result, raw pXRF file, pXRF QA/QC sheet хадгална. |
| 04_Lab_Submission_QAQC | Лабораторид илгээх дээжийн жагсаалт, submission form, CRM, blank, duplicate байрлал, chain-of-custody document хадгална. |
| 05_Assay_Validation | Лабораторийн үр дүн, QA/QC шалгалт, detection limit, unit conversion, duplicate performance, CRM accuracy, blank contamination check хадгална. |
| 06_Soil_Anomaly_Map | Эцсийн хөрсний аномалийн зураг, элемент тус бүрийн anomaly map, multi-element target map, final interpretation map хадгална. |

# 4. Ажил эхлэхийн өмнөх бэлтгэл
## 4.1 Coordinate system шалгах
Бүх spatial data ижил coordinate reference system буюу CRS-д байх ёстой. Монгол орны баруун болон төвийн бүсэд ажиллаж байгаа бол тухайн талбайн байршлаас хамааран UTM zone зөв сонгоно. Жишээ нь WGS 84 / UTM Zone 47N буюу EPSG:32647 ашиглаж болно.
1.  QGIS нээнэ.
2.  Project → Properties → CRS цэсээр project CRS-ийг шалгана.
3.  Layer бүрийн CRS-ийг Layer Properties → Source хэсгээс шалгана.
4.  Өөр CRS-тэй layer байвал Export → Save Features As ашиглан зөв CRS-ээр дахин хадгална.
5.  Бүх layer нэг project-д зөв давхцаж байгаа эсэхийг license boundary, drainage, basemap дээр тулган шалгана.
## 4.2 Өмнөх фазын target area шалгах
Phase 9 хийх талбайг бүх лицензийн хэмжээнд шууд хийхгүй. Өмнөх фазуудаар батлагдсан, олон эх сурвалжийн давхцалтай хэсгийг сонгож systematic soil grid байрлуулна.
- Geological favourable unit;
- Fault / fracture intersection;
- Alteration zone;
- Drainage anomaly;
- Heavy mineral anomaly;
- Historical mineral occurrence;
- Rock chip sample anomaly;
- pXRF anomaly;
- Satellite alteration anomaly;
- Accessible terrain;
- Soil cover suitable area.
# 5. Grid spacing буюу торлолын зай сонгох аргачлал
Grid spacing нь Phase 8 orientation result-д үндэслэн сонгогдоно. Нэг талбайд нэгээс олон grid spacing ашиглаж болно. Жишээлбэл: зах хэсэгт recon grid, төв хэсэгт target grid, өндөр аномалийн хэсэгт infill grid, нарийн судлын бүсэд vein detail grid ашиглана.

| Grid төрөл | Spacing | Ашиглах нөхцөл | Гүйцэтгэх зарчим |
| --- | --- | --- | --- |
| Recon grid | 200 m × 50 m | Target area том боловч аномали бүрэн баталгаажаагүй, мэдээлэл sparse, 1–5 км structural corridor шалгах үед. | Line spacing 200 м, sample spacing 50 м. Traverse line нь geological strike буюу structural trend-д перпендикуляр байна. |
| Target grid | 100 m × 25 m | Recon grid дээр аномали илэрсэн, rock chip/pXRF/alteration/structure зэрэг олон мэдээлэл давхцсан үед. | Line spacing 100 м, sample spacing 25 м. Аномалийн төв болон суналын чиглэлийг тодруулна. |
| Infill grid | 50 m × 25 m | Target grid дээр өндөр утгатай, үргэлжилсэн аномали гарсан, trench/drilling төлөвлөх гэж байгаа үед. | Line spacing 50 м, sample spacing 25 м. Аномалийн төв, зах, open direction-ийг тогтооно. |
| Vein detail grid | 25 m × 10 m | Нарийн кварцын судал, Au-Ag vein, polymetallic vein, epithermal target, 5–50 м өргөн structure шалгах үед. | Line spacing 25 м, sample spacing 10 м. Line нь судлын суналд перпендикуляр байна. |

# 6. Grid orientation буюу торлолын чиглэл тогтоох
Ерөнхий дүрэм: дээж авах шугам нь хүдэржилтийн суналын чиглэлд перпендикуляр байх ёстой. Ингэснээр дээжлэлт хүдэржилтийн өргөнийг зөв огтолж, аномалийн бодит өргөн, төвийг тодорхойлно.
## 6.1 Геологийн strike тодорхойлох
- Давхаргын сунал;
- Хагарлын чиглэл;
- Судлын сунал;
- Alteration zone-ийн чиглэл;
- Drainage direction;
- Slope direction;
- Historical mineral occurrence-ийн байрлал.
## 6.2 Торлолын чиглэл сонгох жишээ
- Кварцын судал NE-SW чиглэлтэй бол дээж авах line NW-SE чиглэлтэй байна.
- Fault zone N-S чиглэлтэй бол line E-W чиглэлтэй байна.
- Alteration corridor ENE-WSW бол line NNW-SSE чиглэлтэй байна.
# 7. QGIS дээр хөрсний sample grid үүсгэх заавар
## 7.1 Ажлын project бэлтгэх
1.  QGIS нээнэ.
2.  Project CRS-ийг UTM-д тохируулна.
3.  License boundary layer оруулна.
4.  Target area polygon layer оруулна.
5.  Geological map layer оруулна.
6.  Fault / structure layer оруулна.
7.  DEM, slope, drainage layer оруулна.
8.  Rock chip, field observation, pXRF point layer оруулна.
9.  Historical occurrence / deposit layer оруулна.
10.  Бүх layer зөв байрлаж байгаа эсэхийг шалгана.
## 7.2 Grid extent тодорхойлох
1.  Target polygon layer-ийг сонгоно.
2.  Buffer хэрэгтэй бол Processing Toolbox → Buffer ашиглана.
3.  Target zone-ийн гадна талаар 100–300 м buffer өгч болно.
4.  Buffer polygon-ийг Soil_Grid_Extent нэрээр хадгална.
5.  Хэт налуу, голын хөндий, хад асгатай, дээж авах боломжгүй хэсгийг exclusion area болгон тэмдэглэнэ.
## 7.3 Sample line үүсгэх
### Арга 1: Create Grid tool ашиглах
1.  Processing Toolbox → Create Grid нээнэ.
2.  Grid type: Line сонгоно.
3.  Grid extent: Soil_Grid_Extent сонгоно.
4.  Horizontal spacing / vertical spacing-ийг grid төрлөөс хамааран тохируулна.
5.  Grid CRS: Project CRS сонгоно.
6.  Output: Soil_Grid_Lines_100x25.gpkg эсвэл холбогдох нэрээр хадгална.
7.  Үүссэн line-ийг geological strike-д перпендикуляр чиглэлд rotate хийнэ.
### Арга 2: Manual baseline + parallel line
1.  Хүдэржилтийн strike-д перпендикуляр baseline зурна.
2.  Offset line tool ашиглан 50 м, 100 м, 200 м зайтай parallel line үүсгэнэ.
3.  Line бүрийг target polygon дотор clip хийнэ.
4.  Line ID өгнө.
## 7.4 Sample point үүсгэх
1.  Processing Toolbox → Points along geometry нээнэ.
2.  Input layer: Soil grid line сонгоно.
3.  Distance: 10 м, 25 м эсвэл 50 м оруулна.
4.  Start offset: 0, End offset: 0 гэж тохируулна.
5.  Output: XV-023222_Buduunkhad_Soil_Sample_Points.gpkg гэж хадгална.
6.  Point layer дээр attribute fields үүсгэнэ.
sample_id
grid_type
line_id
station_id
easting
northing
elevation
sample_spacing
line_spacing
target_name
soil_type
slope
landform
depth_cm
sample_weight_kg
pXRF_id
lab_id
qa_qc_type
collector
date
comment
## 7.5 Sample ID үүсгэх стандарт
Sample ID нь давхцахгүй, уншихад ойлгомжтой байх ёстой. Энгийн хөрсний дээжийн жишээ:
BK-SO-0001
BK-SO-0002
BK-SO-0003
QA/QC дээжүүдийн жишээ:
BK-SO-DUP-001
BK-SO-BLK-001
BK-SO-CRM-001
Field duplicate-ийн бодит original sample ID-г тусдаа QA/QC log-д тэмдэглэнэ. Field team-д duplicate sample аль original sample-тай холбоотойг ил тод тэмдэглэхгүй байж болно. QA/QC manager тусдаа confidential QA/QC key file хадгална.
# 8. Талбайн дээжлэлт хийх заавар
## 8.1 Талбайд гарахын өмнөх checklist
- GPS / handheld device;
- QField project;
- Offline basemap;
- Printed grid map;
- Sample bags;
- Permanent marker;
- Sample tags;
- Plastic scoop эсвэл stainless-steel scoop;
- Sieve, шаардлагатай бол;
- Gloves;
- Field notebook;
- Camera / phone;
- pXRF instrument;
- Calibration standard;
- CRM, blank material;
- Duplicate bag;
- Sample register sheet;
- Chain-of-custody form.
## 8.2 QField дээр sample point оруулах
1.  QGIS дээр бэлдсэн sample point layer-ийг QField project болгон export хийнэ.
2.  QFieldSync ашиглан package үүсгэнэ.
3.  Google Drive эсвэл USB ашиглан Android төхөөрөмж рүү хуулна.
4.  QField дээр project нээнэ.
5.  Sample point layer editable эсэхийг шалгана.
6.  Field form дээр заавал бөглөх талбаруудыг тохируулна.
sample_id
date
collector
soil_type
depth_cm
sample_weight_kg
landform
slope
comment
photo
## 8.3 Дээж авах байршил дээр очих
1.  GPS-ээр тухайн sample point дээр очно.
2.  5–10 м дотор байрлалыг баталгаажуулна.
3.  Байршил дээж авах боломжгүй бол offset авна.
4.  Offset авсан бол comment хэсэгт шалтгааныг бичнэ.
Жишээ comment:
Original point relocated 8 m east due to exposed bedrock.
Дээж авах боломжгүй нөхцөлүүд:
- Голын идэвхтэй суваг;
- Зам;
- Хад асга;
- Суурин газар;
- Хэт их бохирдсон газар;
- Ус тогтсон газар;
- Малын хашаа, бууц, хүний үйл ажиллагааны нөлөөтэй газар.
## 8.4 Хөрсний дээж авах арга
1.  Гадаргуугийн органик давхаргыг зайлуулна.
2.  10–30 см гүнээс B-horizon буюу тогтвортой хөрсний үеэс авна.
3.  Ойролцоогоор 0.5–1.0 кг дээж авна.
4.  Том чулуу, үндэс, органик материал, бохирдлыг ялгана.
5.  Дээжийг цэвэр уутанд хийнэ.
6.  Sample ID-г уутны гадна болон sample tag дээр давхар бичнэ.
7.  GPS point, depth, soil colour, texture, slope, landform тэмдэглэнэ.
8.  Зураг авна.
## 8.5 Field observation бичих
Sample ID
Date
Collector
Easting
Northing
Elevation
Soil horizon
Soil colour
Soil texture
Depth
Moisture
Slope
Landform
Vegetation
Rock fragment
Nearby outcrop
Alteration evidence
Visible mineralization
Contamination risk
Photo ID
Comment
# 9. pXRF screening хийх заавар
## 9.1 pXRF-ийн зорилго
pXRF screening нь лабораторийн шинжилгээг орлохгүй. Энэ нь талбай дээр урьдчилсан элементүүдийн өөрчлөлт, аномалийн чиг хандлагыг хурдан харах зориулалттай. Au-г pXRF-ээр найдвартай хэмжих боломж ихэвчлэн хязгаарлагдмал тул алтны хувьд лабораторийн fire assay эсвэл ICP-MS/ICP-OES үр дүнг үндсэн гэж үзнэ.
- Cu
- Zn
- Pb
- As
- Mo
- Mn
- Fe
- K
- Ca
- Ti
- Ni
- Cr
## 9.2 pXRF хэмжилтийн бэлтгэл
1.  Instrument warm-up хийнэ.
2.  Calibration check хийнэ.
3.  Standard sample хэмжинэ.
4.  Blank material хэмжинэ.
5.  Дээжийг хатаах боломжтой бол хатаана.
6.  Чийг ихтэй дээжийн үр дүнг болгоомжтой тайлбарлана.
7.  Нэг дээж дээр 30–60 секунд хэмжилт хийнэ.
8.  Дээж бүрийн pXRF result-ийг sample ID-тай яг тааруулна.
## 9.3 pXRF QA/QC
- 20 дээж тутамд нэг standard;
- 20 дээж тутамд нэг blank;
- 20 дээж тутамд нэг duplicate;
- Өдөр бүр instrument calibration log;
- Raw file backup.
Хэрэв standard-ийн үр дүн зөвшөөрөгдөх хязгаараас хэтэрвэл тухайн өдрийн pXRF үр дүнг дахин шалгана.
# 10. Лабораторийн шинжилгээний бэлтгэл
## 10.1 Дээж хүлээлцэх
1.  Sample bag бүрэн бүтэн эсэх;
2.  Sample ID уншигдах эсэх;
3.  Field register-тэй таарч байгаа эсэх;
4.  Дээжийн тоо бүрэн эсэх;
5.  Duplicate, blank, CRM зөв орсон эсэх;
6.  Sample sequence тасарсан эсэх;
7.  Chain-of-custody form бүрэн бөглөгдсөн эсэх.
## 10.2 Лабораторид илгээх sample submission file
Dispatch_No
Sample_ID
Sample_Type
QAQC_Type
Project
Target
Easting
Northing
Requested_Assay
Preparation_Code
Analysis_Code
Submitted_By
Submission_Date
Comment
Sample type утгууд:
SOIL
FIELD_DUPLICATE
BLANK
CRM
PULP_DUPLICATE
LAB_REPEAT
## 10.3 Шинжилгээний арга сонгох

| Target төрөл | Зөвлөх элементүүд | Санал болгох арга |
| --- | --- | --- |
| Порфир Cu-Au target | Cu, Au, Mo, Ag, As, Pb, Zn, Bi, Te, Re, W | Multi-element ICP-MS / ICP-OES; Au fire assay; Cu өндөр үед ore-grade re-assay. |
| Epithermal Au-Ag target | Au, Ag, As, Sb, Hg, Pb, Zn, Cu, Mo, Se, Te | Au fire assay; Multi-element ICP-MS; Hg тусгай арга шаардлагатай байж болно. |
| Polymetallic vein target | Pb, Zn, Ag, Cu, Au, As, Sb, Cd, Mn, Ba | ICP-OES / ICP-MS; Ag, Pb, Zn өндөр үед ore-grade method. |
| Skarn target | Cu, Au, Fe, Zn, W, Mo, Bi, Co, As, Ca, Mg | Multi-element ICP; Au fire assay; W, Sn шаардлагатай бол тусгай багц. |

# 11. QA/QC дээж оруулах стандарт
## 11.1 QA/QC insertion schedule
- 20 дээж тутамд 1 duplicate;
- 20 дээж тутамд 1 blank;
- 20–30 дээж тутамд 1 CRM;
- 50 дээж тутамд 1 pulp duplicate эсвэл lab repeat;
- Нийт QA/QC хэмжээ хамгийн багадаа 10–15% байх.
## 11.2 Field duplicate
Field duplicate нь нэг байршлаас хоёр тусдаа дээж авах арга бөгөөд field sampling variability, хөрсний жигд бус байдал, аномалийн бодит байдлыг шалгана.
1.  Original sample авна.
2.  Ижил цэгээс эсвэл 1–2 м дотор duplicate sample авна.
3.  Duplicate sample-д өөр sample ID өгнө.
4.  QA/QC key file дээр duplicate-ийн original ID-г бичнэ.
5.  Лабораторид blind duplicate байдлаар илгээнэ.
## 11.3 Blank sample
Blank нь sample preparation болон laboratory carry-over contamination байгаа эсэхийг шалгана. Цэвэр кварцын элс, certified blank material эсвэл геохимийн хувьд бага агуулгатай inert material ашиглаж болно.
- Өндөр агуулгатай дээжийн дараа blank оруулах;
- Blank value detection limit-тэй ойролцоо байх;
- Blank value anomaly threshold-д хүрэхгүй байх;
- Blank failure гарвал тухайн batch-ийн өмнөх болон дараах дээжүүдийг шалгах.
## 11.4 CRM буюу certified reference material
CRM нь лабораторийн accuracy буюу бодит утгад ойр хэмжиж байгаа эсэхийг шалгана. CRM сонгохдоо target element-тэй ойролцоо certified value-тэй, soil/geochemical matrix-тэй төстэй, Cu-Au, Au-Ag, Pb-Zn target-д тохирсон материал ашиглана.
## 11.5 Lab duplicate / pulp duplicate
Pulp duplicate нь sample preparation болон assay repeatability шалгана. Аномали өндөр гарсан дээж, critical decision sample, drilling/trenching шийдвэрт нөлөөлөх дээж, batch quality баталгаажуулах үед ашиглана.
# 12. Лабораторийн үр дүн хүлээн авах ба шалгах
## 12.1 Raw assay file хадгалах
Лабораториос ирсэн бүх raw assay result-ийг засварлахгүйгээр хадгална.
05_Assay_Validation/01_Raw_Lab_Result/
XV-023222_Buduunkhad_Soil_Assay_Raw_LabResult_Batch01.xlsx
## 12.2 Working file үүсгэх
Raw file-ийг шууд засахгүй. Түүний хуулбарыг working file болгон хадгална.
XV-023222_Buduunkhad_Soil_Assay_Validation_Working_Batch01.xlsx
- Sample ID match;
- Missing sample;
- Duplicate sample;
- Unit check;
- Detection limit;
- Negative value;
- Overlimit value;
- QA/QC sample identification;
- Element column consistency.
## 12.3 Unit conversion шалгах
Лабораторийн үр дүн ppm, ppb, %, g/t, mg/kg зэрэг unit-ээр ирж болно. Soil geochemistry-д ихэнх элемент ppm буюу mg/kg болгоно. Au ихэвчлэн ppb эсвэл g/t-ээр ирдэг тул тайлбартаа unit-ийг заавал тодорхой бичнэ.

| Conversion | Тайлбар |
| --- | --- |
| 1 ppm = 1 mg/kg | Soil geochemistry-д түгээмэл ашиглана. |
| 1000 ppb = 1 ppm | Au ppb-ийг ppm-д шилжүүлэхэд ашиглана. |
| 1% = 10,000 ppm | Өндөр base metal утгыг ppm болгоход ашиглана. |
| 1 g/t = 1 ppm | Au болон Ag-ийн зарим тайлангийн unit. |
| Au 25 ppb = 0.025 ppm | Жишээ conversion. |
| Cu 0.12% = 1200 ppm | Жишээ conversion. |

## 12.4 Detection limit шалгах
Доорх хэлбэртэй утгуудыг зөв боловсруулах шаардлагатай:
<0.01
<1
- 999
Below detection
N/A
- <DL утгыг статистик анализад DL/2 болгож ашиглаж болно;
- Map label дээр анхны хэлбэрийг хадгалж болно;
- Detection limit-ээс доош утгыг өндөр аномали гэж тайлбарлаж болохгүй;
- Detection limit column тусдаа хадгална.
# 13. QA/QC validation хийх арга
## 13.1 CRM performance шалгах
- ±2 standard deviation дотор байвал acceptable;
- ±2SD–±3SD хооронд warning;
- ±3SD-ээс гадуур бол failure.
CRM failure гарвал тухайн batch-ийг flag хийж, лабораторитой холбогдон repeat assay хүснэ. Critical samples-ийг дахин шинжлүүлж, QA/QC report-д action taken болон тайлбарыг бичнэ.
## 13.2 Blank performance шалгах
Blank value detection limit-тэй ойролцоо байх ёстой. Blank value anomaly threshold-д хүрч болохгүй. Өндөр утга гарвал contamination буюу бохирдол гэж үзнэ.
1.  Blank-ийн өмнөх болон дараах дээжүүдийг шалгана.
2.  Өндөр агуулгатай дээжийн дараа carry-over гарсан эсэхийг шалгана.
3.  Тухайн batch-д contamination flag өгнө.
4.  Шаардлагатай бол re-assay хийнэ.
## 13.3 Duplicate performance шалгах
Duplicate result-ийг original result-тэй харьцуулж RPD буюу relative percent difference тооцно.
RPD = |Original - Duplicate| / ((Original + Duplicate) / 2) × 100
- Low concentration үед RPD өндөр байж болно;
- Anomalous concentration үед RPD 20–30%-иас бага байвал сайн;
- 30–50% бол warning;
- 50%-иас дээш бол sampling variability эсвэл lab issue шалгана.
## 13.4 Outlier check
Outlier буюу хэт өндөр эсвэл хэт бага утгыг шууд устгахгүй. Эхлээд sample ID, unit, decimal, coordinate, QA/QC type, overlimit, nearby sample болон geological explanation-ийг шалгана. Isolated single-point anomaly байвал re-check, re-sample, infill grid эсвэл field mapping төлөвлөнө.
# 14. Геохимийн дата боловсруулах
## 14.1 Data cleaning
- Давхардсан sample ID устгахгүй, flag хийх;
- Missing coordinate нөхөх;
- Invalid coordinate шалгах;
- QA/QC sample-ийг ordinary sample-аас тусгаарлах;
- Unit standardize хийх;
- Detection limit утгыг боловсруулах;
- Null value шалгах;
- Element column нэршлийг стандарт болгох.
## 14.2 QGIS-д assay result холбох
1.  Soil sample point layer нээнэ.
2.  Assay result Excel/CSV оруулна.
3.  Join хийх field: sample_id.
4.  Layer Properties → Joins нээнэ.
5.  Assay table сонгоно.
6.  Join field: Sample_ID сонгоно.
7.  Target field: sample_id сонгоно.
8.  Joined result шалгана.
9.  Join unmatched sample list гаргана.
Unmatched sample гарвал typo, space, hyphen ялгаа, duplicate ID, missing lab result эсвэл wrong sample batch байж болно.
## 14.3 Element anomaly threshold тогтоох
Аномалийн threshold-ийг зөвхөн нэг тогтмол утгаар тогтоохгүй. Mean, median, standard deviation, percentile, background, 90th percentile, 95th percentile, 98th percentile, geological domain, soil type, lithology, drainage influence зэрэг үзүүлэлтийг хамтад нь ашиглана.

| Ангилал | Ерөнхий percentile |
| --- | --- |
| Background | <75th percentile |
| Weak anomaly | 75–90th percentile |
| Moderate anomaly | 90–95th percentile |
| Strong anomaly | 95–98th percentile |
| Very strong anomaly | >98th percentile |

# 15. Soil anomaly map гаргах
## 15.1 Element map
Элемент тус бүрээр Cu, Au, Ag, Pb, Zn, Mo, As, Sb, Bi, W anomaly map гаргана. Зураг бүр дээр license boundary, sample points, element value, anomaly class, geological unit, fault/structure, drainage, target boundary, north arrow, scale bar, legend, CRS, data source, date, prepared by заавал орно.
## 15.2 Multi-element anomaly map

| Deposit / target model | Multi-element association |
| --- | --- |
| Porphyry Cu-Au | Cu + Au + Mo + Ag ± Bi ± Te |
| High-sulfidation epithermal Au-Ag | Au + Ag + As + Sb + Hg ± Cu |
| Low-sulfidation epithermal Au-Ag | Au + Ag + Pb + Zn + As ± Sb |
| Polymetallic vein | Pb + Zn + Ag + Cu + Au + As |
| Skarn | Cu + Au + Fe + W + Mo + Bi ± Zn |

## 15.3 Аномалийн үргэлжлэл шалгах
- Нэг цэгийн isolated anomaly биш байх;
- Хэд хэдэн adjacent sample дээр үргэлжилсэн байх;
- Geological structure-тэй давхцсан байх;
- Alteration zone-той холбоотой байх;
- Rock chip / pXRF anomaly-той давхцсан байх;
- Drainage anomaly-той нийцсэн байх;
- Trend нь geological strike-тэй уялдсан байх;
- Open-ended буюу цаашаа үргэлжлэх боломжтой байх.
# 16. QA/QC check table бөглөх заавар

| QA/QC item | Шалгах зүйл | Хүлээн авах нөхцөл |
| --- | --- | --- |
| Grid spacing justified by orientation results | Торлолын зай Phase 8 orientation result-д үндэслэсэн эсэх | QA/QC log-д reviewer/date/decision бичигдсэн байх. |
| QA/QC performance acceptable | CRM, blank, duplicate, lab repeat acceptable эсэх | Failure гарсан бол action taken бичсэн байх. |
| Assay unit/detection limit validated | Unit conversion, detection limit зөв эсэх | Working file дээр validation sheet байх. |
| Anomaly continuity checked | Аномали үргэлжилсэн эсэх | Map болон interpretation note-оор баталгаажсан байх. |

# 17. Expected outputs
Phase 9 дуусахад дараах output файлууд заавал гарсан байна.
XV-023222_Buduunkhad_Systematic_Soil_Grid_Plan.pdf
XV-023222_Buduunkhad_Soil_Sample_Points.gpkg
XV-023222_Buduunkhad_Soil_Sample_Register.xlsx
XV-023222_Buduunkhad_Soil_QAQC_Report.docx
XV-023222_Buduunkhad_Soil_Assay_Results.xlsx
XV-023222_Buduunkhad_Soil_Anomaly_Map.pdf
Нэмэлтээр гаргаж болох файлууд:
XV-023222_Buduunkhad_Cu_Anomaly_Map.pdf
XV-023222_Buduunkhad_Au_Anomaly_Map.pdf
XV-023222_Buduunkhad_Pb_Zn_Ag_Anomaly_Map.pdf
XV-023222_Buduunkhad_Multi_Element_Target_Map.pdf
XV-023222_Buduunkhad_QAQC_Log.xlsx
XV-023222_Buduunkhad_Lab_Submission_Form.xlsx
XV-023222_Buduunkhad_Chain_of_Custody.pdf
# 18. Decision gate / next phase condition
## 18.1 Дараагийн шат руу шилжих нөхцөл
- Баталгаажсан геохимийн аномали гарсан;
- Аномали олон дээжээр үргэлжилсэн;
- QA/QC acceptable;
- Аномали geological structure-тэй давхцсан;
- Rock chip / pXRF / field observation-той нийцсэн;
- Аномали open direction-тэй;
- Target ranking-д high priority болсон.
## 18.2 Дахин шалгах нөхцөл
- Аномали нэг цэгийн isolated anomaly;
- QA/QC failure шийдэгдээгүй;
- Coordinate error байгаа;
- Unit conversion тодорхойгүй;
- Blank contamination өндөр;
- Duplicate variation хэт их;
- Geological explanation сул;
- Field observation хангалтгүй.
Энэ тохиолдолд re-sampling, infill soil grid, additional pXRF screening, field mapping, QA/QC re-assay хийх шаардлагатай.
# 19. Ажлын дарааллын товч workflow
1.  Өмнөх фазын мэдээлэл цуглуулах
2.  Target area сонгох
3.  Geological strike ба structure шалгах
4.  Grid spacing сонгох
5.  QGIS дээр grid line үүсгэх
6.  Points along line ашиглан sample point үүсгэх
7.  Sample ID, attribute table бэлтгэх
8.  QField project үүсгэх
9.  Талбайн хөрсний дээжлэлт хийх
10.  pXRF screening хийх
11.  Sample register шалгах
12.  QA/QC sample оруулах
13.  Lab submission form бэлтгэх
14.  Лабораторид илгээх
15.  Assay result хүлээн авах
16.  Unit, detection limit, sample ID шалгах
17.  CRM, blank, duplicate QA/QC шалгах
18.  Assay result-ийг QGIS-д холбох
19.  Element anomaly map гаргах
20.  Multi-element interpretation хийх
21.  Soil QA/QC report бичих
22.  Final target ranking update хийх
23.  Next phase decision гаргах
# 20. Чанарын үндсэн шаардлага
- Grid spacing нь Phase 8 orientation result-д үндэслэсэн байх;
- Grid orientation нь geological strike, structure, drainage-тэй уялдсан байх;
- Sample ID давхцаагүй байх;
- Field register бүрэн бөглөгдсөн байх;
- QA/QC дээжүүд blind байдлаар batch-д орсон байх;
- CRM, blank, duplicate result шалгагдсан байх;
- Detection limit болон unit conversion баталгаажсан байх;
- Аномали нэг цэгээр бус үргэлжилсэн байдлаар тайлбарлагдсан байх;
- Geological interpretation map-тай уялдсан байх;
- Final soil anomaly map болон QA/QC report гарсан байх.
# 21. Эцсийн үр дүн
Энэ Phase 9-ийн ажлын төгсгөлд хөрсний геохимийн баталгаажсан аномалийн зураг, QA/QC тайлан, лабораторийн баталгаажсан үр дүн, sample point database, final target ranking update бэлэн болсон байна. Энэ нь дараагийн шатны trench, geophysical survey, drilling target сонгох үндсэн техникийн баримт болно.
