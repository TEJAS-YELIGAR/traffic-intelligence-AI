import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_dashboard(df):

    os.makedirs("static", exist_ok=True)

    # Accidents by Hour
    plt.figure(figsize=(8,5))
    sns.countplot(x="Hour", data=df)
    plt.title("Accidents by Hour")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/accidents_by_hour.png")
    plt.close()

    # Severity Distribution
    plt.figure(figsize=(6,4))
    sns.countplot(x="Severity", data=df)
    plt.title("Severity Distribution")
    plt.tight_layout()
    plt.savefig("static/severity_distribution.png")
    plt.close()

    # Weather Distribution
    top_weather = df["Weather_Condition"].value_counts().head(10)
    plt.figure(figsize=(8,5))
    top_weather.plot(kind="bar")
    plt.title("Top Weather Conditions")
    plt.tight_layout()
    plt.savefig("static/weather_distribution.png")
    plt.close()
