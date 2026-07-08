<!-- source: Phase_6_Recon_Mapping_and_pXRF_Field_Screening_Detailed_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

# 06. Phase 6 — Recon Mapping and Portable XRF Field Screening
Дэлгэрэнгүй ажлын заавар
Энэхүү баримт бичиг нь өмнөх Phase 4–5 болон геологийн/металлогенийн эх сурвалжаар сонгосон A/B зэрэглэлийн target-уудыг талбай дээр шалгах, литологи, хувирал, хүдэржилт, судал, структур, weathering, илэрц, access нөхцөлийг баталгаажуулах, мөн portable XRF-ээр vectoring хийх аргачлалыг бүрэн тайлбарлана.
# 1. Ажлын зорилго
Phase 6-ийн зорилго нь өмнөх боловсруулалтын үр дүнд гарсан priority target буюу эрэмбэлсэн хайгуулын бүсүүдийг газар дээр нь шалгах, геологийн нотолгоо цуглуулах, portable XRF-ээр анхан шатны элементүүдийн тархалт, anomaly, zoning, vector чиглэл тодорхойлох юм.
Энэ шатны үр дүнгээр дараах шийдвэр гаргана:
- Дээж авах шаардлагатай эсэх;
- Target-ийг ахиулах эсвэл бууруулах эсэх;
- Дараагийн шатны trenching, detailed sampling, geophysics, drilling зэрэг ажилд оруулах эсэх.
Portable XRF-ийн үр дүн нь лабораторийн шинжилгээний орлуулах эцсийн баталгаат үр дүн биш, харин талбай дээр хурдан decision support хийх, anomaly vectoring хийх, сорьц авах цэгийг оновчлох зориулалттай.
# 2. Ашиглах input data
## 2.1 Заавал ашиглах үндсэн input

| Input data | Ашиглах зорилго / тайлбар |
| --- | --- |
| Phase 4 target polygons | Өмнөх шатанд гарсан target талбайнууд. A/B/C зэрэглэлтэй байвал A болон B target-уудыг эхэлж шалгана. |
| Phase 5 drone outputs | Ортофото, DEM, hillshade, slope, lineament, structural interpretation, outcrop visibility map зэрэг. |
| Detailed geological map / legend | Литологи, стратиграфи, интрузив, хувирал, структур, fault, contact, dyke, vein zone-уудыг шалгах үндсэн суурь зураг. |
| Mineral occurrence map | Ойролцоох илрэл, орд, хүдэржилтийн бүс, historical occurrence, showings. |
| Prospectivity map | Өмнөх өгөгдлүүдийг нэгтгэж гаргасан ашигт малтмалын хэтийн төлөвийн зураг. |
| Source materials map / legend | Геологийн тайлбар, regional metallogenic map, stream sediment, шлих, геохими, геофизик зэрэг эх сурвалжийн мэдээлэл. |
| Occurrence / register files | Ашигт малтмалын илрэл, хуучин цэг, дээж, маршрутын бүртгэл. |
| Terrain and basemap files | DEM, hillshade, slope, satellite basemap, access route, road, river, ridge, valley. |
| License boundary | Судалгааны талбайн хил зааг. Бүх ажил license boundary дотор төлөвлөгдөж, хил давсан тохиолдолд тусгай тэмдэглэл хийнэ. |

