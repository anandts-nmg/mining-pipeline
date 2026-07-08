<!-- source: QGIS_4_0_2_Google_HighResolution_Basemap_Detailed_Guide.docx (converted from Word; canonical form for LLM ingestion) -->

XV-023222 Buduunkhad Project
QGIS 4.0.2 дээр Google / High-resolution Basemap боловсруулах дэлгэрэнгүй заавар
Phase 10: Google / high-resolution basemap


| Ажлын үндсэн зорилго | Google basemap imagery raster файлыг шалгаж, зөв CRS рүү хөрвүүлж, хайгуулын лицензийн талбайгаар эсвэл 500 м–1 км buffer-ээр тайрч, field access, outcrop visibility, old workings/disturbance, road/track mapping-д ашиглахад бэлэн болгох. |
| --- | --- |

# 10. Google / High-resolution Basemap боловсруулах заавар
## QGIS 4.0.2
# 1. Ажлын зорилго
Энэ ажлаар дараах 2 төрлийн basemap raster өгөгдлийг боловсруулна.
## 10.1 №75 WGS84 basemap
Input raster:
XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif
Target CRS:
EPSG:32647
Output raster:
XV023222_Buduunkhad_GoogleMaps_Basemap_RGB_2p4m_EPSG32647_v01.tif
## 10.2 №76 EPSG:3857 high-resolution basemap
Input raster:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif
Source CRS:
EPSG:3857
Target CRS:
EPSG:32647
Clip area:
license + 500 m эсвэл 1 km buffer
Output raster:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_v01.tif
# 2. Ажлын фолдерийн бүтэц бэлтгэх
QGIS дээр ажил эхлэхээс өмнө дараах байдлаар фолдер үүсгэнэ.
XV023222_Buduunkhad/
│
├── 01_Input/
│   ├── Raster/
│   │   ├── Google_Basemap/
│   │   └── HighResolution_Basemap/
│   └── Vector/
│       ├── License_Boundary/
│       └── Buffer/
│
├── 02_Processing/
│   ├── Reprojected_Raster/
│   ├── Clipped_Raster/
│   └── Temporary/
│
├── 03_Output/
│   ├── Basemap_EPSG32647/
│   └── Map_Layout/
│
└── 04_QGIS_Project/
Файлуудыг дараах байдлаар байрлуулна.
01_Input/Raster/Google_Basemap/
XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif

01_Input/Raster/HighResolution_Basemap/
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif

