# Local STT Services

ถอดเสียงไทยปนอังกฤษด้วย **Whisper Turbo / faster-whisper** บน CPU INT8 (4 threads)
พร้อมข้อความและเวลาแต่ละช่วง ส่งออก JSON, TXT และ SRT รองรับ WAV, MP3, M4A, FLAC
และ MP4 ที่มีเสียง สูงสุด 1 GiB / 2 ชั่วโมงต่อไฟล์ ยังไม่แยกผู้พูด

## ติดตั้ง: Python 3.12 + uv + .venv

รันจาก repository root ใน PowerShell สร้าง `.env.local` จากตัวอย่างเมื่อยังไม่มีไฟล์
ไฟล์นี้ถูก ignore โดย Git และใช้เก็บ path/cache settings เฉพาะเครื่อง:

```powershell
if (-not (Test-Path .env.local)) { Copy-Item .env.local.example .env.local }
$localSettings = Get-Content .env.local | ConvertFrom-StringData
$env:UV_CACHE_DIR = $localSettings.UV_CACHE_DIR
uv sync --locked
```

`uv sync` ติดตั้ง dependencies ลง `.venv`; ก่อน sync ให้อ่าน `UV_CACHE_DIR` จากไฟล์
เพราะ `uv sync` ไม่โหลด dotenv เอง ใช้ `uv run --env-file .env.local ...`
สำหรับคำสั่งแอป เพื่อโหลดค่าจากไฟล์เดียวกัน
uv สร้าง `.venv` ในโปรเจกต์ ไม่ต้อง activate เอง
ติดตั้ง dependencies จาก `uv.lock` และไม่ต้องติดตั้ง PyTorch หรือ FFmpeg แยก
PyAV ถูกจำกัดเป็นรุ่น 18 เพราะ faster-whisper 1.2.1 ยังใช้ argument ที่ PyAV 19 ลบออก
ดู [upstream issue](https://github.com/SYSTRAN/faster-whisper/issues/1589)

ครั้งแรกที่เรียกโมเดลต้องใช้อินเทอร์เน็ตเพื่อดาวน์โหลดน้ำหนักประมาณ 1.6 GB
เก็บใน Hugging Face cache เพียงที่เดียว การไม่มี symlink support บน Windows อาจเพิ่มพื้นที่ cache
รอบถัดไปใช้ cache เดิมได้ ค่า `HF_HOME`/`UV_CACHE_DIR` ที่ตั้งไว้จะมีผลเหนือค่าเริ่มต้น

## CLI

```powershell
uv run --env-file .env.local stt transcribe '.\แอปเปิลขึ้นราคา-SnapYT.App.mp4' --output-dir '[private local path]'
```

ได้ `transcript.json`, `transcript.txt`, `transcript.srt` ใน directory ใหม่
CLI ไม่เขียนทับ directory ที่มีอยู่ ไม่ลบไฟล์ต้นฉบับ และไม่ล้างผลตามอายุ
Timestamp เป็นวินาทีเทียบกับเสียงต้นฉบับ รวมช่วงเงียบที่ VAD ข้ามไป
ภาษาใช้การตรวจอัตโนมัติ ผลลัพธ์เป็น transcription ไม่ใช่ translation

## API และ worker

### Profile ทดลองปรับคุณภาพบน CPU

ผลทดลองจริงล่าสุดใช้ค่าใน `.env.local` ดังนี้:

```dotenv
STT_TEMPERATURE_ZERO=true
STT_CONDITION_ON_PREVIOUS_TEXT=true
STT_NO_REPEAT_NGRAM_SIZE=8
```

ค่า n-gram จำกัดการวนซ้ำใน decoder รองรับ 0–20; 0 คือปิดและเป็นค่า baseline
profile ทดลองนี้ลดอักขระเพี้ยนและรูปแบบข้อความวนซ้ำที่ตรวจพบใน Kob แต่ยังมีคำสะกด/ชื่อผิด
จึงต้องตรวจแก้ transcript และยังไม่ใช่การรับรองความแม่นยำทั้งไฟล์
ค่าเริ่มต้นในโค้ดและ profile baseline เดิมยังอยู่ครบ
ตั้งค่าก่อนเริ่ม CLI/API/worker; worker ที่เปิดอยู่ต้องเริ่มใหม่เพื่อโหลด profile ใหม่
ดู [ผลทดสอบจริงและไฟล์ TXT/SRT](docs/cpu-quality-progress-20261018.md)

เปิดสอง terminal โดยใช้ environment variables เดียวกัน:

```powershell
# Terminal 1: API bind เฉพาะ 127.0.0.1
uv run --env-file .env.local stt serve --port 8000

# Terminal 2: โหลดโมเดลหนึ่งครั้งแล้วทำงานจากคิวทีละงาน
uv run --env-file .env.local stt worker
```

ตัวอย่างเรียกจาก PowerShell (`curl.exe` เพื่อไม่ใช้ alias ของ PowerShell):

```powershell
curl.exe -F 'file=@แอปเปิลขึ้นราคา-SnapYT.App.mp4' http://127.0.0.1:8000/jobs
curl.exe http://127.0.0.1:8000/jobs/JOB_ID
curl.exe -o transcript.srt 'http://127.0.0.1:8000/jobs/JOB_ID/result?format=srt'
curl.exe http://127.0.0.1:8000/health
```

`POST /jobs` เป็น multipart ที่มี field `file` เพียงรายการเดียว คืน HTTP 202 พร้อม `job_id`
ตรวจสถานะ `queued`, `running`, `succeeded`, `failed` ผ่าน GET และดาวน์โหลดผลเมื่อสำเร็จ
`GET /jobs/{job_id}` มี `progress_percent` เป็นจำนวนเต็ม: งานรอเริ่มที่ 0,
ระหว่างถอดเสียงประมาณจากตำแหน่งเสียงล่าสุดเทียบความยาวเสียงที่ decode ได้ สูงสุด 99,
และเป็น 100 พร้อมสถานะ `succeeded` หลังเผยแพร่ JSON/TXT/SRT ครบแล้ว
Frontend poll เส้นเดิมได้ เช่น ทุก 1–2 วินาที ค่าอาจกระโดดหรือหยุดนิ่งระหว่าง
validation, VAD, ช่วงเงียบ หรือการประมวลผลแต่ละ batch จึงไม่ใช่เปอร์เซ็นต์เวลาที่ใช้
และไม่มีเวลาที่คาดว่าจะเหลือ งานล้มเหลวหรือถูกขัดจังหวะคงเปอร์เซ็นต์ล่าสุดไว้
ให้ตรวจ `status` ร่วมด้วยเสมอ งานใหม่เริ่มที่ 0 โดยไม่รับค่าจากงานก่อน
ฐานข้อมูลเดิมอัปเกรดอัตโนมัติโดยเก็บงานเดิมไว้; งานสำเร็จเดิมแสดง 100
ส่วนงานเดิมที่ยังไม่สำเร็จเริ่มที่ 0 เพราะไม่มีประวัติความคืบหน้า
`format` รองรับ `json` (default), `txt`, `srt` โดยไม่ถอดเสียงซ้ำ
คิวรอเต็ม 10 งานคืน 429; ไฟล์ใหญ่คืน 413; นามสกุลไม่รองรับคืน 415;
เสียงเสีย/ไม่มีเสียง/ยาวเกินกำหนดหรือ timeline แตกย่อยผิดปกติคืน 422; ผลยังไม่สำเร็จคืน 409;
รหัสไม่พบหรือหมดอายุคืน 404; multipart ผิดรูปแบบคืน 400
`/health` คืน 503 จน worker โหลดโมเดลสำเร็จและมี heartbeat สด จากนั้นคืน 200
heartbeat ทุก 5 วินาที หมดอายุหลัง 30 วินาที

เปิด worker ได้หนึ่งตัวต่อ data directory ใช้ OS-backed file lock ป้องกันการทำงานซ้อน
API restart ไม่แตะงานที่กำลังทำ หาก worker หยุดกลางงาน เมื่อเริ่มใหม่งานนั้นเป็น
`failed / interrupted` ส่วนงานรอคงอยู่ ไม่มี retry อัตโนมัติ ให้ส่งไฟล์ใหม่เอง
หยุด terminal ด้วย Ctrl+C; รหัสออก 130 หมายถึงผู้ใช้ขัดจังหวะ

## Storage และ retention

```text
[private local path]
  cache\huggingface\     HF_HOME: น้ำหนักโมเดล
  cache\uv\              UV_CACHE_DIR: dependency cache
  jobs.sqlite3           durable queue + worker heartbeat
  worker.lock            singleton worker ownership
  locks\                 bounded download/cleanup lock stripes (สูงสุด 1,024)
  jobs\<job_id>\
    input.<extension>    API-owned source
    result\              JSON/TXT/SRT ที่เขียนเสร็จแล้ว
  output\                ตัวอย่าง CLI/benchmark destinations
```

worker ตรวจ cleanup ตอนเริ่มและทุกชั่วโมง:

- งานสำเร็จ: ลบ input หลังสำเร็จ 24 ชั่วโมง เก็บผลและสถานะ 7 วัน
- งานล้มเหลว: ลบ input, artifacts และสถานะหลังล้มเหลว 24 ชั่วโมง
- ไม่ลบ queued/running, cache, `.venv` หรือไฟล์และผลของ CLI
- ข้ามผลที่กำลังดาวน์โหลดและลองลบใหม่ในรอบถัดไปเมื่อ filesystem ล้มเหลว
- GET ไม่เปิดผลที่หมดอายุ แม้ยังรอ cleanup; lock markers ไม่มีเสียง/ข้อความและอาจคงอยู่
  ใช้จำนวนคงที่เพื่อไม่ให้ lock files สะสมตามจำนวน request บน Unix

เก็บ data directory บน local disk (ไม่ใช้ network share) และป้องกันสิทธิ์เข้าถึงตาม OS
MVP ไม่มี authentication และออกแบบเฉพาะ localhost ไม่เปิด LAN/Internet
ตรวจ Host และ Origin; ไม่รองรับ cross-origin browser clients

ใช้ `STT_DATA_DIR` เปลี่ยนพื้นที่จัดเก็บ ค่าเริ่มต้น Windows คือ `[private local path]`
บนระบบอื่นคือ `~/.local/share/ai-stt` ตัวเลือกเพิ่มเติมใช้ prefix `STT_`:
`CPU_THREADS`, `MAX_BYTES`, `MAX_DURATION_SECONDS`, `MAX_QUEUED`,
`POLL_SECONDS`, `HEARTBEAT_SECONDS`, `HEARTBEAT_TIMEOUT_SECONDS`
ข้อจำกัดไฟล์และคิวลดได้แต่เพิ่มเกินเพดาน MVP ไม่ได้ ไม่มีการอ่าน `.env` อัตโนมัติ

## ตรวจโค้ดและทดสอบ

```powershell
uv run --env-file .env.local -- python -m pytest
uv run --env-file .env.local ruff check .
uv run --env-file .env.local ruff format --check .
uv run --env-file .env.local -- python -m mypy
```

ชุดปกติใช้ WAV ที่สร้างใน test กับ fake engine ผ่าน CLI/API ไม่ดาวน์โหลดโมเดล
ทดสอบ integration ด้วยโมเดลจริงแยกต่างหาก:

```powershell
# Set STT_TEST_MEDIA in the ignored .env.local file to one of the approved original recordings.
uv run --env-file .env.local -- python -m pytest -m integration tests/test_real_model.py
```

## Benchmark

```powershell
uv run --env-file .env.local stt benchmark '.\แอปเปิลขึ้นราคา-SnapYT.App.mp4' --output-dir '[private local path]'
```

Cold โหลดโมเดลใน process ใหม่; warm ใช้โมเดลเดิม ไม่มีการ flush OS cache
หากต้องดาวน์โหลดครั้งแรก model-load time จะรวม download ด้วย จึงควรอุ่น cache ก่อนวัด steady state
ได้ผลแยก cold/warm และ `benchmark.json` พร้อม SHA-256, versions/revision, configuration,
hardware, timing, RTFx และ peak process RSS ที่สุ่มทุก 50 ms
`wall_seconds` และ `rtfx_total` ใน benchmark วัดครอบคลุมการเรียก pipeline จน publish เสร็จ
ส่วน metrics ใน transcript วัดก่อนเขียน metrics JSON รอบสุดท้ายและ rename
เพื่อให้ทุกไฟล์เสร็จสมบูรณ์ก่อนเผยแพร่ และไม่แก้ไข bundle หลัง publish
RAM เป็นทั้ง process ไม่ใช่เฉพาะโมเดล และอาจพลาด peak ที่สั้นกว่า sampling interval
ไม่มีคะแนน CER/WER จนมี reference ที่ตรวจแล้วและกำหนด normalization/tokenization

อ่าน [spec](.scratch/stt-mvp/spec.md), [architecture](.scratch/stt-mvp/architecture.md),
[tickets](docs/agents/issue-tracker.md) และ [benchmark reports](benchmarks/reports/README.md)
สำหรับขอบเขตและหลักฐานการตรวจรับ
