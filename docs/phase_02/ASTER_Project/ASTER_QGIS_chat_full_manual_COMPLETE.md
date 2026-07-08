<!-- source: ASTER_QGIS_chat_full_manual_COMPLETE.docx (converted from Word; canonical form for LLM ingestion) -->

ASTER L1B ДАТА, QGIS 4.0.2 БОЛОВСРУУЛАЛТЫН
БҮРЭН ЧАТ-ЭМХЭТГЭЛ, QA/QC REPORT БА ЗААВАР

Сэдэв: ASTER L1B HDF4 датаас VNIR/SWIR/TIR composite, NDVI, Fe oxide, clay/sericite, silica, porphyry Cu-Au target mapping хийх QGIS workflow

| Үзүүлэлт | Утга |
| --- | --- |
| Файл | AST_L1B_00409052005043503_20250520190111(3).hdf |
| Программ | QGIS 4.0.2 |
| Project CRS | EPSG:32647 - WGS 84 / UTM zone 47N |
| Талбай | 45.5037°N–46.1929°N, 95.9718°E–97.0756°E |
| Эмхэтгэсэн огноо | 2026-06-03 |

Тайлбар: Энэ DOCX нь энэ чатад яригдсан бүх гол агуулгыг нэгтгэн эмхэтгэв: дата танилцуулга, QA/QC, QGIS workflow, troubleshooting, хувирлын индексүүд, target map, legend, polygon scoring болон хавсаргасан зураг/скрийншотууд.

# Агуулга
- ASTER L1B датаны үндсэн мэдээлэл
- QA/QC report ба ашиглах боломжийн үнэлгээ
- QGIS project folder, хадгалалт ба эхний setup
- B01-B14 GeoTIFF export ба single-band засвар
- VNIR, SWIR, TIR composite үүсгэх
- Cloud, NoData, pixel/blocky харагдалт ба troubleshooting
- Resolution тааруулах, resampling, Align Rasters
- Лицензийн хилээр clip хийх
- NDVI гаргах, NDVI legend хийх
- Хувирлын индексүүд ба өнгөний тохиргоо
- Ордын системүүд: порфир, эпитермаль, скарн, polymetallic vein
- Порфир Cu-Au target map хийх workflow
- Target polygon-д оноо өгөх, attribute table ба confidence
- Layout, legend, export хийх
- Практик checklist, анхааруулга
- Хавсралт: чатад орсон зураг, screenshot, infographic

# 1. ASTER L1B датаны үндсэн мэдээлэл

| Үзүүлэлт | Утга |
| --- | --- |
| Файлын төрөл | HDF4, ASTER L1B |
| Хиймэл дагуул / мэдрэгч | Terra / ASTER |
| Боловсруулалтын түвшин | Level 1B |
| Авсан огноо, цаг | 2005-09-05 04:35:03 UTC |
| Орон нутгийн ойролцоо цаг | 2005-09-05, 12:35 орчим |
| Боловсруулсан огноо | 2025-05-21 |
| Файлын хэмжээ | Metadata-д ~119 MB, бодитоор ~124.5 MB |
| Төв цэг | 45.8491°N, 96.521498°E |
| Баруун/зүүн хязгаар | 95.9718°E – 97.0756°E |
| Өмнөд/хойд хязгаар | 45.5037°N – 46.1929°N |
| UTM бүс | 47 |
| Нийт cloud cover | 8% |
| Missing / out-of-bounds / interpolated QA | 0% / 0% / 0% |


| Мэдрэгчийн бүлэг | Band | Resolution | Гол хэрэглээ |
| --- | --- | --- | --- |
| VNIR | Band 1, 2, 3N | 15 м | Fe oxide, ургамал, гадаргын өнгө, рельеф |
| VNIR stereo | Band 3B | 15 м | Stereo / DEM боломж |
| SWIR | Band 4–9 | 30 м | Clay, sericite, alunite, carbonate, Mg-OH alteration |
| TIR | Band 10–14 | 90 м | Silica, quartz-rich lithology, lithology contrast |

Дүгнэлт: VNIR, SWIR, TIR сувгууд бүрэн байгаа тул Fe oxide, clay/Al-OH, sericite/illite, advanced argillic, chlorite/epidote, carbonate/Mg-OH, silica anomaly зэрэг урьдчилсан spectral alteration mapping хийх боломжтой.
# 2. QA/QC report ба ашиглах боломжийн үнэлгээ
Ерөнхий QA/QC шийдвэр: Датаг preliminary ASTER-based alteration mapping болон target screening-д ашиглахыг зөвшөөрнө. Гэхдээ cloud/shadow/vegetation mask, NDVI шалгалт, DEM hillshade, geology/structure/geochemistry болон field validation зайлшгүй шаардлагатай.

| Cloud cover | QA/QC үнэлгээ | Ашиглалтын зөвлөмж |
| --- | --- | --- |
| 0–5% | Маш сайн | Шууд ашиглах боломжтой |
| 5–10% | Сайн | Ашиглаж болно, cloud mask хийх шаардлагатай |
| 10–20% | Дунд | Болгоомжтой ашиглана |
| >20% | Эрсдэлтэй | Хувирал ялгахад тохиромж муутай |
| >30% | Муу | Ихэнхдээ ашиглахгүй |


