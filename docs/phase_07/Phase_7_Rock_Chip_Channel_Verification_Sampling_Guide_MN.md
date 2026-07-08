<!-- source: Phase_7_Rock_Chip_Channel_Verification_Sampling_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

Phase 7 — Rock Chip, Channel and Verification Sampling
Чулуулгийн сорьц, суваг сорьц ба баталгаажуулах дээжлэлт хийх дэлгэрэнгүй заавар


| Subsection | Methodology detail |
| --- | --- |
| Scope | Field-confirmed mineralization/alteration/structure дээр лабораторийн дээж авах. |
| Input files | Phase 6 recon/pXRF outputs + direct historical evidence raw inputs N52 field observation table, N55-56 detailed geology/legend, N60 mineral occurrence map, N63 prospectivity map, N64-65 source materials map/legend, N66-68 occurrence/register files, N9-22 terrain and N75-78 basemaps. |
| Software / equipment | Field sampling kit, GPS/GNSS, pXRF support, sample bags/tags, chain-of-custody forms. |

# 1. Үндсэн зорилго
Энэ үе шатны зорилго нь өмнөх шатуудаар илэрсэн ашигт малтмалжилт, хувирал, кварцын судал, госсан, малахит, сульфид, intrusive contact, shear/fault zone, altered lithology зэрэг сонирхолтой геологийн объектуудыг талбай дээр баталгаажуулж, тэдгээрээс стандартын дагуу сорьц авч, лабораторид шинжилгээнд илгээхэд бэлэн болгох юм.
Энэ ажлын үр дүнд дараах зүйлс тодорхой болно:
1. Аль бүсэд бодит хүдэржилт илэрч байгаа эсэх;
2. Чулуулаг, судал, хувирал, сульфиджилтийн тархалт;
3. Дараагийн шатны нарийвчилсан зураглал, суваг малталт, геохими, өрөмдлөгийн зорилтот цэгүүд;
4. Геохимийн шинжилгээнд оруулах анхан шатны дээжийн багц;
5. QA/QC сорьцын хяналттай лабораторийн илгээмж.
# 2. Ажил эхлэхээс өмнөх бэлтгэл
## 2.1. Ашиглах input файлуудыг бэлтгэх
Phase 7 эхлэхээс өмнө дараах файлуудыг нэг хавтсанд цэгцэлж бэлтгэнэ.
- Phase 6 recon / pXRF output;
- N52 field observation table;
- N55-56 detailed geology map болон legend;
- N60 mineral occurrence map;
- N63 prospectivity map;
- N64-65 source materials map болон legend;
- N66-68 occurrence / register files;
- N9-22 terrain болон basemap files;
- GPS/GNSS-д оруулах зорилтот цэгүүд;
- QField/QGIS project;
- Өмнөх дээжлэлт, observation, structure, alteration, lithology мэдээлэл.
Эдгээр input файлуудыг ашиглан талбайд очихоос өмнө дээж авах урьдчилсан цэгүүдийн төлөвлөгөө гаргана.
# 3. Ажлын хавтасны бүтэц үүсгэх
Компьютер дээр Phase 7-д зориулж дараах хавтасны бүтцийг үүсгэнэ.
07_Phase_7_Rock_Chip_Channel_and_Verification_Sampling/
├── 01_Sample_Planning
├── 02_RockChip_Channel_Float_Registers
├── 03_QAQC_Insertion
├── 04_Chain_of_Custody
├── 05_Lab_Submission
└── 06_Assay_Import_Preparation
## 3.1. 01_Sample_Planning
- Дээж авах төлөвлөгөө;
- Дээж авах цэгийн жагсаалт;
- QGIS/QField дээрх sampling target layer;
- PDF хэлбэрийн талбайн маршрут зураг;
- Урьдчилсан rock chip, channel, float sampling plan.
## 3.2. 02_RockChip_Channel_Float_Registers
- Rock chip sample register;
- Channel sample register;
- Float sample register;
- Verification sample register;
- Sample photo register;
- Drone tile/photo reference register.
## 3.3. 03_QAQC_Insertion
- CRMs / standards;
- Blank samples;
- Field duplicates;
- Lab duplicates;
- Pulp duplicates;
- Coarse duplicates;
- QA/QC insertion log.
## 3.4. 04_Chain_of_Custody
- Chain-of-custody form;
- Sample bag handover record;
- Field-to-office transfer record;
- Office-to-lab submission record;
- Хариуцсан ажилтны гарын үсэгтэй баримт.
## 3.5. 05_Lab_Submission
- Lab submission sheet;
- Sample list;
- Requested assay method;
- Element package;
- Turnaround time;
- Лабораторийн хүлээн авсан баталгаажуулалт.
## 3.6. 06_Assay_Import_Preparation
- Assay import template;
- Sample ID matching table;
- QA/QC check table;
- Final validated assay table.
# 4. Талбайд гарахын өмнөх төлөвлөлт
## 4.1. Өмнөх шатны өгөгдөл шалгах
Phase 6-ийн recon болон pXRF үр дүнг нээж дараах зүйлсийг шалгана.
1. Cu, Au, Ag, Pb, Zn, Mo, As, Sb, Bi зэрэг элементүүдийн аномаль утгууд;
2. pXRF өндөр утга өгсөн цэгүүд;
3. Хүдэржилт ажиглагдсан observation цэгүүд;
4. Кварцын судал, госсан, малахит, сульфид, исэлдлийн бүс;
5. Intrusive contact, shear zone, fault zone, breccia zone;
6. Altered lithology буюу хувирсан чулуулаг;
7. Өмнө нь тэмдэглэгдсэн mineral occurrence болон prospectivity zone.
Эдгээрийг QGIS дээр давхарлаж үзээд sampling target цэгүүдийг сонгоно.
## 4.2. Дээж авах сонирхолтой объектыг сонгох
Дараах шинж тэмдэг илэрсэн газрыг дээж авах өндөр ач холбогдолтой гэж үзнэ.
### 4.2.1. Кварцын судал
- Сульфидтэй кварцын судал;
- Исэлдсэн, төмрийн оксидтой кварц;
- Brecciated quartz vein;
- Үеллэг, stockwork, veinlet ихтэй бүс;
- Fault/shear дагасан кварцын судал;
- Гидротермаль хувиралтай хамт илэрсэн судал.
### 4.2.2. Госсан
- Бор, улаан, шар өнгийн төмрийн исэлжилт;
- Boxwork texture;
- Лимонит, гематит, гётит илэрсэн хэсэг;
- Сульфидын исэлдлийн үлдэгдэлтэй хэсэг.
### 4.2.3. Малахит болон зэсийн исэл
- Ногоон өнгийн малахитын толбо;
- Азуритын цэнхэр өнгө;
- Кварцын судал, ан цав, breccia дотор зэсийн исэлжилт;
- Халькопирит, ковеллин, борнитын исэлдлийн шинж.
### 4.2.4. Сульфиджилт
- Pyrite;
- Chalcopyrite;
- Bornite;
- Galena;
- Sphalerite;
- Molybdenite;
- Arsenopyrite;
- Disseminated, vein-hosted, massive, semi-massive хэлбэрийн сульфид.
### 4.2.5. Intrusive contact
- Боржин, диорит, габбро, порфирит болон тунамал/вулканоген чулуулгийн зааг;
- Skarn alteration;
- Hornfels;
- Contact breccia;
- Magnetite, garnet, epidote, actinolite, carbonate alteration.
### 4.2.6. Shear / fault zone
- Хагарал дагасан кварцын судал;
- Катаклазит, милонит, breccia;
- Clay alteration;
- Fe-oxide staining;
- Sulfide-bearing shear zone.
### 4.2.7. Altered lithology
- Silicification;
- Argillic alteration;
- Sericitization;
- Chloritization;
- Epidotization;
- Carbonatization;
- Potassic alteration;
- Propylitic alteration.
# 5. Дээжийн төрөл сонгох аргачлал
Phase 7-д дараах үндсэн дээжийн төрлүүдийг ашиглана.
## 5.1. Rock chip sample
Rock chip сорьцыг ил гарсан чулуулаг, судал, хувирлын бүс, хүдэржилттэй хэсгээс авна.
Авах нөхцөл
- Чулуулаг ил гарсан байх;
- Хүдэржилт, хувирал, судал тодорхой ажиглагдсан байх;
- Тухайн цэгийг координатаар бүртгэх боломжтой байх;
- Фото зураг авах боломжтой байх.
Авах арга
1. Дээж авах объектыг тодорхойлно.
2. GPS/GNSS координат авна.
3. Фото зураг авна.
4. Геологийн тайлбар бичнэ.
5. 1-3 кг орчим чулуулгийн жижиг хэлтэрхий цуглуулна.
6. Нэг төрлийн төлөөлөх материал авахыг анхаарна.
7. Дээжийг уутанд хийж Sample ID бичнэ.
8. Register дээр бүртгэнэ.
## 5.2. Channel sample
Channel сорьцыг судал, хүдэржилттэй бүс, altered zone-ийн өргөнийг төлөөлүүлэх зорилгоор авна.
Авах нөхцөл
- Хүдэржилт тодорхой шугаман хэлбэртэй байх;
- Судал эсвэл altered zone-ийн өргөн хэмжигдэх боломжтой байх;
- Дээжийг тогтмол өргөнтэй суваг хэлбэрээр авах боломжтой байх;
- Геологийн зааг, контактыг ялгах боломжтой байх.
Авах арга
1. Сорьц авах суваг тавих шугамыг сонгоно.
2. Судлын сунал, унал, өргөнийг хэмжинэ.
3. Суваг нь хүдэржилттэй биетийг аль болох хөндлөн огтлох ёстой.
4. Сорьц авах interval-ийг тогтооно.
5. Тухайн interval бүрт тусдаа Sample ID өгнө.
6. Алх, цүүц, таслагч ашиглан тогтмол өргөн, тогтмол гүнтэй материал авна.
7. Дээжийг уутанд хийж, шошголно.
8. Эхлэл болон төгсгөлийн координат, interval length, width, structure мэдээллийг бүртгэнэ.
## 5.3. Float sample
Float сорьцыг эх үүсвэр нь тодорхойгүй боловч ашигт малтмалжилтын шинжтэй чулуулгийн хэлтэрхий, өнхрүүш, хэмхдэсээс авна.
Авах нөхцөл
- Малахит, сульфид, кварц, госсан, breccia илэрсэн байх;
- Эх чулуулаг нь шууд илрээгүй байх;
- Float material нь тухайн талбайн дотор эсвэл ойролцоох эх үүсвэртэй байх магадлалтай байх.
Авах арга
1. Float материалын тархалтыг тэмдэглэнэ.
2. Хэмжээ, хэлбэр, зөөгдсөн эсэхийг тайлбарлана.
3. Координат авна.
4. Фото зураг авна.
5. 1-3 кг төлөөлөх материал цуглуулна.
6. Sample ID өгч бүртгэнэ.
7. “Float source unknown / possible nearby source” гэх мэт тайлбар оруулна.
## 5.4. Verification sample
Verification сорьцыг өмнө нь тэмдэглэгдсэн хүдэржилт, occurrence, pXRF anomaly, recon observation, map target-ийг баталгаажуулах зорилгоор авна.
Авах нөхцөл
- Өмнөх шатанд аномаль гэж тэмдэглэгдсэн байх;
- Геологийн зураг дээр mineral occurrence эсвэл alteration zone гэж заагдсан байх;
- pXRF үр дүн өндөр гарсан байх;
- Талбай дээр бодит илрэл ажиглагдсан байх.
Авах арга
1. Өмнөх target цэгийг GPS дээр оруулж очно.
2. Тухайн цэг дээр геологийн баталгаажуулалт хийнэ.
3. Хэрэв бодит хүдэржилт ажиглагдвал rock chip эсвэл channel сорьц авна.
4. Хэрэв илрэл сул байвал observation-only гэж бүртгэж болно.
5. Verification result талбарт “confirmed”, “partially confirmed”, “not confirmed” гэж тэмдэглэнэ.
# 6. Sample ID дугаарлалтын журам
Дээж бүр давтагдашгүй ID дугаартай байна. Жишиг дугаарлалт:
BUD-RC-001
BUD-CH-001
BUD-SOIL-001
BUD-STR-001
BUD-HM-001
BUD-QC-STD-001
BUD-QC-BLK-001
BUD-QC-DUP-001
## 6.1. Тайлбар

