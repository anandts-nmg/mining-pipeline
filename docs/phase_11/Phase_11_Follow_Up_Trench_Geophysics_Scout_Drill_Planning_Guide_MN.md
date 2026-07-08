<!-- source: Phase_11_Follow_Up_Trench_Geophysics_Scout_Drill_Planning_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

# 11. Phase 11 — Follow-up Trench, Geophysics and Scout Drill Planning

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Final A/B target дээр trench, geophysics, scout drilling төлөвлөх. |
| Input files | Phase 10 final A/B targets + direct planning support raw inputs: boundary, DEM/slope/hillshade, detailed geology, occurrence map, prospectivity map, source materials map, mineralized point table, basemap/Sentinel rasters. |
| Software / equipment | QGIS, trench/geophysics planning tools, drilling design spreadsheet, HSE/budget templates. |

# 1. Ажлын зорилго
Phase 11-ийн үндсэн зорилго нь өмнөх шатанд гарсан A/B зэрэглэлийн хайгуулын байнуудыг нарийвчлан шалгаж, дараагийн шатны суваг малталт / trench, IP–resistivity геофизик, соронзон хэмжилт, нэмэлт хөрсний дээжлэлт, эхний хайгуулын өрөмдлөг / scout drilling хийх байршил, шугам, цэг, төсөв, зөвшөөрөл, HSE шаардлагыг бүрэн төлөвлөхөд оршино.
Энэ шатны эцсийн шийдвэр нь: Scout drilling хийх нөхцөл хангагдсан эсэх юм.
# 2. Ашиглах үндсэн input материал
## 2.1 Заавал ашиглах материал
- Final A/B target map
- Target ranking support raw inputs
- License boundary shapefile
- DEM, slope, hillshade
- Detailed geology map
- Occurrence / mineral showing map
- Prospectivity map
- Source materials map
- Mineralized point table
- Basemap / Sentinel raster
- Өмнөх phase-ийн trench санал, дээжлэлт, геологи, бүтэц, alteration, anomaly мэдээлэл
- Field observation points
- Lab assay result / XRF result
- Access road, river, slope, protected area, settlement, HSE constraint layers
# 3. Программ ба тоног төхөөрөмж
## 3.1 Оффисын программ
- QGIS
- Excel
- Google Earth Pro
- PDF map export tool
- Drill planning spreadsheet
- Budget template
- Permit / HSE checklist template
## 3.2 Талбайн тоног төхөөрөмж
- GPS / GNSS
- Tablet with QField
- Geological compass
- Handheld XRF
- Rock hammer
- Sample bags
- Flagging tape
- Measuring tape
- Camera / phone
- PPE
- First aid kit
- Vehicle and access equipment
# 4. Фолдерийн бүтэц
Ажлын бүх файлыг дараах бүтэцтэй хадгална.
11_Phase_11_Follow_Up_Trench_Geophysics_and_Scout_Drill_Planning/
├── 01_Trench_Channel_Planning
├── 02_IP_Resistivity_Planning
├── 03_Magnetic_Survey_Planning
├── 04_Infill_Soil_Planning
├── 05_Scout_Drill_Collar_Design
├── 06_HSE_Environment_Rehabilitation
└── 07_Budget_Permit_Schedule

Фолдер бүрт дараах дэд хавтас үүсгэвэл тохиромжтой.
/Inputs
/Working
/Outputs
/QAQC
/Maps_PDF