| QA/QC шалгуур | Утга | Үнэлгээ |
| --- | --- | --- |
| Cloud cover | 8% | Сайн / зөвшөөрөгдөх |
| Missing data | 0% | Маш сайн |
| Out-of-bounds data | 0% | Маш сайн |
| Interpolated data | 0% | Маш сайн |
| Авсан цаг | 12:35 орчим local | Өдрийн дунд; үүрийн зураг биш |
| Level | L1B | Урьдчилсан band ratio/composite хийхэд тохиромжтой, surface reflectance биш |

- 8% cloud cover нь alteration mapping-д ерөнхийдөө зөвшөөрөгдөнө.
- Гол шалгуур нь үүл scene-ийн хаана байгаа, лицензийн талбай/target area дээр давхцаж байгаа эсэх.
- Тод цайвар жижиг хэсгүүдийг шууд silica/clay alteration гэж тайлбарлахгүй; SWIR/TIR/NDVI/hillshade-тай давхар шалгана.
- ASTER alteration result = spectral anomaly, not confirmed mineralization.
# 3. QGIS project folder, хадгалалт ба эхний setup
D:\ASTER_Project\
├─ ASTER_Alteration_QGIS.qgz
├─ 01_raw\
│  └─ AST_L1B_00409052005043503_20250520190111(3).hdf
├─ 02_bands_geotiff\
├─ 03_resampled\
├─ 04_composites\
├─ 05_indices\
├─ 06_threshold\
├─ 07_clip_license\
├─ 08_layout_maps\
└─ 09_interpretation\
- Project → Save As... сонгоно.
- D:\ASTER_Project\ folder-оо сонгоно.
- File name: ASTER_Alteration_QGIS.qgz гэж хадгална.
- Project CRS доод баруун буланд EPSG:32647 байхыг шалгана.
Хадгалалтын зарчим: Raw HDF файл 01_raw дотор, export хийсэн band GeoTIFF-үүд 02_bands_geotiff дотор, resample хийсэн файлууд 03_resampled, composite VRT/TIF файлууд 04_composites, index raster-ууд 05_indices дотор хадгалагдана.
# 4. B01–B14 GeoTIFF export ба single-band засвар
- Browser panel-оор HDF файлаа нээнэ.
- VNIR_Swath:ImageData1, ImageData2, ImageData3N болон SWIR/TIR ImageData4–14 layer-үүдийг QGIS-д нэмнэ.
- Layer дээр Right click → Export → Save As... сонгоно.
- Output mode = Raw data, Format = GeoTIFF, CRS = EPSG:32647 гэж тохируулна.
- Файлыг D:\ASTER_Project\02_bands_geotiff\B01.tif гэх мэт нэрээр хадгална.
D:\ASTER_Project\02_bands_geotiff\B01.tif
D:\ASTER_Project\02_bands_geotiff\B02.tif
D:\ASTER_Project\02_bands_geotiff\B03N.tif
D:\ASTER_Project\02_bands_geotiff\B04.tif
...
D:\ASTER_Project\02_bands_geotiff\B14.tif
NoData values идэвхгүй байвал: Энэ шатанд асуудал биш. Эхлээд GeoTIFF болгож хадгалаад дараа нь NoData/Transparency/Translate шатанд 0 эсвэл -9999 утгаар засаж болно.
B03 нэршил: ASTER-д B03N болон B03B ялгаатай. Nadir band-ийг B03N.tif гэж нэрлэж хадгалах нь зөв.
2-band асуудал: QGIS зарим export үед Band 1 + alpha/mask Band 2 үүсгэж болно. Alteration/composite хийхэд зөвхөн Band 1 хэрэгтэй.
Raster → Conversion → Translate / Convert format
Input layer: B01
Output: D:\ASTER_Project\02_bands_geotiff\B01_single.tif
Additional command-line parameters: -b 1
- B01, B02, B03N болон бусад band бүрийг Properties → Information → Band count: 1 гэж шалгана.
- Хэрэв Band count: 2 байвал Translate / Convert format дээр -b 1 ашиглаж single-band болгож хадгална.
- Composite хийхдээ B01_single, B02_single, B03N_single гэх мэт single-band файлуудыг ашиглана.
# 5. VNIR, SWIR, TIR composite үүсгэх
## 5.1 VNIR false color — 3N-2-1
Raster → Miscellaneous → Build Virtual Raster
Input layers дараалал:
  B03N.tif / B03N_single.tif / B03N_30m.tif
  B02.tif / B02_single.tif / B02_30m.tif
  B01.tif / B01_single.tif / B01_30m.tif
Заавал чагтал: Place each input file into a separate band
Output: D:\ASTER_Project\04_composites\VNIR_3N_2_1.vrt
Layer Properties → Symbology
Render type: Multiband color
Red band: Band 1
Green band: Band 2
Blue band: Band 3
Min/Max: Cumulative count cut 2–98%, Load min/max values, Apply
## 5.2 SWIR alteration composite — 9-6-4
Input order:
  B09_single.tif
  B06_single.tif
  B04_single.tif
Output: D:\ASTER_Project\04_composites\SWIR_9_6_4.vrt
Render: Multiband color; Red=Band1, Green=Band2, Blue=Band3
## 5.3 TIR lithology composite — 14-12-10
Input order:
  B14_single.tif
  B12_single.tif
  B10_single.tif
