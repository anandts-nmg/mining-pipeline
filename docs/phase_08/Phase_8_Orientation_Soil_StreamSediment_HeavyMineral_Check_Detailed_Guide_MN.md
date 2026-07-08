<!-- source: Phase_8_Orientation_Soil_StreamSediment_HeavyMineral_Check_Detailed_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

08. Phase 8 – Orientation Soil, Stream Sediment and Heavy Mineral Check
Дэлгэрэнгүй ажлын заавар

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Systematic grid өмнө soil/drainage response аргачлал баталгаажуулах. |
| Input files | Direct raw input files: №47 Heavy Mineral Sampling Results Map, №48 Heavy Mineral legend, №49 Stream Sediment legend, №50 Stream Sediment Polyelement map, №51 field route notebook, №52 field observation table; support inputs №9-22 DEM/drainage, №53-56 geology, №60 occurrence map, №63-64 prospectivity/source materials, №68 mineralized point table. |
| Software / equipment | Soil auger/shovel/sieve, GPS, pXRF, lab submission workflow. |

# 1. Ажлын зорилго
Энэ үе шатны үндсэн зорилго нь тухайн хайгуулын талбайд хөрсний геохими, голын хурдас, шлих буюу heavy mineral-ийн анхны шалгалт хийж, ямар төрлийн дээжлэлт хамгийн үр дүнтэй ажиллахыг тогтоох юм.
Өөрөөр хэлбэл, шууд бүх талбайд системтэй торон дээжлэлт хийхээс өмнө аль гүнээс дээж авах вэ, ямар mesh хэмжээ ашиглах вэ, ямар орчинд аномаль илүү тод илрэх вэ, хөрсний B/C horizon тохиромжтой юу, эсвэл transported material их байна уу, голын хурдасны дээжлэлт upstream эх үүсвэрийг зааж чадах уу гэдгийг туршилтаар баталгаажуулна.
Энэхүү ажлын үр дүнгээр дараагийн системтэй хөрсний геохимийн тор, голын хурдасны follow-up, heavy mineral follow-up ажлын төлөвлөгөө гарна.
# 2. Ашиглах үндсэн input материал
Ажил эхлэхээс өмнө дараах материалуудыг нэг дор цуглуулж, QGIS project дотор давхарга болгон оруулсан байна.

| Input материал | Ашиглах зорилго |
| --- | --- |
| №47 Heavy Mineral Sampling Results Map | Heavy mineral буюу шлихийн дээжийн өмнөх үр дүнг шалгана. |
| №48 Heavy Mineral Legend | Heavy mineral зураг дээрх тэмдэглэгээ, элемент, эрдсийн тайлбарыг уншина. |
| №49 Stream Sediment Legend | Голын хурдасны зураг дээрх тэмдэглэгээг тайлбарлахад ашиглана. |
| №50 Stream Sediment Polyelement Map | Олон элементийн аномаль бүсүүдийг тодорхойлно. |
| №51 Field Route Notebook | Өмнөх маршрутын ажиглалт, дээжлэлтийн байршил, геологийн тэмдэглэлийг шалгана. |
| №52 Field Observation Table | Илэрц, чулуулаг, хувирал, хүдэржилт, структурын тэмдэглэлүүдийг ашиглана. |
| №9–22 DEM / Drainage data | Ус зайлуулах систем, голдрил, watershed/catchment, upstream–downstream чиглэлийг тодорхойлно. |
| №53–56 Geological maps | Чулуулаг, нас, контакт, хагарал, интрузив, вулканит, тунамал нэгжүүдийг ялгана. |
| №60 Occurrence map | Ашигт малтмалын илрэлүүд, хуучин дээж, минералжсан цэгүүдийг шалгана. |
| №63–64 Prospectivity / source materials | Өмнөх үе шатанд ялгасан боломжит зорилтот талбай, эх үүсвэрийн таамаглалыг ашиглана. |

