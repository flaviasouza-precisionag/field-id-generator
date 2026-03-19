# Field ID Generator

Python geospatial script to create a standardized and unique identifier for polygon feature datasets.

## Identifier format

Each polygon receives a standardized identifier based on:

- `STATEFP` = 2 digits
- `COUNTYFP` = 3 digits
- `SEQ` = 6 digits

Example:

`28 + 001 + 000123 -> 28001000123`

## Outputs

The script creates:

- `Field_ID_TEXT`: text version of the standardized identifier
- `Field_ID`: optional numeric version for platform-specific workflows

## Public county source

This workflow uses a public U.S. Census Bureau county boundary dataset.

A suitable source is the U.S. Census Bureau Cartographic Boundary Files, such as the county layer distributed in `cb_2018_us_county_500k`.

The county dataset must contain:
- `STATEFP`
- `COUNTYFP`

These public Census fields provide the official state and county codes used to build the standardized identifier.

## Method

This workflow uses a single reference point for each polygon.

The reference point is defined as:
- the polygon centroid when it falls within or on the polygon
- otherwise, an internal representative point

This reference point is spatially joined to the county boundary dataset to retrieve:
- `STATEFP`
- `COUNTYFP`

These values are then used to build the standardized identifier.

## Optional numeric field

The script can optionally create a numeric companion field for platform-specific workflows.

Available options:
- `DOUBLE`
- `BIGINTEGER`

This allows flexibility for different publication or data-consumption environments.

## Requirements

- Python geospatial environment
- `geopandas`
- `pandas`
- polygon feature dataset
- county boundary dataset containing `STATEFP` and `COUNTYFP`

## Coordinate reference system (CRS)

For correct spatial operations, both the field polygon dataset and the county boundary dataset must use the same coordinate reference system (CRS).

If the datasets use different CRS, this script automatically reprojects the county dataset to match the CRS of the field dataset.

Ensuring a consistent CRS is essential for accurate spatial joins.

## Parameters to edit in the script

Update these variables in `generate_field_id_geopandas.py`:

- `FIELDS_PATH`
- `FIELDS_LAYER`
- `COUNTY_PATH`
- `COUNTY_LAYER`
- `OUTPUT_PATH`
- `OUTPUT_LAYER`
- `ADD_NUMERIC_FIELD`
- `NUMERIC_FIELD_NAME`
- `NUMERIC_FIELD_TYPE`
- `TEXT_FIELD_NAME`

## Notes

- `Field_ID_TEXT` preserves the standardized identifier structure
- `Field_ID` can be used as an optional numeric companion field
- county assignment is based on a single reference point per polygon

## Author

Flávia Souza

Precision agriculture and geospatial data workflows