Output: D:\ASTER_Project\04_composites\TIR_14_12_10.vrt
Composite дээр пиксел том харагдах: Scale 1:1,400 зэрэг маш ойроос харахад blocky/pixelated харагдах нь хэвийн. VNIR 15 м, SWIR 30 м, TIR 90 м resolution-тэй. Дүрслэхдээ Rendering → Resampling дээр Bilinear/Cubic туршиж, эсвэл 1:50,000–1:100,000 scale-д харах хэрэгтэй.
# 6. Cloud, NoData, pixel/blocky харагдалт ба troubleshooting

| Асуудал | Боломжит шалтгаан | Шийдэл |
| --- | --- | --- |
| Хар хүрээ / гадна талын хоосон хэсэг | Scene эргэсэн footprint-ийн NoData background | Transparency → Additional no data value: 0, эсвэл clip хийх |
| Ногоон давамгай VNIR | Band order буруу, stretch тохируулаагүй, edge NoData нөлөөлсөн | B03N→B02→B01 дараалал шалгах; Cumulative cut 2–98% |
| B01 2 band-тэй | Alpha/mask band хамт export болсон | Translate / Convert format дээр -b 1 ашиглах |
| NoData values идэвхгүй | HDF metadata/QGIS export mode | Эхлээд хадгалаад дараа нь NoData/Transparency тохируулах |
| Том pixel/blocky | Scale хэт ойр, nearest render | Zoom out, Rendering resampling: Bilinear/Cubic |
| Cloud эсэх эргэлзээтэй цайвар хэсэг | Цагаан чулуулаг/аллюви/давс/үүл байж болно | VNIR, SWIR, TIR, NDVI, DEM hillshade давхар шалгах |

Cloud check дүгнэлт: Чатад шалгасан VNIR 3N-2-1 false color зурагт том хэмжээний өтгөн үүл харагдаагүй. Жижиг цайвар толбонууд байж болох тул SWIR/TIR/NDVI/hillshade-аар шалгаж, эргэлзээтэй хэсгийг mask хийх хэрэгтэй.
# 7. Resolution тааруулах, resampling, Align Rasters

| Бүлэг | Band | Resolution |
| --- | --- | --- |
| VNIR | B01, B02, B03N | 15 м |
| SWIR | B04–B09 | 30 м |
| TIR | B10–B14 | 90 м |

- Зөвхөн SWIR band хооронд ratio хийх бол resample хийх шаардлагагүй: B05/B06, B04/B06, B07/B08 бүгд 30 м.
- VNIR + SWIR холих үед VNIR-ийг 30 м болгож resample хийнэ. Жишээ: B05/B03N хийх бол B03N_30m хэрэгтэй.
- TIR-тэй хамтарсан анализ хийх бол 90 м эсвэл зорилгоос хамаарч grid тааруулна.
Processing Toolbox → QGIS → Raster tools → Align rasters
Reference layer: B04_single.tif
Override reference CRS: EPSG:32647
Override reference cell size X: 30
Override reference cell size Y: 30
Input layer(s): B01_single.tif, B02_single.tif, B03N_single.tif
Output:
  D:\ASTER_Project\03_resampled\B01_30m.tif
  D:\ASTER_Project\03_resampled\B02_30m.tif
  D:\ASTER_Project\03_resampled\B03N_30m.tif
Resampling method: VNIR/SWIR/TIR нь continuous spectral data тул resample хийхэд Bilinear тохиромжтой. Nearest Neighbour нь classification/discrete raster-д тохиромжтой. Build Virtual Raster дээр resampling algorithm нь зөвхөн VRT display/overview үед нөлөөлж болох боловч бодит resampling биш байж болно.
Align Rasters алдаа: “An output file is not configured...” алдаа гарвал Input layer(s)-ийн Configure Raster... хэсэгт input бүрийн output file path-г 03_resampled folder руу зааж өгнө.
# 8. Лицензийн хилээр clip хийх
- Лицензийн хилээ QGIS-д нэмнэ: Layer → Add Layer → Add Vector Layer.
- Лицензийн CRS-ийг шалгана: Properties → Information. Боломжтой бол EPSG:32647 болгож Export → Save Features As... хийнэ.
- Raster → Extraction → Clip Raster by Mask Layer нээнэ.
- Input layer дээр ASTER raster/composite/index-ээ сонгоно.
- Mask layer дээр license_area_32647 layer-ээ сонгоно.
- Assign NoData: -9999, Keep resolution, Crop to cutline / Match extent тохируулна.
- Output-ийг D:\ASTER_Project\07_clip_license\..._clip.tif гэж хадгална.
Crop to cutline харагдахгүй бол: QGIS version/interface-аас хамаарч Advanced parameters дотор нуугдсан байж болно. Цонхоо томруулж scroll хийж үзнэ. Эсвэл Processing Toolbox дахь GDAL → Raster extraction → Clip raster by mask layer ашиглана.
# 9. NDVI гаргах, NDVI legend хийх
NDVI = (B03N - B02) / (B03N + B02)
QGIS Raster Calculator:
("B03N@1" - "B02@1") / ("B03N@1" + "B02@1")
Output: D:\ASTER_Project\05_indices\NDVI.tif

| NDVI утга | Тайлбар |
| --- | --- |
| < 0 | Ус, сүүдэр |
| 0–0.2 | Нүцгэн хөрс, чулуулаг |
| 0.2–0.4 | Сийрэг ургамал |
| > 0.4 | Ургамлын нөлөө өндөр |

