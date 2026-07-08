<!-- source: BH_Preliminary_Prospect_Candidate_Areas_Report_v01.docx (converted from Word; canonical form for LLM ingestion) -->

БУДУУНХАД ТАЛБАЙН EVIDENCE ДАВХЦЛЫН ШИНЖИЛГЭЭНИЙ ТАЙЛАН
Preliminary Prospect Candidate Area Selection Report

Талбай: XV-023222 Buduunkhad / BH
Координатын систем: WGS 84 / UTM Zone 47N (EPSG:32647)
Огноо: 2026-06-10
Хувилбар: v01

Зураг 1. Preliminary prospect candidate area-уудын overview map

# 1. Хураангуй
Энэхүү тайланд Будуунхад талбайд бэлтгэсэн геохими, структур, ASTER alteration, DEM terrain, known occurrence, mineralized point, lithology болон access evidence layer-үүдийг QGIS орчинд давхцуулан шинжилж, эхний шатны хайгуулын зорилтот бүс буюу preliminary prospect candidate area-уудыг тодорхойлсон үр дүнг нэгтгэв. 250 м grid evidence scoring арга ашиглан score >=90 хэсгүүдийг нэгтгэж 6 candidate area ялгасан.
- Нийт сонгосон candidate area: 6
- Хамгийн өндөр ач холбогдолтой бүс: PCA-01, талбай 450.00 га, max score 100
- Дараагийн шатны шалгалтын санал болгож буй дараалал: PCA-01 -> PCA-03 -> PCA-04/PCA-05 -> PCA-02/PCA-06
# 2. Ашигласан мэдээлэл
- Геохимийн anomaly polygon: Anomaly_geochem_pan.gpkg
- Геологийн structure: Faults_digitized_BH.gpkg, Dykes_digitized_BH.gpkg, BH_Lithology_digitized.gpkg
- Known occurrence ба mineralized point: Min_occurences_BH.gpkg, Min_pnts_BH.gpkg
- ASTER alteration: Advanced_argillic_Aster.gpkg, Ch_Ep_halo_Aster.gpkg, Porphyry_alteration_Aster.gpkg, Alteration_digitized.gpkg
- DEM terrain: DEM_BH.tif / ALOS-PALSAR DEM 12.5 m
- Remote sensing болон lithology composite raster: idx_argilic_str.tif, lithology_composite_mix_hsi_ilwis.tif, r_fused.tif
- Access: Road_BH.gpkg
- License boundary: BH_license.gpkg
# 3. Аргачлал
Evidence давхцлын үнэлгээг дараах логикоор хийсэн. 250 м хэмжээтэй grid үүсгэн, grid бүр дээр тухайн evidence-ийн оролцоо болон ойролцоо зайг шалгаж оноо өгсөн. Эцэст нь өндөр оноотой grid-үүдийг dissolve/cluster хийж candidate area болгон нэгтгэсэн.

| Evidence шалгуур | Үнэлсэн агуулга |
| --- | --- |
| Геохимийн anomaly | Grid нь anomaly polygon дотор байрлах эсэх. |
| Structure/contact | Fault, dyke, lithological contact zone-той давхцах эсвэл ойр байрлах эсэх. |
| Known occurrence | Known occurrence-оос 750 м дотор эсэх. |
| ASTER alteration | Advanced argillic, chlorite-epidote halo, porphyry alteration, hand-digitized alteration-той давхцах эсэх. |
| DEM structural terrain | Налуу, хөндий/хярын чиглэл, fault/contact-той нийцэх terrain pattern байгаа эсэх. |
| Remote sensing lineament | Dyke/lineament болон geological structure-ийн давхцал байгаа эсэх. |
| Stream/heavy mineral context | Drainage basin дотор эерэг geochemical/heavy mineral indicator байгаа эсэх. |
| Field observation/mineralized point | Mineralized point, alteration, vein, gossan, quartz zone тэмдэглэл ойр эсэх. |
| Deposit model setting | Intrusive-volcanic, granodiorite/quartz diorite/granite/diorite орчин зэрэг Au-Cu-Mo-Pb-Sn context-той нийцэх эсэх. |
| Access | Road layer-ээс 1.5 км дотор эсэх; safety condition-г road/access proxy байдлаар урьдчилан үнэлсэн. |