# 5. Ажил эхлэхээс өмнөх бэлтгэл
## 5.1 QGIS project бэлтгэх
QGIS дээр дараах layer-үүдийг нэг coordinate system-д оруулна.
- License boundary
- Target polygons
- Target ranking points
- Geology
- Structure / fault / lineament
- Alteration
- Geochemical anomaly
- Mineralized points
- DEM / slope / hillshade
- Satellite basemap
- Access road
- River / drainage
- Restricted or risky area
Бүх layer-үүдийн CRS нэг байх ёстой. Монголын талбайд ихэвчлэн UTM zone ашиглана. CRS зөрвөл эхлээд засна.
## 5.2 Байнуудыг шалгах
A болон B зэрэглэлийн target бүр дээр дараах асуултаар шалгана.
- Тухайн target дээр гадаргын эрдэсжилт баталгаатай юу?
- Лабораторийн эсвэл XRF үр дүн дэмжиж байна уу?
- Геологийн таатай нэгж, контакт, хагарал, судал байна уу?
- Slope болон access боломжтой юу?
- Тухайн бай дээр trench хийх боломжтой юу?
- IP эсвэл magnetic survey хийх шугам татах боломжтой юу?
- Өрөмдлөгийн pad байрлуулах боломж байна уу?
- HSE, нөхөн сэргээлт, зөвшөөрлийн эрсдэл байна уу?
# 6. Trench / channel planning хийх заавар
## 6.1 Trench сонгох үндсэн шалгуур
Trench-ийг дараах нөхцөлүүд давхцаж байгаа газарт төлөвлөнө.
- Гадаргын эрдэсжилт илэрсэн
- Lab assay эсвэл XRF anomaly байна
- Хүрэх боломжтой
- Налуу хэт огцом биш
- Судал, контакт, structure-ийг огтолж гарах боломжтой
- Target geometry-г илүү тодруулах шаардлагатай
- Хөрсний зузаан trench хийх боломжтой
- Байгаль орчны эрсдэл бага
## 6.2 QGIS дээр хийх алхам
- Final A/B target layer-ийг нээнэ.
- Mineralized points, XRF/lab assay point layer-ийг давхар харуулна.
- Geology, structure, alteration layer-ийг нэмж асаана.
- DEM slope layer-ээр trench хийх боломжтой налууг шалгана.
- Trench line нь эрдэсжилтийн чиглэлтэй параллель биш, харин огтолж гарах байдлаар төлөвлөгдөнө.
- Trench эхлэл, төгсгөлийн координатыг тэмдэглэнэ.
- Trench бүрт ID өгнө.
Жишээ ID:
TR-01
TR-02
TR-03

