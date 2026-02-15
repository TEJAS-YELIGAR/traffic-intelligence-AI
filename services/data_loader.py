import pandas as pd

def load_data():
    df = pd.read_csv("data/US_Accidents.csv", nrows=200000)

    # Fill missing numerical values
    df['Visibility(mi)'] = df['Visibility(mi)'].fillna(df['Visibility(mi)'].median())
    df['Temperature(F)'] = df['Temperature(F)'].fillna(df['Temperature(F)'].median())
    df['Wind_Speed(mph)'] = df['Wind_Speed(mph)'].fillna(df['Wind_Speed(mph)'].median())

    # Fill categorical
    df['Weather_Condition'] = df['Weather_Condition'].fillna("Unknown")

    return df