# 3. Шаардлагатай программ, багаж хэрэгсэл
## 3.1 Оффисын программ
- QGIS
- Google Earth / KML viewer
- Excel
- PDF map viewer
- Coordinate conversion tool
- GIS attribute table editor
- DEM / drainage analysis plugin
- Lab result comparison template
## 3.2 Талбайн багаж
- GPS эсвэл QField суулгасан гар утас / tablet
- Soil auger
- Хүрз
- Дээжний уут
- Дээжний шошго
- Permanent marker
- Sieve буюу шигшүүр
- pXRF
- Гар линз
- Соронз
- Ус үл нэвтрэх field notebook
- Sample tag
- Камер
- Safety equipment
## 3.3 Лабораторийн хэрэгцээ
- Soil sample submission form
- Stream sediment submission form
- Heavy mineral sample submission form
- Chain of custody form
- Lab assay method request sheet
- QA/QC sample insertion list
# 4. Folder structure үүсгэх заавар
Ажил эхлэхээс өмнө дараах фолдерын бүтцийг заавал үүсгэнэ.
08_Phase_8_Orientation_Soil_StreamSediment_and_HeavyMineral_Check/
├── 01_Orientation_Line_Design
├── 02_Depth_Horizon_Mesh_Test
├── 03_pXRF_Lab_Comparison
├── 04_StreamSediment_FollowUp
├── 05_HeavyMineral_FollowUp
└── 06_Recommended_Systematic_Method

| Фолдер | Зориулалт | Жишээ файл |
| --- | --- | --- |
| 01_Orientation_Line_Design | Orientation soil survey хийх шугам, цэг, profile, traverse, target zone-ийн зураг, координат, shapefile, PDF map хадгална. | XV-023222_Buduunkhad_Orientation_Line_Design.qgz XV-023222_Buduunkhad_Orientation_Line_Design.pdf XV-023222_Buduunkhad_Orientation_Soil_Sample_Points.gpkg |
| 02_Depth_Horizon_Mesh_Test | Хөрсний гүн, horizon, mesh size, spacing туршилтын бүх мэдээллийг хадгална. | Depth_Test_20cm_40cm_60cm.xlsx Soil_Horizon_A_B_C_Residual_Transported_Log.xlsx Mesh_Test_Results.xlsx |
| 03_pXRF_Lab_Comparison | pXRF хэмжилт болон лабораторийн шинжилгээний харьцуулалтыг хадгална. | pXRF_Field_Readings.xlsx Lab_Assay_Results.xlsx pXRF_vs_Lab_Comparison.xlsx QAQC_Check_Log.xlsx |
| 04_StreamSediment_FollowUp | Голын хурдасны follow-up цэг, catchment analysis, upstream source direction, drainage anomaly interpretation хадгална. | StreamSediment_Anomaly_Catchment_Map.pdf StreamSediment_FollowUp_Sample_Points.gpkg StreamSediment_FollowUp_Plan.pdf |
| 05_HeavyMineral_FollowUp | Heavy mineral буюу шлихийн дээжлэлтийн өмнөх үр дүн, follow-up цэг, дээжлэлтийн төлөвлөгөө хадгална. | HeavyMineral_Anomaly_Review.xlsx HeavyMineral_FollowUp_Targets.pdf HeavyMineral_FollowUp_Sample_Points.gpkg |
| 06_Recommended_Systematic_Method | Orientation survey-ийн дүгнэлт, дараагийн системтэй дээжлэлтийн санал болгож буй аргачлал хадгална. | Recommended_Systematic_Soil_Method.pdf Recommended_Soil_Grid_Spacing.xlsx Final_Phase8_Decision_Gate_Report.docx |