## 6.3 Trench attribute table-д оруулах мэдээлэл
- Trench ID
- Target ID
- Start Easting
- Start Northing
- End Easting
- End Northing
- Length
- Azimuth
- Target type
- Reason for trench
- Expected geology
- Expected mineralization
- Access condition
- HSE risk
- Rehabilitation method
- Priority
- Reviewer
- Decision
## 6.4 Trench decision
Trench зөвшөөрөгдөх доод нөхцөл:
- surface mineralization баталгаатай
- assay/XRF support байна
- geological control тодорхой
- access боломжтой
- HSE эрсдэл хүлээн зөвшөөрөх түвшинд
- нөхөн сэргээлтийн төлөвлөгөөтэй
# 7. IP / Resistivity planning хийх заавар
## 7.1 IP survey хийх үндэслэл
IP/resistivity нь дараах нөхцөлд тохиромжтой.
- Sulfide mineralization сэжигтэй
- Chargeability anomaly шалгах шаардлагатай
- Structure болон geology-р хянагдсан target байна
- Cover ихтэй, гадаргын илрэл сул
- Trench-ээр хангалттай баталгаажихгүй гүн target байна
- Өрөмдлөгийн өмнө далд биетийн байрлал тодруулах шаардлагатай
## 7.2 Survey line төлөвлөх арга
- A/B target polygon-уудыг QGIS дээр нээнэ.
- Structure, geology, alteration, geochemical anomaly-г хамтад нь харна.
- IP line нь target trend-ийг огтолж гарах чиглэлтэй байна.
- Нэг target дээр 1–3 шугам төлөвлөж болно.
- Line spacing-ийг target хэмжээ, төсөв, газрын нөхцөлөөр тогтооно.
- Survey line нь access боломжтой, аюулгүй газраар дайрсан байх ёстой.
- Шугамын эхлэл, төгсгөлийн координатыг бүртгэнэ.
## 7.3 IP line attribute table
- Line ID
- Target ID
- Start Easting
- Start Northing
- End Easting
- End Northing
- Length
- Azimuth
- Line spacing
- Array type
- Planned depth of investigation
- Reason for IP
- Expected sulfide target
- Access condition
- HSE risk
- Priority
- Reviewer
- Decision
## 7.4 IP survey-ийн QA/QC
- Шугам target-ийг зөв огтолж байгаа эсэх
- Шугам access боломжтой эсэх
- DEM slope хэт огцом биш эсэх
- Protected area, river, settlement-тэй давхцаагүй эсэх
- Өрөмдлөгийн шийдвэрт ашиглахуйц байрлалтай эсэх
# 8. Magnetic survey planning хийх заавар
## 8.1 Magnetic survey хийх үндэслэл
Magnetic survey-г дараах зорилгоор ашиглана.
- Intrusive body тодруулах
- Mafic unit ялгах
- Contact zone тодруулах
- Fault / structure trace баталгаажуулах
- Skarn, magnetite-bearing alteration, mafic-ultramafic холбоотой target шалгах
- Геологийн зураглалын uncertainty бууруулах
## 8.2 Magnetic line төлөвлөх алхам
- Geology map, structure map, DEM, target layer-ийг нээнэ.
- Intrusive/contact/mafic unit байгаа эсэхийг шалгана.
- Line-уудыг structure болон contact-ийг огтолж гарахаар төлөвлөнө.
- Survey area-г polygon хэлбэрээр тодорхойлно.
- Line spacing болон reading interval тогтооно.
- Base station байрлуулах боломжийг шалгана.
- Өдөр тутмын survey capacity-г тооцно.
## 8.3 Magnetic survey table
- Survey block ID
- Target ID
- Line ID
- Start coordinate
- End coordinate
- Line length
- Line spacing
- Reading interval
- Expected geological target
- Base station location
- Access condition
- HSE risk
- Priority
- Reviewer
- Decision
# 9. Infill soil sampling planning хийх заавар
## 9.1 Infill soil хийх нөхцөл
Infill soil sampling-г дараах үед хийнэ.
- Өмнөх soil anomaly open-ended байгаа
- Anomaly-ийн boundary тодорхойгүй
- Line spacing хэт өргөн
- Transported cover байж болзошгүй
- Anomaly confidence бага
- Trench эсвэл drilling хийхээс өмнө anomaly-г нарийвчлах шаардлагатай
## 9.2 Infill grid төлөвлөх
- Existing soil sample point layer-ийг нээнэ.
- Anomaly map-ийг хамтад нь харна.
- Open-ended anomaly чиглэлийг тодорхойлно.
- Шинэ дээж авах шугам, цэгийг төлөвлөнө.
- Өмнөх grid-тэй нийцсэн spacing сонгоно.
- Drainage, slope, access, private/restricted area шалгана.
- Давхардсан sample ID гарахгүй байхаар бүртгэнэ.
## 9.3 Sample point attribute
- Sample ID
- Target ID
- Easting
- Northing
- Sample type
- Grid line
- Spacing
- Reason for infill
- Expected anomaly
- Access condition
- Field status
- Collected by
- Date
- QA/QC sample type
- Reviewer
## 9.4 QA/QC sample төлөвлөлт
Infill soil sampling-д дараах QA/QC дээжүүдийг төлөвлөнө.
- Field duplicate
- Blank
- Standard reference material
- Repeat sample
- Sample dispatch register
QA/QC дээжийн хувь хэмжээг project-ийн стандартын дагуу тогтооно. Хэрэв тусгай стандарт байхгүй бол дотоод QA/QC протокол гаргаж мөрдөнө.
# 10. Scout drilling төлөвлөх заавар
## 10.1 Scout drilling хийх minimum criteria
Scout drilling зөвшөөрөхөөс өмнө дараах бүх шалгуурыг хангана.
- Гадаргын эрдэсжилт баталгаатай
- Lab assay эсвэл XRF үр дүн дэмжиж байгаа
- Structure баталгаажсан
- Favorable geology/contact байгаа
- Target geometry ойлгомжтой болсон
- Access боломжтой
- Drill pad байгуулах боломжтой
- HSE нөхцөл хангагдсан
- Trench/geophysics хийх шаардлагатай бол хийсэн эсвэл төлөвлөгдсөн
- Permit, budget, schedule боломжтой
## 10.2 Drill collar сонгох арга
- Final target layer-ийг нээнэ.
- Trench, IP, magnetic, soil anomaly layer-ийг давхар харуулна.
- Target-ийн төв бус, харин geological control бүхий хэсгийг сонгоно.
- Өрөмдлөгийн collar нь target-ийг зөв өнцгөөр огтлох байдлаар байрлана.
- Azimuth болон dip нь structure/sudal/contact-ийг огтлох ёстой.
- Collar location нь access, slope, pad, water, safety нөхцөл хангана.
- Drill depth нь target depth estimate дээр үндэслэнэ.
- Хэт урт, тодорхой бус, зөвхөн таамагласан цооног төлөвлөхөөс зайлсхий.
## 10.3 Drill collar table
Доорх багануудыг Excel дээр заавал үүсгэнэ.
- Drill hole ID
- Target ID
- Easting
- Northing
- RL / elevation
- Azimuth
- Dip
- Planned depth
- Target type
- Target rationale
- Expected geology
- Expected mineralization
- Section line
- Access condition
- Drill pad condition
- Water source
- HSE risk
- Permit status
- Rehabilitation plan
- Estimated cost
- Priority
- Reviewer
- Decision
Жишээ ID:
SC-01
SC-02
SC-03

