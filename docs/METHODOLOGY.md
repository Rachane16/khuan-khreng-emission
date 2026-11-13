# Methodology decisions and recommendations

Recorded: 2026-11-13 (Asia/Bangkok)

## Confirmed user decisions
1. Study area: Khuan Khreng peat swamp forest, Thailand.
2. Active Fire polygon area is defined operationally as burned area for this project.
3. Use MODIS Terra/Aqua, VIIRS S-NPP, NOAA-20 and NOAA-21 observations.
4. Display observations and areas by individual calendar day; retain historical days separately.
5. Do not produce the daily display by accumulating all earlier days' burned polygons.
6. Treat peat combustion in the 0-10 cm layer as a scenario.
7. Store new project work under E:\LAB Emission.
8. Use the user-declared final parameters in config/emission_parameters.json.

The operational burned-area definition is a project assumption. FIRMS pixel footprints are observation footprints, not independently mapped fire perimeters.
https://firms.modaps.eosdis.nasa.gov/map/index.html

## Recommended daily spatial processing
- Convert acquisition UTC timestamps to Asia/Bangkok before assigning the calendar day.
- Preserve source, satellite, acquisition timestamp, confidence, scan/track, geometry method and fetch timestamp.
- Remove repeated copies of the same observation from overlapping downloads.
- Obtain pixel footprints where a supported source supplies them; otherwise build explicitly approximate footprints from available geometry information. Verify global/Thailand coverage; US/Canada footprint services alone do not establish Thailand availability.
- For each day and selected sensor policy, take the geometric union of footprints, then clip to the study boundary. Do not sum individual pixel areas before union.
- Calculate metric areas in WGS 84 / UTM zone 47N (EPSG:32647), then convert m2 to ha.
- Rebuild and replace each day's derived output idempotently when new or revised observations arrive. Do not append emission totals on every fetch.
- Retain old daily records and their revisions. Display the selected day's footprint.
- Calculate cross-day overlap as a QA flag without subtracting previous days from the requested daily display.
- Repeated daily detections of the same place do not establish replenishment of pre-fire fuel. A physically cumulative emission total requires a repeated-burning/fuel-consumption policy. A daily independent scenario must state its fuel-reset assumption.

## Land-use overlap and fuel pools
For day d, let B_d be the unioned daily active-fire area and L_j the spatial extent of fuel j.
A_dj = area(B_d intersect L_j), in ha.
E_dj_kg = A_dj * rho_j * eta_j * EF_j.
E_d_total_kg = sum_j(E_dj_kg).

Do not apply every fuel parameter to the entire B_d unless that fuel genuinely covers all of B_d.
- Overlap between distinct physical fuel pools is allowed: mature Melaleuca surface fuel, mature leaves+bark, and underlying peat.
- Overlap between land-cover classes is not automatically an additional fuel pool. Check GRASS versus LEPIRONIA versus PADDY versus Melaleuca for duplicated classification.
- Undergrowth is already included in the Melaleuca surface-fuel parameter. A GRASS/LEPIRONIA layer representing that same undergrowth must not add the same biomass again.
- On the Melaleuca footprint, calculate surface fuel and leaves+bark separately and sum the two emissions.
- Add the peat scenario only on B_d intersect peat extent. Do not infer soil combustion from canopy/surface detection alone.
- Report unique ground area and fuel-pool overlap areas separately. Sum of pool areas can exceed unique ground area and must not be labeled total burned ground area.

## Footprints and sensor policy: recommendation, not yet selected
Pixel polygons support area/intersection operations better than centroids.
MODIS pixels are coarser than VIIRS. Union across all sensors removes duplicated area but can increase the result relative to VIIRS-only coverage.
Compare VIIRS-only and combined-sensor daily area before selecting the production calculation policy.
Do not assign a circular radius of 375 m merely because VIIRS has nominal 375 m pixel dimensions.
https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html
https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html
https://firms.modaps.eosdis.nasa.gov/usfs/active_fire/

## Parameters and scenarios
The confirmed table contains six fuel pools, including two Melaleuca lowland pools.
Peat remains rho=210 tonne DM/ha, eta=0.54, EF=3.02 g/kg, with the user-declared ranges retained.
The later literature alternative rho=124 +/-10 tonne DM/ha is not substituted automatically.
Peat sampling depth is not observed burn depth. The 0-10 cm combustion assumption is explicitly a scenario.
No actual daily area or emissions have been calculated in this design step.

## Prototype architecture recommendation
FIRMS API -> scheduled GitHub Actions collector -> spatial processing -> daily JSON/GeoJSON -> GitHub Pages dashboard.
Store MAP_KEY only in a workflow secret, not in published browser assets.
Preserve raw observations and versioned parameters so results can be reproduced.
The supplied Dataset study boundary is in use. Collector configuration, sensor policy and credential setup remain pending.

## User clarification: intentional overlapping fuel layers (2026-11-13)
Separate fuel shapefiles are intended to overlap. Preserve their extents and use per-layer intersections with each daily active-fire union. Overlap alone is not a data defect and does not require a class-priority or erasure step. Unique ground area is reported separately from fuel-layer area. Shared undergrowth biomass still requires consistent accounting when applying combined fuel parameters.