| Код | Утга |
| --- | --- |
| BUD | Project code буюу Buduunkhad |
| RC | Rock chip sample |
| CH | Channel sample |
| SOIL | Soil sample |
| STR | Stream sediment sample |
| HM | Heavy mineral sample |
| QC-STD | Standard / CRM |
| QC-BLK | Blank sample |
| QC-DUP | Duplicate sample |

## 6.2. Анхаарах зүйл
- Нэг ID-г хоёр удаа ашиглаж болохгүй.
- Field register, sample bag, photo register, lab submission бүгд ижил ID ашиглана.
- Дээжийн дугаар алгассан бол register дээр “not used” гэж тэмдэглэнэ.
- Гараар бичсэн ID болон Excel register-ийн ID зөрж болохгүй.
- QC sample ID нь энгийн дээжийн дараалалд орох боловч тусдаа QC төрлөөр тэмдэглэгдэнэ.
# 7. Талбай дээр бүртгэх мэдээлэл
Дээж бүрт дараах мэдээллийг заавал бүртгэнэ.

| Бүртгэлийн талбар | Заавал оруулах мэдээлэл |
| --- | --- |
| Sample ID | BUD-RC-001 гэх мэт |
| Date | Дээж авсан огноо |
| Collector | Дээж авсан ажилтны нэр |
| Coordinates | Easting, Northing, elevation |
| Coordinate system | WGS84 / UTM Zone 47N эсвэл төслийн хэрэглэж буй систем |
| Sample type | Rock chip / channel / float / verification |
| Lithology | Чулуулаг |
| Alteration | Хувирал |
| Mineralization | Хүдэржилт |
| Structure | Судал, хагарал, shear, breccia |
| Width / strike / dip | Судлын өргөн, сунал, унал |
| Sample mass | Дээжийн жин |
| Photo ID | Зурагтай холбох дугаар |
| pXRF reading | Байгаа бол pXRF утга |
| Drone tile | Байгаа бол drone image reference |
| Remarks | Нэмэлт тайлбар |