# 3. Программ, багаж, тоног төхөөрөмж
## 3.1 Программ
- QGIS
- QField
- GPS/GNSS app эсвэл handheld GPS software
- Excel
- Portable XRF export software
- Google Drive / shared folder буюу төв оффистой өгөгдөл солилцох систем
## 3.2 Талбайн багаж
- Olympus Vanta M portable XRF
- Bruker Titan S1 portable XRF
- GPS / GNSS receiver
- Гар утас эсвэл tablet QField суулгасан
- Compass / clinometer
- Geological hammer
- Hand lens
- Sample bags
- Permanent marker
- Sample tag
- Field notebook
- Camera / phone camera
- PPE: каск, хамгаалалтын шил, бээлий, safety vest, boots
- CRM / blank / duplicate sample материал
- Calibration check sample
- Power bank, spare battery, charger
# 4. Талбайд гарахын өмнөх бэлтгэл
## 4.1 Target review хийх
QGIS дээр бүх target polygon-уудыг нээж дараах байдлаар шалгана. Target бүр дээр дараах мэдээллийг target review sheet-д тэмдэглэнэ:
- Target ID
- Priority rank: A, B, C
- Expected deposit model: porphyry, skarn, epithermal, polymetallic vein гэх мэт
- Expected elements: Cu, Pb, Zn, As, Mo, W, Sn, Mn, Fe, S гэх мэт
- Geological control: fault, contact, intrusive margin, alteration zone, vein corridor
- Nearby known deposits / occurrences
- Access possibility
- Outcrop exposure
- Safety condition
## 4.2 Traverse route төлөвлөх
A/B target бүр дээр traverse route төлөвлөнө. Route нь зөвхөн шулуун алхалт биш, харин geological control-ийг огтолж шалгах байдлаар төлөвлөгдөнө.
Traverse төлөвлөхдөө дараах зарчмыг баримтална:
- Fault, contact, vein zone, alteration boundary-г огтлох
- Ridge, valley, drainage, slope exposure-г ашиглах
- Ил гарсан чулуулгийн цэгүүдийг хамрах
- Хуучин mineral occurrence цэгүүдийг дахин шалгах
- Satellite / drone image дээр тодорсон color anomaly, lineament, gossan, quartz vein, alteration patch-ийг оруулах
- Safety risk өндөр бүсээс зайлсхийх
## 4.3 QField project бэлтгэх
QGIS дээр дараах давхаргуудыг QField-д оруулж бэлдэнэ.
### Үндсэн background layers
- License boundary
- Target polygons
- Priority target labels
- Drone orthophoto
- Hillshade
- DEM
- Geological map
- Structural interpretation
- Mineral occurrence points
- Access route / roads
- Planned traverse lines
### Field data collection layers
- Recon traverse line
- Field observation point
- pXRF reading point
- Sample point
- Photo point
- QA/QC point
## 4.4 Attribute form бэлтгэх
QField form дээр дараах талбаруудыг заавал оруулна.

| Form | Заавал бүртгэх талбарууд |
| --- | --- |
| Field Observation Point | obs_id; date; geologist; target_id; coordinate_x; coordinate_y; elevation; lithology; alteration; mineralization; vein_type; vein_width; structure_type; strike; dip; oxidation/weathering; outcrop_quality; sample_taken: yes/no; sample_id; photo_id; comment |
| pXRF Reading Point | xrf_id; date; operator; target_id; obs_id; sample_id, хэрэв дээж дээр хэмжсэн бол; instrument_brand; instrument_model; serial_number; method/mode; reading_time; surface_condition; moisture_condition; Cu_ppm; Pb_ppm; Zn_ppm; As_ppm; Mo_ppm; W_ppm; Sn_ppm; Mn_ppm; Fe_percent; S_percent; QAQC_type: field/CRM/blank/duplicate/check sample; reliability_flag; decision_note |

