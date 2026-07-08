<!-- source: ASTER_QGIS_402_SOP_non_geologist_MN.docx (converted from Word; canonical form for LLM ingestion) -->

# ASTER L1B сансрын зургийг QGIS 4.0.2 дээр боловсруулах
## Геологи мэдэхгүй хэрэглэгч дагаж хийж болох үйлдвэрлэлийн дэлгэрэнгүй ажлын заавар / SOP
Хамрах ажил: HDF4 ASTER L1B дата унших, B01-B14 GeoTIFF экспортлох, single-band засвар, composite үүсгэх, лицензийн хилээр clip хийх, NDVI ба alteration index гаргах, порфир Cu-Au target map болон эцсийн бүтээгдэхүүн бэлтгэх.
Бэлтгэсэн огноо: 2026-06-03
Ашигласан эх материал: энэ чат дахь QGIS зааврууд, QA/QC дүгнэлт, алдаа засварын тайлбарууд болон өмнөх ASTER_QGIS_chat_full_manual_COMPLETE.docx.
## QA/QC-ийн үндсэн шийдвэр

| Үзүүлэлт | Үнэлгээ |
| --- | --- |
| Датаны хэрэглээ | ASTER spectral alteration anomaly ба target screening хийхэд ашиглаж болно |
| Cloud cover | 8% - зөвшөөрөгдөх түвшин; cloud/shadow mask шалгалт заавал хийнэ |
| QA | Missing / out-of-bounds / interpolated: 0% / 0% / 0% |
| Цаг | 2005-09-05 04:35:03 UTC буюу Монголын цагаар ойролцоогоор 12:35; үүрийн зураг биш |
| Анхаарах зүйл | Эцсийн орд батлахгүй, зөвхөн spectral anomaly ба field checking төлөвлөх суурь болно |

# Агуулга
1. Энэ зааврын зорилго ба бүтээгдэхүүний жагсаалт
2. Датаны үндсэн мэдээлэл ба чанарын шалгалт
3. Ажлын хавтас, нэршил, файлын бүртгэл
4. QGIS project setup
5. HDF доторх B01-B14 band-уудыг GeoTIFF болгох
6. Single-band засвар ба VRT алдааг засах
7. VNIR, SWIR, TIR composite үүсгэх
8. Pixel/blocky харагдалт, resampling, display тохиргоо
9. Лицензийн хилээр clip хийх
10. NDVI гаргах ба ургамлын нөлөө хянах
11. Alteration index-үүд гаргах
12. Өнгө, legend, layout map бэлтгэх
13. Порфир Cu-Au target pattern ба scoring
14. Эцсийн бүтээгдэхүүн, QA/QC, архивлах
15. Troubleshooting ба шалгах checklist

# 1. Энэ зааврын зорилго ба эцсийн бүтээгдэхүүн
Энэ SOP-ийн зорилго нь ASTER L1B HDF4 сансрын зургийг QGIS 4.0.2 дээр шат дараатай боловсруулж, геологи мэдэхгүй хэрэглэгч ч дагаж хийгээд эцсийн зураг, index, target polygon, тайлангийн бүтээгдэхүүн гаргах боломжтой болгох юм.
Энэ зааварт “хувирал” гэж хэлэхдээ шууд эрдсийн баталгаажсан илрэл биш, ASTER сувгуудын spectral anomaly-г хэлнэ. Иймээс field checking, геологийн зураг, геохими, дээжлэлээр баталгаажуулах шаардлагатай.

| Эцсийн бүтээгдэхүүн | Файл / folder | Хэнд хэрэгтэй вэ |
| --- | --- | --- |
| B01-B14 single-band GeoTIFF | 02_bands_geotiff | Цаашдын бүх тооцооны эх файл |
| Resampled 30 м band-ууд | 03_resampled | VNIR+SWIR хамтарсан ratio/composite хийхэд |
| Composite зурагнууд | 04_composites | Ерөнхий харагдац, QA/QC, cloud check |
| NDVI ба alteration index | 05_indices | Fe oxide, clay, silica зэрэг anomaly ялгах |
| Binary anomaly raster | 06_threshold | Target score бодох оролт |
| Лицензийн хилээр clip хийсэн raster | 07_clip_license | Зөвхөн судалгааны талбайн дотор ажиллах |
| Layout map PDF/PNG | 08_layout_maps | Тайлан, танилцуулга, хэвлэх зураг |
| Target polygons ба score | 09_interpretation | Field checking, дараагийн хайгуулын төлөвлөлт |
| QA/QC report | QA-QC_Report.docx/pdf | Датаны чанар ба ашиглах боломжийн баримт |

