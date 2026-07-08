<!-- source: 99_Final_Deliverables_Detailed_Guide_MN.docx (converted from Word; canonical form for LLM ingestion) -->

99. Final Deliverables ажлыг хийх дэлгэрэнгүй заавар
Final report package, GIS package, QA/QC, metadata, target ranking, follow-up plan болон archive/checksum package бэлтгэх аргачлал
# 1. Ерөнхий мэдээлэл

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Бүх output-ийг стандарт folder package болгон бүрдүүлэх. |
| Input files | Input files: All phase outputs and QA/QC logs, with source traceability back to raw input files No1-78. Final package must include the exact raw input filename reference from Section 1A for every evidence layer/report/table/map. |
| Software / equipment | QGIS, Office, PDF export, archive/checksum tools. |

Энэ ажлын зорилго нь өмнөх бүх phase-үүдээр боловсруулсан тайлан, GIS, remote sensing, drone/LiDAR, field form, assay/QAQC, target ranking, follow-up work plan зэрэг бүх эцсийн бүтээгдэхүүнийг нэг стандарттай, шалгагдсан, traceable буюу эх input файл руугаа буцаан мөрдөх боломжтой Final Deliverables Package болгон бэлтгэхэд оршино.
# 2. Ажлын үндсэн зорилго
1.  Бүх эцсийн output файлуудыг нэг folder package-д стандарт бүтэцтэйгээр цуглуулах.
2.  Файл бүрийг эх input data, processing step, reviewer, QA/QC status-тэй холбож бүртгэх.
3.  GIS, тайлан, зураг, хүснэгт, field form, assay, target ranking, follow-up plan зэрэг бүх deliverables-ийг EPSG:32647 стандарттай нэгтгэх.
4.  Final package дотор ямар файл, ямар эх сурвалж дээр үндэслэсэн, хэн шалгасан, ямар хязгаарлалттай болохыг тодорхой бичих.
5.  Management review болон technical review-д бэлэн final archive/checksum package гаргах.
# 3. Ашиглах input data
Энэ ажлыг хийхэд өмнөх бүх phase-ийн output-ууд input болно. Үүнд:
- Phase report-ууд
- GIS project file
- GIS layer package
- QGIS / QField package
- Remote sensing interpretation бүтээгдэхүүнүүд
- Drone / LiDAR / orthomosaic / point cloud бүтээгдэхүүнүүд
- Field observation form
- pXRF register
- Assay table
- QA/QC table
- Target ranking matrix
- Decision matrix
- Follow-up work plan
- Metadata file
- QA/QC log
- Эх input raw file-ийн бүртгэл буюу raw input filename reference
Final package-д орох бүх файл нь raw input file No.1–78 буюу эх өгөгдлийн дугаартайгаа холбогдсон байх ёстой.
# 4. Ашиглах software / equipment
- QGIS
- Microsoft Word
- Microsoft Excel
- PDF export tool
- Archive tool буюу ZIP / 7-Zip / WinRAR
- Checksum tool
- Folder comparison tool
- File naming checker
- Metadata editor
- QA/QC log template
# 5. Final deliverables folder structure үүсгэх
Эхлээд үндсэн folder үүсгэнэ.
99_Final_Deliverables/
Дотор нь дараах 9 үндсэн subfolder-ийг яг энэ дарааллаар үүсгэнэ.
99_Final_Deliverables/
|-- 01_Reports
|-- 02_GIS_GPKG_QGIS_QField
|-- 03_Remote_Sensing_Products
|-- 04_Drone_LiDAR_Orthomosaic_PointCloud
|-- 05_Field_Forms_and_pXRF_Registers
|-- 06_Assay_and_QAQC_Tables
|-- 07_Target_Ranking_and_Decision_Matrix
|-- 08_Follow_Up_Work_Plans
`-- 09_Final_Report_Package
Folder нэрийг өөрчлөхгүй. Дугаарлалт, underscore, том жижиг үсгийг нэг мөр мөрдөнө.
# 6. 01_Reports folder-д хийх ажил
Энэ folder-д бүх эцсийн тайлангуудыг оруулна.
## 6.1 Оруулах боломжтой файлууд
- Final technical report
- Geological interpretation report
- Remote sensing interpretation report
- Drone / LiDAR processing report
- Field mapping report
- Assay interpretation report
- QA/QC summary report
- Target generation report
- Target ranking report
- Follow-up recommendation report
## 6.2 Файл бүрт байх мэдээлэл
- Project name
- License number
- Area name
- Coordinate reference system: EPSG:32647
- Data source list
- Processing method
- Result summary
- Limitation note
- Reviewer name
- Date
- Version number
## 6.3 File naming жишээ
ProjectName_Final_Technical_Report_v01_2026-06-05.pdf
ProjectName_Geological_Interpretation_Report_v01_2026-06-05.docx
ProjectName_Target_Ranking_Report_v01_2026-06-05.pdf
# 7. 02_GIS_GPKG_QGIS_QField folder-д хийх ажил
Энэ folder-д GIS-тэй холбоотой бүх final бүтээгдэхүүнийг оруулна.
## 7.1 Оруулах файлууд
- QGIS project file
- GeoPackage file
- Shapefile ашигласан бол бүх бүрдэлтэй нь
- QField package
- Styled layer file
- Layout template
- Final map export
- CRS metadata
- Layer register
## 7.2 Заавал шалгах зүйлс
1.  Бүх layer нэг CRS буюу EPSG:32647 дээр байгаа эсэх.
2.  Geometry error байгаа эсэх.
3.  Attribute table хоосон эсвэл дутуу талбартай эсэх.
4.  Layer name стандарттай эсэх.
5.  Duplicate layer байгаа эсэх.
6.  QField-ээс ирсэн data алдагдаагүй эсэх.
7.  Project file relative path ашиглаж байгаа эсэх.
8.  Map layout export зөв хийгдсэн эсэх.
## 7.3 GIS package-ийн дэд бүтэц
02_GIS_GPKG_QGIS_QField/
|-- QGIS_Project
|-- GeoPackage
|-- Layers
|-- Styles
|-- Layouts
|-- QField_Package
|-- Exported_Maps
`-- Metadata
# 8. 03_Remote_Sensing_Products folder-д хийх ажил
Энэ folder-д remote sensing боловсруулалтын эцсийн бүтээгдэхүүнийг оруулна.
## 8.1 Оруулах бүтээгдэхүүнүүд
- Multispectral interpretation image
- ASTER / Sentinel / Landsat interpretation product
- Alteration map
- Lineament map
- Structure interpretation map
- Lithological interpretation raster
- Mineral index image
- Remote sensing target map
- Processing note
- Raster metadata
## 8.2 Metadata-д оруулах мэдээлэл
- Sensor name
- Acquisition date
- Processing date
- Processing method
- Band combination
- Index formula used
- CRS
- Pixel size
- Limitation note
- Interpreter / reviewer
## 8.3 Шалгах зүйлс
- Raster CRS EPSG:32647 эсэх
- Extent нь license area-тай давхцаж байгаа эсэх
- NoData утга зөв эсэх
- Raster clipping зөв хийгдсэн эсэх
- Final map дээр scale, north arrow, legend байгаа эсэх
- Interpretation layer нь GIS package-д орсон эсэх
# 9. 04_Drone_LiDAR_Orthomosaic_PointCloud folder-д хийх ажил
Энэ folder-д drone, LiDAR, orthomosaic, point cloud зэрэг high-resolution data бүтээгдэхүүн орно.
## 9.1 Оруулах бүтээгдэхүүнүүд
- Orthomosaic
- DEM
- DSM
- DTM
- Point cloud
- Contour
- Hillshade
- Slope map
- Flight log
- Ground control point register
- Accuracy report
- Processing report
## 9.2 Дэд folder-ийн санал болгож буй бүтэц
04_Drone_LiDAR_Orthomosaic_PointCloud/
|-- Orthomosaic
|-- DEM_DSM_DTM
|-- PointCloud
|-- Contours
|-- Hillshade_Slope
|-- Flight_Logs
|-- GCP_Checkpoints
`-- Processing_Report
## 9.3 QA/QC шалгалт
- Orthomosaic georeference зөв эсэх
- GCP ашигласан бол residual error бүртгэгдсэн эсэх
- DEM / DSM pixel size бүртгэгдсэн эсэх
- Point cloud file corrupt болоогүй эсэх
- LAS / LAZ metadata бүрэн эсэх
- Final raster GIS дээр зөв нээгдэж байгаа эсэх
- Coordinate system EPSG:32647 эсэх
# 10. 05_Field_Forms_and_pXRF_Registers folder-д хийх ажил
Энэ folder-д талбайн бүх observation, sample, pXRF, route, structural measurement, photo log зэрэг data орно.
## 10.1 Оруулах файлууд
- Field observation form
- Sample register
- pXRF register
- Structural measurement register
- Route / traverse register
- Photo register
- Outcrop description
- Alteration observation
- Mineralization observation
- Field QA/QC note
## 10.2 Шалгах зүйлс
1.  Observation ID давхардаагүй эсэх.
2.  Sample ID давхардаагүй эсэх.
3.  Coordinate бүрэн эсэх.
4.  Coordinate system тодорхой бичигдсэн эсэх.
5.  Photo ID observation ID-тэй холбогдсон эсэх.
6.  pXRF measurement sample ID-тэй таарч байгаа эсэх.
7.  Null буюу хоосон заавал бөглөх талбар байгаа эсэх.
8.  Field form болон GIS layer хооронд ID зөрүү байгаа эсэх.
## 10.3 Файл нэрлэх жишээ
ProjectName_Field_Observation_Register_v01.xlsx
ProjectName_pXRF_Register_v01.xlsx
ProjectName_Sample_Register_v01.xlsx
ProjectName_Photo_Log_v01.xlsx
# 11. 06_Assay_and_QAQC_Tables folder-д хийх ажил
Энэ folder-д лабораторийн assay result болон QA/QC хүснэгтүүд орно.
## 11.1 Оруулах файлууд
- Assay result table
- Certified reference material result
- Blank sample result
- Duplicate sample result
- Standard sample result
- QA/QC summary table
- Detection limit table
- Laboratory certificate
- Sample dispatch form
- Chain of custody document
## 11.2 QA/QC шалгалт
- Sample ID field data-тай таарч байгаа эсэх
- Assay result sample dispatch-тэй таарч байгаа эсэх
- Duplicate sample result хүлээн зөвшөөрөгдөх хэмжээнд байгаа эсэх
- Blank sample contamination байгаа эсэх
- Standard sample result expected value-тэй ойролцоо эсэх
- Laboratory certificate бүрэн эсэх
- Unit conversion зөв эсэх
- Detection limit тэмдэглэл орсон эсэх
- QA/QC failure байвал decision note бичигдсэн эсэх
QA/QC result бүр дараах статустай байна.
Pass
Review required
Fail
Not applicable
# 12. 07_Target_Ranking_and_Decision_Matrix folder-д хийх ажил
Энэ folder-д prospect, anomaly, target ranking болон decision matrix орно.
## 12.1 Оруулах файлууд
- Target ranking matrix
- Prospect register
- Anomaly register
- Target score table
- Decision matrix
- Target map
- Follow-up priority table
- Risk / uncertainty table
- Recommended next phase table
## 12.2 Target ranking хийх шалгуур
- Geological favorability
- Alteration intensity
- Structural control
- Geochemical anomaly strength
- Geophysical support
- Remote sensing support
- Field evidence
- Assay support
- Nearby deposit / occurrence relation
- Access and logistics
- Data confidence
- Exploration risk
## 12.3 Target class ангилал
Priority 1 - Immediate follow-up
Priority 2 - Detailed field check required
Priority 3 - Additional data required
Priority 4 - Low priority / archive
## 12.4 Decision matrix-ийн боломжит шийдвэр
Advance to next phase
Conduct follow-up mapping and sampling
Conduct geophysics
Conduct trenching
Conduct drilling preparation
Hold for additional data
Archive / no immediate work
# 13. 08_Follow_Up_Work_Plans folder-д хийх ажил
Энэ folder-д дараагийн шатны хайгуулын ажлын төлөвлөгөөг оруулна.
## 13.1 Оруулах файлууд
- Follow-up mapping plan
- Sampling plan
- Geophysical survey plan
- Trenching plan
- Drilling preparation plan
- Budget estimate
- Timeline
- Personnel and equipment plan
- HSE plan
- Access and logistics plan
## 13.2 Follow-up plan бүрийн агуулга
- Target ID
- Location
- Work type
- Objective
- Method
- Expected output
- Required personnel
- Required equipment
- Estimated duration
- Estimated cost
- Risk and mitigation
- Decision gate
## 13.3 Жишээ
Target T-01:
Recommended work: Detailed mapping, rock-chip sampling, soil grid sampling.
Objective: Confirm Cu-Au mineralization potential.
Decision gate: If assay result confirms anomalous Cu-Au, advance to trenching/geophysics.
# 14. 09_Final_Report_Package folder-д хийх ажил
Энэ folder нь management болон technical review-д өгөх эцсийн багц байна.
## 14.1 Оруулах зүйлс
- Final report PDF
- Final report DOCX
- Executive summary
- Final maps
- Final GIS package reference
- Final target ranking table
- Final QA/QC summary
- Final follow-up recommendation
- Metadata register
- File inventory
- Checksum file
- Archive ZIP package
## 14.2 Final report package-ийн бүтэц
09_Final_Report_Package/
|-- Final_Report_DOCX
|-- Final_Report_PDF
|-- Executive_Summary
|-- Final_Maps
|-- Final_Target_Ranking
|-- Final_QAQC_Summary
|-- Metadata_Register
|-- File_Inventory
|-- Checksum
`-- Archive_ZIP
# 15. Metadata register бэлтгэх
Final package-д заавал metadata register оруулна. Metadata register-д дараах баганууд байна.

