import numpy as np


def insert_nas(df):
    return df.replace(r"^\s*$", np.nan, regex=True)


def clean_names(df, event_name):
    # Define the regular expression pattern

    if "Relay" in event_name:
        pattern = r"([A-Z.\s]+)"

        # Extract the continuous capital letters using str.extract
        df["Name"] = df["Team"].str.extract(pattern, expand=False).str.title()

        # Remove the last letter from the extracted string
        df["Name"] = df["Name"].str[:-1]

        # Modify the column if LSU b/c I couldn't figure it out
        df.loc[df["Name"] == "Lsuls", "Name"] = "LSU"
        df.loc[df["Name"] == "Uscus", "Name"] = "USC"
    else:
        pattern = r"^(\w+)\s([A-Z]+)"
        df["Athlete"] = df["Athlete"].str.replace(r"'", "", regex=True)
        df["Athlete"] = df["Athlete"].str.replace("USC", "U", regex=True)
        df["Athlete"] = df["Athlete"].str.replace("LSU", "L", regex=True)
        # Extract the first name and last name
        df["Name"] = (
            df["Athlete"]
            .str.extract(pattern)
            .apply(" ".join, axis=1)
            .str.title()
            .str.slice(stop=-1)
        )

    return df


def clean_results_df(df, event_name):
    df = insert_nas(df)

    df = clean_names(df, event_name)

    return df


def filter_results_df(df, places):
    # recreate Pl column in case of ties
    df = df.dropna()
    df["Pl"] = range(len(df))
    df["Pl"] = df["Pl"].astype(str)
    # df = df.drop_duplicates(subset="Pl", keep="first")
    return df[df["Pl"].isin(places)]


def convert_to_seconds(time_str):
    if len(time_str) > 5:
        minutes, seconds = time_str.split(":")
        return int(minutes) * 60 + float(seconds)
    else:
        return float(time_str)


def add_time_in_seconds(df):
    df.loc[:, "time_in_seconds"] = df.loc[:, "Time"].apply(convert_to_seconds)
    return df


def get_meters(df):
    df["Mark"] = df["Best"].str.split("m").str[0]
    df["Mark"] = df["Mark"].astype(float)
    return df


def get_points(df):
    df["Mark"] = df["Points"].str.split("\\n").str[0]
    df["Mark"] = df["Mark"].astype(float)
    return df


def add_victory_margin(df, col_name="time_in_seconds"):
    if col_name == "time_in_seconds":
        df.loc[:, "victory_margin_perc"] = (df.loc[:, col_name].pct_change()).round(6)
        df.loc[:, "victory_margin_s"] = df.loc[:, col_name] - df.loc[:, col_name].shift(
            1
        )
        df.loc[:, "victory_margin_s"] = df.loc[:, "victory_margin_s"].round(2)
    else:
        df = df.sort_values(by="Pl", ascending=False)
        df.loc[:, "victory_margin_perc"] = (df.loc[:, col_name].pct_change()).round(6)
        df.loc[:, "victory_margin_s"] = df.loc[:, col_name] - df.loc[:, col_name].shift(
            1
        )
        df.loc[:, "victory_margin_s"] = df.loc[:, "victory_margin_s"].round(2)
        df = df.bfill()
    return df


def pivot_to_one_row(df):
    # Pivot the DataFrame
    pivot_df = df.pivot(index="event", columns="Pl")

    # Flatten the multi-level column index
    pivot_df.columns = [f"{col[0]}_{col[1]}" for col in pivot_df.columns]
    return pivot_df


def final_format_top_two(df, col_name="Time"):
    if col_name == "Time":
        unit = "s"
    elif col_name == "Mark":
        unit = "m"
    df["1st place name"] = df["Name_1"]
    df["2nd place name"] = df["Name_2"]
    df[f"1st place {col_name.lower()}"] = df[f"{col_name}_1"]
    df[f"2nd place {col_name.lower()}"] = df[f"{col_name}_2"]
    df[f"Margin of victory ({unit})"] = df["victory_margin_s_2"]
    df["Margin of victory (%)"] = df["victory_margin_perc_2"]
    df["Event"] = df.index

    return df[
        [
            "Event",
            "1st place name",
            "2nd place name",
            f"1st place {col_name.lower()}",
            f"2nd place {col_name.lower()}",
            f"Margin of victory ({unit})",
            "Margin of victory (%)",
        ]
    ].reset_index(drop=True)


def final_format_all_am(df, col_name="Time"):
    if col_name == "Time":
        unit = "s"
    elif col_name == "Mark":
        unit = "m"
    df["1st place name"] = df["Name_1"]
    df["8th place name"] = df["Name_8"]
    df[f"1st place {col_name.lower()}"] = df[f"{col_name}_1"]
    df[f"8th place {col_name.lower()}"] = df[f"{col_name}_8"]
    df[f"All American Spread ({unit})"] = df["victory_margin_s_8"]
    df["All American Spread (%)"] = df["victory_margin_perc_8"]
    df["Event"] = df.index

    return df[
        [
            "Event",
            "1st place name",
            "8th place name",
            f"1st place {col_name.lower()}",
            f"8th place {col_name.lower()}",
            f"All American Spread ({unit})",
            "All American Spread (%)",
        ]
    ].reset_index(drop=True)