01_Input/Vector/License_Boundary/
license_boundary.shp эсвэл license_boundary.gpkg
QGIS project файлыг дараах нэрээр хадгална.
04_QGIS_Project/XV023222_Buduunkhad_Phase10_Google_HighResolution_Basemap_QGIS402.qgz
# 3. QGIS project үүсгэх ба CRS тохируулах
## 3.1 QGIS 4.0.2 нээх
QGIS-ийг нээгээд шинэ project үүсгэнэ.
Дараах цэсээр орно.
Project → Properties → CRS
Project CRS-ийг дараах байдлаар тохируулна.
EPSG:32647 - WGS 84 / UTM zone 47N
Энэ CRS нь Монгол орны олон хайгуулын талбайд ашиглагддаг UTM координатын систем бөгөөд raster, vector, buffer, clipping, distance measurement хийхэд тохиромжтой.
## 3.2 Project-ийг хадгалах
Project → Save As
Дараах нэрээр хадгална.
XV023222_Buduunkhad_Phase10_Google_HighResolution_Basemap_QGIS402.qgz
# 4. Лицензийн талбайн boundary оруулах
## 4.1 Vector boundary нэмэх
Дараах цэсээр орно.
Layer → Add Layer → Add Vector Layer
эсвэл Browser panel-оос файлаа шууд чирж оруулна.
Оруулах файл:
license_boundary.shp
эсвэл
license_boundary.gpkg
Layer нэмэгдсэний дараа CRS-ийг шалгана.
Layer дээр right click хийнэ.
Properties → Information
CRS нь EPSG:32647 биш байвал vector boundary-г EPSG:32647 руу хөрвүүлнэ.
## 4.2 License boundary-г EPSG:32647 болгох
Хэрэв boundary өөр CRS-тэй байвал:
Processing Toolbox → Vector general → Reproject layer
Тохиргоо:
Input layer: license_boundary
Target CRS: EPSG:32647
Output: license_boundary_EPSG32647.gpkg
Run дарна.
Дараа нь шинэ layer-ийг project-д ашиглана.
# 5. Buffer polygon үүсгэх
High-resolution basemap-ийг зөвхөн лицензийн талбайгаар тайрахгүй, талбайн гаднах зам, access, disturbance, old workings зэрэг мэдээллийг харахын тулд 500 м эсвэл 1 км buffer ашиглана.
## 5.1 Buffer үүсгэх
Дараах цэсээр орно.
Processing Toolbox → Vector geometry → Buffer
Тохиргоо:
Input layer: license_boundary_EPSG32647
Distance: 500
Segments: 20
Dissolve result: Yes
Output: license_boundary_buffer_500m_EPSG32647.gpkg
Хэрэв 1 км buffer хэрэгтэй бол:
Distance: 1000
Output: license_boundary_buffer_1km_EPSG32647.gpkg
Анхаарах зүйл: Buffer distance метрээр зөв гарахын тулд layer болон project CRS заавал EPSG:32647 байх ёстой.
# 6. №75 WGS84 Google basemap боловсруулах
## 6.1 Input raster нэмэх
Дараах raster файлыг QGIS рүү оруулна.
XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif
Оруулах арга:
Layer → Add Layer → Add Raster Layer
эсвэл Browser panel-оос шууд чирж оруулна.
## 6.2 Raster CRS шалгах
Layer дээр right click хийнэ.
Properties → Information
Дараах мэдээллийг шалгана.
CRS
Pixel size
Extent
Band count
Data type
Энэ raster нь WGS84 гэж нэрлэгдсэн тул ихэнхдээ дараах CRS-тэй байна.
EPSG:4326 - WGS 84
Гэхдээ заавал QGIS дээр шалгана. Файлын нэрэнд WGS84 гэж байгаа боловч raster дотор CRS буруу эсвэл хоосон байх боломжтой.
## 6.3 Хэрэв CRS байхгүй эсвэл буруу байвал Define Projection хийх
Хэрэв QGIS дээр raster CRS “Unknown CRS” гэж гарвал шууд reproject хийж болохгүй. Эхлээд зөв source CRS онооно.
Дараах цэсээр орно.
Raster → Projections → Assign Projection
Тохиргоо:
Input layer: XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif
CRS: EPSG:4326
Output: XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_AssignedCRS_v01.tif
Хэрэв raster аль хэдийн EPSG:4326 гэж зөв танигдсан бол энэ алхмыг хийх шаардлагагүй.
## 6.4 Raster-ийг EPSG:32647 руу reproject хийх
Дараах цэсээр орно.
Raster → Projections → Warp (Reproject)
эсвэл
Processing Toolbox → GDAL → Raster projections → Warp (reproject)
Тохиргоо:
Input layer:
XV023222_Buduunkhad_GoogleMaps_BasemapImagery_RGB_2p4m_WGS84_Raw_v01.tif

Source CRS:
EPSG:4326

Target CRS:
EPSG:32647

Resampling method:
Bilinear эсвэл Cubic

Target resolution:
2.4

Output file:
XV023222_Buduunkhad_GoogleMaps_Basemap_RGB_2p4m_EPSG32647_v01.tif
RGB basemap тул дараах resampling тохиромжтой.
Bilinear
эсвэл илүү зөөлөн харагдуулах бол:
Cubic
Nearest neighbour-ийг зөвхөн ангиллын raster дээр ашиглана. Google imagery зэрэг continuous image raster дээр Bilinear/Cubic илүү тохиромжтой.
## 6.5 Output raster шалгах
Reproject дууссаны дараа шинэ raster layer дээр right click хийнэ.
Properties → Information
Дараахыг шалгана.
CRS: EPSG:32647
Pixel size: ойролцоогоор 2.4 m
Extent: license area орчимд зөв байрласан эсэх
Band count: RGB буюу 3 band эсэх
Лицензийн boundary-тэй давхцуулж хараад байрлал зөрж байгаа эсэхийг шалгана.
# 7. №76 EPSG:3857 high-resolution basemap боловсруулах
## 7.1 Input raster нэмэх
QGIS рүү дараах raster файлыг оруулна.
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif
Оруулах цэс:
Layer → Add Layer → Add Raster Layer
## 7.2 CRS шалгах
Layer дээр right click хийнэ.
Properties → Information
CRS дараах байдлаар байх ёстой.
EPSG:3857 - WGS 84 / Pseudo-Mercator
Хэрэв QGIS дээр Unknown CRS гэж гарвал source CRS-ийг EPSG:3857 гэж онооно.
Raster → Projections → Assign Projection
Тохиргоо:
Input layer:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif

CRS:
EPSG:3857

