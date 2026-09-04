"""
Entrypoint runner for the Supply Chain Disruption Predictor Flask Web Application.
Run:
    python run_flask.py
"""

from flask_app.app import app

if __name__ == "__main__":
    print("=" * 70)
    print(">> Starting Supply Chain Disruption Predictor Flask App")
    print(">> Dashboard URL: http://localhost:5000")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=True)
