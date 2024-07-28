import pandas as pd


# Function to convert time to seconds
def convert_to_seconds(time_str):
    if ":" in time_str:
        minutes, seconds = time_str.split(":")
        return int(minutes) * 60 + float(seconds)
    else:
        return float(time_str)


def parse_with_wind(path):
    # Define the column names and their corresponding widths
    column_names = [
        "rank",
        "time",
        "wind",
        "athlete_name",
        "athlete_country",
        "athlete_dob",
        "race_place",
        "race_location",
        "race_date",
    ]
    colspecs = [
        (0, 5),
        (6, 16),
        (17, 24),
        (25, 55),
        (56, 63),
        (64, 75),
        (76, 82),
        (83, 109),
        (110, 121),
    ]

    # Read the fixed-width formatted file
    file_path = path
    df = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=column_names)

    # Select relevant columns
    df = df[["rank", "time", "athlete_name", "race_date"]]

    # Clean the time column
    df["time"] = df["time"].str.replace(r"[^\d.:]", "", regex=True)

    # Convert race_date to datetime and extract the year
    df["race_date"] = pd.to_datetime(df["race_date"], format="%d.%m.%Y")
    df["race_year"] = df["race_date"].dt.year
    df["event"] = path.replace(".txt", "")
    df["time_in_secs"] = df["time"].apply(convert_to_seconds)

    return df


def parse_no_wind(path):
    # Define the column names and their corresponding widths
    column_names = [
        "rank",
        "time",
        "athlete_name",
        "athlete_country",
        "athlete_dob",
        "race_place",
        "race_location",
        "race_date",
    ]
    colspecs = [
        (0, 5),
        (6, 16),
        (17, 47),
        (48, 55),
        (56, 67),
        (68, 74),
        (75, 102),
        (103, 114),
    ]

    # Read the fixed-width formatted file
    file_path = path
    df = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=column_names)

    # Select relevant columns
    df = df[["rank", "time", "athlete_name", "race_date"]]

    # Clean the time column
    df["time"] = df["time"].str.replace(r"[^\d.:]", "", regex=True)

    # Convert race_date to datetime and extract the year
    df["race_date"] = pd.to_datetime(df["race_date"], format="%d.%m.%Y")
    df["race_year"] = df["race_date"].dt.year
    df["event"] = path.replace(".txt", "")
    df["time_in_secs"] = df["time"].apply(convert_to_seconds)

    return df
