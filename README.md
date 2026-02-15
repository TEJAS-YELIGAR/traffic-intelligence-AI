# Urban Traffic Intelligence Platform 🚦

**Real-Time Accident Risk Prediction & Forecasting**

---

## Overview

The **Urban Traffic Intelligence Platform** is a smart AI-driven web application designed to predict and visualize traffic accident risk in real-time. It combines machine learning, geospatial mapping, and interactive visualizations to help users understand traffic risk patterns and make informed decisions.

---

## Features

### Core Features
- **Accident Risk Prediction**: Uses a trained Random Forest model to predict accident probability based on weather, traffic, and location.
- **Interactive Map**: Clickable map with dynamic markers to visualize accident risk.
- **24-Hour Forecast**: Time-series forecast chart to show risk trends throughout the day.
- **Needle-style Risk Gauge**: Professional gauge indicating current risk probability.

### Advanced Enhancements
- **Live Dynamic Risk Colors**: Map areas change color dynamically based on real-time risk.
- **Auto Heatmap Layer**: Automatically displays high-risk zones with heat intensity.
- **Chatbot Integration**:
  - Conversational AI interface for predicting accident risk.
  - Accepts natural language inputs like weather, traffic density, and time.
  - Provides explanations, forecasts, and key influencing factors.
- **ML-based Time-Series Forecast**: Predicts accident risk trends for the next 24 hours.
- **Context-Aware UI Updates**: Gauge, map, and heatmap update automatically when predictions are made via chatbot.

---

## Technology Stack

- **Backend**: Python, Flask, scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript, Leaflet.js, Chart.js
- **Machine Learning**: Random Forest Classifier with preprocessed features
- **Deployment**: Local Flask server (can be extended to cloud deployment)
- **Optional Enhancements**:
  - Chatbot NLP: Regex-based entity extraction & intent detection
  - Live API integration for weather & traffic

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/urban-traffic-intelligence.git
   cd urban-traffic-intelligence
   Create a virtual environment:
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   Install dependencies:
   pip install -r requirements.txt
   Run the application:
   python app.py
   Open your browser and go to:
   http://127.0.0.1:5000


---
## Usage

Click on the Interactive Risk Map to get a prediction at a location.

Use the Chatbot in the bottom-right corner to provide inputs like:

"Weather is rainy, wind speed 15, heavy traffic at 7 PM"

The Gauge, Map, and Forecast Chart update automatically.

Toggle Heatmap Layer to view high-risk zones dynamically.

---