# 8. Талбай дээр ажиллах дараалал
## 8.1. Алхам 1. Өдрийн ажлын төлөвлөгөө гаргах
Өглөө талбайд гарахаас өмнө:
1. Өдрийн маршрутыг тогтооно.
2. Очих target цэгүүдийг GPS/QField дээр шалгана.
3. Дээжийн уут, шошго, marker, алх, GPS, pXRF, камер, chain-of-custody form бэлдэнэ.
4. Аюулгүй ажиллагааны зааварчилгаа өгнө.
5. Өдрийн sample ID range-ийг багт хуваарилна.
2026-06-05
Team A: BUD-RC-001 to BUD-RC-030
Team B: BUD-RC-031 to BUD-RC-060
QC samples: BUD-QC-STD-001, BUD-QC-BLK-001, BUD-QC-DUP-001
## 8.2. Алхам 2. Target цэг дээр очиж баталгаажуулах
1. GPS координат шалгана.
2. Газрын гадаргын нөхцөл, outcrop, float, alteration, vein, structure ажиглана.
3. Өмнөх зураг, pXRF anomaly, occurrence map-тай харьцуулна.
4. Хэрэв хүдэржилт байхгүй бол “not confirmed” гэж тэмдэглэнэ.
5. Хэрэв хүдэржилт илэрвэл дээж авах төрлийг сонгоно.
## 8.3. Алхам 3. Геологийн тайлбар бичих
Дээж авахын өмнө тухайн цэгийн геологийн тайлбарыг бичнэ.
English example:
Outcrop of strongly silicified and limonitic quartz vein zone hosted in altered volcanic rock. Quartz vein width approximately 0.8 m, striking NE-SW, dipping 65° SE. Visible malachite staining and disseminated pyrite observed along fractures. Rock chip sample collected across representative mineralized zone.