## Ажил эхлэхээс өмнөх богино checklist
[ ] QGIS 4.0.2 суусан эсэхийг шалгах.
[ ] Processing Toolbox болон GDAL provider идэвхтэй эсэхийг шалгах.
[ ] ASTER HDF файлыг 01_raw хавтаст байрлуулах.
[ ] Лицензийн хил vector файл байгаа эсэхийг шалгах. Байхгүй бол эхлээд бэлдэнэ.
[ ] Project CRS-ийг EPSG:32647 болгох.
# 2. Датаны үндсэн мэдээлэл ба чанарын шалгалт

| Үзүүлэлт | Утга |
| --- | --- |
| Файлын төрөл | HDF4, ASTER L1B |
| Хиймэл дагуул / мэдрэгч | Terra / ASTER |
| Боловсруулалтын түвшин | Level 1B |
| Авсан огноо, цаг | 2005-09-05 04:35:03 UTC |
| Орон нутгийн ойролцоо цаг | 12:35 орчим |
| Боловсруулсан огноо | 2025-05-21 |
| Файлын хэмжээ | metadata-д ~119 MB, бодитоор ~124.5 MB |
| Төв цэг | 45.8491°N, 96.521498°E |
| Хязгаар | 95.9718°E-97.0756°E; 45.5037°N-46.1929°N |
| UTM бүс | 47 |
| Cloud cover | 8% |
| QA | Missing / out-of-bounds / interpolated = 0% / 0% / 0% |


| Band бүлэг | Band | Resolution | Хэрэглээ |
| --- | --- | --- | --- |
| VNIR | B01, B02, B03N | 15 м | Ургамал, Fe oxide, гадаргын ялгаа, рельеф |
| VNIR stereo | B03B | 15 м | Stereo/DEM чиглэлд ашиглаж болно; энэ workflow-д ихэвчлэн ашиглахгүй |
| SWIR | B04-B09 | 30 м | Clay, sericite, alunite/kaolinite, carbonate/Mg-OH alteration |
| TIR | B10-B14 | 90 м | Silica/quartz-rich lithology, дулааны литологийн ялгаа |

## Cloud ба image quality-ийн шийдвэр

| Cloud cover | Үнэлгээ | Ашиглах шийдвэр |
| --- | --- | --- |
| 0-5% | Маш сайн | Шууд ашиглахад тохиромжтой |
| 5-10% | Сайн | Ашиглаж болно; cloud/shadow mask хийх |
| 10-20% | Дунд | Болгоомжтой ашиглана |
| >20% | Эрсдэлтэй | Хувирал ялгахад тохиромж муутай |
| >30% | Муу | Ихэнхдээ ашиглахгүй |

Энэ датаны cloud cover 8% тул ашиглаж болно. Гэхдээ cloud яг лицензийн талбай дээр давхцаж байгаа эсэхийг VNIR 3N-2-1 болон SWIR 9-6-4 composite дээр заавал нүдээр шалгана.

Зураг 1. ASTER VNIR false color preview - B03N/B02/B01.

Зураг 2. ASTER SWIR preview - B09/B06/B04.
# 3. Ажлын хавтас, нэршил, файлын бүртгэл
QGIS project, raw data, index, interpretation файлуудыг нэг үндсэн project folder дотор хадгална. Файлуудыг задгай, олон газар тарааж хадгалбал VRT эвдэрч, “No such file or directory” алдаа гардаг.

| D:\ASTER_Project\ ├─ ASTER_Alteration_QGIS.qgz ├─ 01_raw\ │  └─ AST_L1B_00409052005043503_20250520190111(3).hdf ├─ 02_bands_geotiff\ ├─ 03_resampled\ ├─ 04_composites\ ├─ 05_indices\ ├─ 06_threshold\ ├─ 07_clip_license\ ├─ 08_layout_maps\ └─ 09_interpretation\ |
| --- |


| Folder | Юу хадгалах вэ |
| --- | --- |
| 01_raw | Эх HDF файл, өөрчлөхгүй хадгална |
| 02_bands_geotiff | B01-B14 single-band GeoTIFF |
| 03_resampled | 30 м болгосон B01_30m, B02_30m, B03N_30m |
| 04_composites | VNIR_3N_2_1.vrt, SWIR_9_6_4.vrt, TIR_14_12_10.vrt |
| 05_indices | NDVI, Ferric Iron, Clay, Advanced Argillic, Chlorite/Epidote, Silica |
| 06_threshold | Binary anomaly raster-ууд |
| 07_clip_license | Лицензийн хилээр тайрсан raster/vector |
| 08_layout_maps | PDF, PNG, JPG layout map |
| 09_interpretation | Target score raster, target polygon, lineament, note |

# 4. QGIS project setup
- QGIS нээнэ.
- Project -> Save As... дарж D:\ASTER_Project\ASTER_Alteration_QGIS.qgz гэж хадгална.
- Project CRS-ийг доод баруун булангаас EPSG:32647 - WGS 84 / UTM zone 47N болгож шалгана.
- View -> Panels -> Browser болон Processing -> Toolbox-ийг асаана.
- Browser panel дээр D:\ASTER_Project хавтсаа олж 01_raw доторх HDF файлыг шалгана.
## QGIS project-ийн үндсэн тохиргоо