Output:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_AssignedCRS_v01.tif
## 7.3 EPSG:3857 raster-ийг EPSG:32647 руу reproject хийх
Дараах цэсээр орно.
Raster → Projections → Warp (Reproject)
Тохиргоо:
Input layer:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_EPSG3857_0p15m_Raw_v01.tif

Source CRS:
EPSG:3857

Target CRS:
EPSG:32647

Resampling method:
Bilinear эсвэл Cubic

Target resolution:
0.15

Output:
02_Processing/Reprojected_Raster/XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_Reprojected_v01.tif
Анхаарах зүйл: 0.15 м resolution маш өндөр нарийвчлалтай тул файл маш том болно. Хэрэв QGIS удааширвал эхлээд license + 500 м buffer хэмжээнд clip хийж, дараа нь pyramid үүсгэх хэрэгтэй.
# 8. High-resolution raster-ийг license + buffer-ээр clip хийх
## 8.1 Clip Raster by Mask Layer ашиглах
Дараах цэсээр орно.
Raster → Extraction → Clip Raster by Mask Layer
эсвэл
Processing Toolbox → GDAL → Raster extraction → Clip raster by mask layer
Тохиргоо:
Input layer:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_Reprojected_v01.tif

Mask layer:
license_boundary_buffer_500m_EPSG32647.gpkg
эсвэл 1 км buffer ашиглавал:
Mask layer:
license_boundary_buffer_1km_EPSG32647.gpkg
Доорх тохиргоог идэвхжүүлнэ.
Crop to cutline: Yes
Keep resolution of input raster: Yes
Create output alpha band: Yes
Output file:
03_Output/Basemap_EPSG32647/XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_v01.tif
Run дарна.
## 8.2 Clip output шалгах
Шинэ raster дээр right click:
Properties → Information
Дараахыг шалгана.
CRS: EPSG:32647
Pixel size: ойролцоогоор 0.15 m
Extent: license + 500 m эсвэл 1 km buffer
NoData / Alpha band: зөв үүссэн эсэх
Map canvas дээр дараах layer-үүдийг давхар харуулна.
license_boundary_EPSG32647
license_boundary_buffer_500m_EPSG32647
high-resolution clipped basemap
Хэрэв raster boundary-гээс хол зөрсөн байвал source CRS буруу оноосон байх магадлалтай. Энэ тохиолдолд reproject хийхээс өмнөх source CRS-ийг дахин шалгана.
# 9. Raster display тохиргоо хийх
## 9.1 RGB band тохируулах
Raster layer дээр right click:
Properties → Symbology
Render type:
Multiband color
Band тохиргоо:
Red band: Band 1
Green band: Band 2
Blue band: Band 3
Contrast enhancement:
Stretch to MinMax
Min / Max value settings:
Cumulative count cut
эсвэл
Min / Max
Apply дарна.
## 9.2 Transparency тохируулах
Хэрэв raster-ийн гадна тал хар эсвэл цагаан background-тай байвал:
Properties → Transparency
NoData value оруулна.
Жишээ нь:
0 0 0
эсвэл
255 255 255
Гэхдээ RGB raster дээр шууд NoData оноохдоо болгоомжтой хандана. Учир нь бодит хар/цагаан объектууд устаж харагдах эрсдэлтэй.
# 10. Raster pyramid / overview үүсгэх
High-resolution 0.15 м raster маш том тул QGIS дээр хурдан ачаалахын тулд pyramids үүсгэнэ.
Layer дээр right click:
Properties → Pyramids
эсвэл Processing Toolbox ашиглана.
Processing Toolbox → GDAL → Raster miscellaneous → Build overviews
Тохиргоо:
Input layer:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_v01.tif

Overview levels:
2, 4, 8, 16, 32, 64

