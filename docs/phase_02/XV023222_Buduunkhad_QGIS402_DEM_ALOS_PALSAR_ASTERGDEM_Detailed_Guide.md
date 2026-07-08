<!-- source: XV023222_Buduunkhad_QGIS402_DEM_ALOS_PALSAR_ASTERGDEM_Detailed_Guide.docx (converted from Word; canonical form for LLM ingestion) -->

6. DEM / ALOS-PALSAR / ASTER GDEM боловсруулах дэлгэрэнгүй заавар
QGIS 4.0.2 дээр гүйцэтгэх ажлын бүрэн аргачлал
Project: XV-023222 Buduunkhad
Date: 2026-06-05

# Агуулга
- 6.0 Ажлын зорилго
- 6.1 DEM metadata шалгах
- 6.2 DEM reproject хийх
- 6.3 License + buffer-аар DEM clip хийх
- 6.4 Hillshade гаргах
- 6.5 Slope гаргах
- 6.6 Aspect гаргах
- 6.7 Contour гаргах
- 6.8 Drainage / watershed гаргах
- 6.9 Terrain ruggedness / curvature гаргах
- 6.10 DEM final package бэлтгэх
- 6.11 QGIS project дотор layer group зохион байгуулах
- 6.12 QA/QC шалгах эцсийн checklist
- 6.13 Common error болон засах арга
- 6.14 Mineral exploration-д ашиглах тайлбар

# 6.0 Ажлын зорилго
Энэ ажлын зорилго нь ALOS-PALSAR DEM болон ASTER GDEM өгөгдлийг QGIS 4.0.2 дээр нэг стандарт координатын системд оруулж, лицензийн талбай болон buffer бүсээр тайран, газрын гадаргын морфологи, налуу, өндөршил, усны урсац, хагарал/шугаман бүтэц тайлбарлахад хэрэгтэй бүх derivative output-уудыг гаргах явдал юм.
Энэ ажлын үр дүнд дараах төрлийн өгөгдлүүд гарна.
DEM raster
Reprojected DEM
Clipped DEM
Hillshade
Slope
Aspect
Contour
Drainage network
Watershed / catchment
Terrain ruggedness index
Profile curvature
Plan curvature
DEM QA/QC log
Эдгээр output нь дараагийн үе шатуудад буюу дараах ажлуудад ашиглагдана.
Lineament interpretation
Structural interpretation
Stream sediment planning
Heavy mineral follow-up
Field route planning
Mineral prospectivity ranking
# 6.1 DEM metadata шалгах
## 6.1.1 Input өгөгдөл
Ашиглах үндсэн DEM өгөгдөл:
ALOS-PALSAR DEM
ASTER GDEM
Файлуудын жишиг нэр:
XV023222_Buduunkhad_ALOS_PALSAR_DEM_Raw.tif
XV023222_Buduunkhad_ASTERGDEM_DEM_Raw.tif
## 6.1.2 QGIS-д DEM оруулах
QGIS 4.0.2 дээр raster өгөгдлийг дараах замаар оруулна.
Layer -> Add Layer -> Add Raster Layer
Мөн .tif файлыг QGIS canvas руу шууд drag & drop хийж оруулж болно. Оруулсны дараа DEM raster layer дээр дараах байдлаар орж metadata-г шалгана.
Right click -> Properties -> Information
## 6.1.3 Заавал шалгах зүйлс
CRS
Extent
Pixel size
Band count
Data type
NoData value
Statistics
Resolution
## 6.1.4 CRS шалгах
Information хэсэгт CRS дараах байдлаар харагдаж болно.
EPSG:4326 - WGS 84
EPSG:32647 - WGS 84 / UTM zone 47N
Энэ төсөлд боловсруулалтын үндсэн CRS дараах байдлаар тохируулагдана.
EPSG:32647
WGS 84 / UTM zone 47N
Хэрэв DEM нь EPSG:4326 буюу geographic coordinate system дээр байвал заавал UTM буюу EPSG:32647 руу reproject хийнэ. Учир нь slope, contour, drainage зэрэг тооцоолол метрийн нэгж дээр илүү зөв хийгдэнэ.
## 6.1.5 Pixel size шалгах
Information хэсэгт pixel size ихэвчлэн дараах хэлбэрээр харагдана.
Pixel Size: 12.5, -12.5
Pixel Size: 30, -30
ALOS-PALSAR DEM ихэвчлэн 12.5 м орчим, ASTER GDEM ихэвчлэн 30 м орчим resolution-тэй байдаг. Reproject хийх үед эх өгөгдлийн resolution-г аль болох хадгалах ёстой.
## 6.1.6 NoData value шалгах
NoData value дараах байдлаар байж болно.
- 9999
0
nan
NoData value буруу танигдсан бол дараагийн slope, aspect, hillshade, drainage гаргалтад буруу утга үүсэх эрсдэлтэй. Иймээс QA/QC log дээр заавал тэмдэглэнэ.
## 6.1.7 QA/QC register бөглөх
Excel файл үүсгэж metadata шалгалтын үр дүнг бүртгэнэ.
XV023222_Buduunkhad_DEM_QAQC_Log.xlsx
Баганын бүтэц:
source_raw_input_no
source_raw_filename
raster_type
native_crs
pixel_size
extent
nodata_value
band_count
sidecar_available
processing_action
qaqc_status
reviewer
review_date
comment

