# สรุป HTTP API ของ STT Services

บริการนี้เปิด REST API ในเครื่องด้วย FastAPI เพื่อรับงานถอดเสียง ตรวจสถานะงาน และดาวน์โหลดผลลัพธ์ ตัว API ไม่รอให้การถอดเสียงเสร็จในคำขอเดียว แต่สร้าง Job ให้ worker ประมวลผลแยกต่างหาก

## ที่อยู่ API และหน้าเอกสาร

คำสั่ง `uv run --env-file .env.local stt serve` เปิด API ที่ `http://127.0.0.1:8000` โดยค่าเริ่มต้น ตัวเลือก `--port` กำหนดพอร์ตอื่นได้

API ทำงานบน `127.0.0.1` เท่านั้น Worker เป็น process แยกที่รันด้วย `uv run --env-file .env.local stt worker` เพื่อรับงานและโหลดโมเดล หาก worker ไม่พร้อม `GET /health` จะตอบ `503` แม้ API จะยังตอบคำขอได้

FastAPI สร้างหน้าเอกสารและ OpenAPI ให้อัตโนมัติ:

| Path | ใช้ทำอะไร |
| --- | --- |
| `/docs` | เปิด Swagger UI เพื่อดูและเรียก API |
| `/redoc` | เปิดเอกสาร API ในรูปแบบ ReDoc |
| `/openapi.json` | ดาวน์โหลดสัญญา OpenAPI ในรูป JSON |

## เส้นทางของ API

| Method | Path | ใช้ทำอะไร | คำตอบเมื่อสำเร็จ |
| --- | --- | --- | --- |
| `POST` | `/jobs` | อัปโหลดไฟล์และสร้างงานถอดเสียง เลือก `model=turbo` หรือ `large-v3` ได้ | `202 Accepted` พร้อม `job_id` และ `status` |
| `GET` | `/jobs/{job_id}` | อ่านสถานะ รุ่นโมเดล ความคืบหน้า เวลา และข้อผิดพลาดของงาน | `200 OK` พร้อมข้อมูล Job |
| `GET` | `/jobs/{job_id}/result` | ดาวน์โหลด JSON, TXT, SRT หรือ JSON ต้นฉบับด้วย `format=original-json` | `200 OK` พร้อมไฟล์ผลลัพธ์ |
| `PUT` | `/jobs/{job_id}/transcript` | บันทึกข้อความที่ตรวจแก้แล้วครบทุก segment ของงานที่สำเร็จ | `200 OK` พร้อม `status=saved` |
| `GET` | `/health` | ตรวจว่า API และ worker พร้อมรับงาน พร้อมดูค่าโมเดลเริ่มต้น | `200 OK` เมื่อพร้อม, `503` เมื่อ worker ไม่พร้อม |

### `POST /jobs`

รับไฟล์ด้วย `multipart/form-data` โดยส่งไฟล์หนึ่งรายการใน field ชื่อ `file` รองรับนามสกุล `.wav`, `.mp3`, `.m4a`, `.flac` และ `.mp4` ระบบตรวจสอบไฟล์ก่อนนำงานเข้าคิว จะส่ง field `model` เพิ่มก็ได้ โดยรับเฉพาะ `turbo` และ `large-v3` หากไม่ส่ง ระบบบันทึกค่าจาก `STT_MODEL` ไว้กับ Job ตอนสร้างงาน

ตัวอย่างคำตอบ:

```json
{
  "job_id": "0123456789abcdef0123456789abcdef",
  "status": "queued"
}
```

API ตอบกลับทันทีหลังสร้างงาน Worker จะถอดเสียงแยกจากคำขออัปโหลด

### `GET /jobs/{job_id}`

ใช้ `job_id` ที่ได้จาก `POST /jobs` เพื่อตรวจสถานะ งานมีสถานะ `queued`, `running`, `succeeded` หรือ `failed`

ข้อมูลตอบกลับประกอบด้วย `id`, `status`, `model`, `progress_percent`, `created_at`, `started_at`, `finished_at`, `updated_at`, `error` และ `error_message` ค่าเวลาเริ่มหรือจบอาจเป็น `null` หากงานยังไปไม่ถึงช่วงนั้น

API ตอบ `404 Not Found` เมื่องานไม่มีอยู่หรือหมดอายุ

### `GET /jobs/{job_id}/result`

ดาวน์โหลดผลได้เมื่องานมีสถานะ `succeeded` ระบุ query parameter `format` เพื่อเลือกรูปแบบ ค่าเริ่มต้นคือ `json`

| Query | ไฟล์ | Content-Type |
| --- | --- | --- |
| `format=json` | `transcript.json` | `application/json` |
| `format=txt` | `transcript.txt` | `text/plain` |
| `format=srt` | `transcript.srt` | `application/x-subrip` |
| `format=original-json` | `transcript-original.json` | `application/json` |