| Тохиргоо | Утга |
| --- | --- |
| Project CRS | EPSG:32647 - WGS 84 / UTM zone 47N |
| Project file | D:\ASTER_Project\ASTER_Alteration_QGIS.qgz |
| Output mode | Raster export хийхдээ Raw data |
| Base map | OpenStreetMap байж болно, гэхдээ эцсийн geologic interpretation-д зөвхөн суурь харагдац |

# 5. HDF доторх B01-B14 band-уудыг GeoTIFF болгох
HDF файл дээр шууд ажиллаж болох ч үйлдвэрлэлийн workflow-д band бүрийг GeoTIFF болгож хадгална.
- Browser panel дээр AST_L1B...hdf-г дэлгэнэ.
- Доорх subdataset-үүдийг QGIS canvas руу нэмнэ: ImageData1, ImageData2, ImageData3N, ImageData4 ... ImageData14.
- Layer дээр Right click -> Export -> Save As...
- Output mode = Raw data, Format = GeoTIFF, CRS = EPSG:32647 гэж тавина.
- File name дээр 02_bands_geotiff хавтас руу нэр өгнө. Жишээ: D:\ASTER_Project\02_bands_geotiff\B01.tif
- Add saved file to map чагттай байж болно.
- OK дарж хадгална. Дараагийн band-уудыг ижил аргаар хадгална.

| D:\ASTER_Project\02_bands_geotiff\B01.tif D:\ASTER_Project\02_bands_geotiff\B02.tif D:\ASTER_Project\02_bands_geotiff\B03N.tif D:\ASTER_Project\02_bands_geotiff\B04.tif ... D:\ASTER_Project\02_bands_geotiff\B14.tif |
| --- |

## NoData values идэвхгүй байвал яах вэ?
Export цонх дээр NoData values идэвхгүй байвал энэ шатанд асуудал биш. Эхлээд Raw data GeoTIFF болгож хадгална. Дараа нь шаардлагатай бол Raster -> Conversion -> Translate ашиглан 0 эсвэл -9999 NoData оноож болно.

Зураг 3. GeoTIFF export хийх жишээ. Raw data, GeoTIFF, EPSG:32647 тохиргоо зөв.
# 6. Single-band засвар ба VRT алдааг урьдчилан сэргийлэх
ASTER band бүр single-band байх ёстой. Заримдаа QGIS export хийхдээ alpha/mask band нэмж 2-band GeoTIFF үүсгэдэг. Энэ үед composite буруу өнгөтэй, хэт ногоон эсвэл улаан харагдана.
## Band count шалгах
- Layer дээр Right click -> Properties -> Information орно.
- Bands хэсгээс Band count-г харна.
- B01, B02, B03N, B04 ... бүгд Band count: 1 байх ёстой.
## Хэрэв B01 хоёр band-тэй бол засах
- Raster -> Conversion -> Translate / Convert format нээнэ.
- Input layer = B01 гэж сонгоно.
- Output = D:\ASTER_Project\02_bands_geotiff\B01_single.tif
- Additional command-line parameters дээр -b 1 гэж бичнэ.
- Run дарна.
- Үүссэн B01_single.tif дээр Properties -> Information -> Band count = 1 гэж шалгана.

| -b 1 |
| --- |

B02, B03N, B04-B14 дээр ч мөн ижил шалгалт хийнэ. Цаашдын бүх тооцоонд single-band файлуудыг ашиглана.

Зураг 4. B01 хоёр band-тэй орсон жишээ. Ийм үед -b 1 ашиглаж single-band болгоно.
# 7. VNIR, SWIR, TIR composite үүсгэх
Composite нь ratio хийхээс өмнө cloud, рельеф, гадаргын ялгаа, структур, боломжит anomaly-г харахад ашиглана.
## 7.1 VNIR false color - 3N-2-1
- Raster -> Miscellaneous -> Build Virtual Raster нээнэ.
- Input layers сонгохдоо дарааллыг заавал B03N, B02, B01 гэж сонгоно.
- Place each input file into a separate band гэдгийг чагтална.
- Output = D:\ASTER_Project\04_composites\VNIR_3N_2_1.vrt
- Run дарна.
- Үүссэн layer дээр Properties -> Symbology: Render type = Multiband color, Red=Band 1, Green=Band 2, Blue=Band 3

| Input order: 1) B03N_single.tif or B03N_30m.tif 2) B02_single.tif  or B02_30m.tif 3) B01_single.tif  or B01_30m.tif  Output: D:\ASTER_Project\04_composites\VNIR_3N_2_1.vrt |
| --- |

## 7.2 SWIR alteration composite - 9-6-4
- Raster -> Miscellaneous -> Build Virtual Raster нээнэ.
- Input order = B09, B06, B04.
- Place each input file into a separate band чагтална.
- Output = D:\ASTER_Project\04_composites\SWIR_9_6_4.vrt
- Symbology: Red=Band 1, Green=Band 2, Blue=Band 3.

