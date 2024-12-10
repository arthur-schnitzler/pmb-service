import pandas as pd


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