| Багана | Жишээ утга |
| --- | --- |
| source_raw_input_no | DEM_001 |
| source_raw_filename | ALOS_PALSAR_DEM_Raw.tif |
| raster_type | ALOS-PALSAR DEM |
| native_crs | EPSG:4326 |
| pixel_size | 12.5 m |
| extent | License + regional coverage |
| nodata_value | -9999 |
| band_count | 1 |
| sidecar_available | Yes |
| processing_action | Reproject to EPSG:32647 |
| qaqc_status | Accepted |
| reviewer | нэр |
| review_date | 2026-06-05 |
| comment | Suitable for DEM derivative processing |

# 6.2 DEM reproject хийх
## 6.2.1 Зорилго
DEM өгөгдлийг төслийн нэг ижил CRS болох EPSG:32647 буюу WGS 84 / UTM zone 47N руу хөрвүүлнэ. Энэ нь зай, талбай, налуу, contour, drainage зэрэг тооцооллыг метрийн нэгжээр зөв хийх үндсэн нөхцөл юм.
EPSG:32647
WGS 84 / UTM zone 47N
## 6.2.2 QGIS tool
Raster -> Projections -> Warp (Reproject)
эсвэл Processing Toolbox-оос:
Processing Toolbox -> GDAL -> Raster projections -> Warp (reproject)
## 6.2.3 ALOS-PALSAR DEM reproject тохиргоо
Warp цонхонд дараах байдлаар тохируулна.
Input layer: ALOS-PALSAR DEM
Source CRS: native CRS
Target CRS: EPSG:32647
Resampling method: Bilinear
Output file resolution: эх raster-ийн resolution-д ойролцоо
NoData value: эх NoData-г хадгална
Output data type: Float32
Хэрэв ALOS-PALSAR DEM 12.5 м resolution-тэй бол output resolution 12.5 гэж тохируулж болно. Зарим тохиолдолд QGIS автоматаар санал болгосон утгыг шалгаж хэрэглэнэ.
12.5
Output нэр:
XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif
## 6.2.4 ASTER GDEM reproject тохиргоо
ASTER GDEM дээр мөн ижил tool ашиглана.
Input layer: ASTER GDEM
Source CRS: native CRS
Target CRS: EPSG:32647
Resampling method: Bilinear
Output resolution: 30 m орчим
NoData value: эх NoData-г хадгална
Output data type: Float32
Output нэр:
XV023222_Buduunkhad_ASTERGDEM_DEM_EPSG32647_v01.tif
## 6.2.5 Reproject хийсний дараах шалгалт
Output raster дээр дараах байдлаар орж шалгана.
Right click -> Properties -> Information
Шалгах зүйлс:
CRS = EPSG:32647
Pixel size зөв эсэх
Extent зөв эсэх
NoData хадгалагдсан эсэх
Raster canvas дээр зөв байрлаж байгаа эсэх
Лицензийн boundary-тэй давхцаж байгаа эсэх
Хэрэв лицензийн талбайтай зөрж харагдвал дараах шалтгаануудыг шалгана.
CRS буруу сонгосон
Layer-ийн CRS буруу тодорхойлогдсон
Project CRS буруу байна
Project CRS-г QGIS-ийн доод баруун буланд дарж EPSG:32647 болгон тохируулна.
EPSG:32647
# 6.3 License + buffer-аар DEM clip хийх
## 6.3.1 Зорилго
Reproject хийсэн DEM-г лицензийн хил болон buffer бүсээр тайрч, зөвхөн ажлын талбайд хэрэгтэй raster болгон бэлтгэнэ.
Buffer ашиглах шалтгаан:
Лицензийн хилийн гаднах drainage direction харах
Watershed boundary зөв гаргах
Lineament үргэлжлэл шалгах
Field route planning хийх
## 6.3.2 Input өгөгдөл
Reprojected DEM
License boundary polygon
License boundary buffer 1 km эсвэл 5 km
Жишиг buffer layer:
license_boundary_buffer_1km.gpkg
license_boundary_buffer_5km.gpkg
## 6.3.3 Buffer байхгүй бол үүсгэх
License boundary layer дээр дараах tool ашиглана.
Vector -> Geoprocessing Tools -> Buffer
Тохиргоо:
Input layer: license_boundary
Distance: 1000 m эсвэл 5000 m
Segments: 20
Dissolve result: checked
Output: license_boundary_buffer_1km.gpkg
5 км buffer хэрэгтэй бол:
Distance: 5000 m
Output: license_boundary_buffer_5km.gpkg
## 6.3.4 DEM clip хийх
Raster -> Extraction -> Clip Raster by Mask Layer
эсвэл:
Processing Toolbox -> GDAL -> Raster extraction -> Clip raster by mask layer
## 6.3.5 Clip тохиргоо
Input raster: reprojected DEM
Mask layer: license_boundary_buffer_1km эсвэл 5km
Crop to cutline: checked
Keep resolution of input raster: checked
Target CRS: EPSG:32647
Assign specified NoData value to output bands: -9999
ALOS-PALSAR DEM output:
XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_Clip1km_EPSG32647_v01.tif
Хэрэв 5 км buffer ашиглавал:
XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_Clip5km_EPSG32647_v01.tif
ASTER GDEM output:
XV023222_Buduunkhad_ASTERGDEM_DEM_Clip1km_EPSG32647_v01.tif
## 6.3.6 Clip output шалгах
Right click -> Zoom to Layer
Дараа нь license boundary-г давхар харуулж шалгана.
DEM нь buffer хилээр зөв тайрагдсан эсэх
NoData хэсэг зөв харагдаж байгаа эсэх
Лицензийн хил raster-ийн дотор бүрэн багтсан эсэх
Pixel size өөрчлөгдөөгүй эсэх
CRS EPSG:32647 хэвээр эсэх
# 6.4 Hillshade гаргах
## 6.4.1 Зорилго
Hillshade нь газрын гадаргын хэлбэр, хөндий, нуруу, fault/lineament, structural trend-ийг харахад ашиглагдана.
## 6.4.2 QGIS tool
Raster -> Analysis -> Hillshade
эсвэл:
Processing Toolbox -> GDAL -> Raster analysis -> Hillshade
## 6.4.3 Үндсэн hillshade тохиргоо
Input layer: clipped DEM
Z factor: 1
Azimuth: 315
Vertical angle: 45
Output:
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_12p5m_EPSG32647_v01.tif
## 6.4.4 Lineament харахад олон азимуттай hillshade гаргах
Lineament зөвхөн нэг гэрэлтүүлгийн өнцгөөр бүрэн харагдахгүй. Иймээс дараах azimuth-уудаар нэмж гаргана.
Azimuth 045
Azimuth 090
Azimuth 135
Azimuth 315
Output нэршил:
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az045_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az090_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az135_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az315_12p5m_EPSG32647_v01.tif
## 6.4.5 Hillshade display тохиргоо
Right click -> Properties -> Symbology
Тохиргоо:
Render type: Singleband gray
Min/Max: Cumulative count cut 2-98%
Contrast enhancement: Stretch to MinMax
Blending mode: Multiply эсвэл Overlay
Transparency: 30-50%
Hillshade-г geology, satellite image, lineament layer-ийн доор эсвэл дээр transparency-тэй харуулна.
# 6.5 Slope гаргах
## 6.5.1 Зорилго
Slope буюу налуугийн зураг нь дараах зүйлсийг тодорхойлоход ашиглагдана.
Хадархаг өндөрлөг
Хөндий
Элэгдлийн бүс
Хөдөлгөөн хийх боломжтой маршрут
Stream sediment sample авах боломжтой хэсэг
## 6.5.2 QGIS tool
Raster -> Analysis -> Slope
эсвэл:
Processing Toolbox -> GDAL -> Raster analysis -> Slope
## 6.5.3 Slope тохиргоо
Input layer: clipped DEM
Slope expressed as: degrees
Z factor: 1
Output:
XV023222_Buduunkhad_ALOS_PALSAR_SlopeDeg_12p5m_EPSG32647_v01.tif
## 6.5.4 Slope ангилал хийх
Right click -> Properties -> Symbology
Render type: Singleband pseudocolor

