"""Generate simplified web display copies; never use these for area/emission."""
from pathlib import Path
import json
import fiona
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform

root=Path(__file__).resolve().parents[1]
source=root/"data"/"processed"/"spatial"
out=root/"web"/"data"
out.mkdir(parents=True,exist_ok=True)
to_metric=Transformer.from_crs(4326,32647,always_xy=True).transform
to_wgs=Transformer.from_crs(32647,4326,always_xy=True).transform
stats=[]
def rounded(x):
    if isinstance(x,(list,tuple)):
        return [rounded(v) for v in x]
    if isinstance(x,float):
        return round(x,7)
    return x
for name in ["study_area.geojson","landuse_layers.geojson"]:
    features=[]
    with fiona.open(source/name) as collection:
        for f in collection:
            g=transform(to_metric,shape(f["geometry"]))
            simple=g.simplify(5.0,preserve_topology=True)
            props=dict(f["properties"])
            props["display_only"]=True
            props["simplification_m"]=5
            geo=mapping(transform(to_wgs,simple))

            exported=shape(geo)
            if not exported.is_valid or exported.is_empty:
                raise ValueError("Invalid simplified display export")
            features.append({"type":"Feature","properties":props,"geometry":geo})
            stats.append({"file":name,"code":props.get("landuse_code","boundary"),
                "original_area_ha":g.area/10000,"simplified_area_ha":simple.area/10000,
                "area_difference_ha":(simple.area-g.area)/10000})
    dest=out/name
    dest.write_text(json.dumps({"type":"FeatureCollection",
        "metadata":{"use":"display only","simplification_m":5,"calculation_source":str(source/name)},
        "features":features},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    with fiona.open(dest) as check:
        if len(check)!=len(features):
            raise ValueError("Display feature count mismatch")
    print(name,dest.stat().st_size,"bytes",flush=True)
(root/"outputs"/"tables"/"web_display_geometry_audit.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
config_path=root/"config"/"spatial_dataset.json"
config=json.loads(config_path.read_text(encoding="utf-8"))
config["display_geojson"]={"boundary":str(out/"study_area.geojson"),"landuse":str(out/"landuse_layers.geojson")}
config["display_geometry_note"]="5 m topology-preserving simplification for visualization only. Use full prepared geometry for area/emission calculations."
config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Verified simplified display files; full calculation geometry unchanged.",flush=True)
