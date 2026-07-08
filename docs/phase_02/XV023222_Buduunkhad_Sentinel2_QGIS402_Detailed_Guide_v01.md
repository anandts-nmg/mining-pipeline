<!-- source: XV023222_Buduunkhad_Sentinel2_QGIS402_Detailed_Guide_v01.docx (converted from Word; canonical form for LLM ingestion) -->

# Sentinel-2 боловсруулах дэлгэрэнгүй заавар
QGIS 4.0.2 | XV023222 Buduunkhad | EPSG:32647
Энэ баримт нь өмнөх зааврын бүх агуулгыг алгасалгүй DOCX хэлбэрт оруулсан хувилбар бөгөөд Sentinel-2 raster-ийг шалгах, resample/reproject хийх, mask үүсгэх, composite болон lithology/alteration index гаргах ажлыг QGIS 4.0.2 дээр хийхэд зориулагдсан.
Гол output файлууд:

| XV023222_​Buduunkhad_​Sentinel2_​NaturalRGB_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​Geology_​RGB_​B12_​B08_​B03_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​FalseColor_​B08_​B04_​B03_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​LithologyIndex_​B11B12_​B08B11_​B04B03_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​NDVI_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​NDWI_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​VegetationMask_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​WaterShadowMask_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​QAQC_​Log.xlsx |
| --- |

# 1. Ажлын folder бүтэц бэлдэх
QGIS project-ийн дотор дараах folder бүтэц үүсгэнэ.

| XV023222_​Buduunkhad/​ \|   \|         \|   \| |
| --- |

QGIS project файлыг дараах нэрээр хадгална.

| XV023222_​Buduunkhad_​Sentinel2_​Processing_​QGIS4_​v01.qgz |
| --- |

# 2. QGIS 4.0.2 project тохируулах
QGIS 4.0.2 нээнэ. Дээд цэснээс дараах тохиргоог хийнэ.

|  |
| --- |

CRS-ийг дараах байдлаар тохируулна.

| EPSG:32647 WGS 84 /​ UTM zone 47N |
| --- |

Дараа нь project файлыг хадгална.

|  |
| --- |

# 3. Sentinel raster status шалгах
## 3.1 Raster файлуудыг QGIS дээр оруулах
QGIS Browser panel эсвэл Layer цэсээр Sentinel-2 raster файлуудаа нэмнэ.

|  |
| --- |

Оруулах raster-ууд:

| B02 Blue B03 Green B04 Red B08 NIR B11 SWIR1 B12 SWIR2 |
| --- |

Хэрэв таны файл аль хэдийн composite буюу derivative raster бол зөвхөн status шалгаад, дахин Sen2Cor хийх шаардлагагүй.
## 3.2 Raster CRS шалгах
Layer panel дээр raster дээрээ right click хийнэ.

|  |
| --- |

Шалгах зүйл:

| CRS: EPSG:32647 эсэх Pixel size: 10 m эсэх Extent: license boundary-тай давхцаж байгаа эсэх Band count NoData value Data type |
| --- |

Хэрэв CRS өөр байвал дараагийн Reproject алхамд засна.
## 3.3 Pixel size шалгах
Raster layer дээр дараах замаар мэдээллийг шалгана.

|  |
| --- |

Доорх мэдээллийг харна.

| Pixel Size X Pixel Size Y |
| --- |

Хүссэн утга:

| 10 m × 10 m |
| --- |

B02, B03, B04, B08 нь ихэвчлэн 10 m байдаг. B11, B12 нь Sentinel-2 дээр 20 m байдаг тул 10 m grid рүү resample хийх шаардлагатай.
# 4. SNAP дээр L1C → L2A боловсруулах
Энэ алхам зөвхөн raw Sentinel-2 L1C SAFE folder байгаа тохиолдолд хийнэ. Хэрэв аль хэдийн L2A бүтээгдэхүүнтэй бол энэ алхмыг алгасаж болно.
## 4.1 SNAP 13.0.0 дээр Sentinel product нээх
SNAP нээнэ.

|  |
| --- |

Sentinel-2 SAFE folder-ийн доторх product файлыг сонгоно. Ихэвчлэн:

| MTD_​MSIL1C.xml |
| --- |

эсвэл SAFE product folder-ийг сонгож болно.
## 4.2 Sen2Cor ажиллуулах
SNAP дээр дараах замаар Sen2Cor ажиллуулна.