- NDVI layer дээр Right click → Properties → Symbology.
- Render type = Singleband pseudocolor.
- Min = -1, Max = 1 гэж оруулна.
- Mode = Equal interval, Classes = 5 эсвэл гараар 4 class тохируулна.
- Color ramp: RdYlGn эсвэл өөрийн ангилал. Ургамал өндөр хэсгийг ногоон, ус/сүүдрийг хөх/бараан, нүцгэн хөрсийг шар/бороор харуулж болно.
- Legend Settings дээр continuous legend хэрэгтэй бол Use continuous legend; ангилсан legend хэрэгтэй бол class label-уудыг гараар засна.
- Apply → OK дарж хадгална.
Геологийн тайлбарт: NDVI > 0.3 эсвэл > 0.4 хэсгийг болгоомжтой авч үзнэ; ургамлын spectral нөлөөтэй байж болно.
# 10. Хувирлын индексүүд ба өнгөний тохиргоо

| Хувирал | Индекс | Тайлбар | Санал өнгө |
| --- | --- | --- | --- |
| Ferric Iron / Fe oxide | B02 / B01 | Hematite, goethite, limonite, gossan | Reds |
| Ferrous Iron / Fe-Mg | B05 / B03N_30m | Fe-Mg, propylitic/mafic шинж | Magma/Turbo |
| Clay / Al-OH | B05 / B06 | Kaolinite, illite, smectite, sericite/muscovite | Magma/Spectral/Turbo |
| Advanced Argillic | B04 / B06 | Alunite, kaolinite, pyrophyllite, lithocap | Magma/Spectral |
| Chlorite / Epidote / Mg-OH | B07 / B08 | Propylitic halo, chlorite, epidote | Greens |
| Carbonate / Mg-OH | B07 / B08 | Calcite, dolomite, ankerite, Mg-OH | Greens/Cividis |
| Silica / Quartz-rich | B13 / B12; B14 / B12 | Quartz-rich lithology, silicification | Greys/Cividis/Viridis |

Ferric Iron өнгө: Ferric Iron_B02_B01 layer-д хамгийн ойлгомжтой color ramp нь Reds. Өндөр утга илүү тод улаан болж Fe oxide anomaly-г шууд онцолдог.
# 11. Ордын системүүд ба хувирлууд

| Систем | Гол хувирал | ASTER дээр хайх pattern |
| --- | --- | --- |
| Порфир Cu-Au | Potassic, phyllic/sericitic, argillic, advanced argillic, propylitic, Fe oxide, silica | Clay/sericite + Fe oxide + chlorite/epidote halo + silica |
| High-sulfidation epithermal Au-Ag | Silicification, advanced argillic, argillic, Fe oxide | Alunite/kaolinite + silica + ferric iron |
| Low/intermediate-sulfidation epithermal Au-Ag | Silicification, argillic, sericitic, carbonate, Fe oxide | Silica + clay/illite + carbonate + Fe oxide |
| Скарн | Carbonate, calc-silicate, chlorite-epidote, Fe oxide, silica | Carbonate/Mg-OH + chlorite/epidote + Fe oxide + silica |
| Polymetallic vein | Silicification, sericite, argillic, carbonate, Fe-Mn oxide | Linear Fe oxide + silica + sericite/clay + carbonate |

# 12. Порфир Cu-Au target map хийх workflow
Ашиглах layer-үүд:
Ferric_Iron_B02_B01
Clay_AlOH_B05_B06
Sericite_Illite_B05_B06
Chlorite_Epidote_MgOH_B07_B08
Silica_B13_B12
NDVI
SWIR_9_6_4

| Дотор/гадна бүс | Хувирал | QGIS layer |
| --- | --- | --- |
| Төв/дээд | Phyllic / sericite | Clay_AlOH, Sericite_Illite |
| Дээд cap | Argillic / advanced argillic | Clay_AlOH, Advanced_Argillic |
| Гадна halo | Propylitic | Chlorite_Epidote |
| Исэлдсэн бүс | Fe oxide | Ferric_Iron |
| Зарим | Silica | Silica index |

Layer order:
1. License boundary
2. Porphyry_Target_Score / Target polygons
3. Ferric Iron anomaly
4. Clay / Sericite anomaly
5. Chlorite / Epidote anomaly
6. Silica anomaly
7. Lineaments / faults
8. SWIR_9_6_4 composite
9. Base map
Сайн порфир target pattern: Clay/Sericite өндөр + Fe oxide өндөр + гадна талд Chlorite/Epidote halo + заримдаа Silica anomaly. Энэ нь lineament intersection, intrusive contact эсвэл circular/ring feature-тэй давхцвал илүү сонирхолтой.
Жишээ binary layer expressions:
Ferric_binary:             "Ferric_Iron_B02_B01@1" > 1.10
Clay_binary:               "Clay_AlOH_B05_B06@1" > 1.15
Chlorite_Epidote_binary:   "Chlorite_Epidote_MgOH_B07_B08@1" > 1.10
Silica_binary:             "Silica_B13_B12@1" > 1.05
Threshold сонгох: Layer statistics-аас Mean, StdDev авч Threshold = Mean + 1.5 × StdDev байдлаар илүү үндэслэлтэй сонгоно. Дээрх утгууд нь зөвхөн эхний жишээ.
Porphyry_Target_Score:
("Ferric_binary@1" * 1) +
("Clay_binary@1" * 2) +
("Chlorite_Epidote_binary@1" * 1) +
("Silica_binary@1" * 1)
Output: D:\ASTER_Project\09_interpretation\Porphyry_Target_Score.tif

