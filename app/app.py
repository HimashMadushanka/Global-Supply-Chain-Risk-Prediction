import streamlit as st
import pandas as pd
import joblib
import folium

from datetime import date
from pathlib import Path
from geopy.distance import geodesic
from streamlit_folium import st_folium


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

CONNECTIVITY_PATH = (
    ROOT
    / "data"
    / "raw"
    / "route_connectivity_195_completed.csv"
)

PORT_LOCATIONS = {
    "Antwerp": {"country": "Belgium", "coordinates": (51.2194, 4.4025)},
    "Busan": {"country": "South Korea", "coordinates": (35.1796, 129.0756)},
    "Dubai": {"country": "United Arab Emirates", "coordinates": (25.2048, 55.2708)},
    "Hamburg": {"country": "Germany", "coordinates": (53.5511, 9.9937)},
    "Los Angeles": {"country": "United States", "coordinates": (33.7701, -118.1937)},
    "Marseille": {"country": "France", "coordinates": (43.2965, 5.3698)},
    "Rotterdam": {"country": "Netherlands", "coordinates": (51.9244, 4.4777)},
    "Shanghai": {"country": "China", "coordinates": (31.2304, 121.4737)},
    "Singapore": {"country": "Singapore", "coordinates": (1.3521, 103.8198)},
    "Sri Lanka": {"country": "Sri Lanka", "coordinates": (6.9271, 79.8612)},
    "India": {"country": "India", "coordinates": (19.0760, 72.8777)},
}


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
    "to experience disruption with physical route feasibility validation."
)


# --------------------------------------------------
# LOAD CONNECTIVITY DATA
# --------------------------------------------------

@st.cache_data
def load_connectivity_data():
    if CONNECTIVITY_PATH.exists():
        return pd.read_csv(CONNECTIVITY_PATH)
    return None

connectivity_df = load_connectivity_data()


def get_route_connectivity(origin_port, destination_port, df_conn):
    """
    Evaluates physical connectivity between origin and destination.
    Returns:
      is_same_location (bool)
      mode_status (dict of mode: bool)
      allowed_modes (list of str)
    """
    all_modes = ["Air", "Rail", "Road", "Sea"]
    default_status = {"Sea": True, "Air": True, "Road": True, "Rail": True}

    if not origin_port or not destination_port:
        return False, default_status, all_modes

    if origin_port.strip().lower() == destination_port.strip().lower():
        return True, {m: False for m in all_modes}, []

    orig_country = PORT_LOCATIONS.get(origin_port, {}).get("country", origin_port).strip()
    dest_country = PORT_LOCATIONS.get(destination_port, {}).get("country", destination_port).strip()

    # Domestic shipment within the same country
    if orig_country.lower() == dest_country.lower():
        return False, default_status, all_modes

    if df_conn is not None:
        match = df_conn[
            (df_conn["origin"].str.strip().str.lower() == orig_country.lower()) &
            (df_conn["destination"].str.strip().str.lower() == dest_country.lower())
        ]
        if not match.empty:
            row = match.iloc[0]
            status = {
                "Sea": bool(row.get("sea", 0) == 1),
                "Air": bool(row.get("air", 0) == 1),
                "Road": bool(row.get("road", 0) == 1),
                "Rail": bool(row.get("railway", 0) == 1),
            }
            allowed = [m for m in all_modes if status.get(m, False)]
            if not allowed:
                allowed = ["Air"]
            return False, status, allowed

    return False, default_status, all_modes


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
# ROUTE SELECTION (ORIGIN & DESTINATION)
# --------------------------------------------------

all_port_options = sorted(
    set(train_df["origin_port"].dropna().astype(str).unique())
    | set(train_df["destination_port"].dropna().astype(str).unique())
    | set(PORT_LOCATIONS)
)

default_origin_index = (
    all_port_options.index("Sri Lanka")
    if "Sri Lanka" in all_port_options
    else 0
)