## 4.5 XRF багажийн урьдчилсан шалгалт
- Багажийн battery бүрэн цэнэгтэй эсэхийг шалгана.
- Method/application зөв сонгогдсон эсэхийг шалгана.
- Calibration check sample уншуулж үр дүн хэвийн эсэхийг шалгана.
- CRM уншуулж reference value-тэй харьцуулна.
- Blank уншуулж contamination байгаа эсэхийг шалгана.
- Internal clock, date, GPS setting зөв эсэхийг шалгана.
- Data export format Excel/CSV тохиргоо зөв эсэхийг шалгана.
- Radiation safety warning, interlock, shutter ажиллаж байгаа эсэхийг шалгана.
# 5. Талбай дээр хийх үндсэн ажиллагаа
## 5.1 Target дээр очих
- QField дээр target polygon-оо нээнэ.
- Planned traverse route-оо дагаж хөдөлнө.
- GPS track recording эхлүүлнэ.
- Route эхэлсэн цэгийг тэмдэглэнэ.
- Target ID, weather, багийн гишүүд, эхэлсэн цагийг field note-д бичнэ.
## 5.2 Traverse mapping хийх
Traverse хийх явцад дараах зүйлсийг системтэй ажиглана.
### Литологи
- Чулуулгийн төрөл
- Grain size
- Texture
- Intrusive / volcanic / sedimentary / metamorphic эсэх
- Contact relationship
- Dyke, vein, breccia байгаа эсэх
- Host rock type
### Хувирал
- Silicification
- Sericite alteration
- Chlorite alteration
- Epidote alteration
- Carbonate alteration
- Argillic alteration
- Propylitic alteration
- Potassic alteration
- Skarn alteration
- Gossan / oxidation
### Хүдэржилт
- Malachite
- Azurite
- Chalcopyrite
- Pyrite
- Bornite
- Covellite
- Galena
- Sphalerite
- Arsenopyrite
- Magnetite
- Hematite
- Limonite
- Manganese oxide
### Судал ба структур
- Quartz vein
- Carbonate vein
- Sulfide vein
- Stockwork
- Breccia zone
- Fault
- Shear zone
- Joint set
- Fold
- Strike/dip
- Vein density
- Vein width
- Vein orientation
### Surface condition
- Outcrop эсэх
- Float эсэх
- Subcrop эсэх
- Soil cover
- Weathering intensity
- Moisture condition
- Slope exposure
- Vegetation cover
# 6. pXRF хэмжилт хийх аргачлал
## 6.1 Хэмжилт хийх цэг сонгох
pXRF хэмжилтийг дараах төрлийн цэгүүд дээр хийнэ.
- Ил гарсан fresh rock
- Хүдэржилттэй судал
- Хувиралтай host rock
- Gossan / iron oxide zone
- Fault breccia
- Contact zone
- Mineralized float
- Background буюу хүдэржилтгүй host rock
- Duplicate check хийх ижил цэг
- CRM / blank / check sample
Зөвхөн тод өнгөтэй, сонирхолтой чулуу дээр хэмжихгүй. Заавал background болон weak alteration цэгүүдийг хамтад нь хэмжиж, anomaly-г харьцуулах боломжтой болгоно.
## 6.2 Чулууны гадаргуу бэлтгэх
- Тоос, шавар, ус, органик бохирдлыг арилгана.
- Боломжтой бол fresh surface гаргана.
- Weathered surface болон fresh surface-ийг ялгаж тэмдэглэнэ.
- Нойтон гадаргуу дээр хэмжсэн бол moisture condition-д тэмдэглэнэ.
- Хэт барзгар гадаргуу дээр хэмжилт хийхээс зайлсхийж, flat surface сонгоно.
## 6.3 Хэмжилтийн горим
- Нэг цэг дээр 1 удаа primary reading
- Сонирхолтой anomaly гарвал 2–3 удаа repeat reading
- Өдөр бүр CRM, blank, duplicate, check sample уншуулна
- Reading time-ийг бүх хэмжилтэд нэгэн жигд барина
- Method/application-г солих бол тэмдэглэл хийнэ
- Багаж солигдсон бол instrument ID-г тодорхой бичнэ
## 6.4 Заавал бүртгэх metadata
- xrf_id
- obs_id
- sample_id, хэрэв дээж авсан бол
- target_id
- GPS coordinate
- date/time
- operator
- instrument model
- serial number
- method/application
- reading time
- lithology
- alteration
- mineralization
- surface condition
- moisture condition
- Cu
- Pb
- Zn
- As
- Mo
- W
- Sn
- Mn
- Fe
- S
- reliability flag
- comment
# 7. QA/QC шалгалт
Phase 6-д QA/QC маш чухал. Учир нь portable XRF-ийн үр дүн нь гадаргуугийн нөхцөл, чийг, ширхэглэл, багажийн тохиргоо, calibration, sample geometry-оос их хамаардаг.
## 7.1 Өдөр бүр хийх QA/QC
### Өдөр бүр талбайн ажил эхлэхэд
- Warm-up хийх
- Calibration check sample уншуулах
- CRM уншуулах
- Blank уншуулах
- Багажийн date/time шалгах
- Battery болон memory шалгах
- GPS болон coordinate system шалгах
### Өдөр дуусахад
- CRM дахин уншуулах
- Blank дахин уншуулах
- Өдрийн duplicate results шалгах
- Data export хийх
- QA/QC log бөглөх
- Өдрийн pXRF anomaly summary гаргах
## 7.2 Duplicate check
- Нэг ижил гадаргуу дээр давтан хэмжинэ.
- Боломжтой бол 90 градус эргүүлж дахин хэмжинэ.
- Хэрэв chip sample эсвэл powder sample бол нэг sample bag-аас давтан уншуулна.
- Duplicate хооронд хэт их зөрүү гарвал surface condition, moisture, heterogeneity, mineral grain effect гэж тэмдэглэнэ.
## 7.3 CRM шалгалт
CRM буюу certified reference material нь багажийн хэмжилтийн найдвартай байдлыг шалгах зориулалттай.
- Хүлээн зөвшөөрөх хязгаарт байвал “Pass”
- Хязгаараас гарвал “Warning”
- Их зөрүүтэй бол “Fail / recalibration required”
Fail гарсан үед тухайн өдрийн бүх field reading-д reliability flag тавина.
## 7.4 Blank шалгалт
Blank sample нь contamination байгаа эсэхийг шалгана. Blank дээр Cu, Pb, Zn, As зэрэг элемент өндөр гарвал:
- Багажийн window бохирдсон эсэхийг шалгана.
- Sample cup, bag, surface contamination байгаа эсэхийг шалгана.
- Дахин blank уншуулна.
- Шаардлагатай бол өмнөх хэмжилтүүдийг “suspect” гэж тэмдэглэнэ.
## 7.5 Acceptance note