| Score | Тайлбар |
| --- | --- |
| 0–1 | Сул |
| 2 | Дунд |
| 3 | Сайн target |
| 4 | Өндөр сонирхолтой |
| 5 | Маш өндөр сонирхолтой |

## 12.1 Порфирийн сайн target pattern шалгах
- Clay/Sericite өндөр хэсгийг олно.
- Тэр хэсэг Fe oxide anomaly-тэй давхцаж байгаа эсэхийг шалгана.
- Clay/Sericite төв хэсгийн гадна талд Chlorite/Epidote halo байгаа эсэхийг шалгана.
- Silica anomaly структур, ridge эсвэл quartz-rich zone дагаж байгаа эсэхийг шалгана.
- Lineament/fault intersection дээр байрласан эсэхийг шалгана.
- Intrusive contact, circular/ring feature, radial drainage байгаа эсэхийг шалгана.
Clay polygon → Buffer 300–500 m → Intersection with Chlorite_Epidote_Halo_Polygon
Clay_Anomaly_Polygon ∩ Ferric_Anomaly_Polygon → Clay + Fe oxide overlap
Silica_Anomaly_Polygon ∩ Lineament_Buffer_200m → Structural silica anomaly
# 13. Target polygon-д оноо өгөх, attribute table ба confidence
Хаана хийх вэ: Эдгээр талбаруудыг raster layer дээр биш, Porphyry_Final_Target_Polygons гэх мэт target polygon vector layer-ийн Attribute Table дотор нэмнэ.
- Porphyry_Final_Target_Polygons layer дээр Right click → Open Attribute Table.
- Attribute Table дээр Toggle Editing буюу шар харандаа icon дарна.
- New Field товч дарж дараах талбаруудыг нэг нэгээр нэмнэ.

| Field name | Type | Length | Тайлбар |
| --- | --- | --- | --- |
| clay | Whole number / Integer | 1 эсвэл 2 | Clay/Sericite anomaly байгаа эсэх; 0 эсвэл 2 |
| ferric | Whole number / Integer | 1 эсвэл 2 | Fe oxide anomaly байгаа эсэх; 0 эсвэл 1 |
| chlorite | Whole number / Integer | 1 эсвэл 2 | Chlorite/Epidote halo байгаа эсэх; 0 эсвэл 1 |
| silica | Whole number / Integer | 1 эсвэл 2 | Silica anomaly байгаа эсэх; 0 эсвэл 1 |
| lineament | Whole number / Integer | 1 эсвэл 2 | Fault/lineament-тэй давхцсан эсэх; 0 эсвэл 1 |
| intrusive | Whole number / Integer | 1 эсвэл 2 | Intrusive contact/circular feature-тэй эсэх; 0 эсвэл 1 |
| target_score | Whole number / Integer | 2 | Нийт оноо |
| confidence | Text / String | 20 | Low / Moderate / High |
| note | Text / String | 255 | Тайлбар |


| Нөхцөл | Оноо |
| --- | --- |
| Clay/Sericite өндөр | 2 |
| Fe oxide давхцсан | 1 |
| Chlorite/Epidote halo | 1 |
| Silica anomaly | 1 |
| Lineament intersection | 1 |
| Intrusive contact/circular feature | 1 |

Field Calculator → Update existing field: target_score
Expression:
"clay" + "ferric" + "chlorite" + "silica" + "lineament" + "intrusive"
Field Calculator → Update existing field: confidence
Expression:
CASE
WHEN "target_score" >= 5 THEN 'High'
WHEN "target_score" >= 3 THEN 'Moderate'
ELSE 'Low'
END

| Target score | Confidence | Тайлбар |
| --- | --- | --- |
| 0–2 | Low | Сул target, давхцал бага |
| 3–4 | Moderate | Дунд зэрэг сонирхолтой |
| 5–7 | High | Өндөр ач холбогдолтой target |

- Олон polygon үнэлэхдээ Vector → Research Tools → Select by Location ашиглаж давхцсан target-уудыг сонгоод Field Calculator дээр Only update selected features чагталж оноо өгнө.
- Lineament-тэй intersection илрүүлэхдээ lineament line-г 100–200 м buffer болгон target polygon-той intersect хийвэл илүү бодитой.
- Attribute Table бөглөсний дараа Save Layer Edits дарж, Toggle Editing унтраана.
# 14. Layout, legend, export хийх
- Project → New Print Layout сонгоно.
- Layout нэр өгнө: жишээ Porphyry_Cu_Au_Target_Map.
- Add Map товчоор map frame оруулна.
- Add Legend товчоор legend оруулна.
- Item Properties → Legend Items дээр шаардлагагүй layer-үүдийг хасна.
- Add Scale Bar, Add North Arrow, Add Label нэмж гарчиг, CRS, scale, тайлбар оруулна.
- Layout → Export as PDF эсвэл Export as Image сонгоно.
Жишээ title:
ASTER-Based Porphyry Cu-Au Target Map
Ferric Iron + Clay/Sericite + Chlorite/Epidote + Silica

Доод тайлбар:
ASTER alteration products represent spectral anomalies only.
Targets require validation by geology, structure, geochemistry, and field checking.
# 15. Практик checklist, анхааруулга

