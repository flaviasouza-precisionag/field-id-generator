# =========================================================
# Field ID Generator
# ---------------------------------------------------------
# Creates a standardized and unique identifier for each polygon:
#
#   Field_ID_TEXT = STATEFP (2) + COUNTYFP (3) + SEQ (6)
#   Example: 28 + 001 + 000123 -> 28001000123
#
# Outputs:
# - Field_ID_TEXT: text version of the standardized identifier
# - Field_ID: optional numeric version for platform-specific workflows
#
# Public county source:
# - U.S. Census Bureau Cartographic Boundary Files
# - Example county layer: cb_2018_us_county_500k
# - Required fields in county dataset: STATEFP, COUNTYFP
#
# Method:
# - Uses a single reference point for each polygon
# - Uses centroid when it falls inside the polygon
# - Otherwise uses representative_point() to guarantee an internal point
# - Assigns county attributes through spatial join
# - Generates a sequential identifier within each county
# =========================================================

from pathlib import Path
import geopandas as gpd
import pandas as pd


# =========================
# USER SETTINGS
# =========================
FIELDS_PATH = r"C:\path\to\field_polygons.gpkg"
FIELDS_LAYER = None   # Use None for single-layer files; set layer name if needed

COUNTY_PATH = r"C:\path\to\cb_2018_us_county_500k.shp"
COUNTY_LAYER = None   # Use None for shapefile; set layer name if needed

OUTPUT_PATH = r"C:\path\to\field_polygons_with_id.gpkg"
OUTPUT_LAYER = "field_polygons_with_id"

# Optional numeric companion field
ADD_NUMERIC_FIELD = True
NUMERIC_FIELD_NAME = "Field_ID"
NUMERIC_FIELD_TYPE = "DOUBLE"   # Options: "DOUBLE", "BIGINTEGER"

TEXT_FIELD_NAME = "Field_ID_TEXT"