# 4. Candidate area-уудын нэгтгэл

| Rank | Candidate | Area ha | Max score | Mean score | Elements | Anomaly polygons | Key interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PCA-01 | 450.0 | 100 | 97.1 | Au,Ba,Cu,Mo,Pb,Py | GAP-4186-001,GAP-4186-002,GAP-4186-004,GAP-4186-005,GAP-4186-006,GAP-4186-007,GAP-4186-011,GAP-7255-010 | Au-Cu-Mo-Py structural/alteration target; Pb context |
| 2 | PCA-02 | 6.25 | 93 | 93.0 | Ba,Cu,Py,Sn | GAP-4186-001,GAP-4186-002,GAP-4186-004,GAP-4186-005,GAP-7255-008 | Au-Cu-Mo-Py structural/alteration target; Sn-bearing HM context |
| 3 | PCA-03 | 81.25 | 90 | 90.0 | Ba,Co,Cu,Mo,Py,Sn | GAP-4186-001,GAP-4186-002,GAP-4186-003,GAP-4186-004,GAP-4186-005,GAP-7255-008,GAP-7255-009 | Au-Cu-Mo-Py structural/alteration target; Sn-bearing HM context |
| 4 | PCA-04 | 35.7 | 90 | 90.0 | Co,Cu,Mo | GAP-4186-003,GAP-4186-004,GAP-4186-005,GAP-7255-009 | Au-Cu-Mo-Py structural/alteration target |
| 5 | PCA-05 | 35.17 | 90 | 90.0 | Ba,Cu,Py,Sn | GAP-4186-001,GAP-4186-002,GAP-4186-004,GAP-4186-005,GAP-7255-008 | Au-Cu-Mo-Py structural/alteration target; Sn-bearing HM context |
| 6 | PCA-06 | 6.25 | 90 | 90.0 | Ba,Co,Cu | GAP-4186-001,GAP-4186-004,GAP-4186-005,GAP-7255-009 | Au-Cu-Mo-Py structural/alteration target |