| Багана | Тайлбар |
| --- | --- |
| File ID | Файлын дотоод дугаар |
| Folder name | Аль folder-т байгаа |
| File name | Яг final filename |
| File type | PDF, DOCX, XLSX, GPKG, TIF гэх мэт |
| Source input file | Raw input No.1-78-тай холбох |
| Processing phase | Аль phase дээр үүссэн |
| CRS | EPSG:32647 эсэх |
| Processing date | Боловсруулсан огноо |
| Processor | Боловсруулсан хүн |
| Reviewer | Шалгасан хүн |
| QA/QC status | Pass / Review / Fail |
| Limitation note | Хязгаарлалт |
| Final decision | Final-д оруулах эсэх |

# 16. File inventory бэлтгэх
File inventory нь final package дотор байгаа бүх файлын бүртгэл байна. Inventory-д дараах мэдээллийг заавал оруулна.
- Folder path
- File name
- File extension
- File size
- Version
- Date modified
- Responsible person
- Final / draft status
- Include / exclude decision
- Remarks
Файл бүрийг нэг бүрчлэн бүртгэнэ. Folder-д байгаа боловч inventory-д байхгүй файл байж болохгүй.
# 17. Naming consistency шалгах
Бүх final файлын нэр дараах зарчмыг баримтална.
- Project name байна
- Data/product type байна
- Version number байна
- Огноо байна
- Space ашиглахгүй, underscore ашиглана
- Монгол үсэг, тусгай тэмдэгт, slash, comma, bracket аль болох ашиглахгүй
- “final_final”, “new”, “copy”, “last” гэх мэт тодорхойгүй үг хэрэглэхгүй
## 17.1 Зөв жишээ
Buduunkhad_Final_Technical_Report_v01_2026-06-05.pdf
Buduunkhad_Target_Ranking_Matrix_v01_2026-06-05.xlsx
Buduunkhad_GIS_Package_EPSG32647_v01_2026-06-05.zip
## 17.2 Буруу жишээ
final report last.pdf
new map copy.tif
target ranking final final.xlsx
# 18. CRS шалгалт хийх
Final package-д орох spatial data бүр дээр CRS шалгана. Заавал байх CRS:
EPSG:32647
WGS 84 / UTM Zone 47N
## 18.1 Шалгах зүйлс
- QGIS project CRS
- Layer CRS
- Raster CRS
- GeoPackage CRS
- Drone orthomosaic CRS
- DEM / DSM CRS
- Export map CRS
- Metadata CRS field
## 18.2 CRS өөр байвал хийх алхам
1.  Original file-г backup хийнэ.
2.  QGIS дээр Reproject Layer ашиглана.
3.  EPSG:32647 болгож хадгална.
4.  Metadata register-д өөрчлөлтийг тэмдэглэнэ.
5.  QA/QC log-д decision note бичнэ.
# 19. QA/QC log бөглөх
QA/QC log-д дараах үндсэн шалгалтууд орно.