| Slope degree | Тайлбар |
| --- | --- |
| 0-5° | Тэгш, хөндий, sediment хуримтлалтай байж болзошгүй |
| 5-15° | Нам налуу |
| 15-25° | Дунд налуу |
| 25-35° | Огцом налуу |
| >35° | Хадан, өндөрлөг, field access хүндрэлтэй |

## 6.5.5 Slope output шалгах
Хэт их NoData үүссэн эсэх
DEM-ийн ирмэг дагуу буруу утга гарсан эсэх
Налуу degree-ээр гарсан эсэх
Percent slope-оор андуурч гаргаагүй эсэх
# 6.6 Aspect гаргах
## 6.6.1 Зорилго
Aspect нь газрын гадаргын аль зүг рүү харсан налуу болохыг харуулна. Энэ нь дараах зүйлсийг шалгах үед хэрэгтэй.
Нарны тусгал
Чийгшил
Ургамалжилт
Элэгдэл
Field access
Structural slope orientation
## 6.6.2 QGIS tool
Raster -> Analysis -> Aspect
эсвэл:
Processing Toolbox -> GDAL -> Raster analysis -> Aspect
## 6.6.3 Aspect тохиргоо
Input layer: clipped DEM
Z factor: 1
Output:
XV023222_Buduunkhad_ALOS_PALSAR_Aspect_12p5m_EPSG32647_v01.tif
## 6.6.4 Aspect утгын тайлбар
Aspect нь 0-360 градусын утгатай.