origin_port = st.sidebar.selectbox(
    "origin_port",
    options=all_port_options,
    index=default_origin_index,
    key="origin_port_select"
)
user_input["origin_port"] = origin_port

default_dest_index = (
    all_port_options.index("India")
    if "India" in all_port_options
    else min(1, len(all_port_options) - 1)
)

destination_port = st.sidebar.selectbox(
    "destination_port",
    options=all_port_options,
    index=default_dest_index,
    key="destination_port_select"
)
user_input["destination_port"] = destination_port


# --------------------------------------------------
# ROUTE CONNECTIVITY VALIDATION & TRANSPORT MODE
# --------------------------------------------------

is_same_location, mode_status, allowed_modes = get_route_connectivity(
    origin_port,
    destination_port,
    connectivity_df
)

if is_same_location:
    st.sidebar.error("⚠️ Origin and Destination cannot be the same location.")
    user_input["transport_mode"] = ""
else:
    # Ensure active session state for transport mode is valid
    if "transport_mode_select" in st.session_state and st.session_state["transport_mode_select"] not in allowed_modes:
        st.session_state["transport_mode_select"] = allowed_modes[0]

    selected_mode = st.sidebar.selectbox(
        "transport_mode",
        options=allowed_modes,
        key="transport_mode_select"
    )
    user_input["transport_mode"] = selected_mode

    unavailable_modes = [
        m for m in ["Road", "Rail", "Sea", "Air"]
        if not mode_status.get(m, False)
    ]
    if unavailable_modes:
        st.sidebar.caption(
            f"🚫 **{', '.join(unavailable_modes)}** unavailable for this route "
            f"(no direct overland / physical connection)."
        )


# --------------------------------------------------
# REMAINING INPUT FIELDS
# --------------------------------------------------

# Pre-calculate estimated map distance if locations are known
estimated_distance = None
if origin_port in PORT_LOCATIONS and destination_port in PORT_LOCATIONS and not is_same_location:
    estimated_distance = geodesic(
        PORT_LOCATIONS[origin_port]["coordinates"],
        PORT_LOCATIONS[destination_port]["coordinates"]
    ).km

