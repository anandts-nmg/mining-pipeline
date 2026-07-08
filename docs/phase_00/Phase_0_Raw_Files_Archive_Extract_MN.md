<!-- EXTRACT: Phase 00 has no standalone guide on Drive; its only methodology source is
     the v9 master (sections 00, 1A, 1B). Extracted verbatim from the master markdown in
     docs/ so every phase folder is self-contained for LLM ingestion. Do not edit content
     here without updating the master. -->

# Phase 00 — Raw Files Archive (extract from Methodology v9)

# 00. Raw Files Archive

| Subsection | Methodology detail |
| --- | --- |
| Зорилго | Raw data-г өөрчлөхгүй архивлах, integrity/metadata/source хяналт тогтоох. |
| Input files | Direct raw input files: №1-78 бүх raw input file. Яг filename, evidence group, primary phase, methodology action-ийг Section 1A-д бүрэн заасан. Sidecar files (.tfw, .aux.xml, .ovr, .rpc, .eph, .txt) parent raster/image-ээс салгахгүй. |
| Software / equipment | File system, checksum utility, inventory workbook. |

## Processing folder structure
00_Raw_Files_Archive/
├── 01_Tectonic_Terrane_KMZ
├── 02_DEM_ALOS_ASTERGDEM
├── 03_KOMPSAT2_MSC_L1G
├── 04_HeavyMineral_StreamSediment_Field
├── 05_Geology_Mineral_Prospectivity
├── 06_Regional_Metallogenic_L47B
└── 07_Basemap_Sentinel2_ASTER
## Step-by-step methodology
- 78 raw input файлыг evidence group-ийн дагуу raw archive хавтас руу байршуулна.
- Original filename, standardized filename, file type, source note, owner/responsible person, read status, processing copy status бүртгэнэ.
- SHA-256 checksum үүсгэж integrity log-д бичнэ.
- Sidecar файлуудыг parent file-аас салгахгүй: .tfw/.aux.xml/.ovr/.rpc/.eph/.txt metadata нь тухайн raster/image bundle-ийн хэсэг.
- Raw file дээр rename/overwrite/clip/reproject хийхгүй; working copy-г дараагийн phase-д хуулна.
## QA/QC check

| QA/QC item | Acceptance note |
| --- | --- |
| Checksum match | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Raw overwrite хийгдээгүй | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Sidecar completeness | Recorded in phase QA/QC log; reviewer/date/decision required. |
| Source note and owner registered | Recorded in phase QA/QC log; reviewer/date/decision required. |

## Expected outputs
- XV-023222_Buduunkhad_78Input_Master_Inventory.xlsx
- XV-023222_Buduunkhad_Raw_Data_Integrity_Log.xlsx
- XV-023222_Buduunkhad_Source_Data_Readme.docx
- SHA-256_Checksum_Register.csv
## Decision gate / next phase condition
- All files archived, checksum complete, processing copies available.

## Phase-00 rows from the master input-control matrices

### §1A.1 Phase-level input control

| Workflow phase | Exact direct raw input № | How to apply | Handover note |
| --- | --- | --- | --- |
| 00 Raw Files Archive | №1-78 | Бүх raw file болон sidecar файлыг read-only archive-д бүртгэж checksum үүсгэнэ. | All later phases use working copies only. |

### §1B.1 Software / output summary

| Phase folder | Raw inputs | Software | Outputs |
| --- | --- | --- | --- |
| 00_Raw_Files_Archive | 1-78 | File system, checksum utility, Excel | Master inventory, checksum register, source data README |

## Cross-cutting rules that bind Phase 00 outputs (§1A.3 / §1B.3)

## 1A.3 Mandatory rule for every phase
- Phase бүрийн аргачлалд input-ийг “geology files” эсвэл “remote sensing files” гэж дангаар бичихгүй; Section 1A.2 дахь raw input № болон exact filename-ийг заавал ашиглана.
- Output layer/report/table бүрт source_input_no, source_raw_filename, source_group, source_phase, processing_version, confidence, limitation талбар/мөр хадгална.
- Historical scanned map-derived evidence нь validation_status = Historical only байхаас field/lab confirmed evidence-тэй холигдохгүй.
- Remote sensing, DEM, KOMPSAT, Sentinel, ASTER, drone/LiDAR, pXRF output нь хүдэржилтийн баталгаа биш; support evidence гэж тэмдэглэнэ.

## 1B.3 Required source-traceability fields for every output

| Output field | Required value | Purpose |
| --- | --- | --- |
| source_raw_input_no | 1-78 дугаар | Output бүрийг аль raw input-оос үүссэнтэй audit trail-аар холбох |
| source_raw_filename | Exact raw filename | Файлын нэр өөрчлөгдөх/холилдох эрсдэлийг хаах |
| processing_phase | 00/01/02/03/03A/04... | Аль workflow шатанд боловсруулсан болохыг тодруулах |
| processing_software | QGIS / SNAP / GDAL / Excel / QField / etc. | Дахин боловсруулахад reproducibility хангах |
| processing_action | Georeference / reproject / digitize / extract / score / QAQC | Юу хийснийг тодорхой бичих |
| output_filename | Standardized output file name | Deliverable package-д нэг мөр нэршилтэй хадгалах |
| qaqc_status | Draft / Checked / Approved / Rejected | Decision-grade биш output-г буруу ашиглахаас хамгаалах |
| validation_status | Historical only / Field checked / Sampled / Lab confirmed | Historical evidence ба баталгаажсан evidence-г салгах |