|  |
| --- |

Тохиргоо:

| Processing resolution: 10 m Output product type: L2A Atmospheric correction: Enable Scene classification: Enable |
| --- |

Run дарна. Output нь L2A product байна.

| L2A product |
| --- |

L2A product-оос дараах band-уудыг ашиглана. 10 m bands:

| B02 Blue B03 Green B04 Red B08 NIR |
| --- |

20 m bands:

| B11 SWIR1 B12 SWIR2 |
| --- |

# 5. B11, B12 band-уудыг 10 m болгон resample хийх
B11, B12 нь 20 m resolution-той тул 10 m raster-уудтай яг тааруулахын тулд resample хийнэ.
## 5.1 Processing Toolbox нээх
QGIS дээр дараах цэсийг нээнэ.

|  |
| --- |

Search хэсэгт дараах үгсээр хайж болно.

| Resampling Warp |
| --- |

## 5.2 Warp / Reproject ашиглан resample хийх
Дээд цэсээр:

|  |
| --- |

эсвэл Processing Toolbox дотроос:

|  |
| --- |

Input raster:

| B11 |
| --- |

Тохиргоо:

| Source CRS: raster-ийн одоогийн CRS Target CRS: EPSG:32647 Resampling method: Bilinear Output file resolution: 10 NoData: эх raster-ийн NoData утгыг хадгалах |
| --- |

Output нэр:

| XV023222_​Buduunkhad_​Sentinel2_​B11_​SWIR1_​10m_​EPSG32647_​v01.tif |
| --- |

B12 дээр мөн адил хийнэ. Output нэр:

| XV023222_​Buduunkhad_​Sentinel2_​B12_​SWIR2_​10m_​EPSG32647_​v01.tif |
| --- |

Анхаарах зүйл: Continuous reflectance raster тул Bilinear тохиромжтой. Categorical raster биш учраас Nearest neighbour хэрэглэх шаардлагагүй.
# 6. Бүх raster-ийг EPSG:32647 руу reproject хийх
Хэрэв raster-ууд аль хэдийн EPSG:32647 байвал энэ алхамд зөвхөн шалгалт хийнэ. Хэрэв өөр CRS байвал бүгдийг reproject хийнэ.

|  |
| --- |

Тохиргоо:

| Target CRS: EPSG:32647 Resampling method: Bilinear Output resolution: 10 m |
| --- |

Output нэрний бүтэц:

| XV023222_​Buduunkhad_​Sentinel2_​B02_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​B03_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​B04_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​B08_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​B11_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​B12_​EPSG32647_​v01.tif |
| --- |

# 7. License boundary-гаар clip хийх
Боловсруулалт license талбайн хүрээнд хийгдэх ёстой тул raster-уудыг boundary polygon-оор clip хийнэ.
## 7.1 Clip Raster by Mask Layer
QGIS дээр:

|  |
| --- |

Input layer:

| Sentinel band raster |
| --- |

Mask layer:

| License boundary polygon |
| --- |

Тохиргоо:

| Source CRS: EPSG:32647 Target CRS: EPSG:32647 Crop to cutline: Yes Keep resolution of input raster: Yes Assign NoData: Yes NoData value: -9999 |
| --- |

Output нэр:

| XV023222_​Buduunkhad_​Sentinel2_​B02_​Clip_​EPSG32647_​v01.tif |
| --- |

Энэ алхмыг B02, B03, B04, B08, B11, B12 дээр давтана.
# 8. NDVI үүсгэх
NDVI нь vegetation-ийг ялгахад ашиглагдана.
## 8.1 Raster Calculator нээх

|  |
| --- |

Expression хэсэгт:

| ("B08@1" - "B04@1") /​ ("B08@1" + "B04@1") |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​NDVI_​EPSG32647_​v01.tif |
| --- |

Output CRS:

| EPSG:32647 |
| --- |

Extent:

| License boundary clipped raster extent |
| --- |

Pixel size:

| 10 m |
| --- |

## 8.2 NDVI symbology тохируулах
NDVI raster дээр right click:

|  |
| --- |

Render type:

| Singleband pseudocolor |
| --- |

Range:

| -1 to +1 |
| --- |

Тайлбар:

| NDVI > 0.3    vegetation NDVI 0.1–0.3  sparse vegetation /​ mixed ground NDVI < 0.1    bare ground, rock, soil, water, shadow |
| --- |

