# Buduunkhad — Phase 0 & 1, in plain language

**In one line:** we organized the project's raw geology & satellite data and built the first
master map — and it works.

*(Монгол хувилбар доор байна — Mongolian version below.)*

---

## What we were doing

Picture the raw data as a big box of old maps, satellite photos, and reports.

- **Phase 0 — Sort & safeguard.** Make a list of everything, give each file a tamper-proof
  "fingerprint" (so we can prove nothing was changed), and file tidy copies — **without ever
  touching the originals**.
- **Phase 1 — Build the master map.** Put the licence boundary onto the standard map grid, draw
  the distance rings around it (500 m to 20 km), check that every image sits on the correct
  coordinates, and combine everything into **one master map database** the next stages build on.

## What went in, and what came out

- **Went in:** 79 raw files (~2 GB) — old geology maps, satellite images, terrain models, the
  licence boundary, and field records.
- **Came out:** a tidy file list + fingerprints, the licence boundary and its distance rings on
  the standard map grid, and one master map database — plus quality-check logs.

## Did it work?

**Yes. ✅** Both stages passed their quality checkpoints on the **real** data (not test data), and
a copy of the final results is published to Google Drive for the team to see.

## Bumps along the way (and how we handled them)

- **The data was huge and online-only (700+ GB).** We found only ~2 GB is actually needed now;
  the rest is drone-survey data for a later stage. → We used just the part we needed.
- **Some files were "invisible" to the computer** because of a Windows limit on very long file
  paths. → We made a short shortcut so everything was readable.
- **One licence document was missing.** → We noted it as a known gap and carried on (it's a
  document, not map data).
- **A GitHub login mix-up blocked an upload once.** → We switched to the correct account; fixed.

## What's next

**Phase 2** — process the satellite and terrain images (trim to the licence area, put them on the
standard map grid, compress them) — then publish those results the same way.

> Need the detail? The other reports in this folder have the full breakdown, the exact methodology
> page references, and the technical notes.

---
---

# Бүдүүнхад — Үе шат 0 ба 1, энгийн хэлээр

**Нэг мөрөөр:** төслийн түүхий геологи, хиймэл дагуулын өгөгдлийг цэгцэлж, эхний нэгдсэн зургийг
бүтээлээ — амжилттай.

## Бид юу хийсэн бэ

Түүхий өгөгдлийг хуучин зураг, хиймэл дагуулын фото, тайлангаар дүүрэн том хайрцаг гэж төсөөл.

- **Үе шат 0 — Цэгцлэх ба хамгаалах.** Бүгдийг жагсаах, файл бүрт өөрчлөгдөшгүй "хурууны хээ" өгөх
  (юу ч өөрчлөгдөөгүйг батлахын тулд), эх хувийг **огт хөндөлгүйгээр** цэвэр хуулбар хийх.
- **Үе шат 1 — Нэгдсэн зураг бүтээх.** Тусгай зөвшөөрлийн хилийг стандарт зургийн торонд буулгах,
  тойрсон зайн бүсүүдийг (500 м – 20 км) зурах, зураг бүр зөв координат дээр байгааг шалгах, бүгдийг
  дараагийн шатны суурь болох **нэг нэгдсэн зургийн санд** нэгтгэх.

## Юу орж, юу гарсан бэ

- **Орсон:** 79 түүхий файл (~2 ГБ) — хуучин геологийн зураг, хиймэл дагуулын зураг, газрын гадаргын
  загвар, тусгай зөвшөөрлийн хил, хээрийн бүртгэл.
- **Гарсан:** файлын цэгц жагсаалт + хурууны хээ, хил болон зайн бүсүүд стандарт торонд, нэг нэгдсэн
  зургийн сан — мөн чанарын хяналтын бүртгэлүүд.

## Амжилттай болсон уу?

**Тийм. ✅** Хоёр шат бодит (туршилтын биш) өгөгдөл дээр чанарын шалгуураа давсан бөгөөд эцсийн
үр дүнгийн хуулбарыг багт зориулж Google Drive-д байршуулсан.

## Замдаа тулгарсан саадууд (ба хэрхэн шийдсэн)

- **Өгөгдөл асар том, зөвхөн онлайн (700+ ГБ).** Одоо ердөө ~2 ГБ хэрэгтэйг тогтоов; үлдсэн нь
  дараагийн шатны дроны өгөгдөл. → Зөвхөн хэрэгтэйг ашигласан.
- **Зарим файл компьютерт "харагдахгүй" байв** — Windows-ийн файлын замын урт хязгаарын улмаас.
  → Богино товчлол хийж бүгдийг уншигдахаар болгов.
- **Нэг лицензийн баримт дутуу байсан.** → Мэдэгдсэн дутагдал гэж тэмдэглээд үргэлжлүүлэв (зургийн
  өгөгдөл биш, баримт).
- **GitHub-д нэвтрэх зөрчил нэг удаа upload-ыг саатуулав.** → Зөв бүртгэл рүү шилжиж засав.

## Дараагийн алхам

**Үе шат 2** — хиймэл дагуул ба газрын гадаргын зургийг боловсруулах (талбайгаар тайрах, стандарт
торонд буулгах, шахах) — дараа нь мөн адил байршуулна.

> Дэлгэрэнгүйг энэ хавтас доторх бусад тайлангаас (бүрэн задаргаа, аргачлалын PDF-ийн хуудасны
> ишлэл, техникийн тэмдэглэл) үзнэ үү.