# =========================
# HELPERS
# =========================
def log(message: str) -> None:
    print(f"[INFO] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def read_geodata(path: str, layer: str | None = None) -> gpd.GeoDataFrame:
    if layer:
        return gpd.read_file(path, layer=layer)
    return gpd.read_file(path)


def validate_numeric_type(value: str) -> None:
    if value not in {"DOUBLE", "BIGINTEGER"}:
        raise ValueError("NUMERIC_FIELD_TYPE must be 'DOUBLE' or 'BIGINTEGER'")


def validate_inputs() -> None:
    if not Path(FIELDS_PATH).exists():
        raise FileNotFoundError(f"Field dataset not found: {FIELDS_PATH}")

    if not Path(COUNTY_PATH).exists():
        raise FileNotFoundError(f"County dataset not found: {COUNTY_PATH}")


def warn_if_fields_exist(fields_gdf: gpd.GeoDataFrame) -> None:
    fields_to_check = ["STATEFP", "COUNTYFP", TEXT_FIELD_NAME]
    if ADD_NUMERIC_FIELD:
        fields_to_check.append(NUMERIC_FIELD_NAME)

    existing = [col for col in fields_to_check if col in fields_gdf.columns]
    if existing:
        warn(
            "The following field(s) already exist and will be overwritten: "
            + ", ".join(existing)
        )


def build_reference_points(fields_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Uses centroid when it falls inside or on the polygon.
    Otherwise uses representative_point() to guarantee an internal point.
    """
    centroids = fields_gdf.geometry.centroid
    inside_mask = centroids.within(fields_gdf.geometry) | centroids.touches(fields_gdf.geometry)
    fallback_points = fields_gdf.geometry.representative_point()
    ref_points = centroids.where(inside_mask, fallback_points)

    ref_gdf = gpd.GeoDataFrame(
        fields_gdf.drop(columns="geometry").copy(),
        geometry=ref_points,
        crs=fields_gdf.crs,
    )

    ref_gdf["SRC_INDEX"] = fields_gdf.index
    ref_gdf["Center_Lon"] = ref_gdf.geometry.x.round(6)
    ref_gdf["Center_Lat"] = ref_gdf.geometry.y.round(6)

    return ref_gdf


def add_state_county(fields_gdf: gpd.GeoDataFrame, county_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ref_gdf = build_reference_points(fields_gdf)

    joined = gpd.sjoin(
        ref_gdf,
        county_gdf[["STATEFP", "COUNTYFP", "geometry"]],
        how="left",
        predicate="within",
    )

    joined = joined.sort_values(by=["SRC_INDEX"]).drop_duplicates(subset=["SRC_INDEX"], keep="first")
    state_county = joined.set_index("SRC_INDEX")[["STATEFP", "COUNTYFP"]]

    out = fields_gdf.copy()
    out["STATEFP"] = state_county["STATEFP"]
    out["COUNTYFP"] = state_county["COUNTYFP"]

    out["STATEFP"] = out["STATEFP"].astype("string").str.zfill(2)
    out["COUNTYFP"] = out["COUNTYFP"].astype("string").str.zfill(3)

    return out


def create_text_id(fields_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = fields_gdf.copy()

    # Sequential order is based on STATEFP, COUNTYFP, and original source index.
    sort_df = out.reset_index().rename(columns={"index": "SRC_INDEX"})
    sort_df = sort_df.sort_values(by=["STATEFP", "COUNTYFP", "SRC_INDEX"], na_position="last").copy()

    current_key = None
    seq = 0
    id_map = {}

    for _, row in sort_df.iterrows():
        src_index = row["SRC_INDEX"]
        st = row["STATEFP"]
        co = row["COUNTYFP"]

        if pd.isna(st) or pd.isna(co):
            id_map[src_index] = None
            continue

        key = (st, co)
        if key != current_key:
            current_key = key
            seq = 1
        else:
            seq += 1

        id_map[src_index] = f"{st}{co}{seq:06d}"

    out[TEXT_FIELD_NAME] = out.index.map(id_map)
    return out


def add_numeric_id(fields_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = fields_gdf.copy()

    if not ADD_NUMERIC_FIELD:
        return out

    if NUMERIC_FIELD_TYPE == "DOUBLE":
        out[NUMERIC_FIELD_NAME] = pd.to_numeric(
            out[TEXT_FIELD_NAME], errors="coerce"
        ).astype("float64")
    elif NUMERIC_FIELD_TYPE == "BIGINTEGER":
        out[NUMERIC_FIELD_NAME] = pd.to_numeric(
            out[TEXT_FIELD_NAME], errors="coerce"
        ).astype("Int64")

    return out


def qa_checks(fields_gdf: gpd.GeoDataFrame) -> None:
    vals = fields_gdf[TEXT_FIELD_NAME].dropna().astype(str)

    duplicates = int(vals.duplicated().sum())
    nulls = int(fields_gdf[TEXT_FIELD_NAME].isna().sum())
    length_errors = int((vals.str.len() != 11).sum())
    assigned_county = int(fields_gdf["STATEFP"].notna().sum())
    total_records = len(fields_gdf)

    log("QA summary:")
    log(f"  Total records: {total_records}")
    log(f"  Records with county assigned: {assigned_county}")
    log(f"  Null IDs: {nulls}")
    log(f"  Duplicate IDs: {duplicates}")
    log(f"  Length errors: {length_errors}")


def main() -> None:
    validate_numeric_type(NUMERIC_FIELD_TYPE)
    validate_inputs()

    log("Reading field polygons...")
    fields_gdf = read_geodata(FIELDS_PATH, FIELDS_LAYER)

    log(f"Field records loaded: {len(fields_gdf)}")
    warn_if_fields_exist(fields_gdf)

    log("Reading county boundaries...")
    county_gdf = read_geodata(COUNTY_PATH, COUNTY_LAYER)

    log(f"County records loaded: {len(county_gdf)}")

    if fields_gdf.crs is None or county_gdf.crs is None:
        raise ValueError("Both input datasets must have a defined CRS.")

    if fields_gdf.crs != county_gdf.crs:
        log("CRS differs between layers. Reprojecting county layer to match fields...")
        county_gdf = county_gdf.to_crs(fields_gdf.crs)

    required_fields = {"STATEFP", "COUNTYFP"}
    missing = required_fields - set(county_gdf.columns)
    if missing:
        raise ValueError(f"County layer is missing required field(s): {sorted(missing)}")

    log("Assigning STATEFP and COUNTYFP...")
    out = add_state_county(fields_gdf, county_gdf)

    log("Creating text identifier...")
    out = create_text_id(out)

    if ADD_NUMERIC_FIELD:
        log(f"Creating optional numeric field: {NUMERIC_FIELD_NAME} ({NUMERIC_FIELD_TYPE})")
        out = add_numeric_id(out)

    log("Running QA checks...")
    qa_checks(out)

    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log("Writing output...")
    if output_path.suffix.lower() == ".gpkg":
        out.to_file(output_path, layer=OUTPUT_LAYER, driver="GPKG")
    else:
        out.to_file(output_path)

    log(f"Done: {output_path}")
    log(f"Output records written: {len(out)}")


if __name__ == "__main__":
    main()