Монгол жишээ:
Хувирсан вулканоген чулуулгад байрласан хүчтэй цахиржсан, лимонитжсан кварцын судал илэрсэн. Судлын өргөн ойролцоогоор 0.8 м, сунал NE-SW, унал 65° SE. Ан цав дагуу малахитын ногоон толбо болон тархмал пирит ажиглагдсан. Хүдэржилттэй хэсгийг төлөөлүүлэн rock chip сорьц авсан.
## 8.4. Алхам 4. Фото зураг авах
Дээж бүр дээр дор хаяж дараах зураг авна.
- Ерөнхий орчны зураг;
- Outcrop буюу ил гарсан чулуулгийн зураг;
- Дээж авсан хэсгийн ойрын зураг;
- Sample bag болон Sample ID харагдах зураг;
- Channel сорьц бол эхлэл, төгсгөл, interval зураг.
BUD-RC-001_context.jpg
BUD-RC-001_outcrop.jpg
BUD-RC-001_closeup.jpg
BUD-RC-001_samplebag.jpg
## 8.5. Алхам 5. Координат авах
GPS/GNSS ашиглан дараах мэдээллийг бүртгэнэ.
- Easting;
- Northing;
- Elevation;
- Accuracy;
- Coordinate system;
- Time;
- Device name.
Координатыг QField болон field notebook/register дээр давхар бүртгэнэ. Улаанбаатарын цагийн бүс эсвэл төслийн тохируулсан цагийн бүсийг шалгана. GPS accuracy боломжтой бол 3-5 м дотор байх нь зохимжтой. Coordinate system Excel, QGIS, GPS дээр ижил байх ёстой.
## 8.6. Алхам 6. Дээж авах
Rock chip авах үед
- Ил гарсан чулуулгийн шинэхэн хэсгээс авна.
- Хэт исэлдсэн гадаргуугийн сул материалд найдахгүй.
- Хүдэржилттэй хэсгийг төлөөлөх байдлаар хэд хэдэн жижиг хэсэг цуглуулна.
- Нэг сорьц нэг геологийн нэгжийг төлөөлөх ёстой.
- Өөр өөр lithology эсвэл alteration zone-ийг нэг уутанд холихгүй.
Channel sample авах үед
- Channel line-ийг тэмдэглэнэ.
- Interval тус бүрийг хэмжинэ.
- Хэрэв судал 2 м өргөн бол 0.5 м эсвэл 1.0 м interval болгон хувааж болно.
- Interval бүрт тусдаа Sample ID өгнө.
- Суваг дагуу авсан материал ижил өргөн, ижил гүнтэй байх ёстой.
- Хөрс, органик материал, loose debris-ийг аль болох оруулахгүй.
Float sample авах үед
- Float тархалтын төв хэсгээс төлөөлөх материал авна.
- Хэт хол зөөгдсөн байж болзошгүй эсэхийг тэмдэглэнэ.
- “Angular”, “sub-angular”, “rounded” гэж хэлбэрийг бичнэ.
- Эх үүсвэрийн чиглэл байж болох газрыг тэмдэглэнэ.
## 8.7. Алхам 7. Sample bag шошголох
Дээжийн уут дээр дараах мэдээлэл бичнэ.
Project: Buduunkhad
Sample ID: BUD-RC-001
Date: 2026-06-05
Sample type: Rock chip
Collector: [Name]
Дотор талд усанд норохгүй шошго хийж, гадна талд marker-аар дахин бичнэ.
- Sample ID тод, уншигдахуйц байх;
- Уутны гадна болон доторх ID ижил байх;
- Register дээр бичсэн ID-тэй таарч байх;
- Нойтон дээжийг битүүмжлэхдээ хөгц, бохирдол үүсэхээс сэргийлэх.
# 9. QA/QC сорьц оруулах заавар
QA/QC нь лабораторийн үр дүнгийн найдвартай байдлыг шалгах үндсэн хяналт юм.
## 9.1. QA/QC төрөл