# 5. Ажил эхлэхийн өмнөх бэлтгэл
## 5.1 Бүх input map-уудыг QGIS-д оруулах
Бүх layer-ийн coordinate reference system нэг байх ёстой. Монголын ихэнх хайгуулын талбайд UTM zone тохирох тул тухайн талбайн байршлаас хамаарч UTM Zone 47N, 48N эсвэл бусад тохирох EPSG ашиглана.
- License boundary
- DEM
- Hillshade
- Drainage network
- Stream sediment polyelement map
- Heavy mineral sampling result map
- Geological map
- Fault / structure layer
- Occurrence map
- Previous field route
- Field observation points
- Prospectivity map
## 5.2 Input map-уудыг давхарлаж шалгах
- Stream sediment anomaly нь ямар drainage дээр байна вэ?
- Heavy mineral anomaly нь ямар голдрилтой холбоотой вэ?
- Аномаль цэгийн upstream талд ямар чулуулаг байна вэ?
- Аномаль нь intrusive contact, fault, alteration zone, occurrence-тэй давхцаж байна уу?
- Геологийн зураг дээр аномаль орчимд ямар lithology давамгайлж байна вэ?
- Хөрсний дээжлэлт хийх боломжтой residual soil байна уу?
- Transported cover буюу зөөгдмөл хучаас их байна уу?
- Хэт их аллювийн нөлөөтэй бүс эсэхийг DEM болон satellite image-аар шалгана.
# 6. Orientation soil survey хийх нарийвчилсан заавар
## 6.1 Orientation soil survey-ийн зорилго
Orientation soil survey нь системтэй хөрсний геохими эхлэхээс өмнө тухайн талбайд хөрсний дээжлэлтийн хамгийн тохиромжтой нөхцөлийг тогтоох туршилтын ажил юм.
- Аль horizon хамгийн сайн геохимийн response өгч байна вэ?
- 20 см, 40 см, 60–80 см гүнээс аль нь илүү тогтвортой үр дүнтэй байна вэ?
- B horizon эсвэл C horizon аль нь илүү тохиромжтой вэ?
- Residual soil болон transported soil-ийг яаж ялгах вэ?
- Ямар mesh size элементүүдийн response-д илүү тохиромжтой вэ?
- pXRF болон лабораторийн үр дүн хоорондоо хэр зэрэг нийцэж байна вэ?
- Аномаль нь геологийн source-тэй логик холбоотой байна уу?
## 6.2 Orientation line сонгох арга
Orientation line-ийг санамсаргүй сонгохгүй. Шугам нь stream sediment, heavy mineral, occurrence, alteration, structure, prospectivity anomaly-г хөндлөн огтолж байх ёстой.
- Аномаль төв хэсэг, аномаль зах хэсэг, background буюу хэвийн бүсийг хамруулна.
- Геологийн контакт, хагарал, ус зайлуулах голдрилын эх хэсгийг огтлуулна.
- Intrusive, volcanic, sedimentary, contact zone, alteration zone, fault zone, drainage-influenced area, residual soil area, transported cover area зэрэг ялгаатай орчныг хамруулна.
- Orientation line-ийг geological trend-тэй параллель биш, харин ихэвчлэн хөндлөн чиглэлд авна. Жишээ нь хагарал NE–SW чиглэлтэй бол orientation line-ийг NW–SE чиглэлд авах нь тохиромжтой.
## 6.3 Orientation soil sample spacing
Эхний туршилтад дараах spacing ашиглаж болно. Эхний шатанд 50 м spacing тохиромжтой. Харин аномаль бүс дээр 25 м болгон нарийсгаж болно.

| Туршилтын төрөл | Санал болгох spacing |
| --- | --- |
| Маш нарийвчилсан profile | 25 м |
| Стандарт orientation line | 50 м |
| Өргөн шалгалт | 100 м |
| Background check | 100–200 м |

# 7. Хөрсний гүн, horizon, mesh туршилт хийх заавар
## 7.1 Гүний туршилтын зорилго
Хөрсний геохимийн үр дүн гүнээс ихээхэн хамаардаг. Иймээс нэг цэг дээр олон гүнээс дээж авч харьцуулна. Санал болгох гүн: 20 см, 40 см, 60 см, 60–80 см.
## 7.2 Нэг цэг дээр гүний дээж авах арга
- GPS-ээр координатыг бичнэ.
- Газрын гадаргын зураг авна.
- Хөрсний profile ухна.
- 0–20 см, 20–40 см, 40–60 см, 60–80 см үеийг ялгана.
- Horizon тус бүрийн өнгө, ширхэглэл, чийг, шаварлаг байдал, карбонат, органик агууламжийг тэмдэглэнэ.
- A horizon органик ихтэй бол үндсэн геохимийн дээжинд ашиглахгүй.
- B horizon илүү тогтвортой байвал B horizon-оос дээж авахыг санал болгоно.
- C horizon weathered bedrock-т ойр бол илүү source-related response өгч магадгүй.
- Transported gravel, alluvium, colluvium давамгайлсан бол тусгай flag тавина.
## 7.3 Horizon ялгах заавар

| Төрөл | Ерөнхий шинж | Ашиглалт |
| --- | --- | --- |
| A horizon | Органик ихтэй, бор/хар хүрэн өнгөтэй, үндэс ихтэй, гадны нөлөө ихтэй. | Үндсэн системтэй хөрсний геохимид аль болох ашиглахгүй. |
| B horizon | Илүү тогтвортой, шаварлаг, төмрийн исэл, карбонат хуримтлагдсан байж болно. | Хэрэв талбайд тогтвортой үргэлжилж байвал үндсэн дээжлэлтийн horizon болгон сонгоно. |
| C horizon | Weathered parent rock буюу эх чулуулгийн задралтай ойр, чулуулаг/regolith ихтэй. | Хөрс нимгэн, B horizon сул хөгжсөн бол ашиглаж болно. |
| Residual soil | Доорх эх чулуулагтайгаа холбоотой, local geology-тэй нийцдэг. | Systematic soil survey-д хамгийн тохиромжтой. |
| Transported soil | Ус, салхи, налуугийн хөдөлгөөнөөр зөөгдсөн, эх чулуулгийг шууд төлөөлөхгүй. | Үндсэн хөрсний геохимид болгоомжтой ашиглана. Заавал flag тавина. |

