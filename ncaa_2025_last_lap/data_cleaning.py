import re

import numpy as np


def insert_nas(df):
    return df.replace(r"^\s*$", np.nan, regex=True)


def parse_time(df):
    df["Time"] = df["Time"].apply(lambda x: x[:8])
    return df


def clean_names(df):
    # Define the regular expression pattern
    pattern = r"^(\w+)\s([A-Z]+)"

    # Extract the first name and last name
    df["Athlete"] = (
        df["Athlete"]
        .str.extract(pattern)
        .apply(" ".join, axis=1)
        .str.title()
        .str.slice(stop=-1)
    )
    return df


# Function to split and clean columns
def split_and_clean_column(df, column_name, delimiter="["):
    # Split the column into two new columns
    new_cols = df[column_name].str.split(delimiter, expand=True)

    # Remove the delimiter from the resulting columns
    new_cols = new_cols.map(lambda x: x.replace("]", "") if isinstance(x, str) else x)

    # Rename new columns and concatenate them with the original DataFrame
    df[[f"{column_name}_tot", f"{column_name}_split"]] = new_cols
    return df


def clean_results_df(df):
    df = insert_nas(df)

    df = parse_time(df)

    df = clean_names(df)

    # Apply the function to columns containing '00m'
    columns_to_split = [col for col in df.columns if "00m" in col or "Lap" in col]

    for col in columns_to_split:
        df = split_and_clean_column(df, col)

    # Drop original columns if desired
    df.drop(columns=columns_to_split, inplace=True)

    return df


def add_ranks(df):
    # Identify columns containing '00m'
    columns_to_rank = [
        col for col in df.columns if "00m_tot" in col or re.search(r"Lap \d+_tot", col)
    ]

    # Create new columns with ranks
    for col in columns_to_rank:
        df[f"{col}_rank"] = df[col].rank(
            method="min", na_option="bottom", ascending=True
        )
        df[f"{col}_rank"] = df[f"{col}_rank"].astype(int)

    return df