| QA/QC төрөл | Зорилго |
| --- | --- |
| CRM / Standard | Лабораторийн нарийвчлал шалгах |
| Blank | Бохирдол шалгах |
| Field duplicate | Талбайн дээжлэлтийн давтагдах чанар шалгах |
| Lab duplicate | Лабораторийн давтагдах чанар шалгах |
| Pulp duplicate | Нунтагласан дээжийн давтагдах чанар шалгах |
| Coarse duplicate | Буталсан дээжийн давтагдах чанар шалгах |

## 9.2. QA/QC оруулах давтамж
Практикт дараах зарчмыг ашиглаж болно.
20 дээж тутамд 1 QA/QC сорьц
эсвэл
нийт дээжийн 5-10%-ийг QA/QC болгох
BUD-RC-001
BUD-RC-002
...
BUD-RC-019
BUD-QC-STD-001
BUD-RC-020
...
BUD-RC-039
BUD-QC-BLK-001
BUD-RC-040
...
BUD-RC-059
BUD-QC-DUP-001
## 9.3. Blank sample
- Дээж бэлтгэл болон лабораторийн бохирдол байгаа эсэхийг шалгах.
- Өндөр хүдэржилттэй дээжийн дараа оруулах.
- Сульфид ихтэй дээжийн дараа оруулах.
- 20-30 дээж тутамд нэг удаа оруулах.
## 9.4. CRM / Standard
- Хүлээгдэж буй хүдэржилтийн төрөлтэй тохирох;
- Cu, Au, Ag, Pb, Zn гэх мэт гол элементүүдтэй тохирох;
- Бага, дунд, өндөр агууламжийн CRM-үүдээс сонгох.
## 9.5. Field duplicate
- Үндсэн дээж авсан хэсэгтэй ойролцоо цэгээс авна.
- Ижил lithology, alteration, mineralization-ийг төлөөлнө.
- Өөр Sample ID өгнө.
- Register дээр duplicate-ийн эх дээжийг тэмдэглэнэ.
Original sample: BUD-RC-025
Duplicate sample: BUD-QC-DUP-001
Duplicate of: BUD-RC-025
# 10. Chain of custody хийх заавар
Chain of custody нь дээжийг авсан цагаас лабораторид хүлээлгэн өгөх хүртэл хэн, хэзээ, хаана хариуцаж байсан тухай албан бүртгэл юм.
## 10.1. Бүртгэх мэдээлэл

