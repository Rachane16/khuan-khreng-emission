"""Per-pixel results must use clipped area and retain between-pixel overlaps."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import fire_pipeline as m
from shapely.geometry import box
class PixelTests(unittest.TestCase):
    def test_pixel_estimate_and_daily_union_have_distinct_meaning(self):
        o=m.normalize({"latitude":8,"longitude":100,"acq_date":"2026-08-15","acq_time":"600","scan":.1,"track":.1},"MODIS_NRT")
        other={**o,"id":"different","source":"VIIRS_NOAA20_NRT"}
        pixel=m.footprint(o);boundary=box(pixel.bounds[0],pixel.bounds[1],pixel.centroid.x,pixel.bounds[3])
        layers={k:pixel for k in ("GRASS","LEPIRONIA","M_CAJU","PADDY","PEAT")}
        params=m.load_json(m.ROOT/"config/emission_parameters.json")
        points=m.point_features([o,other],boundary,layers,params)
        e=points["features"][0]["properties"]["pixel_emission"]
        self.assertAlmostEqual(e["ground_area_ha"],.5)
        self.assertEqual(len(e["fuels"]),6)
        self.assertAlmostEqual(e["peat_emission_kg"],.5*210*.54*3.02)
        daily=m.summarize([o,other],boundary,layers,params)
        self.assertAlmostEqual(sum(f["properties"]["pixel_emission"]["emission_kg"] for f in points["features"]),2*daily["emission_kg"])
        self.assertNotIn("pixel_emission",o)
    def test_month_subtraction_clamps_short_month(self):
        from import_history_range import month_start
        from datetime import date
        self.assertEqual(month_start(date(2026,5,31),3),date(2026,2,28))
if __name__=="__main__":unittest.main()
