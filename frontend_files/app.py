from pathlib import Path
import json
import os
import pandas as pd
import requests
import streamlit as st

schema = json.loads((Path(__file__).resolve().parent / "schema.json").read_text())
api_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:7860").rstrip("/")
st.set_page_config(page_title="SuperKart Sales Prediction", layout="centered")
st.title("SuperKart Sales Prediction")
st.write("Estimate sales revenue for a product at a store.")
st.caption("Use store age as of 2025. Estimates reflect historical data and do not include seasonal changes.")
online, batch = st.tabs(["Single prediction", "Batch prediction"])

with online:
    with st.form("sales_form"):
        payload = {}
        for col in schema["features"]:
            label = col.replace("_", " ")
            if col in schema["numeric_features"]:
                upper = 1.0 if col == "Product_Allocated_Area" else None
                payload[col] = st.number_input(label, min_value=0.0, max_value=upper,
                                               value=float(schema["defaults"][col]))
            else:
                payload[col] = st.selectbox(label, schema["categories"][col])
        submitted = st.form_submit_button("Predict sales")
    if submitted:
        try:
            response = requests.post(api_url + "/v1/predict", json=payload, timeout=30)
            if response.ok:
                st.metric("Estimated sales revenue", f"{response.json()['predicted_sales']:,.2f}")
            else:
                st.error(response.json().get("error", "Prediction failed."))
        except (requests.RequestException, ValueError):
            st.error("Could not reach the prediction service. Check that the backend is running.")

with batch:
    st.write("Upload a CSV with the same columns as Batch_Data_SuperKart.csv.")
    st.caption("Required columns: " + ", ".join(schema["features"]))
    uploaded_file = st.file_uploader("Product data", type=["csv"])
    if st.button("Predict batch sales"):
        if uploaded_file is None:
            st.warning("Upload a CSV first.")
        else:
            try:
                content = uploaded_file.getvalue()
                response = requests.post(api_url + "/v1/predictbatch",
                                         files={"file": ("batch.csv", content, "text/csv")}, timeout=60)
                if response.ok:
                    from io import BytesIO
                    results = pd.read_csv(BytesIO(content))
                    predictions = response.json()
                    unseen = [col for col, values in schema["categories"].items()
                              if not results[col].isin(values).all()]
                    if unseen:
                        st.warning("Unseen categories in " + ", ".join(unseen) + ". Review these predictions carefully.")
                    results["Predicted_Sales"] = [predictions[str(i)] for i in range(len(results))]
                    st.dataframe(results)
                    st.download_button("Download predictions", results.to_csv(index=False),
                                       "superkart_predictions.csv", "text/csv")
                else:
                    st.error(response.json().get("error", "Prediction failed."))
            except (requests.RequestException, ValueError):
                st.error("Could not process the file. Check the CSV and backend connection.")