| B09_single.tif B06_single.tif B04_single.tif Output: 04_composites\SWIR_9_6_4.vrt |
| --- |

## 7.3 TIR lithology composite - 14-12-10

| B14_single.tif B12_single.tif B10_single.tif Output: 04_composites\TIR_14_12_10.vrt |
| --- |

TIR 90 м resolution-тэй тул жижиг объектыг биш, том lithology/silica trend-ийг харна.

Зураг 5. VNIR_3N_2_1 composite зөв үүсэж харагдсан жишээ.
# 8. Pixel/blocky харагдалт, resampling ба display тохиргоо
Pixel blocky харагдах нь заавал алдаа биш. Томруулж харвал ASTER-ийн 15 м, 30 м, 90 м pixel нь блок шиг харагдана. Гэхдээ display resampling болон зөв resolution тааруулах шаардлагатай.
## 8.1 Зөв resolution сонгох

| Зорилго | Ажиллах resolution |
| --- | --- |
| VNIR-only product | 15 м |
| SWIR-only product | 30 м |
| TIR-only product | 90 м |
| VNIR + SWIR ratio/composite | 30 м болгож тааруулах |
| Бүх band хамтарсан PCA/MNF | 30 м эсвэл 90 м; зорилгоос хамаарна |

## 8.2 B01, B02, B03N-ийг 30 м болгох
- Processing Toolbox -> QGIS -> Raster tools -> Align rasters нээнэ.
- Reference layer = B04_single.tif сонгоно. B04 нь SWIR 30 м тул reference болгоно.
- Override reference CRS = EPSG:32647.
- Override reference cell size X = 30, Y = 30.
- Input layer(s) хэсэгт B01_single, B02_single, B03N_single-ийг сонгоно.
- Configure Raster... дээр input бүрийн output файлыг өгнө: B01_30m.tif, B02_30m.tif, B03N_30m.tif.
- Resampling method сонголт Align Rasters цонхонд харагдахгүй бол Advanced буюу tool-н дээд/доод scroll-ийг шалгана. Хэрэв байхгүй бол дараагийн хэсгийн Build Virtual Raster advanced resampling эсвэл GDAL Warp ашиглаж болно.
- Continuous spectral data тул Bilinear хамгийн тохиромжтой. Nearest Neighbour нь classification/discrete layer-д илүү тохиромжтой.

| Input: B03N_single.tif Reference: B04_single.tif Cell size X/Y: 30 / 30 Output: D:\ASTER_Project\03_resampled\B03N_30m.tif  Давтах: B02_single.tif -> B02_30m.tif B01_single.tif -> B01_30m.tif |
| --- |

## 8.3 Nearest Neighbour эсвэл Bilinear?

| Арга | Хэзээ хэрэглэх вэ | Энэ ажилд |
| --- | --- | --- |
| Nearest Neighbour | Ангиллын map, discrete утга, DN-г огт өөрчлөхгүй хадгалах шаардлагатай үед | Зөвхөн display/VRT эсвэл classification-д |
| Bilinear | VNIR/SWIR/TIR зэрэг continuous spectral data-д | Ихэвчлэн зөв сонголт |
| Cubic | Илүү smooth харагдах ч утгыг илүү их интерполяцилна | Зөвхөн display/preview-д болгоомжтой |

## 8.4 Blocky харагдалтыг багасгах display тохиргоо
- Layer дээр Properties -> Symbology орно.
- Min/Max Value Settings = Cumulative count cut 2-98% тохируулж Apply дарна.
- Layer Rendering -> Resampling хэсэгт Zoomed in/out = Bilinear эсвэл Cubic болгож үзнэ.
- Энэ нь зөвхөн харагдац сайжруулна; анхны pixel утгыг өөрчлөхгүй.
# 9. Лицензийн хилээр талбайг тасдаж авах
Судалгааны лицензийн хилээр raster болон index-үүдийг clip хийснээр файл жижиг, map тодорхой, QA/QC илүү хялбар болно.
- Лицензийн хил vector файлаа Layer -> Add Layer -> Add Vector Layer ашиглан нэмнэ.
- Лицензийн хил дээр Right click -> Properties -> Information -> CRS-г шалгана.
- Хэрэв өөр CRS бол Right click -> Export -> Save Features As... ашиглаж EPSG:32647 болгож хадгална.
- Raster -> Extraction -> Clip Raster by Mask Layer нээнэ.
- Input layer = clip хийх raster, Mask layer = license_area_32647.
- Assign NoData = -9999 гэж өгч болно.
- Crop to cutline / Match extent to mask layer байгаа бол чагтална. Зарим QGIS interface-д энэ нь Advanced эсвэл checkbox хэлбэрээр харагдана.
- Output = D:\ASTER_Project\07_clip_license\<нэр>_clip.tif
- Run дарна.
## Batch clip хийх
Олон raster-ийг нэг дор тайрах бол Clip Raster by Mask Layer цонхны Run as Batch Process... товчийг ашиглана. Input layer баганад B01-B14 эсвэл index бүрийг, Mask layer баганад нэг лицензийн хил, Output баганад тус тусын нэрийг өгнө.
# 10. NDVI гаргах ба ургамлын нөлөө хянах
NDVI нь өөрөө геологийн хувирал биш. Харин ургамлын нөлөө өндөр хэсгийг ялгаж, Fe oxide/clay/silica anomaly-г ургамалтай андуурахаас хамгаална.
## NDVI томъёо

