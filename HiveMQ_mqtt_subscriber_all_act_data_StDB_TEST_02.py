import streamlit as st
import paho.mqtt.client as mqtt
import threading
import ssl
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# --- HiveMQ Cloud MQTT Configuration ---
MQTT_BROKER = "1e43f71fd82344509a7b999cbf2cde20.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "wintunlatt"
MQTT_PASSWORD = "Wintunlatt123"
MQTT_TOPIC = "Win/W1411/MachineStatus"

# --- Shared Variables ---
ph1_value = "Waiting..."
ph2_value = "Waiting..."
level_values = {}
current_values = {}
accel_values = {}
update_event = threading.Event()
iteration_count = 0
start_time = datetime.now()

# --- Chart history limit in minutes ---
HISTORY_LIMIT_MINUTES = 5

# --- Initialize historical storage ---
if "accel_history" not in st.session_state:
    st.session_state.accel_history = pd.DataFrame(columns=["Datetime", "Sensor", "Reg", "Value"])

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        print(f"📥 Subscribed to topic: {MQTT_TOPIC}")
    else:
        print("❌ Failed to connect, return code:", rc)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        global ph1_value, ph2_value, level_values, current_values, accel_values, iteration_count

        ph1_value = payload.get("ph_meter_1", "N/A")
        ph2_value = payload.get("ph_meter_2", "N/A")
        level_values = payload.get("level_sensors", {})
        current_values = payload.get("current_draw", {})
        accel_values = payload.get("accelerometers", {})

        iteration_count += 1
        print("\033[92m📄 File path:", os.path.abspath(__file__))
        print("Number of times:", iteration_count)
        print("Program run from:", start_time.strftime("%Y-%m-%d %H:%M:%S"), "and now:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\033[0m")

    except Exception as e:
        print(f"❌ Error parsing message: {e}")

    update_event.set()

# --- MQTT Thread ---
def mqtt_thread():
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

# --- Start MQTT Thread Once ---
if "mqtt_thread_started" not in st.session_state:
    threading.Thread(target=mqtt_thread, daemon=True).start()
    st.session_state.mqtt_thread_started = True



### --- Streamlit UI ---
##st.set_page_config(page_title="Digital I/O Dashboard", layout="wide")
##st.title("🏭 W1411 Workshop Real-Time Sensor Dashboard")
##
##
### --- Logo and Title ---
##col_logo, col_title = st.columns([1, 8])
##with col_title:
##    st.image("SP_logo.png", width=400)
####with col_title:
####    st.markdown("<h1 style='margin-bottom: 0;'>W1411 Workshop Sensor Dashboard</h1>", unsafe_allow_html=True)


# --- Streamlit UI ---
st.set_page_config(page_title="Digital I/O Dashboard", layout="wide")

# --- Logo on Top ---
st.image("SP_logo.png", width=200)

# --- Title ---
st.title("🏭 W1411 Workshop Real-Time Sensor Dashboard")



  

    
# --- Show File Path in UI ---
filepath = os.path.abspath(__file__)
st.markdown(f"<p style='font-size:10px;'>File path: {filepath}</p>", unsafe_allow_html=True)


### --- Custom CSS for Tab Font Size ---
### --- Custom CSS for Tab Font Size ---
##st.markdown("""
##    <style>
##        div[data-testid="stTabs"] > div > div > button {
##            font-size: 20px !important;
##            font-weight: bold !important;
##            color: #003366 !important;
##        }
##
##        div[data-testid="stTabs"] > div > div > button[aria-selected="true"] {
##            background-color: #cce6ff !important;
##            border-radius: 6px;
##        }
##    </style>
##""", unsafe_allow_html=True)


### Inject custom CSS to modify tab label text color and make it bold
##st.markdown("""
##    <style>
##    /* Target the text inside the tab buttons */
##    div[role="tablist"] button p {
##        font-size: 30px !important;  # Keeping the previous font size adjustment
##        font-weight: bold !important;  # Make the text bold
##        color: #0000FF !important;  # Change text color to blue (hex code for blue)
##    }
##    </style>
##""", unsafe_allow_html=True)


