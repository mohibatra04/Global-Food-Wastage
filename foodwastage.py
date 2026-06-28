import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("global_food_wastage_dataset.csv")

print(df.shape)
print(df.isnull().sum())
df.dropna(inplace=True)
print(df.head())

country_waste = df.groupby("Country")["Total Waste (Tons)"].sum().sort_values(ascending=False).head(10)
print(country_waste)

plt.figure(figsize = (10,6))
plt.bar(country_waste.index, country_waste.values)
plt.title("Top 10 countries by food waste")
plt.ylabel("Total Waste (Tons)")
plt.xticks(rotation = 45)
plt.tight_layout()
plt.show()

category_waste = df.groupby("Food Category")["Total Waste (Tons)"].sum().sort_values(ascending=False)
print(category_waste)

plt.figure(figsize=(10,6))
plt.bar(category_waste.index, category_waste.values)
plt.title("Total Waste by Food Category")
plt.ylabel("Total Waste (Tons)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

avg_per_capita = df.groupby("Country")["Avg Waste per Capita (Kg)"].mean().sort_values(ascending=False).head(10)

plt.figure(figsize=(10,6))
plt.bar(avg_per_capita.index, avg_per_capita.values)
plt.title("Top 10 Countries by Avg Waste per Capita")
plt.ylabel("Avg Waste per Capita (Kg)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

year_waste = df.groupby("Year")["Total Waste (Tons)"].sum()

plt.figure(figsize=(10,6))
plt.plot(year_waste.index, year_waste.values, marker='o')
plt.title("Food Waste Trend Over Years")
plt.ylabel("Total Waste (Tons)")
plt.xlabel("Year")
plt.tight_layout()
plt.show()

print("\nCorrelation Matrix:")
print(df[["Total Waste (Tons)", "Economic Loss (Million $)", "Avg Waste per Capita (Kg)", "Household Waste (%)"]].corr())

plt.figure(figsize=(8,8))
plt.pie(category_waste.values, labels=category_waste.index, autopct='%1.1f%%')
plt.title("Food Waste Distribution by Category")
plt.tight_layout()
plt.savefig("top10_countries.png", dpi=150)
plt.show()

print("\nMost wasteful year:", year_waste.index[0])

eco_loss = df.groupby("Country")["Economic Loss (Million $)"].sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(10,6))
plt.bar(eco_loss.index, eco_loss.values, color='blue')
plt.title("Top 10 Countries by Economic Loss")
plt.ylabel("Economic Loss (Million $)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

print("\nKey Insight:")
print("Highest waste country:", country_waste.index[0])
print("Highest waste category:", category_waste.index[0])
print("Average waste per capita (kg):", round(df["Avg Waste per Capita (Kg)"].mean(), 2))

print(df.shape)
print(df[["Total Waste (Tons)", "Economic Loss (Million $)", "Avg Waste per Capita (Kg)", "Household Waste (%)"]].corr())
print("Most wasteful year:", year_waste.index[0])
print("Highest waste country:", country_waste.index[0])
print("Highest waste category:", category_waste.index[0])
print("Average waste per capita (kg):", round(df["Avg Waste per Capita (Kg)"].mean(), 2))