| NDVI = (B03N - B02) / (B03N + B02)  QGIS Raster Calculator expression: ("B03N_30m@1" - "B02_30m@1") / ("B03N_30m@1" + "B02_30m@1")  Output: D:\ASTER_Project\05_indices\NDVI.tif |
| --- |


| NDVI утга | Тайлбар | Геологийн тайлбарт ашиглах нь |
| --- | --- | --- |
| < 0 | Ус, сүүдэр | Хасах/болгоомжлох |
| 0-0.2 | Нүцгэн хөрс, чулуулга | Геологийн interpretation хийхэд тохиромжтой |
| 0.2-0.4 | Сийрэг ургамал | Болгоомжтой |
| > 0.4 | Ургамлын нөлөө өндөр | Хувирал гэж шууд тайлбарлахгүй |

## NDVI legend хийх
- NDVI layer дээр Right click -> Properties -> Symbology орно.
- Render type = Singleband pseudocolor.
- Min = -1, Max = 1.
- Classes = 4 эсвэл 5.
- Classify дарна.
- Value/Label-үүдийг хүснэгтийн дагуу засна: <0 Ус/сүүдэр, 0-0.2 Нүцгэн хөрс/чулуулаг, 0.2-0.4 Сийрэг ургамал, >0.4 Ургамлын нөлөө өндөр.
- Apply -> OK дарна.

Зураг 7. NDVI symbology тохируулах жишээ.
# 11. Alteration index-үүд гаргах
Дараах index-үүдийг QGIS Raster Calculator-аар гаргана. Layer нэр QGIS дээр өөр байж болох тул expression-д өөрийн layer нэрийг зөв сонгоно.

| Index | Formula | Output нэр | Тайлбар |
| --- | --- | --- | --- |
| Ferric Iron / Fe oxide | B02 / B01 | Ferric_Iron_B02_B01.tif | Гематит, гётит, лимонит, gossan байж болох Fe oxide anomaly |
| Clay / Al-OH | B05 / B06 | Clay_AlOH_B05_B06.tif | Каолинит, иллит, смектит, серицит, Al-OH alteration |
| Sericite / Illite | B05 / B06 | Sericite_Illite_B05_B06.tif | Clay index-тэй ижил formula-г phyllic context-д ашиглаж болно |
| Advanced Argillic | B04 / B06 | Advanced_Argillic_B04_B06.tif | Alunite/kaolinite/pyrophyllite боломжит acid alteration |
| Chlorite/Epidote/Mg-OH | B07 / B08 | Chlorite_Epidote_MgOH_B07_B08.tif | Propylitic halo, chlorite/epidote/carbonate response |
| Carbonate/Mg-OH | B07 / B08 | Carbonate_MgOH_B07_B08.tif | Carbonate ба Mg-OH-г дан ratio-оор бүрэн салгахгүй |
| Silica | B13 / B12 | Silica_B13_B12.tif | TIR 90 м; silica/quartz-rich том бүсэд |
| Quartz-rich check | B14 / B12 | Quartz_Rich_B14_B12.tif | Silica тайлбарыг нэмэлтээр шалгах |

## Ferric Iron example

| Raster -> Raster Calculator Expression: "B02_single@1" / "B01_single@1" Output: D:\ASTER_Project\05_indices\Ferric_Iron_B02_B01.tif |
| --- |

Ferric Iron-д Reds color ramp хамгийн ойлгомжтой. Өндөр утга тод улаан болно.

Зураг 8. Ferric Iron layer-ийн улаан өнгийн display жишээ.
## Clay / Al-OH example

| "B05_single@1" / "B06_single@1" Output: 05_indices\Clay_AlOH_B05_B06.tif |
| --- |

## Silica example

| "B13_single@1" / "B12_single@1" Output: 05_indices\Silica_B13_B12.tif |
| --- |

# 12. Өнгө, legend, layout map бэлтгэх
Index layer-үүдийг ойлгомжтой өнгөөр харах нь геологи мэдэхгүй хүн target сонгоход маш чухал. Доорх өнгөний дүрмийг дагана.

