import matplotlib.pyplot as plt
from pandas import DataFrame


def bar_stacked_on_column(df: DataFrame, column: str):

    # --- New Logic to Order the Stack ---

    # 1. Calculate the mean of 'new_periods' for each 'treatment' across all periods
    treatment_means = df.groupby("treatment")[column].mean()

    # 2. Get the order of treatments: sorted ascending (smallest mean first)
    # This places the treatment with the smallest average 'new_periods' at the bottom of the stack.
    sorted_treatments = treatment_means.sort_values(ascending=True).index.tolist()

    # Step 1: Aggregate the data for the stacked bar chart
    # Group by 'period' and 'treatment' and sum 'new_periods', then unstack 'treatment'
    plot_data = (
        df.groupby(["period", "treatment"])[column].sum().unstack()
    )

    # 4. Reindex the columns of the aggregated data to enforce the desired stacking order
    plot_data_ordered = plot_data[sorted_treatments]

    # Step 2: Plot the stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the stacked bars
    plot_data_ordered.plot(kind="bar", stacked=True, ax=ax, width=1.0)

    # Set labels and title
    ax.set_title(f"{column} by Period, Stacked on Treatment")
    ax.set_xlabel("Period")
    ax.set_ylabel(f"col {column}")

    # Format x-axis ticks to display the date nicely
    ax.set_xticklabels(
        [p.strftime("%Y-%m-%d") for p in plot_data_ordered.index],
        rotation=45,
        ha="right",
    )

    # Add a legend
    ax.legend(title="Treatment", bbox_to_anchor=(1.05, 1), loc="upper left")

    # Adjust layout to make room for the rotated x-axis labels and legend
    plt.tight_layout()

