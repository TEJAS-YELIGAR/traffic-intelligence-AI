import pandas as pd
import joblib
import numpy as np
import time

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

print("Loading dataset...")

df = pd.read_csv("data/US_Accidents.csv", nrows=150000)

print("Dataset Loaded.")

# ---------------------------
# FEATURE ENGINEERING
# ---------------------------

df['Start_Time'] = pd.to_datetime(df['Start_Time'])

df['Hour'] = df['Start_Time'].dt.hour
df['DayOfWeek'] = df['Start_Time'].dt.dayofweek
df['Is_Weekend'] = df['DayOfWeek'].apply(lambda x: 1 if x >= 5 else 0)

df['Traffic_Density'] = np.random.randint(1, 4, size=len(df))

# Select Features
df = df[['Severity',
         'Weather_Condition',
         'Visibility(mi)',
         'Temperature(F)',
         'Wind_Speed(mph)',
         'Hour',
         'Is_Weekend',
         'Traffic_Density']]

df.dropna(inplace=True)

X = df.drop("Severity", axis=1)
y = df["Severity"]

categorical_cols = ['Weather_Condition']
numerical_cols = ['Visibility(mi)',
                  'Temperature(F)',
                  'Wind_Speed(mph)',
                  'Hour',
                  'Is_Weekend',
                  'Traffic_Density']

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
    ],
    remainder='passthrough'
)

rf_model = RandomForestClassifier(random_state=42)

pipeline = Pipeline(steps=[
    ('preprocessing', preprocessor),
    ('classifier', rf_model)
])

param_grid = {
    'classifier__n_estimators': [100],
    'classifier__max_depth': [15]
}

grid = GridSearchCV(pipeline, param_grid, cv=3, n_jobs=-1)

print("Training Advanced Model...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

grid.fit(X_train, y_train)

best_model = grid.best_estimator_

y_pred = best_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("Advanced Model Accuracy:", round(accuracy * 100, 2), "%")

joblib.dump(best_model, "models/best_model.pkl")

print("Model Saved Successfully.")