| Aspect утга | Чиглэл |
| --- | --- |
| 0° / 360° | Хойд |
| 45° | Зүүн хойд |
| 90° | Зүүн |
| 135° | Зүүн өмнөд |
| 180° | Өмнөд |
| 225° | Баруун өмнөд |
| 270° | Баруун |
| 315° | Баруун хойд |

Flat area ихэвчлэн дараах байдлаар илэрч болно. Үүнийг QGIS-ийн output утгаас шалгана.
- 9999
0
эсвэл NoData
# 6.7 Contour гаргах
## 6.7.1 Зорилго
Contour буюу өндөршлийн шугам нь талбайн relief, drainage, valley, ridge, structural lineament-ийг зураглал дээр ойлгомжтой харуулахад ашиглагдана.
## 6.7.2 QGIS tool
Raster -> Extraction -> Contour
эсвэл:
Processing Toolbox -> GDAL -> Raster extraction -> Contour
## 6.7.3 Contour тохиргоо
Input layer: clipped DEM
Interval between contour lines: 10 m
Attribute name: elev
Хэрэв талбай маш нам relief-тэй бол:
Interval: 5 m
Хэрэв өндөр уулс, маш их relief-тэй бол:
Interval: 20 m эсвэл 25 m
## 6.7.4 Output
XV023222_Buduunkhad_Contour_10m_EPSG32647_v01.gpkg
Layer name:
contour_10m
## 6.7.5 Contour styling
Right click -> Properties -> Symbology
Энгийн contour:
Line width: 0.1-0.2 mm
Index contour буюу 50 м тутмын том contour гаргах бол field calculator ашиглаж дараах expression ашиглан rule-based symbology хийж болно.
elev % 50 = 0
Жишээ rule:
"elev" % 50 = 0
Index contour:
Line width: 0.4-0.5 mm
Энгийн contour:
Line width: 0.15 mm
## 6.7.6 Label хийх
Contour дээр өндөршлийн label тавих:
Right click -> Properties -> Labels
Тохиргоо:
Single labels
Value: elev
Placement: Curved
Repeat: 500-1000 m
# 6.8 Drainage / watershed гаргах
## 6.8.1 Зорилго
Drainage network болон watershed/catchment нь дараах ажлуудад чухал.
Stream sediment sampling
Heavy mineral follow-up
Alluvial/colluvial transport direction
Erosion pathway interpretation
Upstream source area analysis
Geochemical anomaly source tracing
## 6.8.2 QGIS Processing Toolbox бэлтгэх
Processing -> Toolbox
SAGA эсвэл GRASS algorithm идэвхтэй байгаа эсэхийг шалгана.
Settings -> Options -> Processing -> Providers
Энд дараах provider-ууд идэвхтэй байх хэрэгтэй.
GDAL
GRASS
SAGA
Хэрэв SAGA харагдахгүй байвал QGIS-ийн Processing provider тохиргоо болон суулгалтыг шалгана.
## 6.8.3 Drainage боловсруулах үндсэн дараалал
Зурагт өгсөн дараалал:
Fill sinks
Flow direction
Flow accumulation
Channel network
Watershed / catchment
Энэ дарааллыг алгасахгүй мөрдөнө.
## 6.8.4 Алхам 1 - Fill sinks
DEM-д жижиг алдаа, хиймэл хонхор, sink байвал flow direction буруу гарна. Тиймээс хамгийн түрүүнд sink засна.
Processing Toolbox-оос хайх:
Fill sinks
Боломжит tool:
SAGA -> Terrain Analysis - Hydrology -> Fill sinks
эсвэл:
GRASS -> r.fill.dir
Тохиргоо:
Input DEM: clipped DEM
Minimum slope: default
Output:
XV023222_Buduunkhad_DEM_FillSinks_12p5m_EPSG32647_v01.tif
Шалгах зүйл:
DEM бүрэн гарсан эсэх
NoData нэмэгдээгүй эсэх
Raster extent өөрчлөгдөөгүй эсэх
## 6.8.5 Алхам 2 - Flow direction
Flow direction нь ус аль чиглэл рүү урсахыг raster хэлбэрээр тооцно.
Processing Toolbox-оос:
Flow direction
эсвэл SAGA-ийн:
Flow Accumulation / Flow Direction
tool ашиглана.
Input:
Filled DEM
Output:
XV023222_Buduunkhad_FlowDirection_EPSG32647_v01.tif
## 6.8.6 Алхам 3 - Flow accumulation
Flow accumulation нь cell бүр дээр хэдэн upstream cell хуримтлагдаж байгааг харуулна. Энэ нь голдирол, хуурай сайр, жалга илрүүлэх үндсэн raster юм.
Processing Toolbox:
Flow accumulation
Input:
Filled DEM
Output:
XV023222_Buduunkhad_FlowAccumulation_EPSG32647_v01.tif
## 6.8.7 Flow accumulation styling
Right click -> Properties -> Symbology
Тохиргоо:
Render type: Singleband pseudocolor
Mode: Equal interval эсвэл Quantile
Flow accumulation ихтэй хэсгүүд drainage болох магадлалтай.
## 6.8.8 Алхам 4 - Channel network гаргах
Channel network гаргахдаа flow accumulation threshold сонгоно. Threshold нь DEM resolution болон талбайн relief-ээс хамаарна.

