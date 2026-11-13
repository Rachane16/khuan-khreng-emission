# Khuan Khreng Fire & Emission
ต้นแบบ Web Dashboard สำหรับ Active Fires และการประมาณ PM₂.₅ รายวันในป่าพรุควนเคร็ง

## เริ่มใช้งาน
Python 3.12:
~~~powershell
cd 'E:\LAB Emission'
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/fire_pipeline.py bootstrap
python scripts/fire_pipeline.py collect --prompt-key
python -m http.server 8765 --bind 127.0.0.1 --directory web
~~~
เปิด http://127.0.0.1:8765/ การรับคีย์เป็นแบบซ่อนและไม่บันทึกลงไฟล์
ดู docs/SETUP_GITHUB_TH.md สำหรับ GitHub Pages และการตั้งค่า secret

## ข้อมูลและวิธีคำนวณ
- ขอบเขตจริง 93,105.27 ha และเชื้อเพลิง 5 ชั้นจาก Dataset ของผู้ใช้
- พารามิเตอร์ 6 กลุ่มตามตาราง final ใน config/emission_parameters.json
- E (kg PM₂.₅) = A (ha) × ρ (ตันแห้ง/ha) × η × EF (g/kg)
- วันตาม Asia/Bangkok; union พิกเซลซ้ำภายในวันและชุดดาวเทียมที่เลือก
- ตัดพื้นที่กับแต่ละชั้นเชื้อเพลิงอย่างอิสระ เก็บการซ้อนทับตามนิยามโครงการ
- เสม็ดคำนวณ surface และ leaves+bark บนพื้นที่เดียวกันแล้วรวมมวลการปล่อย
- peat เป็นสถานการณ์สมมติการเผาชั้น 0–10 cm เปิด/ปิดการรวมในยอดได้
- แต่ละวันเป็นสถานการณ์เชื้อเพลิงตั้งต้นอิสระ ยอดหลายวันอาจนับเชื้อเพลิงเดิมซ้ำ
- API ส่งจุดศูนย์กลาง+scan/track ไม่ใช่ขอบเขตไฟจริง: ต้นแบบสร้างสี่เหลี่ยม UTM ประมาณ footprint โดยไม่ทราบมุมสแกน
- ไม่ใช้ผลนี้แทนค่าความเข้มข้น PM₂.₅ หรือ perimeter ที่ยืนยันภาคสนาม
- พื้นที่ไม่มีชั้นเชื้อเพลิงแสดงแยก ไม่เติมชนิดเชื้อเพลิงโดยการคาดเดา
- พุ่ม/หญ้าใน undergrowth ของเสม็ดอาจเป็นชีวมวลเดียวกับชั้นหญ้าหรือกระจูด ต้องยืนยันก่อนใช้อ้างอิงยอดรวมทางวิจัย

## โครงสร้าง
- scripts/fire_pipeline.py: collector, Thai daily archive, spatial overlay และ emission
- scripts/prepare_spatial_data.py: เตรียมข้อมูลต้นฉบับด้วย Fiona
- scripts/prepare_web_layers.py: ลดรายละเอียด 5 m เฉพาะภาพแผนที่
- data/processed/spatial/*.geojson.gz: geometry เต็มสำหรับคำนวณบน GitHub Actions
- web/: หน้าเว็บ static พร้อม Leaflet ที่เก็บในโครงการ
- web/data/history/: ข้อมูลตรวจพบเพื่อประมวลผลซ้ำ ไม่ซ้ำสะสมเมื่อ fetch
- web/data/daily/: ผลรายวันและแต่ละดาวเทียม
- config/: ค่าพารามิเตอร์และขอบเขตดึงข้อมูล
- tests/: ทดสอบหน่วยพื้นที่ การซ้อนทับ วันเวลา การเก็บประวัติและ API ล้มเหลว
- outputs/tables/: รายงานตรวจสอบข้อมูลพื้นที่

Dataset ต้นฉบับ, raw API และ credentials ไม่อยู่ใน Git
ชั้นแผนที่ใช้ geometry ลดรายละเอียดเพื่อแสดงผลเท่านั้น
ค่า ± คงตามผู้ใช้ ยังไม่ตีความเป็น SD/SE/CI หรือใช้สุ่ม uncertainty

## แหล่งข้อมูล
[NASA FIRMS Area API](https://firms.modaps.eosdis.nasa.gov/api/area/)
[Data availability API](https://firms.modaps.eosdis.nasa.gov/api/data_availability/)
[MODIS attributes](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html)
[VIIRS attributes](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html)
Leaflet 1.9.4 license: web/vendor/LEAFLET-LICENSE.txt
Basemap: © OpenStreetMap contributors

ค่าปัจจัยเชื้อเพลิงใช้ตาราง final ของผู้ใช้ ยังไม่มีรายการอ้างอิงตีพิมพ์ที่ตรวจครบทุกค่าใน session นี้