## 7.4 Mesh size туршилт хийх заавар
Нэг дээжийг лабораторид өгөхөөс өмнө өөр өөр ширхэглэлийн фракцаар туршиж болно. Санал болгох mesh: -80 mesh, -120 mesh, -180 mesh. Зорилго нь Cu, Au, Ag, Pb, Zn, As, Sb, Mo зэрэг элементүүд аль фракц дээр илүү тод аномаль өгч байгааг шалгах юм.
- Нэг хөрсний дээжийг сайн хатаана.
- Том чулуу, ургамлын үлдэгдлийг авна.
- Дээжийг нэгэн жигд холино.
- 80 mesh фракцыг ялгана.
- Боломжтой бол -120 mesh болон -180 mesh фракцыг тусад нь ялгана.
- Фракц бүрээс pXRF уншилт хийнэ.
- Фракц бүрийг лабораторид тусад нь илгээж болно.
- Элемент тус бүрийн response-г харьцуулна.
- Аль mesh дээр аномаль/background ялгаа хамгийн сайн байгааг тогтооно.
# 8. pXRF болон лабораторийн харьцуулалт хийх заавар
## 8.1 pXRF-ийн зорилго
pXRF нь талбай дээр шуурхай element screening хийхэд ашиглагдана. Гэхдээ pXRF-ийн үр дүнг лабораторийн баталгаатай шинжилгээг орлох үндсэн assay гэж үзэхгүй.
- Аномаль цэгийг шуурхай ялгах
- Cu, Pb, Zn, As, Mo зэрэг элементүүдийн харьцангуй trend харах
- Дээжлэлтийн гүн, horizon, mesh response харьцуулах
- Follow-up цэгийг талбай дээр урьдчилан сонгох
## 8.2 pXRF хэмжилтийн стандарт арга
- Дээжийг аль болох хатаана.
- Чулуу, органик үлдэгдлийг авна.
- Дээжийг нэгэн жигд холино.
- Сорьцыг sample cup эсвэл XRF bag-д хийнэ.
- Нэг дээж дээр хамгийн багадаа 2–3 удаа уншилт хийнэ.
- Уншилтын хугацаа, method, mode, calibration, operator-ийг бичнэ.
- CRM буюу standard material ашиглавал бүртгэнэ.
- Blank sample хэмжсэн бол тэмдэглэнэ.
- Duplicate хэмжилт хийсэн бол харьцуулна.
- pXRF result-ийг lab result-тэй шууд нэг хүснэгтэд оруулна.
## 8.3 pXRF vs lab comparison

| Үзүүлэлт | Шалгах зүйл |
| --- | --- |
| Element trend | pXRF болон lab ижил trend үзүүлж байна уу |
| Absolute value | Утгууд ойролцоо байна уу |
| Detection limit | pXRF зарим элементийг найдвартай хэмжиж байна уу |
| Sample moisture | Чийг үр дүнд нөлөөлсөн үү |
| Matrix effect | Шавар, Fe, Mn, Si их байх нь нөлөөлсөн үү |
| Duplicate precision | Давтан хэмжилтийн зөрүү зөвшөөрөгдөх хэмжээнд үү |
| Lab method | ICP-MS, ICP-OES, fire assay зэрэг арга тохиромжтой юу |