# 5. Candidate area тус бүрийн тайлбар
## 5.1 PCA-01 - Rank 1
Талбай: 450.0 га; Max score: 100; Mean score: 97.1; Төв координат: E 321511.0, N 5092567.1.
- Гол element/anomaly: Au,Ba,Cu,Mo,Pb,Py.
- Anomaly polygon: GAP-4186-001,GAP-4186-002,GAP-4186-004,GAP-4186-005,GAP-4186-006,GAP-4186-007,GAP-4186-011,GAP-7255-010.
- Known occurrence context: Алтны илрэл; Алтны илрэл
- Mineralized point context: 80.0
- Structure/access: fault 0.0 м, dyke 0.0 м, road 0.0 м.
- Lithology context: γδ₂Ɛ₂₋₃t - Phase II: granodiorite, quartz diorite; γ₃Ɛ₂₋₃t - Phase III: biotite granite, plagiogranite, leucogranite; νδ₁Ɛ₂₋₃t - Phase I: gabbro, gabbrodiorite, diorite
- Тайлбар: Au-Cu-Mo-Py structural/alteration target; Pb context.
- Follow-up: First-pass field traverse; verify fault/dyke/contact, alteration, quartz/vein/gossan; rock-chip + soil/stream sediment follow-up.
## 5.2 PCA-02 - Rank 2
Талбай: 6.25 га; Max score: 93; Mean score: 93.0; Төв координат: E 316570.0, N 5095560.1.
- Гол element/anomaly: Ba,Cu,Py,Sn.
- Anomaly polygon: GAP-4186-001,GAP-4186-002,GAP-4186-004,GAP-4186-005,GAP-7255-008.
- Known occurrence context: Зэс-алтны илрэл
- Mineralized point context: 18.0; 42.0
- Structure/access: fault 0.0 м, dyke 854.5 м, road 391.2 м.
- Lithology context: NP₃₋Ɛ₁us₁ - Andesite, basalt, andesibasalts, andesitic tuffs, tuffaceous felsic rocks, and finely laminated siltstone.; γδ₂Ɛ₂₋₃t - Phase II: granodiorite, quartz diorite
- Тайлбар: Au-Cu-Mo-Py structural/alteration target; Sn-bearing HM context.
- Follow-up: First-pass field traverse; verify fault/dyke/contact, alteration, quartz/vein/gossan; rock-chip + soil/stream sediment follow-up.
## 5.3 PCA-03 - Rank 3
Талбай: 81.25 га; Max score: 90; Mean score: 90.0; Төв координат: E 318473.8, N 5095137.1.
- Гол element/anomaly: Ba,Co,Cu,Mo,Py,Sn.
- Anomaly polygon: GAP-4186-001,GAP-4186-002,GAP-4186-003,GAP-4186-004,GAP-4186-005,GAP-7255-008,GAP-7255-009.
- Known occurrence context: 1 км дотор нэрлэсэн occurrence илрээгүй.
- Mineralized point context: 40.0; 81.0; 42.0
- Structure/access: fault 0.0 м, dyke 0.0 м, road 0.0 м.
- Lithology context: γ₃Ɛ₂₋₃t - Phase III: biotite granite, plagiogranite, leucogranite; νδ₁Ɛ₂₋₃t - Phase I: gabbro, gabbrodiorite, diorite; γδ₂Ɛ₂₋₃t - Phase II: granodiorite, quartz diorite
- Тайлбар: Au-Cu-Mo-Py structural/alteration target; Sn-bearing HM context.
- Follow-up: First-pass field traverse; verify fault/dyke/contact, alteration, quartz/vein/gossan; rock-chip + soil/stream sediment follow-up.
## 5.4 PCA-04 - Rank 4
Талбай: 35.7 га; Max score: 90; Mean score: 90.0; Төв координат: E 320671.7, N 5095266.5.
- Гол element/anomaly: Co,Cu,Mo.
- Anomaly polygon: GAP-4186-003,GAP-4186-004,GAP-4186-005,GAP-7255-009.
- Known occurrence context: 1 км дотор нэрлэсэн occurrence илрээгүй.
- Mineralized point context: 81.0; 41.0
- Structure/access: fault 0.0 м, dyke 0.0 м, road 0.0 м.
- Lithology context: γδ₂Ɛ₂₋₃t - Phase II: granodiorite, quartz diorite; γ₃Ɛ₂₋₃t - Phase III: biotite granite, plagiogranite, leucogranite
- Тайлбар: Au-Cu-Mo-Py structural/alteration target.
- Follow-up: First-pass field traverse; verify fault/dyke/contact, alteration, quartz/vein/gossan; rock-chip + soil/stream sediment follow-up.
## 5.5 PCA-05 - Rank 5
Талбай: 35.17 га; Max score: 90; Mean score: 90.0; Төв координат: E 317278.7, N 5094549.1.
- Гол element/anomaly: Ba,Cu,Py,Sn.
- Anomaly polygon: GAP-4186-001,GAP-4186-002,GAP-4186-004,GAP-4186-005,GAP-7255-008.
- Known occurrence context: 1 км дотор нэрлэсэн occurrence илрээгүй.
- Mineralized point context: 42.0
- Structure/access: fault 0.0 м, dyke 0.0 м, road 0.0 м.
- Lithology context: γδ₂Ɛ₂₋₃t - Phase II: granodiorite, quartz diorite; γ₃Ɛ₂₋₃t - Phase III: biotite granite, plagiogranite, leucogranite; Q₁₋₂ - deluvial–proluvial and proluvial origin gravels, sand, sandy loam, clay, and loam
- Тайлбар: Au-Cu-Mo-Py structural/alteration target; Sn-bearing HM context.
- Follow-up: First-pass field traverse; verify fault/dyke/contact, alteration, quartz/vein/gossan; rock-chip + soil/stream sediment follow-up.
## 5.6 PCA-06 - Rank 6
Талбай: 6.25 га; Max score: 90; Mean score: 90.0; Төв координат: E 320070.0, N 5095060.1.
- Гол element/anomaly: Ba,Co,Cu.
- Anomaly polygon: GAP-4186-001,GAP-4186-004,GAP-4186-005,GAP-7255-009.
- Known occurrence context: 1 км дотор нэрлэсэн occurrence илрээгүй.
- Mineralized point context: 81.0
- Structure/access: fault 36.5 м, dyke 3.7 м, road 488.6 м.
- Lithology context: γδ₂Ɛ₂₋₃t - Phase II: granodiorite, quartz diorite
- Тайлбар: Au-Cu-Mo-Py structural/alteration target.
- Follow-up: First-pass field traverse; verify fault/dyke/contact, alteration, quartz/vein/gossan; rock-chip + soil/stream sediment follow-up.
# 6. Field work-ийн санал болгож буй дараалал