| Талбар | Мэдээлэл |
| --- | --- |
| Project name | Buduunkhad |
| Batch number | Batch-001 |
| Sample ID range | BUD-RC-001 to BUD-RC-080 |
| Number of samples | Жинхэнэ дээж + QA/QC |
| Collector | Дээж авсан хүн |
| Packed by | Савласан хүн |
| Checked by | Шалгасан хүн |
| Delivered by | Хүргэсэн хүн |
| Received by | Хүлээн авсан хүн |
| Date/time | Огноо, цаг |
| Signature | Гарын үсэг |

## 10.2. Сав баглаа боодол
1. Дээж бүрийг тусдаа уутанд хийнэ.
2. Sample ID-г уутны гадна болон дотор бичнэ.
3. Дээжүүдийг дугаарын дарааллаар байрлуулна.
4. Том шуудай эсвэл хайрцагт багцална.
5. Batch ID бичнэ.
6. Chain-of-custody form-ийг тусад нь хавсаргана.
7. Битүүмжилсэн эсэхийг зураг авч баталгаажуулна.
# 11. Lab submission хийх заавар
## 11.1. Lab submission sheet бэлтгэх

| Талбар | Мэдээлэл |
| --- | --- |
| Sample ID | BUD-RC-001 |
| Sample type | Rock chip |
| Batch ID | Batch-001 |
| Requested method | Жишээ нь ICP-MS, ICP-OES, Fire assay |
| Elements | Au, Ag, Cu, Pb, Zn, Mo, As, Sb гэх мэт |
| Preparation | Drying, crushing, pulverizing |
| QA/QC type | Blank / CRM / Duplicate |
| Remarks | Тайлбар |