| Тэмдэг | Шалгах зүйл |
| --- | --- |
| [ ] | B01–B14 single-band эсэх шалгасан |
| [ ] | Project CRS EPSG:32647 |
| [ ] | VNIR 3N-2-1, SWIR 9-6-4, TIR 14-12-10 composite үүссэн |
| [ ] | Cloud/shadow/bright surface шалгасан |
| [ ] | NDVI гаргаж ургамлын нөлөө шалгасан |
| [ ] | Index layer бүрийн statistics харсан |
| [ ] | Threshold-үүдийг үндэслэлтэй сонгосон |
| [ ] | Binary anomaly layer үүсгэсэн |
| [ ] | Porphyry target score үүсгэсэн |
| [ ] | Target polygon үүсгэж attribute оноо өгсөн |
| [ ] | Lineament, intrusive/circular feature, geology-тэй давхар шалгасан |
| [ ] | Field verification хийх цэгүүдийг сонгосон |

Анхааруулга: ASTER-аас гарсан map нь хүдрийн биет эсвэл ордыг батлахгүй. Энэ нь зөвхөн spectral anomaly, target generation, field verification planning-д ашиглах screening tool юм.

# 16. Хавсралт: чатад орсон зураг, screenshot, infographic
Тайлбар: Доорх хавсралтад чатад орсон үндсэн screenshot, QGIS цонх, false-color map, infographic болон preview зургуудыг оруулав. Зарим screenshot нь интерфейсийн зааварчилгааны зориулалттай.
## ASTER VNIR false color preview

ASTER VNIR false color preview
## ASTER SWIR 9-6-4 preview

ASTER SWIR 9-6-4 preview
## ASTER TIR band 13 preview

ASTER TIR band 13 preview
## QGIS Save Raster Layer As тохиргоо

QGIS Save Raster Layer As тохиргоо
## B03/B03N layer үүсэлт

B03/B03N layer үүсэлт
## VNIR_3N_2_1 VRT анхны харагдалт

VNIR_3N_2_1 VRT анхны харагдалт
## VNIR false color cloud check

VNIR false color cloud check
## VNIR clipped map layout screenshot

VNIR clipped map layout screenshot
## QGIS legend үүсгэх infographic

QGIS legend үүсгэх infographic
## VNIR map analysis infographic

VNIR map analysis infographic
## VNIR legend infographic

VNIR legend infographic
## NDVI legend тохируулах infographic

NDVI legend тохируулах infographic
## Ferric Iron infographic check

Ferric Iron infographic check
## 16.1 Чатад орсон бусад PNG файлуудын бүрэн жагсаалт

| № | Файл | Статус |
| --- | --- | --- |
| 1 | 02577359-ec5b-4986-92eb-bc0a7c8b03dc.png | Жагсаалтаар бүртгэв |
| 2 | 100d8716-7884-4112-8645-0810bacf0df4.png | Жагсаалтаар бүртгэв |
| 3 | 1050ee40-5017-43c9-a850-7882cc20e126.png | Жагсаалтаар бүртгэв |
| 4 | 127435cf-a179-43bd-be22-aef804190791.png | Жагсаалтаар бүртгэв |
| 5 | 2ac7b025-d578-4348-80b6-c14006f43eba.png | Жагсаалтаар бүртгэв |
| 6 | 2b918c7d-b924-40b2-8a3c-c1ddd792a104.png | Жагсаалтаар бүртгэв |
| 7 | 3191a9bf-0eee-439a-b973-fde4ac16dcfd.png | Жагсаалтаар бүртгэв |
| 8 | 36b611ff-9fad-4e4b-bb46-c471bdaffa7c.png | Жагсаалтаар бүртгэв |
| 9 | 446f72fe-20b3-4d1c-a192-41ba0b1e260d.png | Жагсаалтаар бүртгэв |
| 10 | 5277e3de-25c1-40d9-ad64-492744bc2626.png | Жагсаалтаар бүртгэв |
| 11 | 5a5d2438-fbf2-40b2-872e-aec1e26fc272.png | Жагсаалтаар бүртгэв |
| 12 | 5ce1b01a-82fb-4645-b4e1-b59296a2c0f7.png | Жагсаалтаар бүртгэв |
| 13 | 6084290f-cfc9-43cf-869f-a84db7d86218.png | Жагсаалтаар бүртгэв |
| 14 | 63048944-a61f-4a36-bbc7-f359b2775781.png | Жагсаалтаар бүртгэв |
| 15 | 6deacd13-458b-4914-a544-7100a1e6f374.png | Жагсаалтаар бүртгэв |
| 16 | 6eed114b-e2dc-412d-ae3a-9546737ee339.png | Жагсаалтаар бүртгэв |
| 17 | 72e47cb2-cb6a-4de7-b02d-b5f2a4da1158.png | Оруулсан |
| 18 | 759271f6-4801-4387-ad49-59a871745477.png | Жагсаалтаар бүртгэв |
| 19 | 772a0005-30e2-48f7-95cb-199c33f01568.png | Жагсаалтаар бүртгэв |
| 20 | 78fb9156-41d8-44b6-9c71-f52f973affb8.png | Жагсаалтаар бүртгэв |
| 21 | 7c6faae8-87a2-47c9-9c0e-8aaa2ae7c3ca.png | Жагсаалтаар бүртгэв |
| 22 | 83169070-e64e-4877-8519-7f625a454263.png | Жагсаалтаар бүртгэв |
| 23 | 85ffb6c9-6ad3-4ae2-9e7a-81e58d8a537f.png | Жагсаалтаар бүртгэв |
| 24 | 8b2e6cef-ba04-4b3b-b958-b0a80f19c487.png | Жагсаалтаар бүртгэв |
| 25 | 91cd997c-f401-4a60-81fe-129edd3e5888.png | Жагсаалтаар бүртгэв |
| 26 | 9d0a14c6-816b-499f-a0b7-ca65d1117fc4.png | Жагсаалтаар бүртгэв |
| 27 | a59bd7b9-5df7-4d8d-bddd-0996c35b4489.png | Жагсаалтаар бүртгэв |
| 28 | a9d0ab08-fdf4-4578-a0ad-0a6896472cc2.png | Жагсаалтаар бүртгэв |
| 29 | a_clean_infographic_style_map_analysis_image_on_a.png | Оруулсан |
| 30 | a_clean_infographic_style_map_legend_image_on_a_li.png | Оруулсан |
| 31 | a_clean_tutorial_style_infographic_screenshot_with.png | Оруулсан |
| 32 | a_screenshot_like_instructional_infographic_page_a.png | Жагсаалтаар бүртгэв |
| 33 | a_screenshot_of_a_computer_gis_application_qgis.png | Оруулсан |
| 34 | a_screenshot_style_instructional_graphic_in_mongol.png | Оруулсан |
| 35 | aadac7a7-baf1-457f-b8f5-b542f1207ba4.png | Оруулсан |
| 36 | ab1a8835-aaee-48eb-9ae1-7627678ca92e.png | Жагсаалтаар бүртгэв |
| 37 | aster_false_color_3N_2_1_preview.png | Оруулсан |
| 38 | aster_swir_9_6_4_preview.png | Оруулсан |
| 39 | aster_tir_band13_preview.png | Оруулсан |
| 40 | c27719d7-9684-4f53-bdc9-6592f37bbbc0.png | Оруулсан |
| 41 | cc9109d9-b4f0-4f8c-ae5d-4ca209e1fe44.png | Жагсаалтаар бүртгэв |
| 42 | ceab482e-f879-4a3a-95a8-66f7989f72f1.png | Оруулсан |
| 43 | db4091da-772e-4a27-a6be-23efef196922.png | Жагсаалтаар бүртгэв |
| 44 | e0e17a2e-df16-42f2-8172-3b97220e6e44.png | Жагсаалтаар бүртгэв |
| 45 | f1fb3b82-2c2a-4b02-8b19-66700b3fa55b.png | Оруулсан |
| 46 | f54a513e-8a1b-4016-9bab-c4961fbf9e0a.png | Жагсаалтаар бүртгэв |

