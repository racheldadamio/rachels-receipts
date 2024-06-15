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


def add_victory_margin(df):
    df.loc[:, "victory_margin_perc"] = (
        df.loc[:, "time_in_seconds"].pct_change()
    ).round(2)
    df.loc[:, "victory_margin_s"] = (
        df.loc[:, "time_in_seconds"] - df.loc[:, "time_in_seconds"].shift(1)
    ).round(4)
    return df


def pivot_to_one_row(df):
    # Pivot the DataFrame
    pivot_df = df.pivot(index="event", columns="Pl")

    # Flatten the multi-level column index
    pivot_df.columns = [f"{col[0]}_{col[1]}" for col in pivot_df.columns]
    return pivot_df


def final_format_top_two(df):
    df["1st place name"] = df["Name_1"]
    df["2nd place name"] = df["Name_2"]
    df["1st place time"] = df["Time_1"]
    df["2nd place time"] = df["Time_2"]
    df["Margin of victory (s)"] = df["victory_margin_s_2"]
    df["Margin of victory (%)"] = df["victory_margin_perc_2"]
    df["Event"] = df.index

    return df[
        [
            "Event",
            "1st place name",
            "2nd place name",
            "1st place time",
            "2nd place time",
            "Margin of victory (s)",
            "Margin of victory (%)",
        ]
    ].reset_index(drop=True)


def final_format_all_am(df):
    df["1st place name"] = df["Name_1"]
    df["8th place name"] = df["Name_8"]
    df["1st place time"] = df["Time_1"]
    df["8th place time"] = df["Time_8"]
    df["All American Spread (s)"] = df["victory_margin_s_8"]
    df["All American Spread (%)"] = df["victory_margin_perc_8"]
    df["Event"] = df.index

    return df[
        [
            "Event",
            "1st place name",
            "8th place name",
            "1st place time",
            "8th place time",
            "All American Spread (s)",
            "All American Spread (%)",
        ]
    ].reset_index(drop=True)