## 8.4 pXRF-ийг хэрхэн ашиглаж болох тухай шийдвэр
pXRF болон лабораторийн үр дүн сайн correlation өгвөл pXRF-ийг field screening-д ашиглаж болно. Хэрэв correlation муу бол pXRF-ийг зөвхөн туслах мэдээлэл гэж үзнэ. Албан ёсны interpretation-д lab assay-г үндсэн өгөгдөл болгоно.
# 9. Stream sediment follow-up хийх заавар
## 9.1 Зорилго
Stream sediment follow-up-ийн зорилго нь өмнөх stream sediment anomaly-ийн эх үүсвэрийг upstream чиглэлд нарийвчлан хөөж тогтоох юм.
## 9.2 Drainage catchment analysis хийх
- Аномаль stream sediment sample point-ийг тэмдэглэнэ.
- Тухайн цэгийн upstream catchment-ийг тодорхойлно.
- Голдрилын салаануудыг ялгана.
- Аль салаа хамгийн их боломжит source area-тэй давхцаж байгааг шалгана.
- Upstream талд occurrence, fault, contact, alteration, intrusive body байгаа эсэхийг шалгана.
- Дараагийн дээж авах цэгүүдийг салаа бүр дээр төлөвлөнө.
## 9.3 Follow-up sample point сонгох
- Аномаль sample point-оос дээш upstream талд
- Салаа нийлдэг confluence дээр
- Салаа тус бүрийн эхэнд
- Хагаралтай огтлолцох drainage хэсэгт
- Alteration zone-оос урсаж гарч буй жижиг сайрт
- Occurrence-ийн доод талын drainage-д
- Background comparison хийх ойролцоо цэвэр drainage-д
## 9.4 Stream sediment дээж авах арга
- GPS дээр sample point үүсгэнэ.
- Голдрилын идэвхтэй sediment хуримтлагдах хэсгийг сонгоно.
- Том чулуу, органик материал, ургамлын үлдэгдлийг авна.
- Fine sediment буюу шаварлаг, элсэрхэг фракцыг авна.
- Нэг цэгээс 5–10 жижиг sub-sample авч composite болгоно.
- Дээжийг уутанд хийж sample ID бичнэ.
- Усны урсгалын чиглэл, голдрилын өргөн, sediment type, lithology, upstream geology-г тэмдэглэнэ.
- Фото зураг авна.
- Хэрэв human contamination байвал тэмдэглэнэ.
- Дээжийг лабораторид илгээхэд chain of custody бөглөнө.
# 10. Heavy mineral follow-up хийх заавар
## 10.1 Зорилго
Heavy mineral follow-up-ийн зорилго нь өмнөх шлихийн аномальд илэрсэн хүнд эрдсийн эх үүсвэрийг тодорхойлох юм.
- Magnetite
- Ilmenite
- Chromite
- Scheelite
- Cassiterite
- Garnet
- Zircon
- Monazite
- Gold
- Sulphide grains
- Oxide minerals
## 10.2 Heavy mineral sample авах тохиромжтой орчин
- Голдрилын bend буюу мурийлт
- Bedrock trap
- Том чулууны ар талын хуримтлал
- Natural riffle zone
- Хар элс хуримтлагдсан хэсэг
- Confluence-ийн доод тал
- Slope wash хуримтлагдсан жижиг сайр
- Fault-controlled drainage
## 10.3 Heavy mineral дээж авах алхам
- GPS координатыг бүртгэнэ.
- Дээж авах газрыг зураг авна.
- Голдрилын heavy mineral trap хэсгийг сонгоно.
- 5–10 кг материал авна.
- Том чулуу, органик үлдэгдлийг авна.
- Боломжтой бол талбай дээр panning хийж хар элс баяжуулна.
- Magnet ашиглан magnetic fraction шалгана.
- Visible sulphide, gold color, scheelite fluorescence зэрэг шинж тэмдэг тэмдэглэнэ.
- Дээжний ID, жин, орчин, sediment type, upstream geology-г бичнэ.
- Дээжийг лабораторид илгээж mineralogical analysis эсвэл geochemical assay хийлгэнэ.
# 11. Field data бүртгэх заавар
Талбай дээрх бүх дээж болон ажиглалтыг нэг стандарт form-д бүртгэнэ.
## 11.1 Soil sample бүртгэл

| Талбар | Бөглөх мэдээлэл |
| --- | --- |
| Sample ID | Жишээ: BK-OS-001 |
| Date | Дээж авсан огноо |
| Team | Дээж авсан баг |
| Easting / Northing | UTM координат |
| Elevation | GPS elevation |
| Sample type | Soil |
| Depth | 20 см, 40 см, 60 см гэх мэт |
| Horizon | A, B, C |
| Residual / transported | Аль болох тодорхой бичнэ |
| Soil colour | Munsell эсвэл энгийн өнгө |
| Grain size | Clay, silt, sand, gravel |
| Carbonate | Yes / No |
| Moisture | Dry / moist / wet |
| pXRF reading | Field value |
| Lab submission | Yes / No |
| Photo ID | Зургийн дугаар |
| Comment | Нэмэлт тэмдэглэл |

## 11.2 Stream sediment бүртгэл

| Талбар | Бөглөх мэдээлэл |
| --- | --- |
| Sample ID | BK-SS-001 |
| Date | Огноо |
| Easting / Northing | UTM координат |
| Drainage order | 1st, 2nd, 3rd order |
| Active / dry channel | Идэвхтэй эсвэл хуурай сайр |
| Sediment type | Sand, silt, clay, gravel |
| Composite method | Хэдэн sub-sample авсан |
| Upstream lithology | Геологийн зурагтай тулгаж бичнэ |
| Contamination | Road, camp, livestock, mining гэх мэт |
| Lab submission | Yes / No |
| Photo ID | Зураг |
| Comment | Тайлбар |

