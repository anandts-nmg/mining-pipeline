# Phase 0 & 1 — Progress Report (Plain Language)

**Project:** Buduunkhad exploration licence **XV-023222 / L23222**
**Status:** ✅ Phases 0 and 1 completed and verified on the **real project data**
**Standard map system:** WGS 84 / UTM Zone 47N (EPSG:32647)

> *A Mongolian version follows below — Доор монгол хувилбар байгаа.*

---

## At a glance

We took the project's raw exploration data (old geology maps, satellite images,
terrain models, the licence boundary, field registers) and ran the **first two stages**
of the automated pipeline:

- **Phase 0 — "tidy and lock the raw files":** make a clean inventory of every raw file,
  fingerprint each one so we can prove it was never altered, and copy them into an
  organized working archive.
- **Phase 1 — "build the master map database":** convert the licence boundary into the
  standard coordinate system, create the 500 m – 20 km buffer zones, check every image's
  coordinates, and assemble one master GIS database with quality logs.

Both stages **passed their quality checkpoints ("GO")** on the real data. Every expected
deliverable was produced.

---

## What went in (the inputs)

- **79 raw data files** in total — 78 from the official methodology plus 1 extra
  (a hand-interpreted geology map) we found and added.
- These are the maps/images/boundary/registers — about **1.8 GB**.
- *(Note: the full project Drive is 700 GB+, but most of that is the **drone survey**, which
  belongs to a later stage and is **not needed** for Phases 0–1.)*

## What came out (the outputs) — expected vs delivered

| What the methodology asks for | Delivered? |
|---|---|
| Master inventory of all raw files | ✅ |
| Tamper-proof fingerprints (checksums) of every file | ✅ (92 files) |
| "Source data" readme + integrity log | ✅ |
| Licence boundary in the standard coordinate system | ✅ (EPSG:32647) |
| 5 buffer zones (500 m, 1 km, 5 km, 10 km, 20 km) | ✅ |
| Master GIS database (13 map layers) | ✅ |
| Coordinate quality-check log | ✅ |
| Data-confidence ranking + data-gap register | ✅ |
| Master map project file + handover package | ✅ |

**Result:** the deliverables match the plan, both quality gates said **GO**, and it all ran
on the real data — not test data.

---

## Problems we hit, and how we solved them

| # | Problem (in plain terms) | What we did | Why | Outcome |
|---|---|---|---|---|
| 1 | **The data is huge (700 GB+) and lives only in the cloud** — it won't fit on a laptop. | Worked out that Phases 0–1 only need ~1.8 GB (the maps/images/boundary). Pointed the tool at just that folder; left the 700 GB drone data alone. | The big 700 GB is drone imagery for a *later* stage. No need to download it now. | Runs comfortably on a normal computer. |
| 2 | **The same files were copied dozens of times**, and data from *other* projects was mixed in. | Built a "master list" (manifest) that pins each needed file to its one official copy. | So we never accidentally use a duplicate or the wrong project's file. | One trustworthy source of truth. |
| 3 | **The folder layout didn't match the plan documents** (the two method documents even disagreed with each other). | Mapped the real folders to the plan and wrote down every difference. | So the software finds the right files and staff aren't confused. | Documented in `DRIVE_MAP.md` and `METHODOLOGY_DISCREPANCIES.md`. |
| 4 | **Windows couldn't "see" some files** — the cloud folder was buried so deep that long file paths exceeded Windows' limit. | Created a short shortcut path to the data folder. | Windows can't handle file paths longer than 260 characters. | All files became visible; nothing skipped. |
| 5 | **One file is genuinely missing** (a KOMPSAT licence PDF). | Made the system record it as a "known gap" and keep going, instead of stopping the whole run. | A licence PDF shouldn't halt the entire process; it's logged for follow-up. | Pipeline completes; the gap is tracked for someone to supply later. |
| 6 | **A map-shape mismatch warning** appeared when saving the boundary. | Standardized boundary/area layers to the proper "multi-area" map type. | Cleaner output, no warnings, and it won't recur for future map layers. | Clean, warning-free result. |

We also set up **automatic quality checks** so the software stays correct as we keep building.

---

## Status & next steps

