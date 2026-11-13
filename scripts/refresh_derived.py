"""Enrich saved observations with per-pixel fuel estimates and chart summaries."""
import time
import fire_pipeline as m

def refresh(root=m.ROOT):
    m.bootstrap(root)
    boundary,layers,indices=m.spatial_inputs(root)
    parameters=m.load_json(root/"config/emission_parameters.json")
    target=root/"web/data"
    index=m.load_json(target/"index.json")
    rows={r["date"]:r for r in index["daily"]}
    count=pixels=0
    for path in sorted((target/"daily").glob("*.json")):
        data=m.load_json(path);day=data["date"]
        history=target/"history"/(day+".json")
        if not history.exists(): continue
        obs=m.load_json(history)["observations"]
        data["footprints"]=m.point_features(obs,boundary,layers,parameters,indices)
        data["pixel_calculation"]="Independent clipped pixel estimate; overlaps between pixels are retained."
        m.write_json(path,data)
        rows[day]=m.index_row(day,data["by_source"],data["data_state"],data["source_status"])
        count+=1;pixels+=len(data["footprints"]["features"])
    m.write_json(target/"index.json",{**index,"dates":sorted(rows),"daily":[rows[d] for d in sorted(rows)]})
    print(f"Enriched {count} days and {pixels} pixel estimates.",flush=True)
if __name__=="__main__":refresh()
