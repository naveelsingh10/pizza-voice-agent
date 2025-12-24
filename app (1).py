import streamlit as st
import main  # Your script
import threading
import os
import time
import queue
import json # Import json
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Mario's Pizza | AI Support", page_icon="🍕", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

if "data_queue" not in st.session_state:
    st.session_state.data_queue = queue.Queue()

if "tracker" not in st.session_state:
    st.session_state.tracker = {"id": "-", "status": "Ready for Session"}
if "running" not in st.session_state:
    st.session_state.running = False

PROGRESS_LOOKUP = {
    "Preparing": 25, "Ready for pickup": 50, "Out for delivery": 75, 
    "Delivered": 100, "Delayed": 40, "Cancelled": 0
}

# --- TOOL OVERRIDE (FIXED) ---

# 1. Capture the ORIGINAL function before we overwrite it to avoid recursion
ORIGINAL_GET_ORDER_STATUS = main.get_order_status

def bridged_get_order_status(params):
    # 2. Call the captured original function
    # It now returns a JSON STRING (because of the fix in main.py)
    result_str = ORIGINAL_GET_ORDER_STATUS(params)
    
    # 3. Parse the string back to a dict for the UI
    try:
        data = json.loads(result_str)
        st.session_state.data_queue.put(data)
    except:
        pass # Handle case where result isn't valid JSON
        
    # 4. Return the original STRING string to ElevenLabs
    return result_str

# 5. Apply the override
main.get_order_status = bridged_get_order_status


# --- HEADER ---
st.title("🍕 Mario's Pizza Intelligence")
st.markdown("---")

col_ctrl, col_viz = st.columns([1, 2], gap="large")

with col_ctrl:
    st.subheader("📡 Agent Control")
    
    if not st.session_state.running:
        st.info("The agent is currently offline.")
        if st.button("📞 GO LIVE", type="primary", use_container_width=True):
            ctx = get_script_run_ctx()
            t = threading.Thread(target=main.main, daemon=True)
            add_script_run_ctx(t, ctx) 
            st.session_state.running = True
            t.start()
            st.rerun()
    else:
        st.success("🎙️ AGENT IS LIVE")
        if st.button("🛑 STOP SESSION", type="secondary"):
            st.session_state.running = False
            os._exit(0) 

with col_viz:
    st.subheader("📦 Fulfillment Pipeline")
    
    try:
        while not st.session_state.data_queue.empty():
            new_data = st.session_state.data_queue.get_nowait()
            if "order_id" in new_data:
                st.session_state.tracker = {
                    "id": new_data.get("order_id", "Unknown"),
                    "status": new_data.get("status", "Unknown")
                }
    except queue.Empty:
        pass

    with st.container():
        track = st.session_state.tracker
        p_val = PROGRESS_LOOKUP.get(track["status"], 0)
        
        m1, m2 = st.columns(2)
        m1.metric("Current Inquiry", f"ID #{track['id']}")
        m2.metric("System Status", track["status"])
        st.progress(p_val / 100)

if st.session_state.running:
    time.sleep(1)
    st.rerun()
