from flask import Flask, jsonify, session
from flask_cors import CORS
from routes import register_routes
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = "super-secret-key"
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

register_routes(app)

def start_schedulers(app):
    if app.extensions.get("apscheduler"):
        return app.extensions["apscheduler"]

    sched = BackgroundScheduler(daemon=True)

    def run_payout():
        with app.app_context():
            from services.schedule_service import payout_for_active_schedules
            payout_for_active_schedules()

    sched.add_job(run_payout, "interval", minutes=10, id="payout-job", replace_existing=True)
    sched.start()
    app.extensions["apscheduler"] = sched
    return sched

@app.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_schedulers(app)
    app.run(debug=True)