## 10.4 Drill section хийх
- Scout drill бүр дээр section line зурна.
- Section нь drill azimuth чиглэлтэй нийцсэн байна.
- Geology, structure, mineralization, trench, geophysics anomaly-г section дээр оруулна.
- Target intercept estimate тэмдэглэнэ.
- Planned drill trace зурна.
- Uncertainty-г тэмдэглэнэ.
# 11. HSE, access, environment, rehabilitation шалгах заавар
## 11.1 Access шалгалт
Тухайн trench, geophysics line, drill collar бүр дээр дараахыг шалгана.
- Машин очих боломжтой эсэх
- Зам шинээр гаргах шаардлагатай эсэх
- Налуу хэт огцом эсэх
- Гол, жалга, намаг, хад асга байгаа эсэх
- Цаг агаарын улирлын нөлөө байгаа эсэх
- Тоног төхөөрөмж оруулах боломжтой эсэх
## 11.2 HSE шалгалт
- Өндөр налуу
- Хад асга
- Гол ус
- Малчин айл, суурин
- Хуучин уурхай, нүх, ухаш
- Цаг агаар
- Холбоо барих боломж
- Онцгой байдлын гарц
- Анхны тусламжийн боломж
## 11.3 Environment шалгалт
- Ургамлын бүрхэвч
- Гол горхи
- Соёлын өв байж болох газар
- Тусгай хамгаалалттай газар
- Малын бэлчээр
- Хөрсний эвдрэл
- Нөхөн сэргээлтийн боломж
## 11.4 Rehabilitation төлөвлөгөө
- Trench бөглөх арга
- Topsoil тусад нь хадгалах
- Drill pad цэвэрлэх
- Шинэ замын мөрийг багасгах
- Хог хаягдал буцаан тээвэрлэх
- Фото баримтжуулалт хийх
- Before/after photo хадгалах
# 12. Төсөв, зөвшөөрөл, schedule боловсруулах
## 12.1 Төсөвт оруулах зүйл
- Trench excavation cost
- Channel sampling cost
- IP/resistivity survey cost
- Magnetic survey cost
- Infill soil sampling cost
- Scout drilling cost
- Assay cost
- Field camp cost
- Vehicle/fuel cost
- HSE cost
- Rehabilitation cost
- Permit cost
- Contingency
## 12.2 Schedule гаргах
Ажлыг дараах дарааллаар төлөвлөнө.
- Office target review
- Field verification
- Trench planning approval
- Geophysics line approval
- Infill soil approval
- Permit and HSE approval
- Trench execution
- Geophysics survey
- Assay/data processing
- Scout drilling final decision
- Drill pad preparation
- Scout drilling
## 12.3 Permit шалгах
- Local authority notification
- Land access agreement
- Environmental approval
- Water use requirement
- Drilling permit condition
- Rehabilitation obligation
- Community communication
# 13. QA/QC check
Phase 11-ийн QA/QC шалгалтыг дараах хүснэгтээр хийнэ.