# 9. Vegetation mask үүсгэх
Vegetation-ийн нөлөөг lithology болон alteration interpretation-оос хасах зорилготой.
Raster Calculator:

|  |
| --- |

Expression:

| ("XV023222_​Buduunkhad_​Sentinel2_​NDVI_​EPSG32647_​v01@1" > 0.3) |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​VegetationMask_​EPSG32647_​v01.tif |
| --- |

Үүсэх утга:

| 1 = vegetation 0 = non-vegetation |
| --- |

Хэрэв талбай хуурай, ургамал багатай бол threshold-ийг багасгаж болно. Жишээ:

| NDVI > 0.25 |
| --- |

# 10. NDWI үүсгэх
NDWI нь water body болон чийгтэй pixel ялгахад ашиглагдана.
Raster Calculator expression:

| ("B03@1" - "B08@1") /​ ("B03@1" + "B08@1") |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​NDWI_​EPSG32647_​v01.tif |
| --- |

## 10.1 Water mask үүсгэх
Raster Calculator:

| ("XV023222_​Buduunkhad_​Sentinel2_​NDWI_​EPSG32647_​v01@1" > 0.2) |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​WaterMask_​EPSG32647_​v01.tif |
| --- |

Үүсэх утга:

| 1 = water 0 = non-water |
| --- |

# 11. Shadow / dark pixel mask үүсгэх
Сүүдэр, бараан pixel нь lithology interpretation-ийг буруу харагдуулах эрсдэлтэй. B02 эсвэл B04 ашиглаж dark pixel ялгана.
Жишээ threshold:

| B04 < 0.05 |
| --- |

Гэхдээ Sentinel raster scale-аас хамаарна. Хэрэв reflectance 0–1 scale-тай бол:

| "B04@1" < 0.05 |
| --- |

Хэрэв DN 0–10000 scale-тай бол:

| "B04@1" < 500 |
| --- |

Raster Calculator expression:

| ("B04@1" < 0.05) |
| --- |

эсвэл DN scale бол:

| ("B04@1" < 500) |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​ShadowMask_​EPSG32647_​v01.tif |
| --- |

# 12. Water + shadow mask нэгтгэх
Water болон shadow pixel-ийг нэг mask болгон нэгтгэж болно.
Raster Calculator:

| ("WaterMask@1" = 1) OR ("ShadowMask@1" = 1) |
| --- |

QGIS Raster Calculator дээр Boolean expression-ийг заримдаа дараах байдлаар бичвэл илүү найдвартай.

| (("WaterMask@1" = 1) + ("ShadowMask@1" = 1)) > 0 |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​WaterShadowMask_​EPSG32647_​v01.tif |
| --- |

Үүсэх утга:

| 1 = water or shadow 0 = usable pixel |
| --- |

# 13. Natural RGB composite үүсгэх
Natural RGB нь хүний нүдэнд ойролцоо харагдах true color зураг юм.
Band composition:

| R = B04 G = B03 B = B02 |
| --- |

## 13.1 Build Virtual Raster ашиглах
QGIS дээр:

|  |
| --- |

Input layers дараах дарааллаар оруулна:

| B04 B03 B02 |
| --- |

Чухал тохиргоо:

| Place each input file into a separate band: Yes Resolution: Highest CRS: EPSG:32647 |
| --- |

Output VRT:

| XV023222_​Buduunkhad_​Sentinel2_​NaturalRGB_​EPSG32647_​v01.vrt |
| --- |

Дараа нь GeoTIFF болгоно.

|  |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​NaturalRGB_​EPSG32647_​v01.tif |
| --- |

# 14. Geological SWIR–NIR–Red composite үүсгэх
Энэ composite нь lithology, alteration, structural contrast харахад ашигтай.
Band composition:

| R = B12 G = B08 B = B03 |
| --- |

QGIS дээр:

|  |
| --- |

Input дараалал:

| B12 B08 B03 |
| --- |

Тохиргоо:

| Place each input file into a separate band: Yes Resolution: Highest /​ 10 m CRS: EPSG:32647 |
| --- |

Output VRT:

| XV023222_​Buduunkhad_​Sentinel2_​Geology_​RGB_​B12_​B08_​B03_​EPSG32647_​v01.vrt |
| --- |

GeoTIFF болгон export хийнэ.

