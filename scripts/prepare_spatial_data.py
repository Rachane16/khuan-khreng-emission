"""Prepare and audit supplied spatial data. Never modifies Dataset inputs."""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib
import itertools
import math
import fiona
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping
from shapely.ops import unary_union, transform
from shapely.validation import explain_validity

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
OUT = ROOT / "data" / "processed" / "spatial"
METRIC = CRS.from_epsg(32647)
WGS84 = CRS.from_epsg(4326)
LAYERS = {
    "GRASS": "Grass_only.shp",
    "LEPIRONIA": "Lepironia_only.shp",
    "M_CAJU": "M_cajuputi_only.shp",
    "PADDY": "paddy_only.shp",
    "PEAT": "Peatsoil_only.shp",
}
THRESHOLD_HA = 0.0001

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def read_polygon(path):
    required = [path.with_suffix(ext) for ext in (".shp", ".shx", ".dbf", ".prj")]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise ValueError(f"Missing sidecars: {missing}")
    with fiona.open(path) as src:
        if not src.crs:
            raise ValueError(f"Missing CRS: {path}")
        source_crs = CRS(src.crs)
        records = list(src)
        parts = [shape(f["geometry"]) for f in records if f["geometry"]]
        if not parts or any(g.is_empty for g in parts):
            raise ValueError(f"Empty geometry: {path}")
        if any(g.geom_type not in ("Polygon", "MultiPolygon") for g in parts):
            raise ValueError(f"Non-polygon geometry: {path}")
        invalid_reasons = [explain_validity(g) for g in parts if not g.is_valid]
        raw_area = sum(g.area for g in parts)
        geom = unary_union(parts)
        if not geom.is_valid:
            raise ValueError(f"Geometry still invalid after union: {path}")
        if source_crs != METRIC:
            geom = transform(Transformer.from_crs(source_crs, METRIC, always_xy=True).transform, geom)
        meta = {
            "path": str(path), "source_crs": source_crs.to_string(),
            "record_count": len(records), "fields": dict(src.schema["properties"]),
            "geometry_type": geom.geom_type, "valid": geom.is_valid,
            "input_invalid_reasons": invalid_reasons,
            "normalization": "unary_union of polygon components; source unchanged",
            "raw_sum_area_source_units": raw_area,
            "source_area_ha": geom.area / 10000,
            "sha256": {p.suffix: hashlib.sha256(p.read_bytes()).hexdigest() for p in required},
        }
    return geom, meta

boundary_candidates = sorted(p for p in DATASET.rglob("*.shp") if "Landuse" not in p.relative_to(DATASET).parts)
if len(boundary_candidates) != 1:
    raise ValueError(f"Expected exactly one study boundary, got {boundary_candidates}")
boundary_path = boundary_candidates[0]
boundary, boundary_meta = read_polygon(boundary_path)
if boundary.is_empty or not boundary.is_valid:
    raise ValueError("Study boundary is invalid")
to_wgs = Transformer.from_crs(METRIC, WGS84, always_xy=True).transform
boundary_wgs = transform(to_wgs, boundary)
bbox = list(boundary_wgs.bounds)
if not all(math.isfinite(v) for v in bbox):
    raise ValueError("Invalid bbox")
clipped, layer_meta, features = {}, {}, []
for code, filename in LAYERS.items():
    geom, meta = read_polygon(DATASET / "Landuse" / filename)
    clip = geom.intersection(boundary)
    if clip.is_empty or not clip.is_valid:
        raise ValueError(f"No valid geometry inside study boundary: {code}")
    print(f"Prepared {code}", flush=True)
    meta["clipped_area_ha"] = clip.area / 10000
    meta["outside_study_area_ha"] = geom.difference(boundary).area / 10000
    meta["clipped_geometry_type"] = clip.geom_type
    meta["fuel_codes"] = ["M_CAJU_SURFACE_LOWLAND", "M_CAJU_LEAVES_BARK_LOWLAND"] if code == "M_CAJU" else [code]
    clipped[code], layer_meta[code] = clip, meta
    features.append({"type": "Feature", "properties": {"landuse_code": code, "area_ha": meta["clipped_area_ha"], "fuel_codes": meta["fuel_codes"]}, "geometry": mapping(transform(to_wgs, clip))})
overlaps = []
for a, b in itertools.combinations(LAYERS, 2):
    overlap_ha = clipped[a].intersection(clipped[b]).area / 10000
    overlaps.append({"layer_a": a, "layer_b": b, "overlap_ha": overlap_ha,
                     "contains_peat": "PEAT" in (a, b),
                     "intentional_layer_overlap": overlap_ha > THRESHOLD_HA})
