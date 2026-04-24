import joblib
from flask import Flask, request, render_template_string

MODEL_FILE = "sensitivity_2019_model.joblib"

app = Flask(__name__)
artifact = joblib.load(MODEL_FILE)
models = artifact["models"]

def predict_country(country_input):
    q = country_input.strip().lower()
    if not q:
        return None, "Please enter a country name or ISO3 code."

    for iso3, model in models.items():
        if q == iso3.lower() or q == model["name"].lower():
            if model["n_obs"] == 0:
                return None, f"No historical sensitivity data available for {model['name']}."
            if model["method"] == "ar1_trend":
                pred = model["forecast_2019"]
            else:
                pred = model.get("last")
            return {
                "country": model["name"],
                "iso3": model["iso3"],
                "prediction": pred,
                "method": model["method"],
                "observations": model["n_obs"]
            }, None

    suggestions = [
        m["name"] for m in models.values()
        if q in m["name"].lower() or q in m["iso3"].lower()
    ][:8]

    if suggestions:
        return None, "Country not found. Did you mean: " + ", ".join(suggestions) + "?"
    return None, "Country not found. Please enter a valid country name or ISO3 code."

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>2019 Sensitivity Predictor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #eef4ff, #f7fbff);
            color: #1f2937;
        }
        .container {
            max-width: 760px;
            margin: 60px auto;
            background: white;
            padding: 36px;
            border-radius: 22px;
            box-shadow: 0 12px 35px rgba(31, 41, 55, 0.12);
        }
        h1 {
            margin-top: 0;
            color: #1d4ed8;
            font-size: 30px;
        }
        p {
            line-height: 1.6;
            color: #4b5563;
        }
        form {
            display: flex;
            gap: 12px;
            margin-top: 24px;
            flex-wrap: wrap;
        }
        input {
            flex: 1;
            min-width: 220px;
            padding: 14px;
            font-size: 16px;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
        }
        button {
            padding: 14px 24px;
            font-size: 16px;
            border: none;
            border-radius: 12px;
            background: #2563eb;
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background: #1d4ed8;
        }
        .result {
            margin-top: 28px;
            padding: 24px;
            border-radius: 16px;
            background: #eff6ff;
            border-left: 6px solid #2563eb;
        }
        .result .value {
            font-size: 36px;
            font-weight: bold;
            color: #1e40af;
        }
        .error {
            margin-top: 28px;
            padding: 18px;
            border-radius: 14px;
            background: #fff7ed;
            border-left: 6px solid #f97316;
            color: #9a3412;
        }
        .small {
            font-size: 14px;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>2019 Sensitivity Predictor</h1>
        <p>Enter a country name or ISO3 code. The app uses a per-country AR(1) time-series model with trend, trained from 1995 to 2018, to forecast 2019 sensitivity.</p>

        <form method="POST">
            <input name="country" placeholder="Example: Singapore or SGP" value="{{ country }}">
            <button type="submit">Predict</button>
        </form>

        {% if result %}
        <div class="result">
            <h2>{{ result.country }} ({{ result.iso3 }})</h2>
            <div class="value">{{ "%.6f"|format(result.prediction) }}</div>
            <p class="small">Predicted 2019 sensitivity</p>
            <p class="small">Model: {{ result.method }} | Observations used: {{ result.observations }}</p>
        </div>
        {% endif %}

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    country = ""

    if request.method == "POST":
        country = request.form.get("country", "")
        result, error = predict_country(country)

    return render_template_string(HTML, result=result, error=error, country=country)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)