# Spatial dataset preparation

Canonical source: E:\LAB Emission\Dataset

Metric CRS: EPSG:32647. Web GeoJSON CRS: EPSG:4326.

Study boundary area: 93105.2729 ha
FIRMS bounding box (west,south,east,north): 99.9505972,7.7230902,100.2580598,8.2511715

| Layer | Records | Original ha | Inside study ha | Outside study ha |
|---|---:|---:|---:|---:|
| GRASS | 1 | 1226.3061 | 1226.3061 | 0.0000 |
| LEPIRONIA | 1 | 12214.7174 | 12214.2249 | 0.4925 |
| M_CAJU | 1 | 26112.0028 | 26111.1310 | 0.8718 |
| PADDY | 1 | 7954.7225 | 7954.7225 | 0.0000 |
| PEAT | 1 | 16205.1056 | 16154.7414 | 50.3642 |

## Overlaps inside the study boundary

| Layer A | Layer B | Overlap ha | Interpretation |
|---|---|---:|---|
| GRASS | LEPIRONIA | 5.4532 | Intentional overlapping fuel layer |
| GRASS | M_CAJU | 62.5542 | Intentional overlapping fuel layer |
| GRASS | PEAT | 102.4450 | Separate peat pool; permitted scenario |
| LEPIRONIA | M_CAJU | 11054.9839 | Intentional overlapping fuel layer |
| LEPIRONIA | PEAT | 4980.4730 | Separate peat pool; permitted scenario |
| M_CAJU | PADDY | 315.8772 | Intentional overlapping fuel layer |
| M_CAJU | PEAT | 8078.3547 | Separate peat pool; permitted scenario |
| PADDY | PEAT | 391.3246 | Separate peat pool; permitted scenario |

Study area without a supplied surface vegetation class: 57033.9750 ha.
Study area without any supplied class (including peat): 49713.3191 ha.

Separate files do not imply non-overlap. Do not add GRASS/LEPIRONIA over Melaleuca surface fuel if they represent the same undergrowth biomass.
No overlap priority has been imposed. Canonical source files and final emission parameters were not modified.
No emissions have been calculated.


User clarification (2026-11-13): Between-layer overlaps are intentional. Use the supplied study boundary, preserve each fuel layer, and calculate intersections independently. No disjoint-class replacement or priority is required solely due to overlap. Shared biomass within the Melaleuca undergrowth parameter remains an accounting consideration, not a geometry error.
