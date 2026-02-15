import requests

url = "http://127.0.0.1:5000/api/predict"

data = {
    "Weather_Condition": "Clear",
    "Visibility(mi)": 10,
    "Temperature(F)": 70,
    "Wind_Speed(mph)": 5,
    "Hour": 18,
    "Is_Weekend": 0,
    "Traffic_Density": 2,
    "Start_Lat": 34.05,
    "Start_Lng": -118.24
}

response = requests.post(url, json=data)

print(response.json())