| DEM resolution | Санал болгох threshold |
| --- | --- |
| 12.5 m | 500-2000 cells |
| 30 m | 100-1000 cells |

Эхлээд дараах байдлаар туршина.
Threshold: 1000
Хэрэв drainage хэт шигүү гарвал threshold нэмнэ.
Threshold: 2000-5000
Хэрэв drainage хэт цөөн гарвал threshold багасгана.
Threshold: 300-700
Output:
XV023222_Buduunkhad_Drainage_Network_EPSG32647_v01.gpkg
Layer name:
drainage_network
## 6.8.9 Drainage network шалгах
Drainage layer-г hillshade, slope, satellite image дээр давхарлаж шалгана.
Гол хөндийтэй давхцаж байна уу
DEM-ийн ирмэг дээр хиймэл drainage үүссэн үү
Лицензийн хил дагуу тасарсан уу
Хэт олон жижиг салаа үүссэн үү
Хэт цөөн голдирол үүссэн үү
## 6.8.10 Алхам 5 - Watershed / catchment гаргах
Watershed буюу catchment нь drainage system-ийн upstream эх үүсвэрийн талбайг тодорхойлно.
Processing Toolbox-оос дараах tool-уудыг хайж ашиглана.
Watershed
Catchment area
Basin
Input:
Filled DEM
Flow direction
Channel network
Outlet point эсвэл drainage pour point
Output:
XV023222_Buduunkhad_Watershed_Catchments_EPSG32647_v01.gpkg
## 6.8.11 Pour point сонгох
Pour point нь дараах байршил дээр байрлана.
Лицензийн хилээс гарах drainage outlet
Stream sediment авах боломжтой голдирлын доод цэг
Geochemical anomaly-ийн downstream point
Point layer үүсгэх:
Layer -> Create Layer -> New GeoPackage Layer
Layer name:
watershed_pour_points
Geometry:
Point
CRS:
EPSG:32647
Field:
point_id
drainage_id
purpose
comment
## 6.8.12 Watershed output шалгах
Watershed polygon-ийг drainage network-тэй давхарлан шалгана.
Watershed boundary нь ridge line дагаж байна уу
Drainage outlet зөв байна уу
Polygon хооронд overlap алдаа байна уу
Лицензийн талбайг бүрэн хамарч байна уу
# 6.9 Terrain ruggedness / curvature гаргах
## 6.9.1 Зорилго
Terrain Ruggedness Index буюу TRI нь газрын гадаргын бартаат байдлыг илэрхийлнэ. Curvature нь газрын гадаргын муруйлтыг харуулна.
Ашиглалт:
Fault scarp илрүүлэх
Lineament тодруулах
Erosion surface ялгах
Ridge / valley morphology харах
Mineralized structure дагасан relief шалгах
## 6.9.2 Ашиглах tool
QGIS эсвэл SAGA tool ашиглана. Processing Toolbox-оос хайх:
Terrain Ruggedness Index
Profile curvature
Plan curvature
Боломжит байрлал:
Processing Toolbox -> GDAL -> Raster analysis -> Terrain ruggedness index
эсвэл:
Processing Toolbox -> SAGA -> Terrain Analysis - Morphometry
## 6.9.3 Terrain Ruggedness Index гаргах
Terrain Ruggedness Index
Input:
Clipped DEM эсвэл Filled DEM
Output:
XV023222_Buduunkhad_Terrain_Ruggedness_EPSG32647_v01.tif
## 6.9.4 TRI styling
Singleband pseudocolor
Mode: Quantile
Classes: 5 эсвэл 7