| Ээлж | Candidate | Үндэслэл |
| --- | --- | --- |
| 1-р ээлж | PCA-01 | Хамгийн том бөгөөд хамгийн өндөр evidence overlap-той. Fault/dyke/contact, ASTER alteration, geochem anomaly, known occurrence, mineralized point бүгд давхцсан. |
| 2-р ээлж | PCA-03 | Cu-Mo-Co-Py-Sn context бүхий structural/alteration target. Road access сайн, mineralized point ойр. |
| 3-р ээлж | PCA-04, PCA-05 | Дунд хэмжээтэй өндөр оноотой бүсүүд. PCA-04 нь Cu-Mo-Co; PCA-05 нь Ba-Cu-Py-Sn context-той. |
| 4-р ээлж | PCA-02, PCA-06 | Жижиг боловч score өндөр. PCA-02 нь known occurrence ойр; PCA-06 нь fault/dyke болон alteration сайн давхцсан. |

# 7. Дараагийн шатны ажлын зөвлөмж
- PCA бүр дээр first-pass field traverse хийж fault, dyke, contact, quartz vein, gossan, alteration zone-ийг газар дээр нь баталгаажуулах.
- PCA-01, PCA-03 дээр rock-chip дээжлэлтийг structure/contact дагуу нягтруулах.
- Soil sampling grid-ийг PCA-01-д 100-200 м spacing, бусад жижиг target дээр 50-100 м spacing-ээр төлөвлөх.
- Stream sediment/heavy mineral follow-up-ийг candidate area-уудын drainage outlet хэсэгт давтан авах.
- ASTER alteration zone-ийг field спектрометр эсвэл hand specimen alteration logging-оор баталгаажуулах.
- Safety/access layer тусдаа байхгүй тул field өмнө road condition, seasonal water crossing, steep slope, communication coverage-г заавал шалгах.
# 8. Хязгаарлалт
Энэ үнэлгээ нь desktop-based preliminary prospectivity screening бөгөөд field verification, лабораторийн assay, detailed structural mapping, болон safety/access ground-truthing-аар баталгаажуулах шаардлагатай. Safety condition-г тусдаа мэдээлэл байхгүйгээс road/access proxy байдлаар урьдчилан үнэлсэн болно.
# 9. Дагалдах output файлууд
- BH_Preliminary_Prospect_Candidate_Areas_Evidence_Overlay_v01.gpkg
- BH_Preliminary_Prospect_Candidate_Areas_Summary_v01.csv
- BH_Preliminary_Prospect_Candidate_Areas_Map_v01.png
