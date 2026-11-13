# สถานะการเตรียม Dataset

วันที่ตรวจ: 2026-11-13
แหล่งข้อมูลปัจจุบัน: E:\LAB Emission\Dataset
แหล่งข้อมูลเดิม E:\Project_FAHP\Landuse ใช้เป็นประวัติเท่านั้น

## ผลตรวจ
- พบขอบเขตศึกษา 1 ชุด และ Landuse 5 ชุด มี .shp .shx .dbf .prj ครบ
- ทุกชั้นเป็น WGS 84 / UTM Zone 47N (EPSG:32647)
- ขอบเขตศึกษาตามไฟล์มีพื้นที่ 93,105.2729 ha
- มีพื้นที่ภายในขอบเขตที่ไม่มีคลาสพืชเหนือดินในข้อมูลที่ส่งมา 57,033.9750 ha
- มี geometry เสม็ดขาวเป็น Ring Self-intersection หนึ่งตำแหน่ง
- รวมส่วน polygon ในสำเนาสำหรับประมวลผลแล้วได้ geometry ถูกต้อง พื้นที่รวมเปลี่ยนประมาณ 1e-9 ha
- ไม่มีการแก้ไข Dataset ต้นฉบับหรือเปลี่ยนค่าพารามิเตอร์ emission final

## พื้นที่ภายในขอบเขตศึกษา
| ชั้นข้อมูล | พื้นที่ ha |
|---|---:|
| GRASS | 1,226.3061 |
| LEPIRONIA | 12,214.2249 |
| M_CAJU | 26,111.1310 |
| PADDY | 7,954.7225 |
| PEAT | 16,154.7414 |

พื้นที่รายชั้นยังซ้อนกัน จึงห้ามรวมคอลัมน์นี้เป็นพื้นที่ดินไม่ซ้ำทั้งหมด

## พืชเหนือดินที่ยังซ้อนกัน
| คู่ชั้นข้อมูล | พื้นที่ซ้อนทับ ha |
|---|---:|
| GRASS / LEPIRONIA | 5.4532 |
| GRASS / M_CAJU | 62.5542 |
| LEPIRONIA / M_CAJU | 11,054.9839 |
| M_CAJU / PADDY | 315.8772 |

ดินพรุซ้อนกับพืชเหนือดินได้ในฐานะเชื้อเพลิงใต้ดินอีกชั้น ภายใต้ scenario 0-10 cm
พืชเหนือดินที่ซ้อนกันต้องกำหนดความหมาย/ลำดับความสำคัญก่อนนำทุกค่ามาบวก โดยเฉพาะ Melaleuca surface fuel ที่รวม undergrowth แล้ว
พื้นที่ที่ไม่มีคลาสพืชต้องแสดงเป็น unclassified ไม่ควรสมมติว่าไม่มีไฟหรือไม่มีการปล่อย

## ไฟล์ที่เตรียมแล้ว
- data/processed/spatial/study_area.geojson: ขอบเขตสำหรับเว็บ EPSG:4326
- data/processed/spatial/landuse_layers.geojson: Landuse ที่ตัดตามขอบเขตแล้ว EPSG:4326 พร้อมรหัสเชื้อเพลิง
- config/spatial_dataset.json: ตำแหน่งข้อมูล พิกัดกรอบ FIRMS และสถานะการจัดการคลาสซ้อนทับ
- outputs/tables/spatial_dataset_audit.json: รายละเอียด QA และ hash ไฟล์ต้นฉบับ
- scripts/prepare_spatial_data.py: สคริปต์ทำซ้ำการเตรียมและตรวจข้อมูล
- docs/SPATIAL_DATA_REVIEW.md: รายงานละเอียด

ตรวจเปิด GeoJSON กลับด้วย Fiona แล้ว: ขอบเขต 1 feature, Landuse 5 features และ geometry ทุก feature ถูกต้อง
ยังไม่ได้บังคับลำดับความสำคัญของพืช ตัดพื้นที่ซ้อนทับออกจากคลาสใด หรือคำนวณ emission
ผู้ใช้ยืนยันว่าชั้นเชื้อเพลิงตั้งใจให้ซ้อนกันได้ ใช้ขอบเขตตามไฟล์ที่ส่งมา และคงพื้นที่ซ้อนทับไว้สำหรับ intersect รายชั้น

## สำเนาแผนที่สำหรับเว็บ
- web/data/study_area.geojson ประมาณ 44 KB
- web/data/landuse_layers.geojson ประมาณ 15.4 MB (ลดจากแบบละเอียด 53.2 MB)
- ลดจำนวนจุดด้วยระยะ 5 เมตรแบบรักษา topology ใช้แสดงผลเท่านั้น
- พื้นที่และ emission ต้องใช้ข้อมูลละเอียดใน data/processed/spatial
- ตรวจเปิดสำเนากลับแล้ว จำนวน feature และ geometry ผ่าน
- ทำซ้ำด้วย python scripts/prepare_spatial_data.py แล้ว python scripts/prepare_web_layers.py


User clarification (2026-11-13): Between-layer overlaps are intentional. Use the supplied study boundary, preserve each fuel layer, and calculate intersections independently. No disjoint-class replacement or priority is required solely due to overlap. Shared biomass within the Melaleuca undergrowth parameter remains an accounting consideration, not a geometry error.
