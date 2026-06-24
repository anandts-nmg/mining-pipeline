# Phase 0–1 — Inputs, Processing & Outputs (with methodology sources)

**Project:** Buduunkhad exploration licence **XV-023222 / L23222** · **Standard CRS:** EPSG:32647
**Status:** Phases 0 & 1 verified on real data (tag `v0.1.0`); deliverables published to Drive.

This report states, for Phases 0 and 1: the raw inputs, what is processed inside each phase, the
expected vs actual outputs, and **exactly where each is specified in the methodology PDF**.

**Source documents (in the repo root):**
- **Doc A (master):** `XV-023222_Buduunkhad_Exploration_Workflow_Methodology_78Inputs_v6_Phasewise_File_Processing_Output_Matrix.docx.pdf` (83 pp) — the authoritative workflow.
- **Doc B (Phase-1 detail):** `XV-023222_Buduunkhad_Phase1_Methodology.docx.pdf` (16 pp).

> *Монгол хувилбар доор байгаа — Mongolian version follows below.*

---

## 1. The 79 raw input files

Doc A defines **78** inputs; we reconciled the real archive and added **1** (the SAS
hand-interpreted 1:25k scan, listed in the Drive's own "…MasterRegister_**79**Inputs" doc) → **79**,
in **7 evidence groups**:

| Group | Count | Contents |
|---|--:|---|
| 01 Tectonic / Terrane (+ KMZ) | 8 | 7 tectonic/terrane map images + the **licence boundary KMZ (#8)** |
| 02 DEM (ALOS / ASTER GDEM) | 14 | ASTER-GDEM + ALOS-PALSAR DEM/hillshade/slope (each .tif with .tfw/.aux.xml/.ovr sidecars) |
| 03 KOMPSAT-2 MSC L1G | 24 | PAN + 4 multispectral bands (each .tif/.txt/.rpc/.eph), browse + thumbnail, + the licence **EULA PDF** |
| 04 Heavy Mineral / Stream Sediment / Field | 6 | heavy-mineral & stream-sediment result maps/legends, field route notebook, field observation table |
| 05 Geology / Mineral Prospectivity | 17 | 1:50k & 1:200k geology maps + legends, mineral occurrence/resource, prospectivity & source-material maps, occurrence registers, **+ SAS 1:25k scan (#79)** |
| 06 Regional Metallogenic L47B | 4 | 1:500k metallogenic map + legend + 2 report books |
| 07 Basemap / Sentinel-2 / ASTER | 6 | ASTER L1B (HDF), Sentinel-2 rasters, Google basemaps (0.15 m & 2.4 m) |
| **Total** | **79** | |

**Caveats:** 78 of 79 are physically present; the **KOMPSAT EULA PDF (#23) is missing** (a documented,
non-spatial gap). Full per-file list: `config/input_register.csv` and `…78Input_Master_Inventory.xlsx`.
**Where in the PDF:** Doc A **Section 1 — "Enhanced 78 raw input file register" (p. 3–17)** lists every
input with its **"Required processing action"** and **"Expected output"** columns; **Section 1A (p. 18–23)**
maps each input to its workflow phase.

---

## 2. Phase 0 — Raw Files Archive

| | |
|---|---|
| **Inputs** | All 79 raw files (Doc A: №1–78), sidecars kept with their parent file. |
| **Processing** | Inventory each file; compute a **SHA-256 fingerprint** (integrity baseline); copy files into an organized working archive by evidence group; verify the raw archive is **unchanged**. Raw is never edited/reprojected. |
| **Expected outputs (Doc A)** | `…_78Input_Master_Inventory.xlsx` · `…_Raw_Data_Integrity_Log.xlsx` · `…_Source_Data_Readme.docx` · `SHA-256_Checksum_Register.csv` |
| **Actual outputs** | All 4 ✅ + Phase-00 QA/QC log + working copies; **92 files checksummed**; gate **GO**. |

> **Doc A quotes (p. 36–37):** *Objective —* "Raw data-г өөрчлөхгүй архивлах, integrity/metadata/source
> хяналт тогтоох." *Expected outputs —* the four files above. *Decision gate —* **"All files archived,
> checksum complete, processing copies available."**

**Where in the PDF:** Doc A **Section 2 → "00. Raw Files Archive", p. 36–37** (subsections: *Objective ·
Input files · Software/equipment · Processing folder structure · Step-by-step methodology · QA/QC check ·
Expected outputs · Decision gate*).

---

## 3. Phase 1 — Data Audit & Master GIS Setup

| | |
|---|---|
| **Inputs** | All 79 (Doc A: №1–78); #8 boundary → master boundary layer; every raster/scan/table checked for CRS, metadata, sidecars, confidence. |
| **Processing** | Set project CRS to **EPSG:32647**; import boundary KMZ → GeoPackage (reprojected); generate **500 m–20 km buffers**; audit each raster's CRS/resolution/extent/NoData/bands; build the **13-layer Master GeoPackage**; assign **data confidence** (High/Medium/Low/Needs verification); write QA/QC + handover artefacts. |
| **Expected outputs (Doc A, 4 core)** | `…_Master_GIS_Database.gpkg` · `…_Master_QGIS_Project.qgz` · `…_CRS_Georeference_QAQC_Log.xlsx` · `…_Data_Confidence_Ranking.xlsx` |
| **Actual outputs** | 4 core ✅ + boundary GPKG (EPSG:32647) + buffer GPKG (5 rings) + file inventory + data-gap register + index-map PDF + desktop-study summary + Phase-2-ready list + QA/QC log = **11 deliverables**; gate **GO**. |

> **Doc A quotes (p. 37–38):** *Objective —* "78 input file-ийг GIS-ready болгох, EPSG:32647 master
> database үүсгэх." *Expected outputs —* the four core files above. *Decision gate —* **"Master GIS
> project opens without missing layers; critical data confidence recorded."**

**Where in the PDF:** Doc A **Section 2 → "01. Phase 1 — Data Audit and Master GIS Setup", p. 37–38**
(steps 6–12 incl. the 13 GeoPackage layer names). Doc B covers the same in **Section 3 inputs (p. 6),
Section 4 processing (p. 7–12), Section 8 deliverables (p. 16)**.

---

## 4. Exact PDF source map (Doc A)

| Topic | Section | PDF page |
|---|---|---|
| Per-file processing action + expected output (all inputs) | 1 — Enhanced 78 raw input file register | **3–17** |
| Which input feeds which phase | 1A — Explicit raw input assignment by workflow phase | **18–23** |
| Required traceability fields for every output | 1B.3 | **35–36** |
| Phase 0 input / processing / output | 2 → 00. Raw Files Archive | **36–37** |
| Phase 1 input / processing / output | 2 → 01. Phase 1 — Data Audit and Master GIS Setup | **37–38** |

*Where Doc A and Doc B disagree, the code follows Doc A (per `CLAUDE.md`); see
`METHODOLOGY_DISCREPANCIES.md`. Drive layout: `DRIVE_MAP.md`. Per-file Drive pins: `config/raw_manifest.csv`.*

---
---

# Үе шат 0–1 — Оролт, боловсруулалт, гаралт (аргачлалын эх сурвалжтай)

**Төсөл:** Бүдүүнхад XV-023222 / L23222 · **Стандарт CRS:** EPSG:32647
**Төлөв:** Үе шат 0 ба 1 бодит өгөгдөл дээр баталгаажсан (`v0.1.0`); бүтээгдэхүүнийг Drive-д нийтэлсэн.

Энэ тайлан нь Үе шат 0, 1-ийн түүхий оролт, дотор нь юу боловсруулдаг, хүлээгдсэн ба бодит гаралт,
мөн **аргачлалын PDF-ийн яг хаана заасан** болохыг харуулна.

**Эх баримтууд (repo root дотор):**
- **Doc A (үндсэн):** `…Methodology_78Inputs_v6_Phasewise…pdf` (83 хууд.) — гол аргачлал.
- **Doc B (Phase-1 дэлгэрэнгүй):** `…Phase1_Methodology…pdf` (16 хууд.).

## 1. 79 түүхий оролт файл

Doc A нь **78** оролт заасан; бодит архивтай тулгаж бид **1** (SAS гараар тайлбарласан 1:25k скан,
Drive-ийн "…MasterRegister_**79**Inputs" баримтад буй) нэмж **79** болгов. **7 evidence group:**

| Бүлэг | Тоо | Агуулга |
|---|--:|---|
| 01 Тектоник / Террейн (+ KMZ) | 8 | 7 тектоник зураг + **тусгай зөвшөөрлийн хил KMZ (#8)** |
| 02 DEM (ALOS / ASTER GDEM) | 14 | ASTER-GDEM + ALOS-PALSAR DEM/hillshade/slope (.tif + .tfw/.aux.xml/.ovr) |
| 03 KOMPSAT-2 MSC L1G | 24 | PAN + 4 multispectral (.tif/.txt/.rpc/.eph), browse + thumbnail, + **EULA PDF** |
| 04 Хүнд эрдэс / Урсгал хурдас / Хээр | 6 | хүнд эрдэс ба урсгал хурдасны зураг/тайлбар, хээрийн маршрут, ажиглалтын хүснэгт |
| 05 Геологи / Ашигт малтмалын хэтийн төлөв | 17 | 1:50k & 1:200k геологийн зураг/тайлбар, илрэл/нөөц, хэтийн төлөв, эх материал, бүртгэл, **+ SAS 1:25k (#79)** |
| 06 Региональ металлогени L47B | 4 | 1:500k металлогений зураг + тайлбар + 2 тайлан |
| 07 Basemap / Sentinel-2 / ASTER | 6 | ASTER L1B (HDF), Sentinel-2, Google basemap (0.15 м & 2.4 м) |
| **Нийт** | **79** | |

**Анхаарах:** 79-өөс 78 нь биетээр байгаа; **KOMPSAT EULA PDF (#23) дутуу** (баримтжуулсан, орон зайн бус
дутагдал). Бүрэн жагсаалт: `config/input_register.csv`. **PDF дэх байршил:** Doc A **Section 1 (хууд. 3–17)**
оролт бүрийн **"Required processing action"** ба **"Expected output"** баганатай; **Section 1A (хууд. 18–23)**
оролт бүрийг шаттай холбоно.

## 2. Үе шат 0 — Түүхий файлын архив

| | |
|---|---|
| **Оролт** | 79 түүхий файл (Doc A: №1–78); sidecar-уудыг эх файлтай хамт. |
| **Боловсруулалт** | Файл бүрийг бүртгэх; **SHA-256 хурууны хээ** тооцох; evidence group-аар эмх цэгцтэй архивт хуулах; түүхий архив **өөрчлөгдөөгүй** эсэхийг шалгах. Түүхийг засварлахгүй. |
| **Хүлээгдсэн гаралт (Doc A)** | `…_78Input_Master_Inventory.xlsx` · `…_Raw_Data_Integrity_Log.xlsx` · `…_Source_Data_Readme.docx` · `SHA-256_Checksum_Register.csv` |
| **Бодит гаралт** | 4 нь бүгд ✅ + Phase-00 QA/QC лог + working copy; **92 файл checksum**; gate **GO**. |

> **Doc A (хууд. 36–37):** *Зорилго —* "Raw data-г өөрчлөхгүй архивлах, integrity/metadata/source
> хяналт тогтоох." *Decision gate —* **"All files archived, checksum complete, processing copies available."**

**PDF дэх байршил:** Doc A **Section 2 → "00. Raw Files Archive", хууд. 36–37**.

## 3. Үе шат 1 — Өгөгдлийн аудит ба Master GIS бэлтгэл

| | |
|---|---|
| **Оролт** | 79 (Doc A: №1–78); #8 хил → master boundary; raster/скан/хүснэгт бүрийн CRS, metadata, sidecar, confidence шалгана. |
| **Боловсруулалт** | Project CRS-г **EPSG:32647** болгох; хилийн KMZ → GeoPackage (reproject); **500 м–20 км buffer** үүсгэх; raster бүрийн CRS/resolution/extent/NoData/band шалгах; **13 давхаргат Master GeoPackage** угсрах; **итгэлцлийн зэрэглэл** өгөх; QA/QC + хүлээлгэн өгөх баримт бичих. |
| **Хүлээгдсэн гаралт (Doc A, 4 үндсэн)** | `…_Master_GIS_Database.gpkg` · `…_Master_QGIS_Project.qgz` · `…_CRS_Georeference_QAQC_Log.xlsx` · `…_Data_Confidence_Ranking.xlsx` |
| **Бодит гаралт** | 4 үндсэн ✅ + хил GPKG (EPSG:32647) + buffer GPKG (5) + inventory + data-gap register + index-map PDF + desktop summary + Phase-2-ready list + QA/QC лог = **11 бүтээгдэхүүн**; gate **GO**. |

> **Doc A (хууд. 37–38):** *Зорилго —* "78 input file-ийг GIS-ready болгох, EPSG:32647 master database
> үүсгэх." *Decision gate —* **"Master GIS project opens without missing layers; critical data confidence recorded."**

**PDF дэх байршил:** Doc A **Section 2 → "01. Phase 1 …", хууд. 37–38** (алхам 6–12, 13 давхаргын нэр).
Doc B: оролт **Section 3 (хууд. 6)**, боловсруулалт **Section 4 (хууд. 7–12)**, бүтээгдэхүүн **Section 8 (хууд. 16)**.

## 4. PDF эх сурвалжийн зураглал (Doc A)

| Сэдэв | Section | PDF хууд. |
|---|---|---|
| Оролт бүрийн боловсруулалт + хүлээгдсэн гаралт | 1 — Enhanced 78 raw input file register | **3–17** |
| Оролт → шат холболт | 1A — Explicit raw input assignment | **18–23** |
| Гаралт бүрийн traceability талбар | 1B.3 | **35–36** |
| Үе шат 0 оролт / боловсруулалт / гаралт | 2 → 00. Raw Files Archive | **36–37** |
| Үе шат 1 оролт / боловсруулалт / гаралт | 2 → 01. Phase 1 — Data Audit and Master GIS Setup | **37–38** |

*Doc A ба Doc B зөрвөл код Doc A-г дагана (`CLAUDE.md`); `METHODOLOGY_DISCREPANCIES.md` үзнэ үү.
Drive бүтэц: `DRIVE_MAP.md`. Файл бүрийн Drive ID: `config/raw_manifest.csv`.*
