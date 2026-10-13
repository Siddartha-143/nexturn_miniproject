
from flask import Flask, jsonify
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.get("/api/health")
    def health_check():
        return jsonify({
            "success": True,
            "message": "Kitchen Order Router API is running"
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