## 16.2 Чатад орсон бүх PNG зураг/скрийншотуудыг бүрэн хавсаргав
Энэ хэсэгт /mnt/data дотор хадгалагдсан чатад орсон бүх PNG файлыг файл нэрээр нь дарааллуулан оруулсан. Ингэснээр өмнөх хавсралтын жагсаалтад бүртгэгдсэн зураг бүр DOCX дотор харагдана.
### 02577359-ec5b-4986-92eb-bc0a7c8b03dc.png

Хавсралтын зураг: 02577359-ec5b-4986-92eb-bc0a7c8b03dc.png
### 100d8716-7884-4112-8645-0810bacf0df4.png

Хавсралтын зураг: 100d8716-7884-4112-8645-0810bacf0df4.png
### 1050ee40-5017-43c9-a850-7882cc20e126.png

Хавсралтын зураг: 1050ee40-5017-43c9-a850-7882cc20e126.png
### 127435cf-a179-43bd-be22-aef804190791.png

Хавсралтын зураг: 127435cf-a179-43bd-be22-aef804190791.png
### 2ac7b025-d578-4348-80b6-c14006f43eba.png

Хавсралтын зураг: 2ac7b025-d578-4348-80b6-c14006f43eba.png
### 2b918c7d-b924-40b2-8a3c-c1ddd792a104.png

Хавсралтын зураг: 2b918c7d-b924-40b2-8a3c-c1ddd792a104.png
### 3191a9bf-0eee-439a-b973-fde4ac16dcfd.png

Хавсралтын зураг: 3191a9bf-0eee-439a-b973-fde4ac16dcfd.png
### 36b611ff-9fad-4e4b-bb46-c471bdaffa7c.png

Хавсралтын зураг: 36b611ff-9fad-4e4b-bb46-c471bdaffa7c.png
### 446f72fe-20b3-4d1c-a192-41ba0b1e260d.png

Хавсралтын зураг: 446f72fe-20b3-4d1c-a192-41ba0b1e260d.png
### 5277e3de-25c1-40d9-ad64-492744bc2626.png

Хавсралтын зураг: 5277e3de-25c1-40d9-ad64-492744bc2626.png
### 5a5d2438-fbf2-40b2-872e-aec1e26fc272.png

Хавсралтын зураг: 5a5d2438-fbf2-40b2-872e-aec1e26fc272.png
### 5ce1b01a-82fb-4645-b4e1-b59296a2c0f7.png

Хавсралтын зураг: 5ce1b01a-82fb-4645-b4e1-b59296a2c0f7.png
### 6084290f-cfc9-43cf-869f-a84db7d86218.png

Хавсралтын зураг: 6084290f-cfc9-43cf-869f-a84db7d86218.png
### 63048944-a61f-4a36-bbc7-f359b2775781.png

Хавсралтын зураг: 63048944-a61f-4a36-bbc7-f359b2775781.png
### 6deacd13-458b-4914-a544-7100a1e6f374.png

