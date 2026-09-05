# Global Supply Chain Risk & Logistics

A machine-learning decision-support application for estimating shipment disruption risk and checking whether a transport mode is physically feasible for a selected trade corridor.

The project combines data preparation, exploratory analysis, feature engineering, model comparison, final evaluation, and two user interfaces:

- A Flask web dashboard for route prediction and analytics.
- A Streamlit application for an interactive prediction workflow.

> This project is a prototype for planning and analysis. Predictions should be validated with current operational data before being used for real business decisions.

## Features

- Predict shipment disruption probability from route, shipment, weather, carrier, fuel, geopolitical, and lead-time features.
- Validate route connectivity for Sea, Air, Road, and Rail transport modes.
- Calculate approximate great-circle distance between supported ports.
- Display risk classification, disruption probability, confidence, expected delay range, and recommendations.
- Explore shipment analytics including disruption rates, weather impact, transport-mode comparison, monthly trends, and feature importance.
- Support numeric input values entered manually in both interfaces.
- Preserve the complete analysis workflow in numbered Jupyter notebooks.

## Project Structure

```text
.
|-- app/
|   `-- app.py                         # Streamlit application
|-- data/
|   |-- raw/                           # Original datasets
|   |-- interim/                       # Cleaned and feature-engineered data
|   `-- processed/                     # Train, validation, and test data
|-- flask_app/
|   |-- app.py                         # Flask application and API routes
|   |-- static/                        # CSS and JavaScript
|   `-- templates/                     # Dashboard HTML templates
|-- models/
|   |-- best_model.pkl
|   |-- preprocessor.pkl
|   |-- random_forest_model.pkl
|   `-- xgboost_model.pkl
|-- notebooks/
|   |-- 01_data_understanding.ipynb
|   |-- 02_data_cleaning.ipynb
|   |-- 03_eda.ipynb
|   |-- 04_feature_engineering.ipynb
|   |-- 05_preprocessing_split.ipynb
|   |-- 06_train_compare_two_models.ipynb
|   |-- 07_retrain_best_model.ipynb
|   `-- 08_final_evaluation.ipynb
|-- reports/
|   |-- final_metrics.csv
|   |-- model_comparison.csv
|   `-- figures/
|-- screenshots/
|-- requirements.txt
|-- run_flask.py
`-- README.md
```

Authentication files:

- `flask_app/schema.sql` - SQLite tables for users and password-reset tokens.
- `flask_app/schema_mysql.sql` - MySQL tables for users and password-reset tokens.
- `flask_app/auth_db.py` - password hashing, login verification, and token management.
- `data/users.sqlite3` - created automatically on first Flask start.

## Technology Stack

- Python
- Flask
- Streamlit
- Pandas and NumPy
- Scikit-learn
- XGBoost
- Joblib
- Matplotlib and Seaborn
- GeoPy
- Folium and Streamlit-Folium
- Chart.js and Leaflet for the Flask dashboard frontend

## Requirements

- Python 3.10 or newer recommended
- Internet access on the first dashboard load for CDN assets used by the Flask frontend
- A virtual environment is recommended

## Installation on Windows

Open PowerShell in the project directory:

```powershell
cd "D:\My_Project\Analyse\capston Project_2-Global Supply Chain Risk & Logistics"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run the following once in a PowerShell window opened with the appropriate user permissions, then activate the environment again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Run the Flask Dashboard

```powershell
cd "D:\My_Project\Analyse\capston Project_2-Global Supply Chain Risk & Logistics"
.\.venv\Scripts\Activate.ps1
python run_flask.py
```

Open the dashboard at:

```text
http://127.0.0.1:5000
```

### Login

The Flask dashboard requires login. For local development, the default credentials are:

```text
Username: admin
Password: change-me
```

Set your own credentials before sharing or deploying the application:

```powershell
$env:FLASK_SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_USERNAME = "your-admin-name"
$env:ADMIN_PASSWORD = "your-strong-password"
python run_flask.py
```

### Use MySQL for Authentication

Install the dependencies and configure the MySQL connection before starting Flask:

```powershell
python -m pip install -r requirements.txt

$env:AUTH_DB_DRIVER = "mysql"
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "your-mysql-password"
$env:MYSQL_DATABASE = "routexa_auth"

$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD = "your-initial-password"
$env:FLASK_SECRET_KEY = "replace-with-a-long-random-secret"

python run_flask.py
```

The application creates the `routexa_auth` database and its tables automatically if the MySQL user has permission to create databases. You can also create it manually:

```sql
CREATE DATABASE routexa_auth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

The MySQL database stores users in `users` and reset tokens in `password_reset_tokens`. When switching from SQLite to MySQL, the initial admin account is created from `ADMIN_USERNAME` and `ADMIN_PASSWORD`; existing accounts are not overwritten.

Dashboard pages and `/api/*` endpoints require an authenticated session. Use the **Sign out** link in the navigation bar to end the session. Never use the development defaults in production.

### Password Management

- **Change password:** sign in and select **Change password** in the dashboard navigation.
- **Forgot password:** select **Forgot password?** on the login page, enter the username, and open the generated reset link.
- Reset tokens are single-use and expire after 30 minutes.
- In this local implementation, the reset link is displayed on the recovery page. A production deployment should send it through a trusted email provider instead.

The SQLite database is initialized automatically. To use a different database location, set:

```powershell
$env:AUTH_DATABASE_PATH = "D:\secure-data\routexa-users.sqlite3"
python run_flask.py
```

Available pages:

- `/` - route predictor
- `/analytics` - analytics dashboard

Stop the server with `Ctrl+C`.

### Flask API Endpoints

#### Get route information

```text
GET /api/route-info?origin=Sri%20Lanka&destination=India
```

Returns route feasibility, supported transport modes, port coordinates, and approximate distance.

#### Get analytics data

```text
GET /api/analytics-data
```

Returns the KPI and chart data used by the analytics page.

#### Predict disruption risk

```text
POST /api/predict
Content-Type: application/json
```

Example request:

```json
{
  "origin_port": "Sri Lanka",
  "destination_port": "India",
  "transport_mode": "Sea",
  "date": "2026-09-05",
  "product_category": "Automotive",
  "distance_km": 1530,
  "weight_mt": 50,
  "fuel_price_index": 3.0,
  "geopolitical_risk_score": 4.0,
  "weather_condition": "Rain",
  "carrier_reliability_score": 0.85,
  "lead_time_days": 10,
  "use_live_data": true
}
```

The response includes disruption probability, risk level, expected delay range, risk factors, recommendations, and shipment telemetry.

## Live Data Integrations

The Flask dashboard can collect a fresh route context when a prediction is made or when the **Refresh & Apply Live Signals** button is used.

### Providers

- **Weather:** Open-Meteo, enabled by default without an API key.
- **Geopolitical attention:** GDELT recent news volume for the selected route, enabled by default as a transparent news-attention proxy.
- **Road traffic:** TomTom Traffic Flow API when `TOMTOM_API_KEY` is configured.
- **Port congestion:** A provider endpoint configured through `PORT_CONGESTION_API_URL`.

Live weather and geopolitical attention are applied to model inputs when available. Traffic and port congestion are returned as operational context because the current trained model was not trained with those features.

### Configure optional providers in PowerShell

```powershell
$env:TOMTOM_API_KEY = "your-tomtom-key"
$env:PORT_CONGESTION_API_URL = "https://your-provider.example/api/congestion"
$env:LIVE_DATA_TIMEOUT_SECONDS = "4"
$env:LIVE_DATA_CACHE_TTL_SECONDS = "300"
python run_flask.py
```

Live context endpoint:

```text
GET /api/live-context?origin=Sri%20Lanka&destination=India
```

Each provider result includes availability, source, timestamp, and an error when data cannot be retrieved. The application continues using form or training-data defaults when a provider is unavailable.

The configured port-congestion endpoint should accept `?port=<port name>` and return JSON such as:

```json
{
  "status": "moderate",
  "congestion_score": 0.62,
  "vessel_wait_hours": 18
}
```

## Run the Streamlit Application

```powershell
cd "D:\My_Project\Analyse\capston Project_2-Global Supply Chain Risk & Logistics"
.\.venv\Scripts\Activate.ps1
python -m streamlit run app\app.py
```

Streamlit normally opens at:

```text
http://localhost:8501
```

## Data and Features

The model uses shipment-level information such as:

- Shipment date
- Origin and destination port
- Transport mode
- Product category
- Distance in kilometres
- Cargo weight in metric tonnes
- Fuel price index
- Geopolitical risk score
- Weather condition
- Carrier reliability score
- Lead time in days

The target variable is shipment disruption, represented as a binary value where `1` indicates disruption and `0` indicates no disruption.

The route connectivity file contains country-pair availability indicators for Sea, Air, Road, and Rail transport.

## Analysis Workflow

Run the notebooks in order:

1. `01_data_understanding.ipynb` - inspect the raw data and identify data quality issues.
2. `02_data_cleaning.ipynb` - clean and standardize the input data.
3. `03_eda.ipynb` - explore distributions, relationships, and disruption patterns.
4. `04_feature_engineering.ipynb` - create model-ready features.
5. `05_preprocessing_split.ipynb` - preprocess data and create train, validation, and test sets.
6. `06_train_compare_two_models.ipynb` - compare Random Forest and XGBoost.
7. `07_retrain_best_model.ipynb` - retrain the selected model and save artifacts.
8. `08_final_evaluation.ipynb` - evaluate the final model and generate figures.

## Reported Evaluation Results

The committed report files currently contain the following results.

### Final metrics

| Metric | Value |
|---|---:|
| Accuracy | 0.7210 |
| Precision | 0.7752 |
| Recall | 0.7663 |
| F1 score | 0.7707 |
| ROC-AUC | 0.8124 |

### Model comparison

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| XGBoost | 0.7160 | 0.7675 | 0.7700 | 0.7687 | 0.8024 |
| Random Forest | 0.7270 | 0.8257 | 0.7031 | 0.7595 | 0.8146 |

These values should be updated whenever the model or data split changes. The dashboard currently displays a `99.4% ROC-AUC` label in some places, which does not match the committed report metrics and should be corrected before formal presentation.

## Important Limitations

- The model is trained on historical data and may not represent current port congestion, weather, conflicts, strikes, customs delays, or carrier capacity.
- Manually entering values far outside the training distribution can produce unreliable predictions even though the interface accepts them.
- Route connectivity is based on the supplied route dataset and should be verified against current logistics networks.
- Geodesic distance is an approximation and is not the same as actual sailing, road, rail, or air distance.
- Live providers can be unavailable, rate-limited, delayed, or incomplete; always inspect the provider status and timestamp.
- The application does not currently provide user authentication, role-based access, or production monitoring.
- The Flask runner currently enables debug mode for local development. Disable debug mode for deployment.

## Recommended Next Steps

1. Reconcile all displayed metrics with `reports/final_metrics.csv` and `reports/model_comparison.csv`.
2. Confirm that the train/test split and feature engineering do not introduce data leakage.
3. Add automated tests for prediction, invalid routes, missing files, and numeric validation.
4. Add input warnings for values outside the training-data range.
5. Add live weather, port congestion, geopolitical, and traffic values as trained model features after collecting labeled historical data.
6. Add model monitoring, periodic retraining, authentication, and production logging.

## License

No license has been specified yet. Add a license before distributing this project publicly or using it as a commercial product.