| Layer | Санал болгох color ramp | Өндөр утгын өнгө | Тайлбар |
| --- | --- | --- | --- |
| Ferric Iron | Reds | Тод улаан | Fe oxide өндөр |
| Clay / Sericite | Magma / Spectral / Turbo | Шар/улбар/ягаан тод | Clay/sericite anomaly өндөр |
| Chlorite/Epidote | Greens | Тод ногоон | Propylitic halo байж болно |
| Silica | Greys / Cividis / Viridis | Цайвар/тод | Silica/quartz-rich zone |
| NDVI | RdYlGn эсвэл custom | Ногоон | Ургамал их |
| Target score | Reds / Turbo | Улаан/тод | Target priority өндөр |

## Layout map хийх алхам
- Project -> New Print Layout дарна.
- Layout нэр өгнө. Жишээ: Porphyry_Cu_Au_Target_Map.
- Add Map ашиглаж картаа оруулна.
- Add Legend ашиглаж тайлбараа оруулна. Legend Items-ээс хэрэггүй layer-үүдийг устгана.
- Add Scale Bar, Add North Arrow, Add Label оруулна.
- Гарчиг, CRS, data source, cloud/QA note бичнэ.
- Layout -> Export as PDF эсвэл Export as Image ашиглан 08_layout_maps дотор хадгална.

| Map title жишээ: ASTER-Based Porphyry Cu-Au Target Map Ferric Iron + Clay/Sericite + Chlorite/Epidote + Silica  Footer note: ASTER alteration products are spectral anomalies only. Field validation required. |
| --- |

# 13. Порфир Cu-Au target pattern ба scoring
Порфир Cu-Au target map-ийн үндсэн зорилго нь хэд хэдэн alteration anomaly-ийн давхцал, бүслүүр, структуртай холбоог нэгтгэж target priority гаргах юм.
## Порфирийн сайн target pattern

| Clay/Sericite өндөр + Fe oxide өндөр + гадна талд Chlorite/Epidote halo + заримдаа Silica anomaly + fault/lineament эсвэл intrusive/circular feature-тэй давхцах |
| --- |


| Хувирал / шинж | QGIS layer | Порфирийн утга |
| --- | --- | --- |
| Clay/Sericite өндөр | Clay_AlOH_B05_B06 эсвэл Sericite_Illite_B05_B06 | Phyllic/sericitic төв, argillic cap байж болно |
| Fe oxide өндөр | Ferric_Iron_B02_B01 | Исэлдсэн пирит, gossan, oxidation zone |
| Chlorite/Epidote halo | Chlorite_Epidote_MgOH_B07_B08 | Propylitic гадна halo |
| Silica anomaly | Silica_B13_B12 | Quartz-rich/silicified zone |
| Lineament | Lineaments.gpkg | Хагарал, структурын control |
| Intrusive/circular feature | Circular_Features.gpkg эсвэл geology layer | Intrusive center/porphyry-related morphology |

## 13.1 Binary anomaly layer үүсгэх
Index бүрийн өндөр anomaly-г 1, бусдыг 0 болгоно. Threshold-г статистикаар сонгох нь зөв.

| Threshold сонгох энгийн арга: Threshold = Mean + 1.5 × Standard deviation  Жишээ: "Ferric_Iron_B02_B01@1" > 1.10 -> Ferric_binary.tif "Clay_AlOH_B05_B06@1" > 1.15 -> Clay_binary.tif "Chlorite_Epidote_MgOH_B07_B08@1" > 1.10 -> Chlorite_binary.tif "Silica_B13_B12@1" > 1.05 -> Silica_binary.tif |
| --- |

## 13.2 Porphyry Target Score raster

| Raster Calculator expression: ("Clay_binary@1" * 2) + ("Ferric_binary@1" * 1) + ("Chlorite_binary@1" * 1) + ("Silica_binary@1" * 1)  Output: D:\ASTER_Project\09_interpretation\Porphyry_Target_Score.tif |
| --- |


| Score | Тайлбар |
| --- | --- |
| 0-1 | Сул |
| 2 | Дунд |
| 3 | Сайн target |
| 4 | Өндөр сонирхолтой |
| 5 | Маш өндөр сонирхолтой |

## 13.3 Target polygon үүсгэх
- Raster Calculator-аар Porphyry_Target_Score >= 3 гэсэн binary raster үүсгэнэ.
- Raster -> Conversion -> Polygonize ашиглаж polygon болгоно.
- Attribute table дээр DN = 1 polygon-уудыг үлдээнэ, DN = 0-г устгана.
- Жижиг noise polygon-уудыг area_ha < 0.5 эсвэл < 1 гэж устгаж болно.
## 13.4 Target polygon-д оноо өгөх attribute талбарууд

