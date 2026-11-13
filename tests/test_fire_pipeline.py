"""Behavior tests: geometry, fuel overlap, Thai dates, archive revisions and failures."""
import sys, json, tempfile, unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import fire_pipeline as m
from shapely.geometry import box
PARAMS=m.load_json(m.ROOT/"config"/"emission_parameters.json")

def obs(source="MODIS_NRT", time="1730", day="2026-11-12"):
    return m.normalize(dict(latitude="8",longitude="100",acq_date=day,
        acq_time=time,scan=".1",track=".1",satellite=source),source)

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.o=obs()
        self.pixel=m.footprint(self.o)
        self.boundary=self.pixel.buffer(100)
        self.layers={k:self.pixel for k in ("GRASS","LEPIRONIA","M_CAJU","PADDY","PEAT")}
    def test_timezone_rollover_and_stable_id(self):
        self.assertEqual(self.o["local_date"],"2026-11-13")
        self.assertEqual(self.o["id"],obs()["id"])
        self.assertEqual(obs(time="30")["acquired_utc"],"2026-11-12T00:30:00+00:00")
    def test_union_across_sensors_not_sum(self):
        r=m.summarize([self.o,obs("VIIRS_NOAA20_NRT")],self.boundary,self.layers,PARAMS)
        self.assertEqual(r["observation_count"],2)
        self.assertAlmostEqual(r["ground_area_ha"],1,places=6)
        self.assertAlmostEqual(r["fuels"][0]["emission_kg"],5.3*.81*5.4)
    def test_overlaps_and_two_melaleuca_pools(self):
        r=m.summarize([self.o],self.boundary,self.layers,PARAMS)
        rows={x["code"]:x for x in r["fuels"]}
        self.assertAlmostEqual(rows["M_CAJU_SURFACE_LOWLAND"]["area_ha"],1)
        self.assertAlmostEqual(rows["M_CAJU_LEAVES_BARK_LOWLAND"]["area_ha"],1)
        self.assertAlmostEqual(r["peat_emission_kg"],210*.54*3.02)
        self.assertAlmostEqual(r["emission_kg"],sum(p["rho"]*p["eta"]*p["ef_pm25"] for p in PARAMS["fuels"]))
        self.assertEqual(r["surface_unclassified_ha"],0)
    def test_boundary_clip_and_unclassified(self):
        half=box(self.pixel.bounds[0],self.pixel.bounds[1],self.pixel.centroid.x,self.pixel.bounds[3])
        empty={k:box(0,0,1,1) for k in self.layers}
        r=m.summarize([self.o],half,empty,PARAMS)
        self.assertAlmostEqual(r["ground_area_ha"],.5)
        self.assertAlmostEqual(r["surface_unclassified_ha"],.5)
        self.assertEqual(r["emission_kg"],0)
    def test_no_data_has_no_geometry(self):
        r=m.summarize([],self.boundary,self.layers,PARAMS)
        self.assertIsNone(r["burned_geometry"])
        self.assertEqual(r["ground_area_ha"],0)
    def test_csv_dedup_and_bad_response(self):
        header="latitude,longitude,acq_date,acq_time,scan,track\n"
        line="8,100,2026-11-12,1730,.1,.1\n"
        self.assertEqual(len(m.parse_csv(header+line+line,"MODIS_NRT")),1)
        self.assertEqual(m.parse_csv(header,"MODIS_NRT"),[])
        with self.assertRaises(ValueError): m.parse_csv("Invalid MAP_KEY","MODIS_NRT")
        with self.assertRaises(ValueError): m.parse_csv(header+"bad,100,2026-11-12,1730,.1,.1","MODIS_NRT")
    def test_network_failure_does_not_expose_key(self):
        def fail(*args,**kwargs): raise m.URLError("https://example/secret-test-key")
        with self.assertRaises(RuntimeError) as r:
            m.fetch_source("secret-test-key","MODIS_NRT",[99,7,101,9],opener=fail,sleeper=lambda _:None)
        self.assertNotIn("secret-test-key",str(r.exception))
    def test_repeat_fetch_revision_and_failure_preserves_archive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            m.write_json(root/"config"/"emission_parameters.json",PARAMS)
            m.write_json(root/"config"/"spatial_dataset.json",{"bbox_wgs84":[99,7,101,9]})
            m.write_json(root/"outputs"/"tables"/"spatial_dataset_audit.json",
                {"study_area_ha":4,"surface_unclassified_ha":0})
            now=datetime(2026,11,13,10,tzinfo=m.UTC)
            available={s:{"min_date":"2026-01-01","max_date":"2026-11-13"} for s in m.SOURCES}
            def fetch(key,source,*a): return ([obs(source)] if source=="MODIS_NRT" else [],"CSV")
            with patch.object(m,"spatial_inputs",return_value=(self.boundary,self.layers,{})), \
                 patch.object(m,"fetch_availability",return_value=available),patch.object(m,"fetch_source",side_effect=fetch):
                self.assertEqual(m.collect(root,key="test",now=now),0)
                self.assertEqual(m.collect(root,key="test",now=now),0)
                day=m.load_json(root/"web"/"data"/"daily"/"2026-11-13.json")
                self.assertEqual(day["by_source"]["ALL"]["observation_count"],1)
                before=(root/"web"/"data"/"index.json").read_bytes()
                with patch.object(m,"fetch_source",side_effect=RuntimeError("service down")):
                    self.assertEqual(m.collect(root,key="test",now=now),2)
                self.assertEqual((root/"web"/"data"/"index.json").read_bytes(),before)
                self.assertEqual(m.load_json(root/"web"/"data"/"status.json")["state"],"error")
                with patch.object(m,"fetch_source",return_value=([],"CSV")):
                    m.collect(root,key="test",now=now)
                day=m.load_json(root/"web"/"data"/"daily"/"2026-11-13.json")
                self.assertEqual(day["by_source"]["ALL"]["observation_count"],0)
    def test_stale_source_not_reported_as_zero_fire(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            m.write_json(root/"config"/"emission_parameters.json",PARAMS)
            m.write_json(root/"config"/"spatial_dataset.json",{"bbox_wgs84":[99,7,101,9]})
            m.write_json(root/"outputs"/"tables"/"spatial_dataset_audit.json",{"study_area_ha":4,"surface_unclassified_ha":0})
            available={s:{"min_date":"2026-01-01","max_date":"2026-11-13"} for s in m.SOURCES}
            available["VIIRS_SNPP_NRT"]["max_date"]="2026-11-02"
            with patch.object(m,"spatial_inputs",return_value=(self.boundary,self.layers,{})), \
                 patch.object(m,"fetch_availability",return_value=available),patch.object(m,"fetch_source",return_value=([],"CSV")) as f:
                m.collect(root,key="test",now=datetime(2026,11,13,10,tzinfo=m.UTC))
                self.assertEqual(f.call_count,3)
                status=m.load_json(root/"web"/"data"/"status.json")
                self.assertEqual(status["state"],"partial")
                self.assertEqual(status["sources"]["VIIRS_SNPP_NRT"]["state"],"unavailable")
                self.assertNotIn("2026-11-11",m.load_json(root/"web"/"data"/"index.json")["dates"])

if __name__=="__main__": unittest.main()
