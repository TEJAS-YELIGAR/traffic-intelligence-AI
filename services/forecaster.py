from prophet import Prophet
import pandas as pd

def forecast_accidents(df):

    daily = df.groupby(df['Start_Time'].dt.date).size().reset_index()
    daily.columns = ['ds', 'y']

    model = Prophet()
    model.fit(daily)

    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)

    return forecast[['ds', 'yhat']]
