import streamlit as st
import pandas as pd
import joblib

from datetime import date
from pathlib import Path


# --------------------------------------------------
# PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    ROOT
    / "models"
    / "best_model.pkl"
)

TRAIN_PATH = (
    ROOT
    / "data"
    / "processed"
    / "train.csv"
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Supply Chain Disruption Prediction",
    page_icon="📦",
    layout="wide"
)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title(
    "📦 Supply Chain Disruption Prediction"
)

st.write(
    "Predict whether a supply-chain record is likely "
    "to experience disruption."
)


# --------------------------------------------------
# CHECK MODEL
# --------------------------------------------------

if not MODEL_PATH.exists():

    st.error(
        "Best model not found."
    )

    st.info(
        "Run notebooks 01 to 08 first."
    )

    st.stop()


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

model = joblib.load(
    MODEL_PATH
)


# --------------------------------------------------
# LOAD TRAINING DATA
# --------------------------------------------------

if not TRAIN_PATH.exists():

    st.error(
        "Training dataset not found."
    )

    st.stop()


train_df = pd.read_csv(
    TRAIN_PATH
)


feature_names = [
    column
    for column in train_df.columns
    if column != "disruption"
]


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header(
    "Supply Chain Information"
)


user_input = {}

date_column = "date"

if date_column in feature_names:

    latest_training_date = pd.to_datetime(
        train_df[date_column],
        errors="coerce"
    ).max().date()

    selected_date = st.sidebar.date_input(
        "Shipment date",
        value=max(date.today(), latest_training_date),
        min_value=pd.to_datetime(
            train_df[date_column],
            errors="coerce"
        ).min().date()
    )

    user_input[date_column] = selected_date.isoformat()

    st.sidebar.caption(
        f"Training data available through {latest_training_date.isoformat()}"
    )


# --------------------------------------------------
# CREATE INPUT FIELDS
# --------------------------------------------------

for column in feature_names:

    if column not in train_df.columns:

        continue

    if column == date_column:

        continue

    series = train_df[column]

    # Numeric feature
    if pd.api.types.is_numeric_dtype(series):

        numeric_series = pd.to_numeric(
            series,
            errors="coerce"
        )

        median = numeric_series.median()

        minimum = numeric_series.min()

        maximum = numeric_series.max()

        if pd.isna(median):

            median = 0

        if pd.isna(minimum):

            minimum = 0

        if pd.isna(maximum):

            maximum = 1

        if minimum == maximum:

            user_input[column] = st.sidebar.number_input(
                column,
                value=float(median)
            )

        else:

            user_input[column] = st.sidebar.number_input(
                column,
                min_value=float(minimum),
                max_value=float(maximum),
                value=float(median)
            )

    # Categorical feature
    else:

        options = (
            series
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        options = sorted(
            options
        )

        if len(options) > 0:

            user_input[column] = (
                st.sidebar.selectbox(
                    column,
                    options
                )
            )

        else:

            user_input[column] = ""


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

if st.button(
    "Predict Disruption",
    type="primary"
):

    input_df = pd.DataFrame(
        [user_input]
    )

    prediction = int(
        model.predict(
            input_df
        )[0]
    )

    probability = float(
        model
        .predict_proba(
            input_df
        )[0][1]
    )


    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------

    st.subheader(
        "Prediction Result"
    )

    if prediction == 1:

        st.error(
            f"⚠️ SUPPLY CHAIN DISRUPTION\n\n"
            f"Disruption Probability: "
            f"{probability:.2%}"
        )

    else:

        st.success(
            f"✅ NO SUPPLY CHAIN DISRUPTION\n\n"
            f"Disruption Probability: "
            f"{probability:.2%}"
        )


    st.progress(
        probability
    )

    st.write(
        f"Model estimated disruption probability: "
        f"**{probability:.2%}**"
    )