# Creating app.py
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

superkart_api = Flask(__name__)
superkart_api.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
folder = Path(__file__).resolve().parent
model = joblib.load(folder / "superkart_model.joblib")
schema = json.loads((folder / "schema.json").read_text())

def prepare_data(frame):
    missing = sorted(set(schema["features"]) - set(frame.columns))
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))
    if frame.empty:
        raise ValueError("Provide at least one row.")
    frame = frame[schema["features"]].copy()
    frame["Product_Sugar_Content"] = frame["Product_Sugar_Content"].replace({"reg": "Regular"})
    for col in schema["numeric_features"]:
        frame[col] = pd.to_numeric(frame[col], errors="raise")
        if not np.isfinite(frame[col]).all() or (frame[col] < 0).any():
            raise ValueError(col + " must contain finite, non-negative numbers.")
    if (frame["Product_Allocated_Area"] > 1).any():
        raise ValueError("Product_Allocated_Area must be between 0 and 1.")
    for col, choices in schema["categories"].items():
        if not frame[col].isin(choices).all():
            raise ValueError(col + " must be one of: " + ", ".join(choices))
    return frame

@superkart_api.get("/health")
def health():
    return jsonify({"status": "ok"})

@superkart_api.post("/v1/predict")
def predict():
    # Predict API
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return jsonify({"error": "Send one non-empty JSON object."}), 400
    try:
        frame = prepare_data(pd.DataFrame([payload]))
        return jsonify({"predicted_sales": float(model.predict(frame)[0])})
    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

@superkart_api.post("/v1/predictbatch")
def predict_batch():
    # Predict batch API
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV using the file field."}), 400
    try:
        frame = prepare_data(pd.read_csv(request.files["file"]))
        predictions = model.predict(frame)
        return jsonify({str(i): float(value) for i, value in enumerate(predictions)})
    except (ValueError, TypeError, UnicodeError, pd.errors.ParserError) as error:
        return jsonify({"error": str(error)}), 400

@superkart_api.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify({"error": "Upload a file smaller than 5 MB."}), 413

if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