# Inject custom CSS to modify tab label font size, color, and weight
st.markdown("""
    <style>
    /* Target the text inside the tab buttons (inactive tabs) */
    div[role="tablist"] button p {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #0000FF !important;  /* Blue */
    }
    /* Target any nested span elements inside the tab buttons */
    div[role="tablist"] button p span {
        color: #0000FF !important;  /* Blue */
    }
    /* Target the button itself to ensure color applies */
    div[role="tablist"] button {
        color: #0000FF !important;  /* Blue */
    }
    /* Target active tab specifically */
    div[role="tablist"] button[aria-selected="true"] p {
        color: #0000FF !important;  /* Blue for active tab */
    }
    </style>
""", unsafe_allow_html=True)


# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["pH and Level Data", "Current Draw Plot", "Accelerometer Plot"])

# --- Initialize DataFrame for current draw history ---
if "current_draw_df" not in st.session_state:
    st.session_state.current_draw_df = pd.DataFrame(columns=["Datetime"] + [f"WS{i}" for i in range(1, 9)])

# --- Placeholders for Tab 1 ---
with tab1:
    st.subheader("pH Meters")
    col1, col2 = st.columns(2)
    ph1_placeholder = col1.empty()
    ph2_placeholder = col2.empty()

    st.subheader("🧪 Level Sensors")
    level_placeholders = {}
    level_cols = st.columns(4)
    for i in range(1, 9):
        key = f"LS{i}"
        level_placeholders[key] = level_cols[(i - 1) % 4].empty()

# --- Update Loop ---
chart_placeholder_current = tab2.empty()
chart_placeholder_accel = tab3.empty()
while True:
    if update_event.wait(timeout=1):
        now = datetime.now()

        with tab1:
            ph1_placeholder.metric("pH Meter 1", ph1_value)
            ph2_placeholder.metric("pH Meter 2", ph2_value)

            for key, placeholder in level_placeholders.items():
                value = level_values.get(key, "N/A")
                placeholder.metric(key, value)

        # --- Log Accelerometer Data ---
        for ip, registers in accel_values.items():
            for reg, val in registers.items():
                st.session_state.accel_history = pd.concat([
                    st.session_state.accel_history,
                    pd.DataFrame([[now, ip, reg, val]], columns=["Datetime", "Sensor", "Reg", "Value"])
                ], ignore_index=True)

        # --- Current Draw Plot ---
        ws_keys = sorted(current_values.keys())
        new_row = {"Datetime": now}
        for key in ws_keys:
            new_row[key] = current_values.get(key, 0)

        st.session_state.current_draw_df = pd.concat([
            st.session_state.current_draw_df,
            pd.DataFrame([new_row])
        ], ignore_index=True)

        threshold_time = now - timedelta(minutes=HISTORY_LIMIT_MINUTES)

        st.session_state.current_draw_df = st.session_state.current_draw_df[
            st.session_state.current_draw_df["Datetime"] >= threshold_time
        ]

        if not st.session_state.current_draw_df.empty:
            chart_df = st.session_state.current_draw_df.copy()
            chart_df["Time"] = chart_df["Datetime"].dt.strftime("%H:%M:%S")
            chart_df = chart_df.drop(columns="Datetime").set_index("Time")
            chart_placeholder_current.line_chart(chart_df, use_container_width=True)

        # --- Accelerometer Line Plot ---
        accel_plot_df = st.session_state.accel_history.copy()
        accel_plot_df = accel_plot_df[accel_plot_df["Datetime"] >= threshold_time]

        if not accel_plot_df.empty:
            pivot_df = accel_plot_df.copy()
            pivot_df["Time"] = pivot_df["Datetime"].dt.strftime("%H:%M:%S")
            pivot_df["Label"] = pivot_df["Sensor"].astype(str) + ":" + pivot_df["Reg"].astype(str)
            pivot_df = pivot_df.pivot(index="Time", columns="Label", values="Value")
            chart_placeholder_accel.line_chart(pivot_df, use_container_width=True)

        update_event.clear()