## 11.3 Heavy mineral бүртгэл

| Талбар | Бөглөх мэдээлэл |
| --- | --- |
| Sample ID | BK-HM-001 |
| Date | Огноо |
| Easting / Northing | UTM координат |
| Trap type | Bend, riffle, bedrock trap гэх мэт |
| Raw sample weight | кг |
| Concentrate weight | гр |
| Magnetic fraction | High / medium / low |
| Visible minerals | Magnetite, sulphide, gold color гэх мэт |
| Upstream geology | Геологийн эх үүсвэр |
| Lab submission | Yes / No |
| Photo ID | Зураг |
| Comment | Нэмэлт тайлбар |

# 12. QA/QC шалгалт
QA/QC нь дээжлэлтийн үр дүн найдвартай эсэхийг шалгах систем юм. Phase 8 дээр дараах зүйлсийг заавал шалгана.
- Depth / horizon / mesh comparison complete
- Transported vs residual flag
- pXRF-lab comparison done
- Drainage source logic documented

| QA/QC item | Acceptance note |
| --- | --- |
| Depth / horizon / mesh comparison complete | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Transported vs residual flag | Recorded in phase QA/QC log; reviewer/date/decision required. |
| pXRF-lab comparison done | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Drainage source logic documented | Recorded in phase QA/QC log; reviewer/date/decision required. |

## 12.2 QA/QC item тус бүрийн заавар
### Depth / horizon / mesh comparison complete
- 20 см, 40 см, 60–80 см гүний дээж авсан эсэх
- Horizon бүрийн тэмдэглэл байгаа эсэх
- Mesh size бүрийн үр дүн харьцуулсан эсэх
- Хамгийн сайн response өгсөн depth/horizon/mesh тодорхойлогдсон эсэх
Acceptance note: Recorded in Phase QA/QC log; reviewer/date/decision required.
### Transported vs residual flag
- Бүх soil sample дээр residual эсвэл transported flag тавьсан эсэх
- Alluvium, colluvium, slope wash нөлөөтэй цэгийг ялгасан эсэх
- Interpretation хийхдээ transported sample-ийг тусад нь тэмдэглэсэн эсэх
Acceptance note: Recorded in Phase QA/QC log; reviewer/date/decision required.
### pXRF-lab comparison done
- pXRF уншилт бүртгэгдсэн эсэх
- Лабораторийн үр дүнтэй харьцуулсан эсэх
- Correlation chart гаргасан эсэх
- pXRF-ийг field screening-д ашиглаж болох эсэх шийдвэр гарсан эсэх
Acceptance note: Recorded in Phase QA/QC log; reviewer/date/decision required.
### Drainage source logic documented
- Stream sediment anomaly-ийн upstream catchment тодорхойлогдсон эсэх
- Heavy mineral anomaly-ийн эх үүсвэрийн таамаглал гарсан эсэх
- Follow-up point-ууд логик үндэслэлтэй эсэх
- Geological map болон occurrence map-тай тулгасан эсэх
Acceptance note: Recorded in Phase QA/QC log; reviewer/date/decision required.
# 13. Data processing хийх заавар
## 13.1 Soil data processing
- Field sample register-ийг Excel-д оруулна.
- Координатыг шалгана.
- Duplicate Sample ID байгаа эсэхийг шалгана.
- Depth, horizon, residual/transported flag бөглөгдсөн эсэхийг шалгана.
- pXRF болон lab result-ийг sample ID-аар холбож нэгтгэнэ.
- Element бүрийн статистик гаргана.
- Background, threshold, anomaly value тодорхойлно.
- Гүн тус бүрийн response-г харьцуулна.
- Horizon тус бүрийн response-г харьцуулна.
- Mesh тус бүрийн response-г харьцуулна.
- Хамгийн сайн response өгч буй аргачлалыг сонгоно.
- QGIS дээр anomaly map гаргана.
## 13.2 Stream sediment data processing
- Stream sediment sample register-ийг нэгтгэнэ.
- Lab result-ийг sample ID-аар холбоно.
- Element бүрийн anomaly threshold тогтооно.
- Sample point-ийг drainage layer дээр давхарлана.
- Upstream catchment polygon гаргана.
- Аномаль sample бүрийн эх үүсвэрийн боломжит талбайг тодорхойлно.
- Geological map, fault, occurrence, alteration map-тай давхарлана.
- Follow-up sample point төлөвлөнө.
- StreamSediment_FollowUp_Plan.pdf гаргана.
## 13.3 Heavy mineral data processing
- Heavy mineral result map болон table-ийг нэгтгэнэ.
- Хүнд эрдсийн төрөл тус бүрийн байршлыг QGIS-д оруулна.
- Drainage direction-тай харьцуулна.
- Upstream lithology болон structure-тай тулгана.
- Mineral assemblage-ийг ордын төрөлтэй холбон тайлбарлана.
- Follow-up цэгүүдийг төлөвлөнө.
- HeavyMineral_FollowUp_Plan.pdf гаргана.
# 14. Interpretation хийх заавар
## 14.1 Soil orientation interpretation
- B horizon хамгийн сайн response өгч байна уу?
- C horizon илүү source-related response өгч байна уу?
- 20 см-ийн дээж органик нөлөөтэй байна уу?
- 60–80 см-ийн дээж илүү тогтвортой юу?
- Residual soil дээр anomaly тод байна уу?
- Transported soil дээр anomaly шилжсэн, сарнисан байна уу?
- Mesh size өөрчлөхөд element contrast сайжирч байна уу?
- Cu, Au, As, Mo, Pb, Zn зэрэг pathfinder element-үүд нэг чиглэлд давхцаж байна уу?
## 14.2 Stream sediment interpretation
- Аномаль sample-ийн upstream талд ямар чулуулаг байна вэ?
- Аномаль зөвхөн нэг салаанаас ирж байна уу, эсвэл олон салаанд тархсан уу?
- Аномаль fault/contact дагаж байна уу?
- Аномаль occurrence map-тай давхцаж байна уу?
- Голын хурдасны аномаль downstream dispersion уу?
- Source талбай нь soil grid хийх боломжтой юу?
## 14.3 Heavy mineral interpretation
- Хүнд эрдсийн assemblage ямар deposit type зааж байна вэ?
- Magnetite + chalcopyrite байвал skarn / IOCG / mafic-ultramafic possibility шалгана.
- Scheelite байвал W-skarn / greisen possibility шалгана.
- Cassiterite байвал Sn-related granite system шалгана.
- Visible gold / sulphide grains байвал Au-bearing vein / epithermal / orogenic possibility шалгана.
- Chromite байвал ultramafic source шалгана.
- Zircon / monazite давамгайлбал heavy mineral background эсвэл felsic source байж болно.
# 15. Output файл бэлтгэх заавар
## 15.1 Заавал гаргах output