## 11.2. Лабораторийн арга сонгох

| Зорилтот хүдэржилт | Санал болгох шинжилгээ |
| --- | --- |
| Au-Ag epithermal | Fire assay Au + multi-element ICP |
| Cu-Au porphyry | Cu, Mo, Au, Ag + multi-element ICP |
| Pb-Zn-Ag vein | Pb, Zn, Ag, Cu + ICP |
| Skarn | Cu, Fe, Zn, Au, Ag, W, Mo + ICP |
| Ni-Cu sulfide | Ni, Cu, Co, PGE боломжтой бол тусгай арга |
| Polymetallic | Multi-element ICP package |

## 11.3. Лабораторид илгээхээс өмнөх шалгалт
- Sample ID давхардаагүй эсэх;
- Sample bag дээрх ID register-тэй таарч байгаа эсэх;
- QA/QC insertion бүрэн эсэх;
- Chain-of-custody form бөглөгдсөн эсэх;
- Lab submission sheet бүрэн эсэх;
- Дээжийн нийт тоо, register-ийн нийт тоо, lab submission-ийн нийт тоо ижил эсэх;
- Фото болон координатын бүртгэл бүрэн эсэх.
# 12. QA/QC check хийх заавар

| QA/QC item | Acceptance note |
| --- | --- |
| Sample ID unique | Phase QA/QC log-д бүртгэж reviewer/date/decision оруулна |
| Coordinates/photo/chain-of-custody complete | Phase QA/QC log-д бүртгэж reviewer/date/decision оруулна |
| QA/QC insertion complete | Phase QA/QC log-д бүртгэж reviewer/date/decision оруулна |
| Lab submission consistent with register | Phase QA/QC log-д бүртгэж reviewer/date/decision оруулна |

## 12.1. Sample ID unique шалгах
- Sample ID баганыг сонгоно.
- Conditional Formatting → Highlight Duplicate Values ашиглана.
- Давхардсан ID илэрвэл register болон sample bag-тай тулгана.
- Засвар хийсэн бол QA/QC log дээр тэмдэглэнэ.
## 12.2. Coordinates/photo/chain-of-custody complete шалгах
- Easting;
- Northing;
- Elevation;
- Photo ID;
- Sample ID;
- Chain-of-custody batch;
- Collector;
- Date.
## 12.3. QA/QC insertion complete шалгах
- Blank орсон эсэх;
- CRM орсон эсэх;
- Duplicate орсон эсэх;
- QA/QC нийт хувь 5-10% хүрч байгаа эсэх;
- Өндөр хүдэржилттэй дээжийн дараа blank орсон эсэх;
- Duplicate-ийн original sample тодорхой эсэх.
## 12.4. Lab submission consistent with register шалгах
- Sample ID бүгд орсон эсэх;
- Илгээсэн дээжийн тоо register-тэй таарч байгаа эсэх;
- QA/QC sample орсон эсэх;
- Дээжийн төрөл зөв эсэх;
- Шинжилгээний арга зөв сонгогдсон эсэх;
- Хоосон мөр, давхар мөр, буруу ID байгаа эсэх.
Хэрэв дутуу талбар илэрвэл “Pending correction” гэж тэмдэглээд талбайн баг эсвэл sample collector-оос тодруулна.
# 13. Expected outputs
Phase 7 дуусахад дараах файлууд бэлэн болсон байна.
XV-023222_Buduunkhad_Rock_Chip_Sampling_Plan.pdf
XV-023222_Buduunkhad_Rock_Chip_Sample_Register.xlsx
XV-023222_Buduunkhad_Rock_Chip_QAQC_Plan.xlsx
XV-023222_Buduunkhad_Lab_Submission_RockChip.xlsx
XV-023222_Buduunkhad_Assay_Import_Template.xlsx
## 13.1. Sampling Plan PDF
- Дээж авах зорилтот бүс;
- Дээж авах цэгүүд;
- Маршрут;
- Геологийн үндэслэл;
- QA/QC төлөвлөгөө;
- Аюулгүй ажиллагааны тэмдэглэл;
- Талбайн багийн ажил үүрэг.
## 13.2. Sample Register XLSX
- Sample ID;
- Date;
- Collector;
- Easting;
- Northing;
- Elevation;
- Sample type;
- Lithology;
- Alteration;
- Mineralization;
- Structure;
- Width/strike/dip;
- pXRF reading;
- Photo ID;
- Sample mass;
- Remarks.
## 13.3. QAQC Plan XLSX
- QA/QC sample ID;
- QA/QC type;
- Original sample ID;
- Insertion position;
- Expected value;
- Accepted range;
- Reviewer;
- Decision;
- Comment.
## 13.4. Lab Submission XLSX
- Batch ID;
- Sample ID;
- Sample type;
- Analysis package;
- Preparation method;
- QA/QC type;
- Number of samples;
- Submission date;
- Laboratory name.
## 13.5. Assay Import Template XLSX
- Лабораторийн хариу ирсний дараа QGIS, database эсвэл master register рүү импортлоход зориулсан загвар файл байна.
# 14. Decision gate / дараагийн шат руу шилжих нөхцөл
Phase 7-г дууссан гэж үзэхийн тулд дараах нөхцөл бүрэн хангагдсан байна.
1. Бүх төлөвлөсөн target цэгүүд шалгагдсан;
2. Ашигт малтмалжилттай цэгүүдээс rock chip/channel/float/verification дээж авсан;
3. Бүх Sample ID давтагдаагүй;
4. Координат, фото, геологийн тайлбар бүрэн;
5. QA/QC сорьцууд зөв байрлалд орсон;
6. Chain-of-custody form бөглөгдсөн;
7. Lab submission sheet бэлэн болсон;
8. Дээж лабораторид илгээгдсэн;
9. Assay import template бэлэн болсон;
10. Reviewer/date/decision QA/QC log дээр бүртгэгдсэн.
# 15. Phase 7 ажлын эцсийн шалгах хуудас

