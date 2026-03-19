# Field ID Generator

Python geospatial script to generate standardized and unique identifiers for polygon feature datasets based on U.S. state and county codes.

## Identifier format

Each polygon receives a standardized identifier based on:

- `STATEFP` = 2 digits  
- `COUNTYFP` = 3 digits  
- `SEQ` = 6 digits  

Example:

`28 + 001 + 000123 -> 28001000123`

## Outputs

The script creates the following fields:

- `Field_ID_TEXT`: primary standardized identifier (recommended)
- `Field_ID`: optional numeric version for platform-specific workflows (e.g., ArcGIS Pro)

## Public county source

This workflow uses a public U.S. Census Bureau county boundary dataset.

A suitable source is the U.S. Census Bureau Cartographic Boundary Files, such as the county layer distributed in `cb_2018_us_county_500k`.

The county dataset must contain:

- `STATEFP`
- `COUNTYFP`

These public Census fields provide the official state and county codes used to build the standardized identifier.

## Method

This workflow uses a single internal reference point for each polygon to perform spatial assignment to county boundaries.

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

## Example output

| STATEFP | COUNTYFP | Field_ID_TEXT | Field_ID |
|--------|----------|--------------|---------|
| 28     | 001      | 28001000001  | 28001000001 |
| 28     | 001      | 28001000002  | 28001000002 |

## Notes

- `Field_ID_TEXT` preserves the standardized identifier structure and is the recommended field for consistent use  
- `Field_ID` is provided as an optional numeric companion field for compatibility with certain platforms  
- County assignment is based on a single internal reference point per polygon  
- The sequential component (`SEQ`) is generated based on dataset ordering within each county. If the dataset changes (e.g., new polygons are added or ordering changes), sequence values may change  

## Author

Flávia Souza  

Precision agriculture and geospatial data workflows
