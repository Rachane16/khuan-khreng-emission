# ตั้งค่า GitHub Pages
ชื่อ repository ที่เตรียม: Rachane16/khuan-khreng-emission
1. อัปโหลดไฟล์โครงการที่ Git ติดตาม โดยไม่รวม Dataset, data/raw หรือคีย์
2. Settings → Secrets and variables → Actions → New repository secret
   - Name: FIRMS_MAP_KEY
   - Secret: คีย์ที่ NASA ส่งในอีเมล "NASA FIRMS: Map key"
3. Settings → Pages → Source: GitHub Actions
4. Actions → Collect FIRMS and deploy dashboard → Run workflow → main
5. ตรวจ workflow สำเร็จ แล้วเปิด URL GitHub Pages ของ repository

Actions จะเรียกเก็บข้อมูลที่นาที 7 และ 37 ของทุกชั่วโมง (UTC) และเก็บ 3 วันล่าสุด
เวลา schedule อาจล่าช้าตามคิว GitHub จึงไม่ใช่การรับประกันอัปเดตทุก 30 นาที
GitHub อาจปิด schedule ของ public repo หลังไม่มี activity 60 วัน

ข้อมูลจาก NASA เป็น Near Real-Time ตามเวลาประมวลผลและรอบผ่านดาวเทียม
ระบบตรวจ data_availability ก่อนดึงแต่ละแหล่ง; แหล่งที่ไม่มีข้อมูลในช่วงที่ขอแสดง unavailable
การเรียกสำเร็จแต่ไม่พบแถวไฟ ต่างจาก API ล้มเหลวหรือแหล่งข้อมูลล้าสมัย
เมื่อ API ขัดข้องยังเก็บผลเดิมและแสดงสถานะ error/partial

รายวันใช้ปฏิทินไทย UTC+7 วันปัจจุบันยังไม่ครบวัน
การดึงซ้ำจะแทนข้อมูลของแต่ละ source ในช่วง UTC ที่ขอ เพื่อรองรับ NASA แก้ไขหรือลบ detection
ข้อมูลวันเก่ากว่าหน้าต่าง query ไม่ถูกเขียนทับด้วยสถานะการดึงวันนี้
เลือกดาวเทียมทีละแหล่ง หรือรวมทุกแหล่ง โดย union footprint ใหม่สำหรับแต่ละ selection
กราฟประวัติใช้รวมทุกดาวเทียมและตอบสนองต่อการเปิด/ปิดสถานการณ์ peat

## การเก็บคีย์
คีย์ต้องอยู่ใน GitHub Actions Secret หรือรับผ่าน hidden prompt ของ collector
ไม่ใส่คีย์ใน web/app.js, URL หน้าเว็บ, .env ที่ commit หรือ raw log
หน้าเว็บโหลดเฉพาะ JSON ที่ประมวลผลแล้ว ไม่เรียก NASA ด้วยคีย์จากเบราว์เซอร์
ไม่ต้องสร้างคีย์ใหม่หาก NASA มีคีย์เดิมแล้ว สามารถขอส่งคีย์เดิมที่หน้า download/account

## ข้อจำกัดต้นแบบ
- footprint เป็นสี่เหลี่ยมประมาณจาก scan/track ไม่ใช่ polygon ที่ NASA ยืนยัน perimeter
- เมฆและรอบโคจรทำให้ตรวจไม่พบไฟบางส่วน
- ไม่มีการประมาณชีวมวลที่ถูกเผาจริงจากข้อมูล Active Fire
- รักษาชั้นที่ซ้อนทับตามผู้ใช้ แต่ต้องยืนยันว่าไม่ได้ใช้ undergrowth ก้อนเดียวซ้ำกับหญ้าหรือกระจูด
- ยังไม่ประเมิน uncertainty เชิงสถิติหรือความเข้มข้นอากาศ