| TRI утга | Тайлбар |
| --- | --- |
| Low | Тэгш гадарга, хөндий |
| Moderate | Дунд зэргийн бартаа |
| High | Хадархаг, хүчтэй огтлогдсон relief |
| Very high | Огцом уулс, structural scarp байж болзошгүй |

## 6.9.5 Profile curvature гаргах
Profile curvature нь налуугийн дагуух муруйлтыг харуулна. Энэ нь дараах зүйлсийг тайлбарлахад хэрэгтэй.
Элэгдэл
Хуримтлал
Flow acceleration/deceleration
Tool:
Profile curvature
Input:
Clipped DEM эсвэл Filled DEM
Output:
XV023222_Buduunkhad_Profile_Curvature_EPSG32647_v01.tif
## 6.9.6 Plan curvature гаргах
Plan curvature нь contour-ийн дагуу буюу хажуу чиглэлийн муруйлтыг харуулна.
Tool:
Plan curvature
Input:
Clipped DEM эсвэл Filled DEM
Output:
XV023222_Buduunkhad_Plan_Curvature_EPSG32647_v01.tif
## 6.9.7 Curvature тайлбарлах ерөнхий зарчим
Curvature output-ийн утга нь positive, negative, near-zero байж болно.

| Утга | Боломжит тайлбар |
| --- | --- |
| Positive | Convex буюу товойсон гадарга |
| Negative | Concave буюу хонхор гадарга |
| Near zero | Тэгш эсвэл шулуун налуу |