| QA/QC item | Acceptance note |
| --- | --- |
| Folder structure complete | Phase QA/QC log-д reviewer/date/decision бичигдсэн байна |
| Files named consistently | Phase QA/QC log-д reviewer/date/decision бичигдсэн байна |
| Metadata and limitations included | Phase QA/QC log-д reviewer/date/decision бичигдсэн байна |
| Final QA/QC notes included | Phase QA/QC log-д reviewer/date/decision бичигдсэн байна |

Нэмэлтээр дараах шалгалтыг оруулна.

| QA/QC item | Шалгах зүйл |
| --- | --- |
| CRS consistency | EPSG:32647 эсэх |
| Source traceability | Raw input No.1-78 reference орсон эсэх |
| Duplicate file check | Давхардсан файл байгаа эсэх |
| Corrupt file check | Файл нээгдэж байгаа эсэх |
| Version control | v01, v02 гэх мэт хувилбар зөв эсэх |
| Review status | Reviewer баталгаажуулсан эсэх |
| Limitation note | Хязгаарлалт бичигдсэн эсэх |
| Final package completeness | Бүх expected output орсон эсэх |

# 20. Checksum үүсгэх
Final package-д орсон бүх final файлын integrity-г баталгаажуулахын тулд checksum үүсгэнэ.
## 20.1 Хийх алхам
1.  Final package-д орсон бүх файлыг шалгаж нээж үзнэ.
2.  Draft болон temporary file-уудыг устгана.
3.  Checksum tool ашиглан MD5 эсвэл SHA256 checksum үүсгэнэ.
4.  Checksum result-ийг дараах нэртэй хадгална.
ProjectName_Final_Deliverables_Checksum_SHA256_v01.txt
Checksum file-д дараах мэдээлэл орно.
- File path
- File name
- Hash value
- Generated date
- Generated by
# 21. Archive package үүсгэх
Бүх folder structure, report, GIS, raster, table, metadata, QA/QC log бүрэн болсон бол final archive үүсгэнэ.
## 21.1 Archive нэрлэх жишээ
ProjectName_99_Final_Deliverables_EPSG32647_v01_2026-06-05.zip
## 21.2 Archive хийхээс өмнө шалгах зүйл
- Бүх файл нээгдэж байгаа эсэхийг шалгана
- Нууц эсвэл draft файл үлдээгүй эсэхийг шалгана
- Temporary файл устгана
- Duplicate файл шалгана
- Metadata register шинэчилнэ
- QA/QC log хаана
- Checksum үүсгэнэ
# 22. Step-by-step workflow
## Алхам 1. Final folder үүсгэх
99_Final_Deliverables folder үүсгээд 01–09 хүртэлх subfolder-үүдийг яг стандарт нэрээр үүсгэнэ.
## Алхам 2. Өмнөх phase-үүдийн output-уудыг цуглуулах
Phase бүрийн final гэж баталгаажсан output файлуудыг цуглуулна. Draft, temporary, working file-уудыг шууд final folder-д оруулахгүй.
## Алхам 3. Файл бүрийн эх сурвалжийг тогтоох
Файл бүр ямар raw input file No.1–78 дээр үндэслэсэн болохыг metadata register-д бичнэ.
## Алхам 4. CRS шалгах
Spatial data бүрийг QGIS дээр нээж CRS-г шалгана. Бүгд EPSG:32647 байх ёстой.
## Алхам 5. Folder бүрт тохирох файлуудыг ангилах
Report-ыг 01_Reports руу, GIS-ийг 02_GIS рүү, remote sensing-ийг 03 руу гэх мэтээр ангилж байршуулна.
## Алхам 6. Naming standard шалгах
Файл бүрийн нэр project name, product type, version, date гэсэн бүтэцтэй эсэхийг шалгана.
## Алхам 7. Metadata register бөглөх
Final package-д орох бүх файлыг metadata register-д нэг бүрчлэн бүртгэнэ.
## Алхам 8. QA/QC log бөглөх
Folder structure, file naming, metadata, CRS, source traceability, limitation note, reviewer decision-г шалгана.
## Алхам 9. Final report package бэлтгэх
09_Final_Report_Package дотор final PDF, DOCX, executive summary, final maps, QA/QC summary, target ranking, follow-up recommendation-ийг нэгтгэнэ.
## Алхам 10. Checksum үүсгэх
Final package-д орсон бүх файлын checksum үүсгэж хадгална.
## Алхам 11. Archive үүсгэх
99_Final_Deliverables folder-ийг ZIP болгож final archive package үүсгэнэ.
## Алхам 12. Management / technical review-д шилжүүлэх
Final package-г reviewer-д өгч, decision gate нөхцөлийг баталгаажуулна.
# 23. Expected outputs
Энэ ажлын төгсгөлд дараах бүтээгдэхүүнүүд гарсан байна.
- Final report package
- GIS package
- Remote sensing products
- Drone / LiDAR products
- Field forms
- pXRF registers
- Assay tables
- QA/QC tables
- Target ranking matrix
- Decision matrix
- Follow-up work plans
- Metadata register
- File inventory
- Checksum file
- Final ZIP archive package
# 24. Decision gate / next phase condition
Энэ phase дууссан гэж үзэх нөхцөл:
1.  Final package folder structure бүрэн байна.
2.  Бүх report, GIS, remote sensing, drone/LiDAR, field form, assay, QA/QC, target ranking, follow-up plan багцад орсон байна.
3.  Бүх spatial data EPSG:32647 CRS-тэй байна.
4.  Файл бүр raw input source reference-тэй байна.
5.  Metadata register бүрэн бөглөгдсөн байна.
6.  QA/QC log reviewer/date/decision-тэй байна.
7.  Final package checksum үүссэн байна.
8.  ZIP archive үүссэн байна.
9.  Management болон technical review-д өгөхөд бэлэн байна.
# 25. Final acceptance checklist