| QA/QC item | Acceptance note |
| --- | --- |
| Minimum scout drill criteria met | Phase QA/QC log-д reviewer/date/decision тэмдэглэсэн байна |
| HSE/access/rehabilitation reviewed | Phase QA/QC log-д reviewer/date/decision тэмдэглэсэн байна |
| Drill collar geometry justified | Phase QA/QC log-д reviewer/date/decision тэмдэглэсэн байна |
| Budget/permit/schedule template completed | Phase QA/QC log-д reviewer/date/decision тэмдэглэсэн байна |
| Trench line target-ийг зөв огтолж байгаа | Reviewer баталгаажуулсан байна |
| IP/magnetic line geological control-той нийцсэн | Reviewer баталгаажуулсан байна |
| Infill soil open-ended anomaly-г хааж байгаа | Reviewer баталгаажуулсан байна |
| Drill hole target rationale бичигдсэн | Reviewer баталгаажуулсан байна |

# 14. Expected outputs
Phase 11 дуусахад дараах файлууд бэлэн болсон байна.
XV-023222_Buduunkhad_Follow_Up_Work_Plan.pdf
XV-023222_Buduunkhad_Proposed_Trench_Locations.gpkg
XV-023222_Buduunkhad_Proposed_IP_Magnetic_Lines.gpkg
XV-023222_Buduunkhad_Scout_Drilling_Proposal.docx
XV-023222_Buduunkhad_Drill_Collar_Table.xlsx

Нэмэлтээр дараах файлуудыг гаргавал зохимжтой.
XV-023222_Buduunkhad_Phase11_QAQC_Log.xlsx
XV-023222_Buduunkhad_HSE_Access_Rehabilitation_Checklist.xlsx
XV-023222_Buduunkhad_Budget_Permit_Schedule.xlsx
XV-023222_Buduunkhad_Drill_Section_Map.pdf
XV-023222_Buduunkhad_Field_Verification_Map.pdf

# 15. Decision gate / дараагийн шат руу шилжих нөхцөл
Scout drilling зөвхөн дараах нөхцөл бүрэн хангагдсан үед үргэлжилнэ.
- Minimum scout drill criteria хангагдсан
- Surface mineralization confirmed
- Lab assay эсвэл XRF дэмжлэгтэй
- Structure/geology/contact баталгаатай
- Target geometry хангалттай ойлгомжтой
- Access, HSE, rehabilitation боломжтой
- Permit issue байхгүй
- Budget approved
- Drill collar geometry justified
- Reviewer/date/decision QA/QC log-д бүртгэгдсэн
Хэрэв дээрх нөхцөлүүдийн аль нэг нь хангагдаагүй бол шууд өрөмдлөг хийхгүй. Харин дараах нэмэлт ажлыг санал болгоно.
- Нэмэлт trench
- Нэмэлт IP/resistivity
- Нэмэлт magnetic survey
- Нэмэлт soil sampling
- Нэмэлт mapping
- Target ranking дахин үнэлэх
# 16. Ажлын дарааллын товч workflow
Input data цуглуулах
↓
QGIS project нэгтгэх
↓
A/B target review хийх
↓
Trench location төлөвлөх
↓
IP/resistivity line төлөвлөх
↓
Magnetic survey line төлөвлөх
↓
Infill soil grid төлөвлөх
↓
Scout drill collar preliminary design хийх
↓
Access/HSE/environment шалгах
↓
Budget/permit/schedule боловсруулах
↓
QA/QC review хийх
↓
Final work plan гаргах
↓
Drilling decision гаргах

# 17. Гол анхаарах зүйл
Энэ шатанд өрөмдлөгийн цэгийг зөвхөн “сонирхолтой харагдаж байна” гэдэг үндэслэлээр сонгож болохгүй. Заавал дараах шалгуурыг хамтад нь үнэлсний дараа scout drilling санал гаргана.
- геологийн үндэслэл
- геохимийн баталгаа
- геофизикийн дэмжлэг
- гадаргын эрдэсжилт
- бүтцийн хяналт
- access/HSE боломж
- төсөв ба зөвшөөрөл
