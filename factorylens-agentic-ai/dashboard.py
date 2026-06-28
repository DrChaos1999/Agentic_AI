from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="FactoryLens AI", layout="wide")
st.title("FactoryLens AI")
st.caption("Visual defect classification, similar-case retrieval, risk scoring and human-approved work orders")

with st.sidebar:
    st.subheader("Connection")
    api_url = st.text_input("API URL", API_URL)
    try:
        health = requests.get(f"{api_url}/health", timeout=5).json()
        st.success("API connected")
        st.json(health)
    except Exception as exc:
        st.error(f"API unavailable: {exc}")

uploaded = st.file_uploader("Upload a component image", type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"])
col1, col2 = st.columns(2)
with col1:
    machine_id = st.text_input("Machine ID", "MOTOR-04")
    criticality = st.selectbox("Machine criticality", ["low", "medium", "high", "critical"], index=2)
with col2:
    symptoms = st.text_area("Observed symptoms", "overheating and unusual vibration")
    approve = st.checkbox("Human approval: create a work order")
    approved_by = st.text_input("Approved by", "Dibya Joy Paul")

if uploaded and st.button("Analyze defect", type="primary"):
    files = {"image": (uploaded.name, uploaded.getvalue(), uploaded.type)}
    data = {
        "machine_id": machine_id,
        "criticality": criticality,
        "symptoms": symptoms,
        "top_k": 5,
        "approve_work_order": str(approve).lower(),
        "approved_by": approved_by,
    }
    try:
        response = requests.post(f"{api_url}/analyze", files=files, data=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        st.image(uploaded, caption="Uploaded component", width=400)
        a, b, c = st.columns(3)
        a.metric("Prediction", result["prediction"]["predicted_class"])
        b.metric("Confidence", f"{result['prediction']['confidence']:.1%}")
        c.metric("Risk", f"{result['risk']['level']} ({result['risk']['score']}/100)")
        if "demo-untrained" in result["prediction"]["model_status"]:
            st.warning("Demo mode is active. Train the transfer-learning model before treating predictions as meaningful.")
        st.subheader("Agent narrative")
        st.write(result["narrative"])
        st.subheader("Recommended actions")
        for action in result["recommended_actions"]:
            st.write(f"- {action}")
        st.subheader("Similar incidents")
        if result["similar_incidents"]:
            st.dataframe(pd.DataFrame(result["similar_incidents"]), use_container_width=True)
        else:
            st.info("The FAISS image index is empty. Build it with the provided script.")
        st.subheader("Maintenance manual evidence")
        for item in result["manual_evidence"]:
            with st.expander(f"{item['heading']} — score {item['score']:.3f}"):
                st.write(item["text"])
        if result.get("work_order"):
            st.success(f"Work order created: {result['work_order']['id']}")
        with st.expander("Raw response"):
            st.json(result)
    except requests.HTTPError as exc:
        st.error(exc.response.text)
    except Exception as exc:
        st.error(str(exc))

st.divider()
st.subheader("Recent incidents")
try:
    incidents = requests.get(f"{api_url}/incidents", timeout=10).json()
    if incidents:
        st.dataframe(pd.DataFrame(incidents), use_container_width=True)
except Exception:
    pass