| Output файл | Агуулга |
| --- | --- |
| XV-023222_Buduunkhad_Orientation_Soil_Survey_Plan.pdf | Orientation soil survey-ийн шугам, дээжийн цэг, гүн, horizon, spacing, mesh test төлөвлөгөөтэй зураг. |
| XV-023222_Buduunkhad_Orientation_Soil_Sample_Register.xlsx | Бүх хөрсний дээжийн бүртгэл. |
| XV-023222_Buduunkhad_Orientation_Soil_pXRF_Lab_Comparison.xlsx | pXRF болон lab assay харьцуулалт. |
| XV-023222_Buduunkhad_StreamSediment_FollowUp_Plan.pdf | Stream sediment anomaly-ийн follow-up цэгүүд болон upstream catchment analysis. |
| XV-023222_Buduunkhad_HeavyMineral_FollowUp_Plan.pdf | Heavy mineral anomaly-ийн follow-up цэгүүд болон эх үүсвэрийн тайлбар. |

## 15.2 Нэмэлт гаргах output
- XV-023222_Buduunkhad_Phase8_QAQC_Log.xlsx
- XV-023222_Buduunkhad_Recommended_Systematic_Soil_Method.pdf
- XV-023222_Buduunkhad_Recommended_Soil_Grid_Spacing.xlsx
- XV-023222_Buduunkhad_StreamSediment_Catchment_Analysis.gpkg
- XV-023222_Buduunkhad_HeavyMineral_Target_Ranking.xlsx
# 16. Decision gate / next phase condition
## 16.1 Soil survey decision
- Аль horizon-оос дээж авах вэ?
- Ямар гүнээс дээж авах вэ?
- Ямар mesh size ашиглах вэ?
- Ямар spacing ашиглах вэ?
- Residual soil болон transported soil-ийг яаж ялгаж flag тавих вэ?
- pXRF-ийг талбайн screening-д ашиглаж болох эсэх
- Lab assay ямар element suite болон ямар method-оор хийх вэ?
## 16.2 Stream sediment decision
- Аль аномаль drainage follow-up шаардлагатай вэ?
- Upstream source area хаана байна вэ?
- Аль салаа гол target болох вэ?
- Soil grid тавих боломжтой upstream catchment байна уу?
- Дараагийн дээж авах цэгүүд баталгаажсан уу?
## 16.3 Heavy mineral decision
- Heavy mineral anomaly ямар эрдсээр тодорхойлогдож байна вэ?
- Эх үүсвэр нь ямар lithology / structure / alteration-тэй холбоотой вэ?
- Follow-up дээж авах шаардлагатай цэгүүд хаана байна вэ?
- Deposit model-ийн ямар төрлийг шалгах хэрэгтэй вэ?
# 17. Ажлын дараалал
- Input data цуглуулах: Бүх input map, table, DEM, field observation, occurrence, prospectivity материалыг нэг folder-т хуулна.
- QGIS project үүсгэх: License boundary, geology, drainage, DEM, stream sediment, heavy mineral, occurrence, prospectivity layer-үүдийг оруулна.
- Аномаль бүсүүдийг ялгах: Stream sediment болон heavy mineral map дээрх өндөр утгатай цэгүүдийг ялгаж, geological map-тай тулгана.
- Orientation line төлөвлөх: Аномаль төв, аномаль зах, background, lithological contact, fault zone-ийг огтолсон orientation line зурна.
- Soil depth/horizon/mesh test төлөвлөх: Нэг цэг дээр олон гүн, олон horizon, олон mesh size турших төлөвлөгөө гаргана.
- Талбайн дээжлэлт хийх: Soil, stream sediment, heavy mineral sample-уудыг стандарт бүртгэлтэй авна.
- pXRF хэмжилт хийх: Хатаасан, шигшсэн дээж бүр дээр pXRF уншилт хийж бүртгэнэ.
- Лабораторид илгээх: Sample submission form, chain of custody, QA/QC sample list-ийг бүрэн бөглөж лабораторид илгээнэ.
- Lab result нэгтгэх: pXRF болон lab result-ийг sample ID-аар нэг хүснэгтэд нэгтгэнэ.
- Харьцуулалт хийх: Depth, horizon, mesh, residual/transported, pXRF/lab correlation, drainage source logic-ийг шалгана.
- Follow-up plan гаргах: Stream sediment болон heavy mineral аномаль бүрийн upstream follow-up цэгүүдийг төлөвлөнө.
- Recommended systematic method гаргах: Системтэй хөрсний дээжлэлтийн дараагийн аргачлалыг баталгаажуулна.
# 18. Эцсийн шалгах checklist