Curvature-г дангаар нь ашиглаж дүгнэлт хийхгүй. Заавал дараах өгөгдлүүдтэй давхар шалгана.
Hillshade
Slope
Drainage
Geological map
Lineament interpretation
Remote sensing alteration
# 6.10 DEM final package бэлтгэх
## 6.10.1 Final output жагсаалт
DEM хэсгийн final output дараах байдлаар багцлагдана.
XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ASTERGDEM_DEM_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_SlopeDeg_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_ALOS_PALSAR_Aspect_12p5m_EPSG32647_v01.tif
XV023222_Buduunkhad_Contour_10m_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Drainage_Network_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Watershed_Catchments_EPSG32647_v01.gpkg
XV023222_Buduunkhad_Terrain_Derivatives_EPSG32647_v01.gpkg
XV023222_Buduunkhad_DEM_QAQC_Log.xlsx
Нэмж terrain ruggedness болон curvature тусдаа raster хэлбэрээр хадгална.
XV023222_Buduunkhad_Terrain_Ruggedness_EPSG32647_v01.tif
XV023222_Buduunkhad_Profile_Curvature_EPSG32647_v01.tif
XV023222_Buduunkhad_Plan_Curvature_EPSG32647_v01.tif
## 6.10.2 Folder structure
Фолдерийг дараах байдлаар зохион байгуулна.
06_DEM_ALOS_PALSAR_ASTERGDEM/
|
|-- 01_Raw/
|   |-- ALOS_PALSAR/
|   |-- ASTER_GDEM/
|
|-- 02_Metadata_QAQC/
|   |-- XV023222_Buduunkhad_DEM_QAQC_Log.xlsx
|
|-- 03_Reprojected/
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_ASTERGDEM_DEM_EPSG32647_v01.tif
|
|-- 04_Clipped/
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_DEM_12p5m_Clip1km_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_ASTERGDEM_DEM_Clip1km_EPSG32647_v01.tif
|
|-- 05_Hillshade/
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az045_12p5m_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az090_12p5m_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az135_12p5m_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_Hillshade_Az315_12p5m_EPSG32647_v01.tif
|
|-- 06_Slope_Aspect/
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_SlopeDeg_12p5m_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_ALOS_PALSAR_Aspect_12p5m_EPSG32647_v01.tif
|
|-- 07_Contour/
|   |-- XV023222_Buduunkhad_Contour_10m_EPSG32647_v01.gpkg
|
|-- 08_Drainage_Watershed/
|   |-- XV023222_Buduunkhad_Drainage_Network_EPSG32647_v01.gpkg
|   |-- XV023222_Buduunkhad_Watershed_Catchments_EPSG32647_v01.gpkg
|
|-- 09_Terrain_Derivatives/
|   |-- XV023222_Buduunkhad_Terrain_Ruggedness_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_Profile_Curvature_EPSG32647_v01.tif
|   |-- XV023222_Buduunkhad_Plan_Curvature_EPSG32647_v01.tif
|
|-- 10_Final_Package/
    |-- Raster/
    |-- Vector/
    |-- QAQC/
    |-- Map_Layouts/
# 6.11 QGIS project дотор layer group зохион байгуулах
QGIS Layers panel дээр дараах group үүсгэнэ.
06_DEM_ALOS_PALSAR_ASTERGDEM
Дотор нь дараах дэд group-уудыг үүсгэнэ.
01 Raw DEM
02 Reprojected DEM
03 Clipped DEM
04 Hillshade
05 Slope Aspect
06 Contour
07 Drainage Watershed
08 Terrain Ruggedness Curvature
09 QAQC Reference
Layer-үүдийг дараах дарааллаар байрлуулна.
License boundary
Buffer boundary
Drainage network
Contour
Slope / Aspect
Hillshade
DEM
Geology / satellite background
# 6.12 QA/QC шалгах эцсийн checklist
Final package гаргахаас өмнө дараах checklist-ийг бөглөнө.