for column in feature_names:

    if column in {date_column, "origin_port", "destination_port", "transport_mode"}:
        continue

    if column not in train_df.columns:
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

        # Use estimated distance as sensible default for distance_km if available
        if column == "distance_km" and estimated_distance is not None:
            default_val = float(min(max(estimated_distance, minimum), maximum))
        else:
            default_val = float(median)

        if minimum == maximum:
            user_input[column] = st.sidebar.number_input(
                column,
                value=default_val
            )
        else:
            user_input[column] = st.sidebar.number_input(
                column,
                min_value=float(minimum),
                max_value=float(maximum),
                value=default_val
            )

        if column == "distance_km" and estimated_distance is not None:
            st.sidebar.caption(
                f"📍 Geodesic distance: ~{estimated_distance:,.0f} km"
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
        options = sorted(options)

        if len(options) > 0:
            user_input[column] = st.sidebar.selectbox(
                column,
                options
            )
        else:
            user_input[column] = ""


# --------------------------------------------------
# ROUTE MAP & FEASIBILITY OVERVIEW
# --------------------------------------------------

if origin_port in PORT_LOCATIONS and destination_port in PORT_LOCATIONS and not is_same_location:

    origin = PORT_LOCATIONS[origin_port]
    destination = PORT_LOCATIONS[destination_port]
    origin_coordinates = origin["coordinates"]
    destination_coordinates = destination["coordinates"]
    route_distance = geodesic(
        origin_coordinates,
        destination_coordinates
    ).km

    st.subheader("Shipment Route & Feasibility")

    route_columns = st.columns(4)
    route_columns[0].metric(
        "Origin",
        f"{origin_port}, {origin['country']}"
    )
    route_columns[1].metric(
        "Destination",
        f"{destination_port}, {destination['country']}"
    )
    route_columns[2].metric(
        "Selected Mode",
        user_input.get("transport_mode", "N/A")
    )
    route_columns[3].metric(
        "Map distance",
        f"{route_distance:,.0f} km"
    )

    # Transport Feasibility Cards
    st.markdown("##### 🌐 Physical Route Feasibility")
    feasibility_cols = st.columns(4)
    mode_labels = {
        "Sea": ("🚢 Sea Freight", "Maritime route accessible"),
        "Air": ("✈️ Air Cargo", "Direct/connecting flights feasible"),
        "Road": ("🚚 Road Transit", "Continuous overland road link"),
        "Rail": ("🚆 Rail Freight", "Interconnected railway network")
    }

    for col, (mode, (title, desc)) in zip(feasibility_cols, mode_labels.items()):
        is_feasible = mode_status.get(mode, False)
        is_current = (user_input.get("transport_mode") == mode)

        with col:
            if is_feasible:
                status_text = "✅ Feasible"
                if is_current:
                    st.success(f"**{title}**\n\n{status_text} *(Active)*")
                else:
                    st.info(f"**{title}**\n\n{status_text}")
            else:
                status_text = "❌ Not Feasible"
                st.warning(f"**{title}**\n\n{status_text}\n\n*(No land border/bridge)*")

    route_map = folium.Map(
        location=(
            (origin_coordinates[0] + destination_coordinates[0]) / 2,
            (origin_coordinates[1] + destination_coordinates[1]) / 2
        ),
        zoom_start=3,
        tiles="CartoDB positron"
    )

    folium.Marker(
        origin_coordinates,
        tooltip=f"Origin: {origin_port}, {origin['country']}",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(route_map)

    folium.Marker(
        destination_coordinates,
        tooltip=f"Destination: {destination_port}, {destination['country']}",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(route_map)

    folium.PolyLine(
        [origin_coordinates, destination_coordinates],
        color="#136f63",
        weight=4,
        tooltip=f"{user_input.get('transport_mode', 'Shipment')} route ({route_distance:,.0f} km)"
    ).add_to(route_map)

    st_folium(
        route_map,
        use_container_width=True,
        height=420,
        returned_objects=[]
    )

    st.caption(
        "Map distance represents great-circle geographic distance. "
        "Physical connectivity reflects whether cross-border land (road/rail) "
        "or maritime access exists between the two locations."
    )

elif is_same_location:
    st.warning("⚠️ Origin and Destination locations are identical. Please choose different endpoints.")


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

can_predict = True
prediction_block_reason = ""

if is_same_location:
    can_predict = False
    prediction_block_reason = "Origin and destination cannot be identical."
elif user_input.get("transport_mode") not in allowed_modes:
    can_predict = False
    prediction_block_reason = (
        f"Selected transport mode '{user_input.get('transport_mode')}' is physically "
        f"impossible between {origin_port} and {destination_port}."
    )

if not can_predict:
    st.error(f"⚠️ Cannot predict disruption: {prediction_block_reason}")

if st.button(
    "Predict Disruption",
    type="primary",
    disabled=not can_predict
):

    # Reorder input DataFrame to match model training features
    input_df = pd.DataFrame([user_input])
    input_df = input_df[feature_names]

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

    no_disruption_probability = 1 - probability


    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------

    st.subheader(
        "Prediction Result"
    )

    result_columns = st.columns(2)
    result_columns[0].metric(
        "Predicted class",
        "Disruption" if prediction == 1 else "No disruption"
    )
    result_columns[1].metric(
        "Predicted outcome probability",
        f"{probability if prediction == 1 else no_disruption_probability:.2%}"
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
            f"No-disruption Probability: "
            f"{no_disruption_probability:.2%}"
        )


    st.progress(
        probability if prediction == 1 else no_disruption_probability
    )

    st.write(
        f"Disruption probability: **{probability:.2%}**"
    )

    st.write(
        f"No-disruption probability: **{no_disruption_probability:.2%}**"
    )