Resampling:
Average эсвэл Gauss
Run дарна.
Үүний дараа raster zoom in / zoom out хийхэд хурдан болно.
# 11. Raster compression хийх
Файл хэт том байвал GeoTIFF compression ашиглана.
Дараах цэсээр орно.
Raster → Conversion → Translate Convert Format
эсвэл
Processing Toolbox → GDAL → Raster conversion → Translate
Advanced parameters хэсэгт дараах creation options оруулж болно.
COMPRESS=LZW
TILED=YES
BIGTIFF=IF_SAFER
Output:
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_LZW_v01.tif
Хэрэв файл 4GB-аас том бол BigTIFF шаардлагатай.
# 12. Basemap дээр ашиглах геологийн тайлбар хийх
Энэ basemap-ийг дараах ажилд ашиглана.
field access
outcrop visibility
old workings/disturbance
track/road mapping
## 12.1 Field access шалгах
High-resolution basemap дээр дараах зүйлсийг digitize хийж болно.
existing road
vehicle track
dry river access
mountain pass
flat area / camp site
blocked access
steep slope access risk
Шинэ vector layer үүсгэнэ.
Layer → Create Layer → New GeoPackage Layer
Layer нэр:
field_access_tracks_EPSG32647
Geometry type:
Line
Fields:
track_id        Text
track_type      Text
condition       Text
access_level    Text
comment         Text
source          Text
date_mapped     Date
Жишээ утга:
track_type: main road / vehicle track / foot track / dry river route
condition: good / moderate / poor / unknown
access_level: easy / difficult / restricted / inaccessible
source: Google high-resolution basemap
## 12.2 Outcrop visibility тэмдэглэх
Basemap дээр харагдах ил гарц, хадархаг бүс, толгодын орой, ridge zone-уудыг polygon хэлбэрээр digitize хийж болно.
Layer нэр:
outcrop_visibility_zones_EPSG32647
Geometry type:
Polygon
Fields:
zone_id         Text
visibility     Text
surface_type   Text
priority       Text
comment        Text
source         Text
Жишээ:
visibility: high / moderate / low
surface_type: outcrop / scree / soil cover / vegetation / alluvial cover
priority: high / medium / low
## 12.3 Old workings / disturbance зураглах
Хуучин ухалт, суваг, замын эвдрэл, ил уурхай төст хэлбэр, trench, pit, disturbed ground харагдвал point эсвэл polygon layer үүсгэнэ.
Layer нэр:
old_workings_disturbance_EPSG32647
Geometry type:
Point эсвэл Polygon
Fields:
feature_id      Text
feature_type    Text
confidence      Text
size_class      Text
comment         Text
source          Text
Жишээ утга:
feature_type: old pit / trench / waste dump / disturbed ground / possible working
confidence: high / medium / low
size_class: small / medium / large
## 12.4 Road / track mapping хийх
Зам, track-ийг тусад нь line layer болгон зураглана.
Layer нэр:
road_track_mapping_EPSG32647
Geometry type:
Line
Fields:
road_id          Text
road_class       Text
surface          Text
condition        Text
field_check      Text
comment          Text
Жишээ:
road_class: main road / local road / exploration track / temporary track
surface: paved / gravel / dirt / unknown
condition: good / moderate / poor
field_check: yes / no
# 13. Digitizing хийх тохиргоо
## 13.1 Snapping тохируулах
Дараах цэсээр орно.
Project → Snapping Options
Тохиргоо:
Enable Snapping: On
Mode: All layers эсвэл Advanced configuration
Tolerance: 5–10 pixels
Units: pixels
Topological editing: On
## 13.2 Editing эхлүүлэх
Layer дээр right click:
Toggle Editing
Дараа нь:
Add Line Feature
Add Polygon Feature
Add Point Feature
Геометрээ зурж дуусгаад attribute бөглөнө.
Жишээ:
road_id: R001
road_class: exploration track
surface: dirt
condition: moderate
field_check: no
comment: Visible on high-resolution Google basemap
# 14. Чанарын шалгалт хийх
## 14.1 CRS шалгалт
Бүх output layer дээр дараахыг шалгана.
Properties → Information → CRS
Зөв байх ёстой CRS:
EPSG:32647
## 14.2 Байршлын шалгалт
Дараах layer-үүдийг хамтад нь харуулна.
license boundary
buffer boundary
Google basemap 2.4 m
High-resolution basemap 0.15 m
road / track mapping
outcrop visibility
old workings / disturbance
Шалгах зүйлс:
Raster ба license boundary давхцаж байна уу?
Зам, track бодитоор raster дээр харагдаж байна уу?
Buffer бүрэн хамрагдсан уу?
Clip хийсний дараа raster тасарсан эсэх
Pixel суналт, distortion байгаа эсэх
## 14.3 Geometry validity шалгах
Digitized vector layer-үүд дээр:
Processing Toolbox → Vector geometry → Check validity
Алдаатай geometry байвал:
Processing Toolbox → Vector geometry → Fix geometries
# 15. Output deliverables
Эцэст нь дараах файлууд гарсан байх ёстой.
## Raster output
XV023222_Buduunkhad_GoogleMaps_Basemap_RGB_2p4m_EPSG32647_v01.tif
XV023222_Buduunkhad_HighResolution_RGB_SurfaceBasemap_GoogleMaps_0p15m_EPSG32647_v01.tif
## Vector output
license_boundary_EPSG32647.gpkg
license_boundary_buffer_500m_EPSG32647.gpkg
license_boundary_buffer_1km_EPSG32647.gpkg
field_access_tracks_EPSG32647.gpkg
outcrop_visibility_zones_EPSG32647.gpkg
old_workings_disturbance_EPSG32647.gpkg
road_track_mapping_EPSG32647.gpkg
## QGIS project
XV023222_Buduunkhad_Phase10_Google_HighResolution_Basemap_QGIS402.qgz
# 16. Recommended layer order in QGIS
QGIS Layers panel дээр дараах дарааллаар байрлуулна.
road_track_mapping_EPSG32647
field_access_tracks_EPSG32647
old_workings_disturbance_EPSG32647
outcrop_visibility_zones_EPSG32647
license_boundary_EPSG32647
license_boundary_buffer_500m_EPSG32647
HighResolution_Basemap_0p15m_EPSG32647
GoogleMaps_Basemap_2p4m_EPSG32647
High-resolution raster-ийг доор, vector interpretation layer-үүдийг дээр байрлуулна.
# 17. Map layout гаргах
## 17.1 Layout үүсгэх
Project → New Print Layout
Layout нэр:
Phase10_Google_HighResolution_Basemap_Map
A3 эсвэл A4 landscape сонгоно.
## 17.2 Map layout-д оруулах элементүүд
Layout дээр дараах элементүүдийг оруулна.
Map frame
Title
Legend
Scale bar
North arrow
Coordinate grid
CRS note
Data source note
Title:
XV-023222 Buduunkhad Project
Google / High-resolution Basemap Interpretation
CRS note:
Coordinate Reference System: EPSG:32647 - WGS 84 / UTM Zone 47N
Data source note:
Basemap imagery reprojected and clipped to license boundary buffer for field access, outcrop visibility, old workings/disturbance and road/track mapping.
# 18. Export хийх
Layout export хийх:
Layout → Export as PDF
Output нэр:
XV023222_Buduunkhad_Phase10_Google_HighResolution_Basemap_Map_EPSG32647_v01.pdf
Мөн PNG export хийж болно.
XV023222_Buduunkhad_Phase10_Google_HighResolution_Basemap_Map_EPSG32647_v01.png
# 19. Эцсийн шалгах checklist
Ажил дуусахаас өмнө дараах checklist-ийг шалгана.
[ ] QGIS project CRS EPSG:32647 болсон эсэх
[ ] License boundary EPSG:32647 болсон эсэх
[ ] 500 м эсвэл 1 км buffer зөв үүссэн эсэх
[ ] №75 WGS84 basemap EPSG:32647 руу reproject хийгдсэн эсэх
[ ] №76 EPSG:3857 high-resolution basemap EPSG:32647 руу reproject хийгдсэн эсэх
[ ] High-resolution raster license + buffer-ээр clip хийгдсэн эсэх
[ ] Raster pixel size 2.4 м болон 0.15 м орчим зөв хадгалагдсан эсэх
[ ] RGB band зөв харагдаж байгаа эсэх
[ ] Pyramids / overviews үүсгэсэн эсэх
[ ] Output raster GeoTIFF файлууд зөв нэршилтэй эсэх
[ ] Road / track mapping layer үүсгэсэн эсэх
[ ] Field access interpretation layer үүсгэсэн эсэх
[ ] Outcrop visibility zones layer үүсгэсэн эсэх
[ ] Old workings / disturbance layer үүсгэсэн эсэх
[ ] Map layout export хийсэн эсэх
[ ] Бүх output файлууд 03_Output folder дотор хадгалагдсан эсэх
# 20. Товч workflow summary
1. QGIS project үүсгэнэ.
2. Project CRS = EPSG:32647 болгоно.
3. License boundary оруулж CRS шалгана.
4. Boundary-г EPSG:32647 болгоно.
5. 500 м эсвэл 1 км buffer үүсгэнэ.
6. №75 WGS84 Google basemap raster оруулна.
7. CRS шалгаж EPSG:32647 руу reproject хийнэ.
8. №76 EPSG:3857 high-resolution raster оруулна.
9. Source CRS EPSG:3857 эсэхийг шалгана.
10. EPSG:32647 руу reproject хийнэ.
11. License + buffer mask ашиглан clip хийнэ.
12. RGB display, contrast, transparency тохируулна.
13. Pyramids үүсгэнэ.
14. Road, track, outcrop, old workings, disturbance layer-үүд үүсгэж digitize хийнэ.
15. Quality control хийж output файлуудыг хадгална.
16. Map layout export хийнэ.
