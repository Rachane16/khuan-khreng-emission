# Dashboard update — 13 November 2026
Display name: Kuan Kreng / KK-PSF OBSERVATORY — FIRE & EMISSION
The repository and deployed URL are retained so existing links continue to work.

## Delivered
- Imported 13 August–12 November 2026 plus current-day NRT: 93 saved Thai calendar days.
- Retained unavailable/partial source status, especially SNPP after 2 November.
- Added independent per-pixel clipped area and six fuel emission estimates.
- The daily total still unions selected footprints; independent popup values must not be summed.
- Added 7-day, 30-day and custom calendar charts with fuel stacks and sensor/peat filters.
- Missing dates remain missing, separate from fetched zero-fire dates.
- Added the six citation strings supplied by the project owner in the original row order.
- Kept all numerical fuel parameters unchanged; PADDY display label is ข้าว.
- Grouped method, parameters, NASA data links and study area under ข้อมูลเพิ่มเติม.
- Increased typography; OpenStreetMap remains default.
- Added Esri World Imagery and World Topo Map with service attribution.
- World Topo raster service is currently available, marked mature support, with retirement planned December 2029:
  https://www.arcgis.com/home/item.html?id=30e5fe3149c34df1ba922e6f5bbf808f

## Data and model
Pixel geometry remains the documented UTM scan/track approximation.
Peat emissions remain a 0–10 cm scenario.
Fuel-layer overlaps and separate Melaleuca pools are retained.
Input shapefiles remain unchanged.
Citation strings are owner-supplied; this change does not independently verify each paper against each parameter.

## Validation
17 Python behavior tests pass (including clipped pixel area, fuel sum and overlap accounting).
Node calendar-chart checks pass (30 dates, missing vs zero, partial sensors and peat toggle).
Browser: pixel popup, citations, imagery layer, topo layer selection, sensor filters and custom date range inspected.
Desktop and 390 px layout inspected; no document-level horizontal overflow observed.
Browser extension errors from Zotero were separate from application logs.

## Repeat imports
python scripts/import_history_range.py --months 3 --prompt-key
python scripts/refresh_derived.py
Existing --start-date/--end-date imports support at most 31 days per call.
The range importer batches larger requests and checks NASA transaction usage before each batch.
Three years can be requested as --months 36 when needed; that range was not imported in this update.