JSON เป็นผลหลัก ส่วน TXT และ SRT สร้างจาก transcript JSON ฉบับล่าสุดที่บันทึกไว้ `format=original-json` ใช้ดูผล ASR เดิมที่แก้ไม่ได้ หากงานยังไม่สำเร็จหรือไฟล์ผลกำลังถูกใช้งาน API ตอบ `409 Conflict` หากงานหรือไฟล์หมดอายุ API ตอบ `404 Not Found`

### `PUT /jobs/{job_id}/transcript`

บันทึกข้อความแก้ไขครบทุก segment โดยไม่รัน inference ซ้ำ:

```json
{
  "segments": [
    {"id": 1, "text": "ข้อความที่ตรวจแก้แล้ว"},
    {"id": 2, "text": "ข้อความของ segment ถัดไป"}
  ]
}
```

รับเฉพาะ Job สถานะ `succeeded` และรับเฉพาะ `id` กับ `text` ต้องส่ง ID ทุกตัวให้ตรงกับผลเดิมโดยไม่มีซ้ำ การแก้ไขบันทึกทั้งชุดด้วยการแทนไฟล์ JSON ล่าสุดแบบ atomic; เวลาและโครงสร้าง segment คงเดิม ASR ต้นฉบับเก็บแยกไว้ และมีเฉพาะฉบับแก้ล่าสุด ไม่มีประวัติการแก้ ส่ง body ได้ไม่เกิน 16 MiB และเอกสารผลลัพธ์ได้ไม่เกิน 64 MiB ค่า `409` หมายถึง Job ยังไม่สำเร็จหรือกำลังใช้งานผลลัพธ์; ค่า `413` หมายถึงข้อมูลเกินขนาด; ค่า `422` หมายถึงข้อมูลแก้ไขไม่ถูกต้อง

### `GET /health`

ตรวจสถานะการให้บริการและ heartbeat ของ worker โดยตอบข้อมูลเหล่านี้:

| Field | Type | ความหมาย |
| --- | --- | --- |
| `ready` | boolean | `true` เมื่อ worker พร้อมรับงาน |
| `api` | string | เป็น `ready` เมื่อ API ตอบคำขอนี้ |
| `worker` | string | เป็น `ready` หรือ `unavailable` |
| `model_ready` | boolean | ระบุว่าโมเดลพร้อมใช้หรือไม่ |
| `default_model` | string | ค่าจาก `STT_MODEL` ที่ใช้เมื่อ `POST /jobs` ไม่ส่ง `model` |
| `heartbeat_at` | number หรือ `null` | เวลาที่ worker ส่ง heartbeat ล่าสุด |
| `heartbeat_age_seconds` | number หรือ `null` | อายุของ heartbeat ล่าสุดเป็นวินาที |

เมื่อ heartbeat หายไปหรือเก่าเกินค่าที่ตั้งไว้ API ตอบ `503 Service Unavailable` และส่ง `ready: false` พร้อมสถานะ worker และโมเดล

## รูปแบบข้อผิดพลาด

ข้อผิดพลาด HTTP ใช้ JSON envelope รูปแบบนี้:

```json
{
  "detail": "Job not found",
  "error": {
    "code": "not_found",
    "message": "Job not found"
  }
}
```

| HTTP status | Error code | ตัวอย่างสาเหตุ |
| --- | --- | --- |
| `400` | `invalid_request` | Multipart ไม่ถูกต้อง หรือ `Content-Length` ไม่ถูกต้อง |
| `403` | `forbidden_origin` | Origin มาจากคนละ host |
| `404` | `not_found` | ไม่พบ Job, Job หมดอายุ หรือไม่มีไฟล์ผล |
| `409` | `result_unavailable` | Job ยังไม่สำเร็จ หรือไฟล์ผลกำลังถูกใช้งาน |
| `413` | `file_too_large` | คำขอมีขนาดเกินค่าที่ตั้งไว้ |
| `415` | `unsupported_format` | ไฟล์ใช้รูปแบบที่ไม่รองรับ |
| `422` | `invalid_input` | ไฟล์เสียงไม่ถูกต้อง หรือพารามิเตอร์ไม่ผ่าน validation |
| `429` | `queue_full` | คิวรับงานเต็ม |

## ขอบเขตการใช้งาน

API นี้ไม่มีระบบ authentication และรับการเชื่อมต่อผ่าน loopback เท่านั้น Middleware ปฏิเสธ Origin ข้าม host จึงไม่รองรับ client จากเว็บคนละ origin

แผนผังคำขอหลักคือ client ส่งไฟล์ผ่าน `POST /jobs`, ใช้ `GET /jobs/{job_id}` ตรวจความคืบหน้า แล้วดาวน์โหลดผลผ่าน `GET /jobs/{job_id}/result` เมื่อสถานะเป็น `succeeded`

รายละเอียดสัญญา HTTP ที่ยอมรับอยู่ใน [เอกสาร HTTP API หลัก](API.md) ส่วน route, controller และ DTO จริงอยู่ใน `src/stt_services/api/routes/`, `src/stt_services/api/controllers/` และ `src/stt_services/api/dto/`
