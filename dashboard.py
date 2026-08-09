"""
Global Food Wastage - Interactive Streamlit Dashboard
-------------------------------------------------------
Run with:
    streamlit run dashboard.py -- --csv global_food_wastage_data.csv

Lets a user filter by year range, country, and food category, and view:
  - Top waste-generating countries (bar)
  - Waste share by food category (pie)
  - Year-over-year trend (line)
  - Correlation heatmap between waste, economic loss, and population
"""

import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Global Food Wastage Dashboard", layout="wide")


@st.cache_data
def load_data(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def get_csv_path() -> str:
    # Allows: streamlit run dashboard.py -- --csv path.csv
    if "--csv" in sys.argv:
        idx = sys.argv.index("--csv")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return "global_food_wastage_dataset.csv"


def main():
    st.title("🌍 Global Food Wastage Dashboard (2018-2024)")
    st.caption("Interactive exploration of food waste, economic loss, and per-capita trends across 20 countries.")

    df = load_data(get_csv_path())

    # ---------------- Sidebar filters ----------------
    st.sidebar.header("Filters")

    year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
    year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

    countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect("Countries", countries, default=countries)

    categories = sorted(df["Food Category"].unique())
    selected_categories = st.sidebar.multiselect("Food categories", categories, default=categories)

    filtered = df[
        (df["Year"].between(year_range[0], year_range[1]))
        & (df["Country"].isin(selected_countries))
        & (df["Food Category"].isin(selected_categories))
    ]

    if filtered.empty:
        st.warning("No data matches the selected filters.")
        return

    # ---------------- KPI row ----------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Waste (Tons)", f"{filtered['Total Waste (Tons)'].sum():,.0f}")
    col2.metric("Total Economic Loss ($M)", f"{filtered['Economic Loss (Million $)'].sum():,.1f}")
    col3.metric("Avg Waste per Capita (Kg)", f"{filtered['Avg Waste per Capita (Kg)'].mean():,.1f}")

    st.divider()

    # ---------------- Top countries + category pie ----------------
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Top 10 Waste-Generating Countries")
        top10 = (
            filtered.groupby("Country")["Total Waste (Tons)"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(x=top10.values, y=top10.index, ax=ax, palette="Blues_r")
        ax.set_xlabel("Total Waste (Tons)")
        st.pyplot(fig)

    with c2:
        st.subheader("Waste Share by Food Category")
        by_cat = filtered.groupby("Food Category")["Total Waste (Tons)"].sum()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(by_cat.values, labels=by_cat.index, autopct="%1.0f%%", textprops={"fontsize": 8})
        ax.axis("equal")
        st.pyplot(fig)

    st.divider()

    # ---------------- Trend line ----------------
    st.subheader("Waste & Economic Loss Trend Over Time")
    trend = filtered.groupby("Year")[["Total Waste (Tons)", "Economic Loss (Million $)"]].sum()
    st.line_chart(trend)

    st.divider()

    # ---------------- Correlation heatmap ----------------
    st.subheader("Correlation Between Key Metrics")
    numeric_cols = [
        "Total Waste (Tons)",
        "Economic Loss (Million $)",
        "Avg Waste per Capita (Kg)",
        "Population (Million)",
        "Household Waste (%)",
    ]
    numeric_cols = [c for c in numeric_cols if c in filtered.columns]
    corr = filtered[numeric_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    st.pyplot(fig)

    st.divider()
    st.subheader("Filtered Data")
    st.dataframe(filtered, use_container_width=True)


if __name__ == "__main__":
    main()