| № | Шалгах зүйл | Төлөв |
| --- | --- | --- |
| 1 | Бүх input map QGIS-д орсон | ☐ |
| 2 | DEM/drainage analysis хийсэн | ☐ |
| 3 | Stream sediment anomaly ялгасан | ☐ |
| 4 | Heavy mineral anomaly ялгасан | ☐ |
| 5 | Orientation line зурсан | ☐ |
| 6 | Soil sample point төлөвлөсөн | ☐ |
| 7 | Depth test төлөвлөсөн | ☐ |
| 8 | Horizon test төлөвлөсөн | ☐ |
| 9 | Mesh test төлөвлөсөн | ☐ |
| 10 | pXRF хэмжилтийн form бэлдсэн | ☐ |
| 11 | Lab submission form бэлдсэн | ☐ |
| 12 | QA/QC log үүсгэсэн | ☐ |
| 13 | Stream sediment follow-up point гаргасан | ☐ |
| 14 | Heavy mineral follow-up point гаргасан | ☐ |
| 15 | Recommended systematic method гаргасан | ☐ |

# 19. Phase 8-ийн гол дүгнэлт
Энэ үе шатны хамгийн чухал үр дүн бол системтэй хөрсний дээжлэлтийг шууд эхлүүлэхээс өмнө дээж авах арга, гүн, horizon, mesh, spacing, pXRF хэрэглээ, drainage source logic-ийг баталгаажуулах явдал юм.
Phase 8 амжилттай дууссаны дараа дараагийн phase-д ямар гүнээс хөрсний дээж авах, ямар horizon ашиглах, ямар mesh size сонгох, ямар grid spacing хэрэглэх, аль stream sediment аномаль дээр follow-up хийх, аль heavy mineral аномаль source area-д илүү анхаарах, pXRF-ийг хэрхэн field screening-д ашиглах гэдэг нь тодорхой болсон байна.