|  |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​Geology_​RGB_​B12_​B08_​B03_​EPSG32647_​v01.tif |
| --- |

# 15. False color vegetation / lithology support composite үүсгэх
Band composition:

| R = B08 G = B04 B = B03 |
| --- |

Build Virtual Raster:

|  |
| --- |

Input дараалал:

| B08 B04 B03 |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​FalseColor_​B08_​B04_​B03_​EPSG32647_​v01.tif |
| --- |

Энэ composite дээр:

| Vegetation = улаан/​тод улаан Bare ground /​ lithology = cyan, brown, grey, greenish tone Water /​ shadow = бараан |
| --- |

# 16. Sentinel lithology / alteration index үүсгэх
Зураг дээрх workflow-ийн дагуу дараах band ratio stack үүсгэнэ.

| B11 /​ B12 B08 /​ B11 B04 /​ B03 |
| --- |

Энэ нь alteration болон lithological contrast-ыг шалгах support layer болно.
## 16.1 Ratio 1: B11 / B12
Raster Calculator:

| "B11@1" /​ "B12@1" |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​Ratio_​B11_​B12_​EPSG32647_​v01.tif |
| --- |

## 16.2 Ratio 2: B08 / B11
Raster Calculator:

| "B08@1" /​ "B11@1" |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​Ratio_​B08_​B11_​EPSG32647_​v01.tif |
| --- |

## 16.3 Ratio 3: B04 / B03
Raster Calculator:

| "B04@1" /​ "B03@1" |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​Ratio_​B04_​B03_​EPSG32647_​v01.tif |
| --- |

## 16.4 Ratio stack үүсгэх
QGIS дээр:

|  |
| --- |

Input дараалал:

| Ratio B11/​B12 Ratio B08/​B11 Ratio B04/​B03 |
| --- |

Тохиргоо:

| Place each input file into a separate band: Yes CRS: EPSG:32647 Resolution: 10 m |
| --- |

Output VRT:

| XV023222_​Buduunkhad_​Sentinel2_​LithologyIndex_​B11B12_​B08B11_​B04B03_​EPSG32647_​v01.vrt |
| --- |

Дараа нь GeoTIFF болгоно.

|  |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​LithologyIndex_​B11B12_​B08B11_​B04B03_​EPSG32647_​v01.tif |
| --- |

# 17. Mask ашиглан final raster цэвэрлэх
Lithology index болон composite-үүд дээр vegetation, water, shadow mask-ийг ашиглаж interpretation-ийн эрсдэлтэй pixel-үүдийг тэмдэглэнэ.
## 17.1 Usable pixel mask үүсгэх
Raster Calculator:

| (("VegetationMask@1" = 0) AND ("WaterShadowMask@1" = 0)) |
| --- |

QGIS дээр илүү найдвартай бичих хувилбар:

| (("VegetationMask@1" = 0) * ("WaterShadowMask@1" = 0)) |
| --- |

Output:

| XV023222_​Buduunkhad_​Sentinel2_​UsablePixelMask_​EPSG32647_​v01.tif |
| --- |

Үүсэх утга:

| 1 = ашиглаж болох pixel 0 = vegetation /​ water /​ shadow |
| --- |

## 17.2 Lithology index-ийг mask хийх
Raster Calculator дээр band тус бүрийг mask-тай үржүүлж болно. Жишээ:

| "LithologyIndex@1" * "UsablePixelMask@1" |
| --- |

Гэхдээ 3 band raster-ийг шууд Raster Calculator-аар бүх band-тай нь цэвэрлэхэд төвөгтэй байж болно. Илүү зөв арга:
1.   Lithology index-ийн 3 band-ийг тус тусад нь export хийх
2.   Band бүрийг UsablePixelMask-тай үржүүлэх
3.   Дахин 3 band stack үүсгэх
Final output:

| XV023222_​Buduunkhad_​Sentinel2_​LithologyIndex_​Masked_​EPSG32647_​v01.tif |
| --- |

# 18. Raster symbology тохируулах
## 18.1 Natural RGB
Layer дээр right click:

|  |
| --- |

Render type:

| Multiband color |
| --- |

Band тохиргоо:

| Red band: Band 1 Green band: Band 2 Blue band: Band 3 |
| --- |

Min / Max тохиргоо:

| Cumulative count cut: 2% – 98% |
| --- |

## 18.2 Geological RGB