| Field name | Type | Утга / дүрэм |
| --- | --- | --- |
| clay | Integer | 0 = байхгүй, 2 = Clay/Sericite anomaly байна |
| ferric | Integer | 0 = байхгүй, 1 = Fe oxide anomaly байна |
| chlorite | Integer | 0 = байхгүй, 1 = Chlorite/Epidote halo байна |
| silica | Integer | 0 = байхгүй, 1 = Silica anomaly байна |
| lineament | Integer | 0 = байхгүй, 1 = fault/lineament-тэй давхцсан |
| intrusive | Integer | 0 = байхгүй, 1 = intrusive/circular feature-тэй |
| target_score | Integer | Нийт оноо |
| confidence | Text | Low / Moderate / High |
| note | Text | Тайлбар, field check note |

### 13.5 Field нэмэх яг хаана хийх вэ?
- Layers panel дээр Porphyry_Final_Target_Polygons layer-ийг сонгоно. Raster layer биш, polygon vector layer байх ёстой.
- Right click -> Open Attribute Table.
- Toggle Editing буюу шар харандаа icon дарна.
- New Field товч дарна.
- Name = clay, Type = Whole number / Integer, Length = 1 эсвэл 2, Precision = 0 гэж оруулаад OK дарна.
- Дараагийн талбаруудыг мөн адил нэмнэ: ferric, chlorite, silica, lineament, intrusive, target_score, confidence, note.
### 13.6 Нийт оноо бодох

| Field Calculator -> Update existing field: target_score Expression: "clay" + "ferric" + "chlorite" + "silica" + "lineament" + "intrusive" |
| --- |

### 13.7 Confidence ангилах

| Field Calculator -> Update existing field: confidence Expression: CASE WHEN "target_score" >= 5 THEN 'High' WHEN "target_score" >= 3 THEN 'Moderate' ELSE 'Low' END |
| --- |


| Target score | Confidence | Тайлбар |
| --- | --- | --- |
| 0-2 | Low | Давхцал бага, сул target |
| 3-4 | Moderate | Боломжит target, нэмэлт шалгалт шаардлагатай |
| 5-7 | High | Өндөр ач холбогдолтой target, field check priority |

# 14. Эцсийн бүтээгдэхүүн, QA/QC ба архивлах
Ажил дууссаны дараа дараах deliverable багц заавал бүрдсэн байна. Энэ нь жил/улирлын эцсийн хайгуулын тайлан, дотоод шийдвэр, field check төлөвлөлтөд ашиглагдана.

| Бүтээгдэхүүн | Файл нэрийн жишээ | QA шалгах зүйл |
| --- | --- | --- |
| Raw HDF | 01_raw/AST_L1B_....hdf | Эх файл хадгалагдсан, өөрчлөгдөөгүй |
| Single-band bands | 02_bands_geotiff/B01_single.tif ... B14_single.tif | Band count = 1, CRS = EPSG:32647 |
| Resampled bands | 03_resampled/B01_30m.tif ... | Cell size 30 м, reference grid зөв |
| Composites | VNIR_3N_2_1.vrt, SWIR_9_6_4.vrt, TIR_14_12_10.vrt | Band order зөв, эх файл зөөгдөөгүй |
| Indices | Ferric_Iron, Clay_AlOH, Advanced_Argillic, Chlorite, Silica, NDVI | Formula зөв, NoData/edge нөлөө шалгасан |
| Clipped products | *_clip.tif | Лицензийн хилтэй давхцсан, гаднах хэсэг NoData |
| Target score | Porphyry_Target_Score.tif | 0-5 score зөв гарсан |
| Target polygons | Porphyry_Final_Target_Polygons.gpkg | Attribute fields, score, confidence, note бөглөсөн |
| Final map | 08_layout_maps/Porphyry_Cu_Au_Target_Map.pdf/png | Legend, scale bar, north arrow, CRS, note орсон |
| QA/QC report | QA_QC_Report.docx/pdf | Cloud, QA, limitation, accepted status орсон |

## Эцсийн QA/QC checklist
[ ] B01-B14 бүгд single-band эсэхийг шалгасан.
[ ] VNIR/SWIR/TIR composite band order зөв эсэхийг шалгасан.
[ ] Cloud/shadow/bright surface хэсгийг VNIR/SWIR дээр нүдээр шалгасан.
[ ] NDVI > 0.3 эсвэл > 0.4 хэсгийг болгоомжтой тайлбарласан.
[ ] Лицензийн хилээр бүх шаардлагатай raster/index clip хийгдсэн.
[ ] Ferric/Clay/Chlorite/Silica index-үүдийн threshold үндэслэлтэй сонгогдсон.
[ ] Target score raster болон polygon үүссэн.
[ ] Target polygon attribute table-д clay, ferric, chlorite, silica, lineament, intrusive, target_score, confidence, note талбарууд бүрэн байна.
[ ] Final map PDF/PNG export хийсэн.
[ ] Field verification required гэсэн disclaimer map/report дээр орсон.
# 15. Troubleshooting ба түгээмэл алдаа