| QA/QC item | Acceptance note |
| --- | --- |
| CRM | Reference value-тэй харьцуулж pass/warning/fail тэмдэглэнэ |
| Blank | Contamination байгаа эсэхийг шалгана |
| Duplicate | Primary reading-тэй харьцуулж repeatability шалгана |
| Vanta vs Titan comparison | Хоёр багажийн үр дүнг харьцуулж systematic bias байгаа эсэхийг шалгана |
| Moisture / surface condition | Үр дүнд нөлөөлөх нөхцөлийг reliability flag-д тусгана |

# 8. Au болон бусад элементийн талаар анхаарах зүйл
Portable XRF-ээр Au-г талбай дээр decision-grade evidence болгон ашиглахгүй. Au бага агууламжтай, nugget effect өндөртэй, detection limit болон matrix effect ихтэй тул pXRF-ийн Au үр дүнг лабораторийн assay-ээр баталгаажуулах шаардлагатай.
Au-bearing system шалгах үед pXRF-ээр дараах pathfinder элементүүдийг илүү анхаарна.
- As
- Sb
- Bi
- Te
- Hg, хэрэв method дэмжиж байвал
- Cu
- Pb
- Zn
- Ag, хэрэв найдвартай хэмжигдэж байвал
- Mn
- Fe
- S
Epithermal Au-Ag target дээр As-Sb-Hg-Ag-Pb-Zn-Mn anomaly чухал байж болно.
Porphyry Cu-Au target дээр Cu-Mo-As-Pb-Zn-Fe-S болон alteration zonation анхаарна.
Skarn target дээр Cu-Zn-Pb-W-Mo-Sn-Fe-Mn-Ca холбоосыг анхаарна.
Polymetallic vein target дээр Pb-Zn-Cu-Ag-As-Sb-Mn-Fe anomaly-г анхаарна.
# 9. Талбай дээр decision хийх арга
## 9.1 Target upgrade хийх нөхцөл
- Хүдэржилттэй судал, stockwork, breccia илэрсэн
- pXRF-ээр Cu/Pb/Zn/As/Mo/W/Sn/Mn зэрэг элементүүд background-оос тод өндөр гарсан
- Хувирал, хүдэржилт, структур нэг бүсэд давхцсан
- Ойролцоох known occurrence-тэй geological continuity харагдсан
- Drone/remote sensing anomaly талбай дээр баталгаажсан
- Дээж авахад хангалттай fresh/mineralized material байгаа
- Multiple readings anomaly-г давтан баталгаажуулсан
## 9.2 Target downgrade хийх нөхцөл
- Геологийн зураг дээрх favorable unit талбай дээр баталгаажаагүй
- Хувирал сул эсвэл огт байхгүй
- Хүдэржилтгүй
- pXRF anomaly байхгүй
- Илэрц муу, ихэнх нь transported float
- Remote sensing anomaly нь vegetation, shadow, weathering эсвэл soil effect байсан
- Access хэт хүндрэлтэй, safety risk өндөр
## 9.3 Lab assay авах шаардлагатай нөхцөл
- pXRF Cu/Pb/Zn/As/Mo/W/Sn өндөр anomaly гарсан
- Au target дээр pathfinder anomaly гарсан
- Visible sulfide, oxide copper, galena, sphalerite, arsenopyrite илэрсэн
- Quartz vein / breccia / stockwork mineralized zone байна
- Skarn alteration болон sulfide хамт илэрсэн
- Porphyry style alteration, veinlet, disseminated sulfide илэрсэн
- Polymetallic vein system баталгаажсан
- Multiple readings consistent anomaly өгсөн
# 10. Дээж авах заавар
## 10.1 Дээжийн төрөл
- Rock chip sample
- Grab sample
- Float sample
- Vein sample
- Altered host rock sample
- Channel sample, хэрэв exposure боломжтой бол
- QA/QC duplicate sample
## 10.2 Дээж авахдаа бүртгэх зүйл
- sample_id
- target_id
- obs_id
- date
- sampler
- coordinate
- lithology
- alteration
- mineralization
- sample type
- sample length, хэрэв channel бол
- vein width
- structure orientation
- photo_id
- pXRF reading ID
- reason for sampling
- lab assay package recommendation
## 10.3 Дээжийн ID систем
Жишээ ID: XV023222-RK-20260605-001
Тайлбар: XV023222 = project/license code; RK = rock sample; 20260605 = огноо; 001 = дарааллын дугаар.
pXRF ID: XV023222-XRF-20260605-001
Observation ID: XV023222-OBS-20260605-001
# 11. Өдөр тутмын data management
## 11.1 Өдөр бүр хадгалах файл
- QField observation points
- Traverse track
- pXRF raw export
- pXRF cleaned Excel
- Photos
- Sample register
- QA/QC log
- Daily field summary
## 11.2 Folder structure
Phase 6-ийн processing folder structure дараах байдлаар байна.
06_Phase_6_Recon_Mapping_and_Portable_XRF_Field_Screening/
├── 01_Traverse_Planning
├── 02_Field_Mapping_Forms
├── 03_pXRF_VantaM_Primary
├── 04_pXRF_TitanS1_Duplicate_Check
├── 05_pXRF_QAQC_CRM_Blank_Duplicate
├── 06_Field_Database
└── 07_Recon_Report
## 11.3 Folder тус бүрийн агуулга
### 01_Traverse_Planning
- Target ranking map
- Planned traverse lines
- Access route map
- Safety route
- Daily field plan
- Target review sheet
### 02_Field_Mapping_Forms
- QField form template
- Observation form
- Sample form
- Structure form
- Photo log form
- Lithology/alteration code list
### 03_pXRF_VantaM_Primary
- Olympus Vanta M raw export
- Vanta M cleaned data
- Vanta M field readings
- Vanta M instrument log
### 04_pXRF_TitanS1_Duplicate_Check
- Bruker Titan S1 duplicate readings
- Vanta vs Titan comparison
- Duplicate check Excel
- Instrument comparison note
### 05_pXRF_QAQC_CRM_Blank_Duplicate
- CRM readings
- Blank readings
- Duplicate readings
- QA/QC acceptance sheet
- Daily QA/QC log
- Failed/flagged readings list
### 06_Field_Database
- Final observation points
- Final pXRF points
- Final sample points
- Traverse lines
- Photo index
- Master field database
### 07_Recon_Report
- Recon mapping report
- pXRF QA/QC report
- Target upgrade/downgrade memo
- Recommended sampling plan
- Next phase recommendation
# 12. Өгөгдөл боловсруулах аргачлал
## 12.1 pXRF raw data цэвэрлэх
- Raw file-ийг хадгалж, өөрчлөхгүй.
- Copy үүсгээд cleaned file дээр ажиллана.
- Хоосон мөр, test reading, failed reading-ийг ялгана.
- CRM, blank, duplicate, field reading гэж ангилна.
- Coordinate-тэй холбож шалгана.
- Sample ID болон observation ID-г тулгана.
- Element columns-ийг ppm эсвэл percent нэгжээр стандартчилна.
- Detection limit-аас доош утгыг тусгай тэмдэглэгээтэй хадгална.
- Moisture/surface condition flag-ийг нэмнэ.
- Reliability flag өгнө.
## 12.2 GIS-д оруулах
- Coordinate system зөв эсэх
- Цэгүүд license boundary дотор байгаа эсэх
- Target ID зөв холбогдсон эсэх
- Observation point болон sample point-тэй давхцаж байгаа эсэх
- Duplicate/QAQC цэгүүд field reading-тэй холилдоогүй эсэх
## 12.3 Anomaly map гаргах
Дараах элементүүдээр тус тусдаа anomaly map гаргана: Cu, Pb, Zn, As, Mo, W, Sn, Mn, Fe, S.
Deposit model-оос хамааран multi-element index үүсгэж болно.