surface_union = unary_union([g for code, g in clipped.items() if code != "PEAT"])
all_union = unary_union(list(clipped.values()))
surface_overlap = any(r["overlap_ha"] > THRESHOLD_HA and not r["contains_peat"] for r in overlaps)
report = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "canonical_dataset_root": str(DATASET),
    "metric_crs": METRIC.to_string(), "web_crs": WGS84.to_string(),
    "boundary": boundary_meta, "study_area_ha": boundary.area / 10000,
    "bbox_wgs84": bbox, "bbox_order": "west,south,east,north",
    "layers": layer_meta, "pairwise_overlap": overlaps,
    "surface_covered_ha": surface_union.area / 10000,
    "surface_unclassified_ha": boundary.difference(surface_union).area / 10000,
    "all_layers_union_ha": all_union.area / 10000,
    "all_layers_unclassified_ha": boundary.difference(all_union).area / 10000,
    "surface_overlap_detected": surface_overlap,
    "geometry_ready": True, "spatial_overlay_policy_ready": True,
    "fuel_layer_overlap_policy": "intentional_overlapping_fuel_layers",
    "biomass_accounting_status": "Not validated by this geometry audit.",
    "notes": [
        "Inputs are separate shapefiles; this does not imply geometric non-overlap.",
        "Areas are clipped to the supplied study boundary and calculated in EPSG:32647.",
        "Peat overlaps are allowed as a separate soil-fuel scenario.",
        "Between-layer overlaps are intended. Preserve per-layer intersections; evaluate shared biomass separately.",
        "No priority, difference, dissolve-across-classes or fuel policy has been imposed.",
        "Pairwise overlap totals must not be added as a unique overlap area.",
        "No actual active-fire data or emission totals have been calculated.",
    ],
}
OUT.mkdir(parents=True, exist_ok=True)
write_json(OUT / "study_area.geojson", {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "Khuan Khreng study area", "area_ha": boundary.area / 10000}, "geometry": mapping(boundary_wgs)}]})
write_json(OUT / "landuse_layers.geojson", {"type": "FeatureCollection", "features": features})
write_json(ROOT / "outputs" / "tables" / "spatial_dataset_audit.json", report)
write_json(ROOT / "config" / "spatial_dataset.json", {
    "schema_version": 1, "dataset_root": str(DATASET),
    "boundary_path": str(boundary_path), "layers": {c: str(DATASET / "Landuse" / f) for c, f in LAYERS.items()},
    "metric_crs": "EPSG:32647", "web_crs": "EPSG:4326",
    "bbox_wgs84": bbox, "timezone": "Asia/Bangkok",
    "surface_class_overlap_policy": "intentional_overlapping_fuel_layers",
    "spatial_overlay_policy_ready": True,
    "study_boundary_policy": "use_supplied_boundary",
    "peat_policy": "separate_0_10_cm_scenario",
    "prepared_geojson": {"boundary": str(OUT / "study_area.geojson"), "landuse": str(OUT / "landuse_layers.geojson")},
})
lines = ["# Spatial dataset preparation", "", "Canonical source: E:\\LAB Emission\\Dataset", "",
         "Metric CRS: EPSG:32647. Web GeoJSON CRS: EPSG:4326.", "",
         f"Study boundary area: {boundary.area / 10000:.4f} ha",
         f"FIRMS bounding box (west,south,east,north): {','.join(f'{v:.7f}' for v in bbox)}", "",
         "| Layer | Records | Original ha | Inside study ha | Outside study ha |",
         "|---|---:|---:|---:|---:|"]
for code, m in layer_meta.items():
    lines.append(f"| {code} | {m['record_count']} | {m['source_area_ha']:.4f} | {m['clipped_area_ha']:.4f} | {m['outside_study_area_ha']:.4f} |")
lines.extend(["", "## Overlaps inside the study boundary", "",
              "| Layer A | Layer B | Overlap ha | Interpretation |", "|---|---|---:|---|"])
for r in overlaps:
    if r["overlap_ha"] > THRESHOLD_HA:
        interpretation = "Separate peat pool; permitted scenario" if r["contains_peat"] else "Intentional overlapping fuel layer"
        lines.append(f"| {r['layer_a']} | {r['layer_b']} | {r['overlap_ha']:.4f} | {interpretation} |")
lines.extend(["", f"Study area without a supplied surface vegetation class: {report['surface_unclassified_ha']:.4f} ha.",
              f"Study area without any supplied class (including peat): {report['all_layers_unclassified_ha']:.4f} ha.", "",
              "Separate files do not imply non-overlap. Do not add GRASS/LEPIRONIA over Melaleuca surface fuel if they represent the same undergrowth biomass.",
              "No overlap priority has been imposed. Canonical source files and final emission parameters were not modified.",
              "No emissions have been calculated.", ""])
(ROOT / "docs" / "SPATIAL_DATA_REVIEW.md").write_text("\n".join(lines), encoding="utf-8")
# Verify exported features can be reopened and read by the installed GIS library.
for path, expected in [(OUT / "study_area.geojson", 1), (OUT / "landuse_layers.geojson", 5)]:
    with fiona.open(path) as src:
        if len(src) != expected:
            raise ValueError(f"Wrong exported feature count: {path}")
        for feat in src:
            g = shape(feat["geometry"])
            if g.is_empty or not g.is_valid:
                raise ValueError(f"Invalid export: {path}")
print(json.dumps({"study_area_ha": report["study_area_ha"], "bbox_wgs84": bbox,
                  "layers": {k: round(v["clipped_area_ha"], 4) for k,v in layer_meta.items()},
                  "overlaps": [r for r in overlaps if r["overlap_ha"] > THRESHOLD_HA],
                  "surface_unclassified_ha": report["surface_unclassified_ha"],
                  "surface_overlap_detected": surface_overlap,
                  "exports_verified": True}, indent=2), flush=True)
