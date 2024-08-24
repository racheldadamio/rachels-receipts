import numpy as np


def replace_value_with_nan(df, columns, value):
    """
    Replace '-' with NaN in the specified columns of a pandas DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame to modify.
    columns (list): A list of column names where '-' should be replaced with NaN.

    Returns:
    pd.DataFrame: The modified DataFrame with '-' replaced by NaN.
    """
    df[columns] = df[columns].replace(value, np.nan)
    return df


def get_result(result_table, sb_table, rank_col="WRK_rank"):
    # Clean columns
    sb_table = replace_value_with_nan(sb_table, ["pb", "sb", "WRK"], "-")
    result_table = replace_value_with_nan(result_table, ["pos"], "DNF")
    sb_table["WRK"] = sb_table["WRK"].astype("Int64")
    result_table["pos"] = result_table["pos"].astype("Int64")

    # Add ranking columns
    sb_table["pb_rank"] = (
        sb_table["pb"].rank(method="min", na_option="bottom").astype("Int64")
    )
    sb_table["WRK_rank"] = (
        sb_table["WRK"]
        .replace(np.nan, 10000)
        .rank(method="min", na_option="bottom")
        .astype("Int64")
    )

    # Join results and WR
    result_sb_joined = result_table.merge(
        sb_table, on=["athlete", "bib", "country"], how="inner"
    )

    # Get difference between world ranking and finish place
    result_sb_joined["place_rank_diff"] = (
        result_sb_joined[rank_col] - result_sb_joined["pos"]
    )

    return result_sb_joined


def final_tables(result_sb_joined):
    usa_table = result_sb_joined[result_sb_joined["country"] == "USA"]

    over_performers = result_sb_joined.sort_values(
        "place_rank_diff", ascending=False
    ).head(5)

    under_performers = result_sb_joined.sort_values(
        "place_rank_diff", ascending=True
    ).head(5)

    pr_table = result_sb_joined[
        result_sb_joined["parsed_mark_time"] < result_sb_joined["pb"]
    ]

    return usa_table, over_performers, under_performers, pr_table
