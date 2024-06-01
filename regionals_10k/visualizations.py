import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns


def melt_rank_df(rank_df, top_n=12):
    # Select columns with rank
    rank_df = rank_df.loc[:, rank_df.columns.str.contains("rank|Athlete", case=False)]
    # Melt the DataFrame to long format for easier plotting
    df_melted = rank_df.head(top_n).melt(
        id_vars="Athlete", var_name="meters", value_name="rank"
    )
    # Sort the DataFrame by athlete and lap
    df_melted["meters"] = df_melted["meters"].str.extract("(\d+)").astype(int)
    df_melted = df_melted.sort_values(["Athlete", "meters"])
    return df_melted


def race_progression_plot(df, gender, region):
    # Set up the plot
    plt.figure(figsize=(12, 8))
    sns.lineplot(data=df, x="meters", y="rank", hue="Athlete", marker="o")

    # Customizing the plot
    plt.gca().invert_yaxis()  # Invert y-axis to show 1st rank at the top
    plt.xlabel("Meters")
    plt.ylabel("Place")
    plt.title(f"{region} region {gender}'s 10,000m: Athlete Progression")

    # Get the ranks of athletes at 10000 meters
    ranks_at_10000m = df[df["meters"] == 10000].set_index("Athlete")["rank"]

    # Adding and sorting the legend
    handles, labels = plt.gca().get_legend_handles_labels()
    sorted_labels_handles = sorted(
        zip(labels, handles), key=lambda x: ranks_at_10000m[x[0]], reverse=False
    )
    sorted_labels, sorted_handles = zip(*sorted_labels_handles)

    # Display the legend with sorted labels and handles
    plt.legend(sorted_handles, sorted_labels, title="Athlete (sorted by finish place)")

    # Show the plot
    plt.show()


def race_progression_plot_interactive(df, gender, region):
    # Create an interactive line plot with Plotly
    fig = px.line(
        df,
        x="meters",
        y="rank",
        color="Athlete",
        hover_name="Athlete",
        title=f"{region} region {gender}'s 10,000m: Athlete Progression",
        labels={"meters": "Meters", "rank": "Place"},
        line_shape="linear",
        render_mode="svg",
        markers=True,
        category_orders={
            "Athlete": df[df["meters"] == 10000].sort_values("rank")["Athlete"]
        },
    )

    # Customize the layout
    fig.update_yaxes(autorange="reversed")  # Invert y-axis to show 1st rank at the top
    # Move legend to overlay the plot
    fig.update_layout(
        legend=dict(
            title="Athlete (sorted by finish place)",
            orientation="v",  # Vertical orientation
            font=dict(size=6),  # Set legend font size
        )
    )

    # Show the plot
    fig.show()


def get_top_12_df(
    df,
):
    df["top_12"] = df["rank"].apply(lambda row: (row <= 12))
    top_12_perc = df.groupby("meters")["top_12"].sum()  # * 100
    # Convert the result to a DataFrame for plotting
    top_12_df = top_12_perc.reset_index()
    top_12_df.columns = ["meters", "percent_top_12"]
    return top_12_df


def top_12_plot(df, gender, region):
    # Plotting the line chart
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x="meters", y="percent_top_12", marker="o")

    # Customizing the plot
    plt.xlabel("Meters")
    plt.ylabel("Number of Qualifiers in Top 12")
    plt.title(
        f"{region} region {gender}'s 10,000m: Number of Qualifiers in Top 12 at Each Lap"
    )
    plt.grid(True)

    # Show the plot
    plt.show()


def top_12_plot_interactive(df, gender, region):
    # Create an interactive line plot using Plotly
    fig = px.line(
        df,
        x="meters",
        y="percent_top_12",
        title="Number of Qualifiers in Top 12 at each lap",
        labels={"meters": "Meters", "percent_top_12": "Number of Qualifiers in Top 12"},
        markers=True,
        line_shape="linear",
    )

    # Customize the layout
    fig.update_layout(
        xaxis=dict(title="Meters"),
        yaxis=dict(title="Number of Qualifiers in Top 12"),
        title=dict(
            text=f"{region} region {gender}'s 10,000m: Number of Qualifiers in Top 12 at Each Lap"
        ),
    )

    # Show the plot
    fig.show()
