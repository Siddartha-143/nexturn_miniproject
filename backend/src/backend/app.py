
from flask import Flask, jsonify
from flask_cors import CORS
from backend.database import init_db
from backend.menu import menu_bp
from backend.orders import orders_bp

app = Flask(__name__)
CORS(app)

init_db()

app.register_blueprint(menu_bp, url_prefix="/api")
app.register_blueprint(orders_bp, url_prefix="/api")


@app.route("/api/health")
def health_check():
    return jsonify({
        "success": True,
        "message": "Kitchen Order Router API is running"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
