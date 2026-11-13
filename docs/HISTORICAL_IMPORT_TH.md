# การนำเข้าข้อมูลย้อนหลัง
การเลือกวันที่บนเว็บ static จะอ่านข้อมูลที่บันทึกไว้ ไม่ส่ง MAP_KEY จากเบราว์เซอร์ไป NASA
วันที่ยังไม่ได้โหลดจะแสดง “— / ยังไม่ได้โหลดข้อมูลย้อนหลัง” และไม่ตีความว่าไม่พบไฟ

GitHub → Actions → Collect FIRMS and deploy dashboard → Run workflow:
- backfill_start: YYYY-MM-DD ตามวันเวลาไทย
- backfill_end: วันสุดท้าย inclusive (เว้นว่าง = วันเดียว)
- สูงสุด 31 วันต่อครั้ง; เว้นทั้งคู่สำหรับดึง NRT ปัจจุบันตามเดิม

ตัวอย่างตรวจภาพ NASA วันที่ 2026-08-15:
นำเข้า 2026-08-15 ถึง 2026-08-16 เพื่อครอบคลุมรายการ UTC วันที่ 15 ที่อาจเป็นวันไทยที่ 16
ระบบดึง UTC วันที่ 14–16 แล้วแยกลงปฏิทินไทย ไม่ปนเวลาสองระบบในตัวเลขวันเดียวกัน
เปรียบเทียบ count ใน web/data/backfill_status.json ซึ่งแยก UTC date, sensor, bbox และ study AOI

CLI:
python scripts/backfill_firms.py --start-date 2026-08-15 --end-date 2026-08-16 --prompt-key

ใช้ data_availability เลือก SP ก่อน ถ้ามีข้อมูลวันนั้น มิฉะนั้นเลือก NRT
API product จริงถูกเก็บใน api_product แต่จัดกลุ่มตามดาวเทียมเดิม
ไม่รวม SP และ NRT ของดาวเทียมเดียวกันซ้ำในวัน UTC เดียว
ไม่เขียนทับสถานะ NRT ปัจจุบัน และไม่แก้ข้อมูลนอกวันไทยที่ขอ
เมื่อบาง source ล้มเหลว จะรักษารายการเดิมไว้และทำเครื่องหมาย partial/error

แหล่งอ้างอิง:
https://firms.modaps.eosdis.nasa.gov/api/area/
https://firms.modaps.eosdis.nasa.gov/api/data_availability/