| Deposit model / index | Анхаарах элементүүд |
| --- | --- |
| Porphyry Cu-Au index | Cu; Mo; As; Fe; S |
| Epithermal Au-Ag index | As; Sb; Pb; Zn; Mn; Fe; Ag, хэрэв хэмжигдсэн бол |
| Skarn index | Cu; Zn; W; Mo; Sn; Fe; Mn |
| Polymetallic vein index | Pb; Zn; Cu; As; Sb; Mn; Fe |

## 12.4 Target ranking шинэчлэх
- Previous rank
- Field evidence
- pXRF evidence
- QA/QC reliability
- Sampling recommendation
- Upgrade / downgrade decision
- Next phase recommendation
# 13. Тайлан гаргах бүтэц
## 13.1 Cover page
- Project name
- License number
- Phase name
- Date
- Field team
- Prepared by
- Reviewed by
## 13.2 Executive summary
- Хэдэн target шалгасан
- Хэдэн traverse хийсэн
- Хэдэн observation point авсан
- Хэдэн pXRF reading хийсэн
- Хэдэн дээж авсан
- Хэдэн target upgrade/downgrade болсон
- Дараагийн шатны санал
## 13.3 Methodology
- Traverse mapping арга
- pXRF screening арга
- QA/QC арга
- Data processing арга
- GIS analysis арга
## 13.4 Target-by-target result
- Target ID
- Location
- Geological setting
- Field observation
- pXRF result
- QA/QC reliability
- Photos
- Map
- Sampling decision
- Final ranking
- Recommendation
## 13.5 QA/QC result
- CRM result
- Blank result
- Duplicate result
- Vanta vs Titan comparison
- Failed / flagged readings
- Reliability conclusion
## 13.6 Maps
- Traverse route map
- Observation point map
- pXRF Cu map
- pXRF Pb-Zn map
- pXRF As map
- Multi-element anomaly map
- Target upgrade/downgrade map
- Sample location map
## 13.7 Conclusion and next phase
- Lab assay шаардлагатай дээжүүд
- Detailed mapping хийх бүсүүд
- Trenching санал
- Geophysics санал
- Drilling-ready болох боломжтой target
- Downgrade хийх target
# 14. Expected outputs
Phase 6-ийн төгсгөлд дараах output файлууд бэлэн болсон байна.
XV-023222_Buduunkhad_Recon_Traverse_Lines.gpkg
XV-023222_Buduunkhad_Field_Observation_Points.gpkg
XV-023222_Buduunkhad_pXRF_Field_Screening_Register.xlsx
XV-023222_Buduunkhad_pXRF_QAQC_Report.docx
XV-023222_Buduunkhad_Recon_Mapping_Report.docx
Нэмж гаргах боломжтой файлууд:
XV-023222_Buduunkhad_Target_Upgrade_Downgrade_Map.pdf
XV-023222_Buduunkhad_pXRF_Cu_Anomaly_Map.pdf
XV-023222_Buduunkhad_pXRF_PbZn_Anomaly_Map.pdf
XV-023222_Buduunkhad_pXRF_As_Pathfinder_Map.pdf
XV-023222_Buduunkhad_Field_Photo_Register.xlsx
XV-023222_Buduunkhad_Rock_Sample_Register.xlsx
XV-023222_Buduunkhad_Daily_Field_Log.xlsx
# 15. Decision gate / Next phase condition
Phase 6 дууссаны дараа дараах decision gate хэрэглэнэ.
## Proceed to next phase
- Field evidence байгаа
- pXRF anomaly байгаа
- Geological setting favorable
- Structure/alteration/mineralization давхцсан
- Дээж авах боломжтой
- QA/QC үр дүн найдвартай
- Lab assay-аар баталгаажуулах шаардлагатай
## Hold / additional check
- pXRF anomaly байгаа боловч geology сул
- Geology сайн боловч pXRF anomaly сул
- Илэрц муу
- QA/QC flag ихтэй
- Өгөгдөл дутуу
## Downgrade
- Field evidence байхгүй
- Хүдэржилтгүй
- Хувиралгүй
- pXRF anomaly байхгүй
- Өмнөх remote sensing anomaly талбай дээр баталгаажаагүй
- Access/safety нөхцөл хэт муу
# 16. Талбайн багт өгөх богино checklist
## Өглөө талбайд гарахын өмнө
- QField project нээгдэж байгаа эсэх
- Target map, traverse route харагдаж байгаа эсэх
- GPS ажиллаж байгаа эсэх
- XRF battery бүрэн эсэх
- CRM / blank / duplicate материал байгаа эсэх
- Sample bag, tag, marker бэлэн эсэх
- Camera/photo ID system бэлэн эсэх
- Safety equipment бүрэн эсэх
## Target дээр
- Traverse эхлүүл
- Observation point бүртгэ
- Фото ав
- Lithology бич
- Alteration бич
- Mineralization бич
- Structure хэмж
- pXRF уншуул
- Сонирхолтой цэгээс дээж ав
- Background цэгийг заавал хэмж
- Reliability flag бөглө
## Өдөр дуусахад
- QField data export хий
- pXRF raw data тат
- Photo backup хий
- Sample register бөглө
- QA/QC log бөглө
- Daily summary бич
- Маргаашийн target plan шинэчил
# 17. Анхаарах гол зарчим
Энэ Phase 6-ийн хамгийн чухал зарчим бол pXRF-ийн тоо дангаараа шийдвэр биш юм. Шийдвэрийг дараах 4 нотолгоог хамтад нь харж гаргана.
- Геологийн орчин
- Хувирал ба структур
- Хүдэржилтийн талбайн нотолгоо
- pXRF multi-element response
Эдгээр 4 хүчин зүйл нэг дор давхцаж байвал target-ийн ач холбогдол өснө. Харин зөвхөн ганц өндөр pXRF reading, эсвэл зөвхөн өнгөний anomaly байвал лабораторийн баталгаажуулалтгүйгээр эцсийн шийдвэр гаргахгүй.