| Шалгах зүйл | Тийм/Үгүй | Тайлбар |
| --- | --- | --- |
| Бүх raster EPSG:32647 болсон эсэх |  |  |
| Pixel size хадгалагдсан эсэх |  |  |
| NoData value зөв эсэх |  |  |
| DEM license + buffer-ээр зөв clip хийгдсэн эсэх |  |  |
| Hillshade олон azimuth-аар гарсан эсэх |  |  |
| Slope degree-ээр гарсан эсэх |  |  |
| Aspect 0-360 утгатай эсэх |  |  |
| Contour elev attribute-тэй эсэх |  |  |
| Drainage network terrain-тэй нийцэж байгаа эсэх |  |  |
| Watershed outlet зөв эсэх |  |  |
| TRI болон curvature raster зөв гарсан эсэх |  |  |
| Файлын нэршил стандарттай эсэх |  |  |
| Final folder structure бүрэн эсэх |  |  |
| QA/QC log бөглөгдсөн эсэх |  |  |

# 6.13 Common error болон засах арга
## Алдаа 1: DEM license boundary-тай давхцахгүй байна
Шалтгаан:
CRS буруу
Layer CRS буруу assign хийсэн
Project CRS буруу
Reproject хийгээгүй
Засах:
Layer Properties -> Information дээр CRS шалгах
Project CRS-г EPSG:32647 болгох
Raster -> Projections -> Warp ашиглан дахин reproject хийх
## Алдаа 2: Slope хэт өндөр эсвэл буруу гарч байна
Шалтгаан:
DEM geographic CRS буюу degree нэгжтэй байна
Z factor буруу
DEM reproject хийгдээгүй
Засах:
DEM-г EPSG:32647 руу reproject хийнэ
Slope дахин гаргана
Z factor = 1 ашиглана
## Алдаа 3: Drainage буруу чиглэлтэй гарч байна
Шалтгаан:
Fill sinks хийгээгүй
DEM NoData буруу
DEM edge effect
Threshold буруу
Засах:
Fill sinks дахин хийх
NoData утга шалгах
Buffer-тэй DEM ашиглах
Threshold өөрчилж дахин channel network гаргах
## Алдаа 4: Contour хэт шигүү байна
Шалтгаан:
Contour interval хэт бага
DEM noise ихтэй
Засах:
Interval 10 м -> 20 м болгох
Шаардлагатай бол DEM smoothing хийх
## Алдаа 5: Hillshade дээр шугаман бүтэц сайн харагдахгүй байна
Шалтгаан:
Зөвхөн нэг azimuth ашигласан
Contrast тохиргоо сул
Засах:
Azimuth 045, 090, 135, 315-аар нэмж гаргах
Symbology дээр contrast stretch хийх
Transparency болон blending mode тохируулах
# 6.14 Mineral exploration-д ашиглах тайлбар
DEM derivative output-уудыг ашиглан дараах геологийн тайлбаруудыг гаргаж болно.

| Output | Хайгуулын хэрэглээ |
| --- | --- |
| Hillshade | Fault, fracture, lineament, ridge, valley илрүүлэх |
| Slope | Access planning, erosion intensity, outcrop likelihood |
| Aspect | Налуугийн чиглэл, exposure condition |
| Contour | Relief, ridge-valley system, map layout |
| Drainage | Stream sediment sampling, anomaly tracing |
| Watershed | Upstream source area, catchment-based interpretation |
| TRI | Rugged terrain, structural scarp, resistant lithology |
| Curvature | Convex/concave landform, erosion/deposition pattern |

Энэ DEM багц нь дангаараа орд тогтоохгүй. Харин geological map, alteration, geochemistry, geophysics, known deposits, mineral occurrence data-тай overlay хийж ашигт малтмалын боломжит бүсүүдийг эрэмбэлэх суурь өгөгдөл болно.
