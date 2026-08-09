"""
Global Food Wastage Analysis - SQL + Statistical Deep Dive
-------------------------------------------------------------
Extends the original matplotlib-only analysis by:
  1. Loading the data into SQLite and answering the core questions with SQL
     (instead of pure pandas), so aggregation logic is transparent and reusable.
  2. Year-over-year trend analysis per country and per food category.
  3. Correlation analysis between waste, economic loss, and population.
  4. IQR-based outlier detection to flag countries with abnormally high waste
     relative to their population.

Dataset: Kaggle "Global Food Wastage Dataset (2018-2024)"
Expected columns:
    Country, Year, Food Category, Total Waste (Tons),
    Economic Loss (Million $), Avg Waste per Capita (Kg),
    Population (Million), Household Waste (%)

Usage:
    python sql_trend_analysis.py --csv global_food_wastage_data.csv
"""

import argparse
import sqlite3
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# 0. Setup
# ---------------------------------------------------------------------------

NUMERIC_COLS = [
    "Total Waste (Tons)",
    "Economic Loss (Million $)",
    "Avg Waste per Capita (Kg)",
    "Population (Million)",
    "Household Waste (%)",
]


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [c for c in NUMERIC_COLS + ["Country", "Year", "Food Category"] if c not in df.columns]
    if missing:
        print(f"WARNING: expected columns not found: {missing}")
        print(f"Columns present: {list(df.columns)}")
    return df


def to_sql(df: pd.DataFrame) -> sqlite3.Connection:
    """Push the dataframe into an in-memory SQLite DB so we can query it with SQL."""
    conn = sqlite3.connect(":memory:")
    df.to_sql("food_waste", conn, index=False, if_exists="replace")
    return conn


# ---------------------------------------------------------------------------
# 1. SQL-driven aggregations (replaces pure-pandas groupby calls)
# ---------------------------------------------------------------------------

def top_10_countries_sql(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            Country,
            ROUND(SUM("Total Waste (Tons)"), 0) AS total_waste_tons,
            ROUND(SUM("Economic Loss (Million $)"), 1) AS total_economic_loss_million
        FROM food_waste
        GROUP BY Country
        ORDER BY total_waste_tons DESC
        LIMIT 10;
    """
    return pd.read_sql_query(query, conn)


def waste_by_category_sql(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            "Food Category" AS food_category,
            ROUND(SUM("Total Waste (Tons)"), 0) AS total_waste_tons,
            ROUND(AVG("Avg Waste per Capita (Kg)"), 2) AS avg_waste_per_capita_kg
        FROM food_waste
        GROUP BY "Food Category"
        ORDER BY total_waste_tons DESC;
    """
    return pd.read_sql_query(query, conn)


def yearly_trend_sql(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            Year,
            ROUND(SUM("Total Waste (Tons)"), 0) AS total_waste_tons,
            ROUND(SUM("Economic Loss (Million $)"), 1) AS total_economic_loss_million
        FROM food_waste
        GROUP BY Year
        ORDER BY Year;
    """
    return pd.read_sql_query(query, conn)


def category_trend_sql(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            Year,
            "Food Category" AS food_category,
            SUM("Total Waste (Tons)") AS total_waste_tons
        FROM food_waste
        GROUP BY Year, "Food Category"
        ORDER BY Year, "Food Category";
    """
    return pd.read_sql_query(query, conn)


# ---------------------------------------------------------------------------
# 2. Correlation analysis
# ---------------------------------------------------------------------------

def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return df[NUMERIC_COLS].corr(numeric_only=True)


def plot_correlation_heatmap(corr: pd.DataFrame, outpath: str):
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1)
    plt.title("Correlation Matrix - Food Waste Metrics")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved correlation heatmap -> {outpath}")


# ---------------------------------------------------------------------------
# 3. Trend visualisations
# ---------------------------------------------------------------------------

def plot_yearly_trend(trend_df: pd.DataFrame, outpath: str):
    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax2 = ax1.twinx()

    ax1.plot(trend_df["Year"], trend_df["total_waste_tons"], color="tab:blue",
              marker="o", label="Total Waste (Tons)")
    ax2.plot(trend_df["Year"], trend_df["total_economic_loss_million"], color="tab:red",
              marker="s", linestyle="--", label="Economic Loss (Million $)")

    ax1.set_xlabel("Year")
    ax1.set_ylabel("Total Waste (Tons)", color="tab:blue")
    ax2.set_ylabel("Economic Loss (Million $)", color="tab:red")
    plt.title("Global Food Waste & Economic Loss Trend (2018-2024)")
    fig.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved yearly trend chart -> {outpath}")


def plot_category_trend(cat_trend_df: pd.DataFrame, outpath: str):
    pivot = cat_trend_df.pivot(index="Year", columns="food_category", values="total_waste_tons")
    pivot.plot(figsize=(10, 6), marker="o")
    plt.title("Waste by Food Category Over Time")
    plt.ylabel("Total Waste (Tons)")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved category trend chart -> {outpath}")


# ---------------------------------------------------------------------------
# 4. Outlier detection (IQR method) - flag unusually high waste per capita
# ---------------------------------------------------------------------------

def detect_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    country_avg = df.groupby("Country")[column].mean().reset_index()
    q1 = country_avg[column].quantile(0.25)
    q3 = country_avg[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    country_avg["is_outlier"] = (country_avg[column] < lower) | (country_avg[column] > upper)
    return country_avg.sort_values(column, ascending=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SQL + statistical analysis of global food wastage data")
    parser.add_argument("--csv", required=True, help="Path to the global food wastage CSV file")
    parser.add_argument("--outdir", default=".", help="Directory to save output charts")
    args = parser.parse_args()

    df = load_data(args.csv)
    conn = to_sql(df)

    print("\n=== Top 10 Waste-Generating Countries (via SQL) ===")
    top10 = top_10_countries_sql(conn)
    print(top10.to_string(index=False))

    print("\n=== Waste by Food Category (via SQL) ===")
    by_cat = waste_by_category_sql(conn)
    print(by_cat.to_string(index=False))

    print("\n=== Year-over-Year Trend (via SQL) ===")
    trend = yearly_trend_sql(conn)
    print(trend.to_string(index=False))
    plot_yearly_trend(trend, f"{args.outdir}/yearly_trend.png")

    cat_trend = category_trend_sql(conn)
    plot_category_trend(cat_trend, f"{args.outdir}/category_trend.png")

    print("\n=== Correlation Matrix ===")
    corr = correlation_matrix(df)
    print(corr.round(2).to_string())
    plot_correlation_heatmap(corr, f"{args.outdir}/correlation_heatmap.png")

    print("\n=== Outlier Countries (Avg Waste per Capita, IQR method) ===")
    outliers = detect_outliers_iqr(df, "Avg Waste per Capita (Kg)")
    print(outliers.to_string(index=False))
    flagged = outliers[outliers["is_outlier"]]
    if not flagged.empty:
        print(f"\nFlagged as statistical outliers: {', '.join(flagged['Country'])}")
    else:
        print("\nNo countries flagged as outliers at the 1.5*IQR threshold.")

    conn.close()
    print("\nDone. All charts saved to:", args.outdir)


if __name__ == "__main__":
    main()