| Шалгах зүйл | Төлөв |
| --- | --- |
| 99_Final_Deliverables folder үүссэн | ☐ |
| 01–09 subfolder бүрэн үүссэн | ☐ |
| Report-ууд бүрэн орсон | ☐ |
| GIS package бүрэн орсон | ☐ |
| Remote sensing бүтээгдэхүүнүүд орсон | ☐ |
| Drone/LiDAR бүтээгдэхүүнүүд орсон | ☐ |
| Field form болон pXRF register орсон | ☐ |
| Assay болон QA/QC table орсон | ☐ |
| Target ranking болон decision matrix орсон | ☐ |
| Follow-up work plan орсон | ☐ |
| Final report package бүрдсэн | ☐ |
| Metadata register бөглөгдсөн | ☐ |
| File inventory бөглөгдсөн | ☐ |
| CRS EPSG:32647 шалгагдсан | ☐ |
| Source traceability бүрэн | ☐ |
| File naming consistent | ☐ |
| Limitation note орсон | ☐ |
| Reviewer/date/decision бүртгэгдсэн | ☐ |
| Checksum үүссэн | ☐ |
| Final ZIP archive үүссэн | ☐ |

# 26. Дүгнэлт
Энэ ажил нь хайгуулын бүх боловсруулсан материалыг final review-д бэлэн болгох хамгийн сүүлийн багцлалтын phase юм. Гол шаардлага нь зөвхөн файлуудыг нэг folder-т хуулж хийх биш, харин файл бүрийн эх сурвалж, боловсруулалтын үе шат, CRS, QA/QC төлөв, reviewer decision, metadata, limitation note-ийг бүрэн бүртгэж, менежмент болон техникийн баг шууд шалгах боломжтой final deliverables package үүсгэх явдал юм.