| Red band: B12 Green band: B08 Blue band: B03 |
| --- |

Хэрэв Build Virtual Raster-аар үүсгэсэн бол:

| Red: Band 1 Green: Band 2 Blue: Band 3 |
| --- |

Stretch:

| Cumulative count cut 2% – 98% |
| --- |

## 18.3 Lithology Index

| Red: B11/​B12 Green: B08/​B11 Blue: B04/​B03 |
| --- |

Interpretation хийхдээ дараах зүйлсийг анхаарна.

| Өнгөний огцом өөрчлөлт = lithological boundary байж болно Linear contrast = structure /​ fault /​ dyke байж болно Өндөр ratio anomaly = alteration эсвэл lithology difference байж болно Vegetation /​ water /​ shadow area = interpretation-оос болгоомжтой хасна |
| --- |

# 19. QA/QC шалгалт хийх
Доорх мэдээллийг Excel log файлд бүртгэнэ.
Output файл:

| XV023222_​Buduunkhad_​Sentinel2_​QAQC_​Log.xlsx |
| --- |

Бүртгэх баганууд:

| File name Input source Processing step CRS Pixel size Extent NoData value Resampling method Formula /​ band composition Output location Checked by Date Comment |
| --- |

Жишээ бүртгэл:

| File name: XV023222_​Buduunkhad_​Sentinel2_​NDVI_​EPSG32647_​v01.tif Input: B08, B04 Formula: (B08 - B04) /​ (B08 + B04) CRS: EPSG:32647 Pixel size: 10 m Status: OK Comment: Vegetation mask threshold NDVI > 0.3 |
| --- |

# 20. Final package шалгах
Final folder дотор дараах файлууд бүрэн байх ёстой.

| XV023222_​Buduunkhad_​Sentinel2_​NaturalRGB_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​Geology_​RGB_​B12_​B08_​B03_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​FalseColor_​B08_​B04_​B03_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​LithologyIndex_​B11B12_​B08B11_​B04B03_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​NDVI_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​NDWI_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​VegetationMask_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​WaterShadowMask_​EPSG32647_​v01.tif XV023222_​Buduunkhad_​Sentinel2_​QAQC_​Log.xlsx |
| --- |

# 21. QGIS layer зохион байгуулалт
Layer panel дээр дараах group үүсгэнэ.

| Sentinel-2 Processing \|        \|  \|      \|     \| |
| --- |

# 22. Хамгийн чухал анхаарах зүйлс
1.   B11, B12 заавал 10 m grid рүү resample хийгдсэн байх ёстой. Үгүй бол ratio болон composite буруу гарна.
2.   Бүх raster нэг CRS-тэй байх ёстой. Энэ workflow дээр зорилтот CRS: EPSG:32647.
3.   Бүх raster ижил extent, pixel size, alignment-тай байх ёстой.
4.   NDVI, NDWI, shadow mask-ийг interpretation-д шууд ашиглахгүй, харин support / exclusion layer болгон ашиглана.
5.   Lithology index нь орд илрүүлэх эцсийн баталгаа биш. Энэ нь зөвхөн field mapping, geological map, structure, deposit proximity, geochemistry, geophysics-тэй хамт тайлбарлагдах support layer юм.
Зорилтот CRS:

| EPSG:32647 |
| --- |

# 23. Богино workflow summary

| 1. Sentinel raster оруулах 2. CRS, pixel size, band status шалгах 3. L1C бол SNAP дээр L2A болгох 4. B11, B12-ийг 10 m resample хийх 5. Бүх band-ийг EPSG:32647 болгох 6. License boundary-гаар clip хийх 7. NDVI үүсгэх 8. Vegetation mask үүсгэх 9. NDWI үүсгэх 10. Water /​ shadow mask үүсгэх 11. Natural RGB composite үүсгэх 12. Geology RGB composite үүсгэх 13. False color composite үүсгэх 14. B11/​B12, B08/​B11, B04/​B03 ratio үүсгэх 15. Lithology index stack үүсгэх 16. QA/​QC log бөглөх 17. Final Sentinel package хадгалах |
| --- |

Энэ зааврын дагуу боловсруулсан Sentinel-2 package нь дараагийн шатны геологийн зурагтай тулгалт, хувирал/литологийн ялгалт, бүтэц шугаман элементүүдийн тайлбар, ордын загварчлал, target ranking хийхэд ашиглагдана.
