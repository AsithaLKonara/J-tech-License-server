from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Mock data
MOCK_USER = {
    "id": 1,
    "email": "test@example.com",
    "name": "Local Test User"
}

MOCK_ENTITLEMENT = {
    "id": 1,
    "plan": "perpetual",
    "status": "ACTIVE",
    "features": ["verify", "probe", "ota", "comprehensive_metrics"],
    "max_devices": 10,
    "current_devices": 1,
    "expires_at": "2030-01-01T00:00:00Z",
    "is_active": True
}

@app.route('/api/v2/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "timestamp": str(time.time())})

@app.route('/api/v2/auth/login', methods=['POST'])
def login():
    data = request.json
    return jsonify({
        "session_token": "mock_session_token_" + str(time.time()),
        "entitlement_token": {
            "token": "mock_entitlement_token_" + str(time.time()),
            "plan": "perpetual",
            "issued_at": int(time.time()),
            "expires_at": int(time.time()) + 3600,
            "features": MOCK_ENTITLEMENT["features"]
        },
        "user": MOCK_USER
    })

@app.route('/api/v2/auth/refresh', methods=['POST'])
def refresh():
    return login()

@app.route('/api/v2/license/validate', methods=['GET'])
def validate_license():
    return jsonify({"valid": True, "timestamp": str(time.time())})

@app.route('/api/v2/license/info', methods=['GET'])
def license_info():
    return jsonify({"entitlement": MOCK_ENTITLEMENT})

@app.route('/api/v2/devices/register', methods=['POST'])
def register_device():
    return jsonify({"success": True, "message": "Device registered locally (Mock)"})

if __name__ == '__main__':
    print("Starting Mock License Server on http://localhost:8000")
    app.run(port=8000)
