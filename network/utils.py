import pandas as pd
from datetime import datetime, date


def df_to_geojson_vect(
    df: pd.DataFrame, properties: list, lat="latitude", lon="longitude"
) -> tuple:
    """converts a dataframe into a geojson
    taken from https://blog.finxter.com/5-best-ways-to-convert-a-pandas-dataframe-to-geojson/

    Args:
        df (pd.DataFrame): a pandas DataFrame
        properties (list): column keys which should be used as properties
        lat (str, optional): the name of the column holding the latitute. Defaults to 'latitude'.
        lon (str, optional): the anem of the column holding the longitute. Defaults to 'longitude'.

    Returns:
        tuple: (lat, long)
    """
    features = df.apply(
        lambda row: {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row[lon], row[lat]],
            },
            "properties": {prop: row[prop] for prop in properties},
        },
        axis=1,
    ).tolist()
    return {"type": "FeatureCollection", "features": features}


def get_coords(row):
    if pd.isna(row["source_lat"]):
        return (row["target_lat"], row["target_lng"])
    else:
        return row["source_lat"], row["source_lng"]


def iso_to_lat_long(iso_date, start_date="1700-01-01", end_date="1990-12-31"):
    """
    Maps an ISO date string or datetime.date to latitude and longitude, ensuring
    earlier dates are more south (latitude) and earlier days within a year are more west (longitude).

    Args:
        iso_date (str | datetime.date): An ISO-formatted date string (e.g., "2023-01-01")
                                        or a datetime.date object.
        start_date (str): Start of the date range in ISO format (default: "1900-01-01").
        end_date (str): End of the date range in ISO format (default: "2100-12-31").

    Returns:
        tuple: A tuple containing latitude and longitude (both as floats).
    """
    try:
        # Ensure iso_date is a datetime.date object
        if isinstance(iso_date, str):
            date_obj = datetime.strptime(iso_date, "%Y-%m-%d").date()
        elif isinstance(iso_date, date):
            date_obj = iso_date
        else:
            raise ValueError("Invalid input type. Must be a string or datetime.date.")

        # Convert start_date and end_date to datetime.date objects
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Ensure date_obj is within range
        if not (start_date_obj <= date_obj <= end_date_obj):
            raise ValueError("Date is out of the specified range.")

        # Latitude: Based on the position of the date within the range (0–90)
        total_days = (end_date_obj - start_date_obj).days
        date_position = (date_obj - start_date_obj).days / total_days
        lat = 90 * date_position

        # Longitude: Inverted position of the day within the year (0–180)
        day_of_year = date_obj.timetuple().tm_yday
        days_in_year = (
            date(datetime(date_obj.year, 12, 31).year, 12, 31)
            - date(datetime(date_obj.year, 1, 1).year, 1, 1)
        ).days + 1
        day_position = (
            day_of_year - 1
        ) / days_in_year  # Normalize day position in the year
        lon = 180 * day_position

        return lat, lon
    except Exception as e:
        raise ValueError(f"Invalid input: {iso_date}") from e