- **Done:** Phases 0 and 1 work end-to-end on the real data and produce all expected outputs.
- **Open item:** obtain the one missing KOMPSAT licence PDF (minor — it's a document, not map data).
- **Next:** Phase 2 — process the satellite and terrain imagery (crop to the licence area,
  convert to the standard coordinate system, compress for efficiency).

*Technical detail for the team lives in `DRIVE_MAP.md`, `METHODOLOGY_DISCREPANCIES.md`,
`docs/adr/0001-raw-data-storage-and-ingest.md`, and `config/raw_manifest.csv`.*

---
---

# Үе шат 0 ба 1 — Явцын тайлан (энгийн хэлээр)

**Төсөл:** Бүдүүнхад хайгуулын тусгай зөвшөөрөл **XV-023222 / L23222**
**Төлөв:** ✅ Үе шат 0 ба 1 нь **төслийн бодит өгөгдөл** дээр гүйцэтгэгдэж, баталгаажсан
**Стандарт зургийн систем:** WGS 84 / UTM Zone 47N (EPSG:32647)

---

## Товч тойм

Бид төслийн түүхий хайгуулын өгөгдлийг (хуучин геологийн зураг, хиймэл дагуулын зураг,
газрын гадаргын загвар, тусгай зөвшөөрлийн хил, хээрийн бүртгэл) аваад автоматжуулсан
процессын **эхний хоёр үе шатыг** ажиллууллаа:

- **Үе шат 0 — "түүхий файлуудыг цэгцлэх ба хамгаалах":** түүхий файл бүрийг бүртгэх,
  өөрчлөгдөөгүй гэдгийг батлах "хурууны хээ" (checksum) үүсгэх, эмх цэгцтэй ажлын архивт
  хуулах.
- **Үе шат 1 — "нэгдсэн зургийн өгөгдлийн сан байгуулах":** тусгай зөвшөөрлийн хилийг
  стандарт координатын системд хөрвүүлэх, 500 м – 20 км-ийн буфер бүсүүд үүсгэх, зураг
  бүрийн координатыг шалгах, чанарын бүртгэлтэйгээр нэг нэгдсэн GIS сан угсрах.

Хоёр үе шат хоёулаа бодит өгөгдөл дээр **чанарын шалгуураа давсан ("GO")**. Хүлээгдэж байсан
бүх бүтээгдэхүүн гарсан.

---

## Оролт (юу орсон бэ)

- Нийт **79 түүхий файл** — аргачлалын 78 файл дээр нэмж бид олж нэмсэн 1 файл
  (гараар тайлбарласан геологийн зураг).
- Эдгээр нь зураг/дүрс/хил/бүртгэлүүд — ойролцоогоор **1.8 ГБ**.
- *(Тэмдэглэл: бүх төслийн Drive нь 700 ГБ-аас их боловч ихэнх нь **дроны зураглал** бөгөөд
  дараагийн үе шатад хамаарах тул Үе шат 0–1-д **шаардлагагүй**.)*

## Гаралт (юу гарсан бэ) — хүлээгдсэн ба гаргасан

| Аргачлалын шаардлага | Гаргасан уу? |
|---|---|
| Бүх түүхий файлын нэгдсэн бүртгэл | ✅ |
| Файл бүрийн өөрчлөгдөшгүй "хурууны хээ" (checksum) | ✅ (92 файл) |
| "Эх сурвалжийн" танилцуулга + бүрэн бүтэн байдлын лог | ✅ |
| Тусгай зөвшөөрлийн хил стандарт координатад | ✅ (EPSG:32647) |
| 5 буфер бүс (500 м, 1 км, 5 км, 10 км, 20 км) | ✅ |
| Нэгдсэн GIS өгөгдлийн сан (13 давхарга) | ✅ |
| Координатын чанарын шалгалтын лог | ✅ |
| Өгөгдлийн итгэлцлийн зэрэглэл + дутуу өгөгдлийн бүртгэл | ✅ |
| Нэгдсэн зургийн төслийн файл + хүлээлгэн өгөх багц | ✅ |

**Үр дүн:** бүтээгдэхүүн төлөвлөгөөтэй тохирч, хоёр шалгуур **GO** гэж зөвшөөрсөн бөгөөд
бүгд туршилтын биш бодит өгөгдөл дээр ажиллав.

---

## Тулгарсан асуудлууд ба хэрхэн шийдсэн нь

| # | Асуудал (энгийнээр) | Бидний хийсэн зүйл | Яагаад | Үр дүн |
|---|---|---|---|---|
| 1 | **Өгөгдөл асар том (700 ГБ+) бөгөөд зөвхөн үүлэн дээр** — зөөврийн компьютерт багтахгүй. | Үе шат 0–1-д ердөө ~1.8 ГБ (зураг/дүрс/хил) хэрэгтэйг тогтоож, зөвхөн тэр хавтас руу чиглүүлэв; 700 ГБ дроны өгөгдлийг хөндөөгүй. | 700 ГБ нь *дараагийн* шатны дроны зураг. Одоо татах шаардлагагүй. | Энгийн компьютер дээр асуудалгүй ажиллана. |
| 2 | **Нэг файл олон арван удаа давхардсан**, бусад төслийн өгөгдөл холилдсон. | Хэрэгтэй файл бүрийг түүний цорын ганц албан ёсны хувьтай холбосон "мастер жагсаалт" (manifest) үүсгэв. | Давхардсан эсвэл өөр төслийн файлыг андуурч ашиглахгүйн тулд. | Нэг найдвартай эх сурвалж. |
| 3 | **Хавтасны бүтэц аргачлалын баримттай таарахгүй** (бүр хоёр аргачлалын баримт хоорондоо зөрүүтэй). | Бодит хавтсуудыг төлөвлөгөөтэй харгалзуулж, бүх зөрүүг бичиж тэмдэглэв. | Програм зөв файлаа олж, ажилтнууд эргэлзэхгүй байх үүднээс. | `DRIVE_MAP.md`, `METHODOLOGY_DISCREPANCIES.md`-д баримтжуулсан. |
| 4 | **Windows зарим файлыг "харж" чадаагүй** — хавтас хэт гүн байрласнаас файлын зам Windows-ийн хязгаарыг хэтэрсэн. | Өгөгдлийн хавтас руу богино товчлол (shortcut) зам үүсгэв. | Windows нь 260 тэмдэгтээс урт замыг боловсруулж чаддаггүй. | Бүх файл харагдах болж, нэг ч файл алгасагдсангүй. |
| 5 | **Нэг файл үнэхээр дутуу** (KOMPSAT-ийн лицензийн PDF). | Бүх ажлыг зогсоохын оронд "мэдэгдсэн дутагдал" гэж бүртгээд үргэлжлүүлэхээр тохируулав. | Лицензийн PDF бүхэл процессыг зогсоох ёсгүй; дараа нөхөхөөр логт тэмдэглэв. | Процесс дуусдаг; дутагдлыг хожим нөхөхөөр хянаж байгаа. |
| 6 | **Зургийн хэлбэрийн анхааруулга** хил хадгалах үед гарсан. | Хил/талбайн давхаргуудыг зөв "олон-талбай" (MultiPolygon) хэлбэрт стандартчиллаа. | Илүү цэвэр гаралт, анхааруулгагүй, ирээдүйд давтагдахгүй. | Цэвэр, анхааруулгагүй үр дүн. |

Мөн програм зөв хэвээр байхын тулд **автомат чанарын шалгалт** тохируулсан.

---

## Төлөв ба дараагийн алхам

- **Хийгдсэн:** Үе шат 0 ба 1 нь бодит өгөгдөл дээр бүрэн ажиллаж, хүлээгдсэн бүх гаралтыг гаргаж байна.
- **Нээлттэй асуудал:** дутуу байгаа KOMPSAT-ийн лицензийн PDF-ийг олж авах (бага зэргийн — энэ нь баримт бичиг болохоос зургийн өгөгдөл биш).
- **Дараагийн:** Үе шат 2 — хиймэл дагуул ба газрын гадаргын зургийг боловсруулах (тусгай зөвшөөрлийн талбайгаар тайрах, стандарт координатад хөрвүүлэх, үр ашигтай шахах).

*Багт зориулсан техникийн дэлгэрэнгүйг `DRIVE_MAP.md`, `METHODOLOGY_DISCREPANCIES.md`,
`docs/adr/0001-raw-data-storage-and-ingest.md`, `config/raw_manifest.csv`-аас үзнэ үү.*