Хавсралтын зураг: 6deacd13-458b-4914-a544-7100a1e6f374.png
### 6eed114b-e2dc-412d-ae3a-9546737ee339.png

Хавсралтын зураг: 6eed114b-e2dc-412d-ae3a-9546737ee339.png
### 72e47cb2-cb6a-4de7-b02d-b5f2a4da1158.png

Хавсралтын зураг: 72e47cb2-cb6a-4de7-b02d-b5f2a4da1158.png
### 759271f6-4801-4387-ad49-59a871745477.png

Хавсралтын зураг: 759271f6-4801-4387-ad49-59a871745477.png
### 772a0005-30e2-48f7-95cb-199c33f01568.png

Хавсралтын зураг: 772a0005-30e2-48f7-95cb-199c33f01568.png
### 78fb9156-41d8-44b6-9c71-f52f973affb8.png

Хавсралтын зураг: 78fb9156-41d8-44b6-9c71-f52f973affb8.png
### 7c6faae8-87a2-47c9-9c0e-8aaa2ae7c3ca.png

Хавсралтын зураг: 7c6faae8-87a2-47c9-9c0e-8aaa2ae7c3ca.png
### 83169070-e64e-4877-8519-7f625a454263.png

Хавсралтын зураг: 83169070-e64e-4877-8519-7f625a454263.png
### 85ffb6c9-6ad3-4ae2-9e7a-81e58d8a537f.png

Хавсралтын зураг: 85ffb6c9-6ad3-4ae2-9e7a-81e58d8a537f.png
### 8b2e6cef-ba04-4b3b-b958-b0a80f19c487.png

Хавсралтын зураг: 8b2e6cef-ba04-4b3b-b958-b0a80f19c487.png
### 91cd997c-f401-4a60-81fe-129edd3e5888.png

Хавсралтын зураг: 91cd997c-f401-4a60-81fe-129edd3e5888.png
### 9d0a14c6-816b-499f-a0b7-ca65d1117fc4.png

Хавсралтын зураг: 9d0a14c6-816b-499f-a0b7-ca65d1117fc4.png
### a59bd7b9-5df7-4d8d-bddd-0996c35b4489.png

Хавсралтын зураг: a59bd7b9-5df7-4d8d-bddd-0996c35b4489.png
### a9d0ab08-fdf4-4578-a0ad-0a6896472cc2.png

Хавсралтын зураг: a9d0ab08-fdf4-4578-a0ad-0a6896472cc2.png
### a_clean_infographic_style_map_analysis_image_on_a.png

Хавсралтын зураг: a_clean_infographic_style_map_analysis_image_on_a.png
### a_clean_infographic_style_map_legend_image_on_a_li.png

Хавсралтын зураг: a_clean_infographic_style_map_legend_image_on_a_li.png
### a_clean_tutorial_style_infographic_screenshot_with.png

Хавсралтын зураг: a_clean_tutorial_style_infographic_screenshot_with.png
### a_screenshot_like_instructional_infographic_page_a.png

Хавсралтын зураг: a_screenshot_like_instructional_infographic_page_a.png
### a_screenshot_of_a_computer_gis_application_qgis.png

Хавсралтын зураг: a_screenshot_of_a_computer_gis_application_qgis.png
### a_screenshot_style_instructional_graphic_in_mongol.png

Хавсралтын зураг: a_screenshot_style_instructional_graphic_in_mongol.png
### aadac7a7-baf1-457f-b8f5-b542f1207ba4.png

Хавсралтын зураг: aadac7a7-baf1-457f-b8f5-b542f1207ba4.png
### ab1a8835-aaee-48eb-9ae1-7627678ca92e.png

Хавсралтын зураг: ab1a8835-aaee-48eb-9ae1-7627678ca92e.png
### aster_false_color_3N_2_1_preview.png

Хавсралтын зураг: aster_false_color_3N_2_1_preview.png
### aster_swir_9_6_4_preview.png

Хавсралтын зураг: aster_swir_9_6_4_preview.png
### aster_tir_band13_preview.png

Хавсралтын зураг: aster_tir_band13_preview.png
### c27719d7-9684-4f53-bdc9-6592f37bbbc0.png

Хавсралтын зураг: c27719d7-9684-4f53-bdc9-6592f37bbbc0.png
### cc9109d9-b4f0-4f8c-ae5d-4ca209e1fe44.png

Хавсралтын зураг: cc9109d9-b4f0-4f8c-ae5d-4ca209e1fe44.png
### ceab482e-f879-4a3a-95a8-66f7989f72f1.png

Хавсралтын зураг: ceab482e-f879-4a3a-95a8-66f7989f72f1.png
### db4091da-772e-4a27-a6be-23efef196922.png

Хавсралтын зураг: db4091da-772e-4a27-a6be-23efef196922.png
### e0e17a2e-df16-42f2-8172-3b97220e6e44.png

Хавсралтын зураг: e0e17a2e-df16-42f2-8172-3b97220e6e44.png
### f1fb3b82-2c2a-4b02-8b19-66700b3fa55b.png

Хавсралтын зураг: f1fb3b82-2c2a-4b02-8b19-66700b3fa55b.png
### f54a513e-8a1b-4016-9bab-c4961fbf9e0a.png

Хавсралтын зураг: f54a513e-8a1b-4016-9bab-c4961fbf9e0a.png