| Асуудал | Шалтгаан | Шийдэл |
| --- | --- | --- |
| NoData values идэвхгүй байна | HDF metadata-д NoData тодорхой заагдаагүй эсвэл export цонх disabled | Эхлээд Raw data export хийнэ. Дараа Translate-аар NoData оноож болно. |
| B01 2 band-тэй орж ирлээ | Alpha/mask band хамт хадгалагдсан | Raster -> Conversion -> Translate, Additional parameter: -b 1 |
| VNIR composite хэт ногоон харагдаж байна | Band order буруу эсвэл 2-band input орсон | Input order B03N, B02, B01; single-band файлуудыг ашиглана. |
| VRT нээгдэхгүй / No such file | VRT эх TIFF файлуудын absolute path-г заасан, файл зөөгдсөн | TIFF-үүдээ буцааж байрлуулах эсвэл VRT-г дахин үүсгэх. |
| Pixel blocky харагдаж байна | Zoom хэт ойр, nearest display resampling, resolution ялгаа | Zoom out, Layer Rendering -> Resampling Bilinear/Cubic, шаардлагатай бол resample. |
| Align Rasters output file алдаа | Input бүрийн output path тохируулаагүй | Input layers хэсэг -> Configure Raster -> output бүрийг 03_resampled-д заах. |
| Resampling method харагдахгүй | Tool interface/scroll/хувилбарын ялгаа | Цонх томруулах, Advanced/scroll шалгах, эсвэл GDAL Warp/Build VRT advanced resampling ашиглах. |
| Crop to cutline харагдахгүй | Advanced хэсэгт нуугдсан эсвэл цонх багассан | Clip Raster by Mask Layer цонхыг томруулж scroll хийх, Processing Toolbox-оос нээх. |
| Ferric Iron бүхэлдээ улаан харагдана | Min/max stretch буруу, color ramp continuous | Cumulative count cut 2-98%, Reds ramp, high values-д transparency/threshold ашиглах. |

## Аюулгүй тайлбар хийх зарчим
[ ] ASTER anomaly-г шууд орд, хүдэр гэж нэрлэхгүй.
[ ] Цайвар хэсгийг silica гэж шууд тайлбарлахгүй; cloud/salt/bright soil/slope lighting шалгана.
[ ] B07/B08 нь carbonate ба chlorite/epidote response-г давхар өгч болох тул geology map ашиглана.
[ ] TIR silica 90 м тул жижиг quartz vein-г найдвартай барихгүй.
[ ] Порфир target нь field checking хийх priority болохоос баталгаа биш.
# Хавсралт A. Томъёоны хурдан лавлах

| Бүтээгдэхүүн | Томъёо | Output |
| --- | --- | --- |
| NDVI | (B03N - B02) / (B03N + B02) | NDVI.tif |
| Ferric Iron | B02 / B01 | Ferric_Iron_B02_B01.tif |
| Clay / Al-OH | B05 / B06 | Clay_AlOH_B05_B06.tif |
| Advanced Argillic | B04 / B06 | Advanced_Argillic_B04_B06.tif |
| Chlorite/Epidote/Mg-OH | B07 / B08 | Chlorite_Epidote_MgOH_B07_B08.tif |
| Carbonate/Mg-OH | B07 / B08 | Carbonate_MgOH_B07_B08.tif |
| Silica | B13 / B12 | Silica_B13_B12.tif |
| Quartz-rich check | B14 / B12 | Quartz_Rich_B14_B12.tif |
| Porphyry score | Clay*2 + Ferric + Chlorite + Silica | Porphyry_Target_Score.tif |

# Хавсралт B. Ажил хүлээлцэх бүртгэлийн загвар

| Огноо | Ажил | Файл / output | Шалгасан хүн | Төлөв |
| --- | --- | --- | --- | --- |
|  | HDF raw data бүртгэх | 01_raw |  |  |
|  | B01-B14 export | 02_bands_geotiff |  |  |
|  | Single-band QA | Band count = 1 |  |  |
|  | Composite үүсгэх | VNIR/SWIR/TIR |  |  |
|  | Cloud/NDVI QA | QA note |  |  |
|  | Index гаргах | 05_indices |  |  |
|  | Clip хийх | 07_clip_license |  |  |
|  | Target score/polygon | 09_interpretation |  |  |
|  | Final map export | 08_layout_maps |  |  |
|  | QA/QC report | report docx/pdf |  |  |

# Эцсийн анхааруулга
Энэ зааврыг дагаж гаргасан бүтээгдэхүүн нь ASTER L1B spectral screening-ийн урьдчилсан хайгуулын бүтээгдэхүүн юм. Порфир Cu-Au, эпитермаль Au-Ag, скарн, polymetallic vein системийн боломжит target area-г тодруулахад тусална. Гэвч эцсийн геологийн шийдвэр, хөрөнгө оруулалт, өрөмдлөгийн шийдвэрийг зөвхөн энэ зураг дээр үндэслэн гаргахгүй. Геологийн зураглал, дээжлэл, геохими, геофизик болон газар дээрх баталгаажуулалт шаардлагатай.