| № | Шалгах зүйл | Төлөв |
| --- | --- | --- |
| 1 | Sampling target map бэлэн эсэх | ☐ |
| 2 | Field sample register бэлэн эсэх | ☐ |
| 3 | Sample ID range баталгаажсан эсэх | ☐ |
| 4 | GPS/QField project бэлэн эсэх | ☐ |
| 5 | Sample bags, tags, marker, tools бэлэн эсэх | ☐ |
| 6 | Rock chip дээж бүртгэгдсэн эсэх | ☐ |
| 7 | Channel sample interval бүртгэгдсэн эсэх | ☐ |
| 8 | Float sample source тайлбарлагдсан эсэх | ☐ |
| 9 | Verification result бичигдсэн эсэх | ☐ |
| 10 | Фото бүр sample ID-тай холбогдсон эсэх | ☐ |
| 11 | QA/QC sample оруулсан эсэх | ☐ |
| 12 | Chain-of-custody бүрэн эсэх | ☐ |
| 13 | Lab submission sheet register-тэй таарч байгаа эсэх | ☐ |
| 14 | Assay import template бэлэн эсэх | ☐ |
| 15 | Phase QA/QC log бөглөгдсөн эсэх | ☐ |

# 16. Богино дүгнэлт
Энэ Phase 7-ийн гол зарчим нь “геологийн үндэслэлтэй цэгээс, зөв төрлийн дээжийг, давтагдашгүй Sample ID-тай, QA/QC хяналттайгаар авч, лабораторид мөрдөх боломжтой бүртгэлтэй илгээх” явдал юм.
Хамгийн чухал анхаарах зүйлс:
- Дээж бүр координат, зураг, тайлбар, ID-тай байх;
- Rock chip, channel, float, verification дээжийг хооронд нь ялгаж бүртгэх;
- QA/QC сорьцыг заавал оруулах;
- Chain-of-custody-г орхигдуулахгүй бөглөх;
- Lab submission болон field register хооронд зөрүү гаргахгүй байх;
- Дараагийн шатанд ашиглах assay import template-ийг урьдчилан бэлдэх.
