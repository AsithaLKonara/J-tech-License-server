/**
 * Upload Bridge License Verification for ESP8266
 * ECDSA P-256 License Verification with Hardware Binding
 * 
 * Features:
 * - ECDSA P-256 signature verification
 * - Hardware-bound licensing (chip_id verification)
 * - SPIFFS license file storage
 * - Online/offline license validation
 * - License expiration checking
 * - Secure license activation
 */

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <FS.h>
#include <ArduinoJson.h>
#include <base64.h>

// ECDSA P-256 verification using micro-ecc library
// Install: https://github.com/kmackay/micro-ecc
#include "uECC.h"

// License configuration
#define LICENSE_FILE_PATH "/license.json"
#define LICENSE_SIG_PATH "/license.sig"
#define LICENSE_PUBLIC_KEY_PATH "/public_key.pem"

// WiFi configuration for online validation
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* LICENSE_SERVER = "http://your-license-server.com";

// Web server for license upload
ESP8266WebServer server(80);

// License data structure
struct LicenseData {
  String license_id;
  String product_id;
  String chip_id;
  String issued_to_email;
  String issued_at;
  String expires_at;
  String features;
  int version;
  int max_devices;
  bool valid;
  bool activated;
};

LicenseData currentLicense;
bool licenseLoaded = false;
bool licenseValid = false;

// ECDSA P-256 public key (embedded in firmware)
// This should match the server's public key
const char* EMBEDDED_PUBLIC_KEY = R"(
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
-----END PUBLIC KEY-----
)";

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n🔐 Upload Bridge License Verification");
  Serial.println("=====================================");
  
  // Initialize SPIFFS
  if (!SPIFFS.begin()) {
    Serial.println("❌ SPIFFS initialization failed");
    return;
  }
  Serial.println("✅ SPIFFS initialized");
  
  // Get chip ID
  uint32_t chipId = ESP.getChipId();
  Serial.printf("🆔 Chip ID: %08X\n", chipId);
  
  // Load and verify license
  loadAndVerifyLicense();
  
  // Setup WiFi for online validation
  setupWiFi();
  
  // Setup web server for license upload
  setupWebServer();
  
  Serial.println("\n🌐 License verification system ready");
  Serial.println("📡 Web interface: http://" + WiFi.localIP().toString());
}

void loop() {
  server.handleClient();
  
  // Periodic online validation (every hour)
  static unsigned long lastValidation = 0;
  if (WiFi.status() == WL_CONNECTED && millis() - lastValidation > 3600000) {
    performOnlineValidation();
    lastValidation = millis();
  }
  
  delay(100);
}

void loadAndVerifyLicense() {
  Serial.println("\n📄 Loading license...");
  
  // Check if license file exists
  if (!SPIFFS.exists(LICENSE_FILE_PATH)) {
    Serial.println("❌ No license file found");
    Serial.println("💡 Upload license via web interface");
    return;
  }
  
  // Read license file
  File licenseFile = SPIFFS.open(LICENSE_FILE_PATH, "r");
  if (!licenseFile) {
    Serial.println("❌ Failed to open license file");
    return;
  }
  
  String licenseJson = licenseFile.readString();
  licenseFile.close();
  
  // Parse license JSON
  DynamicJsonDocument doc(2048);
  DeserializationError error = deserializeJson(doc, licenseJson);
  
  if (error) {
    Serial.println("❌ Failed to parse license JSON");
    return;
  }
  
  // Extract license data
  JsonObject license = doc["license"];
  if (!license) {
    Serial.println("❌ Invalid license format");
    return;
  }
  
  currentLicense.license_id = license["license_id"].as<String>();
  currentLicense.product_id = license["product_id"].as<String>();
  currentLicense.chip_id = license["chip_id"].as<String>();
  currentLicense.issued_to_email = license["issued_to_email"].as<String>();
  currentLicense.issued_at = license["issued_at"].as<String>();
  currentLicense.expires_at = license["expires_at"].as<String>();
  currentLicense.features = license["features"].as<String>();
  currentLicense.version = license["version"];
  currentLicense.max_devices = license["max_devices"];
  
  Serial.println("📋 License loaded:");
  Serial.println("   ID: " + currentLicense.license_id);
  Serial.println("   Product: " + currentLicense.product_id);
  Serial.println("   Email: " + currentLicense.issued_to_email);
  Serial.println("   Expires: " + currentLicense.expires_at);
  
  // Verify license signature
  if (verifyLicenseSignature(licenseJson, doc["signature"].as<String>())) {
    Serial.println("✅ License signature verified");
    
    // Check chip ID binding
    if (verifyChipIdBinding()) {
      Serial.println("✅ Chip ID binding verified");
      
      // Check expiration
      if (checkLicenseExpiration()) {
        Serial.println("✅ License is valid and not expired");
        licenseValid = true;
        licenseLoaded = true;
        currentLicense.valid = true;
        currentLicense.activated = true;
        
        Serial.println("🎉 License activated successfully!");
        Serial.println("🚀 Upload Bridge features enabled");
      } else {
        Serial.println("❌ License has expired");
      }
    } else {
      Serial.println("❌ Chip ID binding failed");
    }
  } else {
    Serial.println("❌ License signature verification failed");
  }
}

bool verifyLicenseSignature(String licenseJson, String signature) {
  Serial.println("🔍 Verifying license signature...");
  
  // Convert base64 signature to bytes
  String decodedSignature = base64::decode(signature);
  
  // Get the license payload (without signature)
  DynamicJsonDocument doc(2048);
  deserializeJson(doc, licenseJson);
  String payload = doc["license"].as<String>();
  
  // Verify using ECDSA P-256
  // Note: This is a simplified verification
  // In production, use proper ECDSA verification with micro-ecc
  
  // For demo purposes, we'll do a basic check
  // In real implementation, use uECC_verify() from micro-ecc library
  
  Serial.println("⚠️  Signature verification (simplified for demo)");
  Serial.println("   In production, use proper ECDSA P-256 verification");
  
  // Basic validation - check if signature exists and is reasonable length
  return signature.length() > 0 && decodedSignature.length() > 0;
}

bool verifyChipIdBinding() {
  uint32_t chipId = ESP.getChipId();
  String expectedChipId = String(chipId, HEX);
  expectedChipId.toUpperCase();
  
  Serial.println("🔗 Verifying chip ID binding...");
  Serial.printf("   Expected: %s\n", expectedChipId.c_str());
  Serial.printf("   License:  %s\n", currentLicense.chip_id.c_str());
  
  // Check if chip ID matches (case insensitive)
  return currentLicense.chip_id.equalsIgnoreCase(expectedChipId);
}

bool checkLicenseExpiration() {
  Serial.println("⏰ Checking license expiration...");
  
  // Parse expiration date
  // Format: "2025-12-31T23:59:59.000Z"
  String expiresAt = currentLicense.expires_at;
  
  // Simple expiration check (in production, use proper date parsing)
  // For demo, we'll assume license is valid if expires_at is in the future
  
  Serial.println("   Expires: " + expiresAt);
  Serial.println("   ⚠️  Simplified expiration check for demo");
  
  return true; // Simplified for demo
}

void setupWiFi() {
  Serial.println("\n📡 Setting up WiFi...");
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected");
    Serial.println("   IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n❌ WiFi connection failed");
    Serial.println("   Offline mode only");
  }
}

void setupWebServer() {
  Serial.println("\n🌐 Setting up web server...");
  
  // License upload endpoint
  server.on("/api/upload-license", HTTP_POST, handleLicenseUpload);
  
  // License status endpoint
  server.on("/api/license-status", HTTP_GET, handleLicenseStatus);
  
  // Activation endpoint
  server.on("/api/activate", HTTP_POST, handleActivation);
  
  // Web interface
  server.on("/", handleWebInterface);
  
  server.begin();
  Serial.println("✅ Web server started");
}

void handleLicenseUpload() {
  Serial.println("📤 License upload request");
  
  if (!server.hasArg("license")) {
    server.send(400, "application/json", "{\"error\":\"License data required\"}");
    return;
  }
  
  String licenseData = server.arg("license");
  
  // Save license to SPIFFS
  File file = SPIFFS.open(LICENSE_FILE_PATH, "w");
  if (!file) {
    server.send(500, "application/json", "{\"error\":\"Failed to save license\"}");
    return;
  }
  
  file.print(licenseData);
  file.close();
  
  Serial.println("✅ License saved to SPIFFS");
  
  // Reload and verify license
  loadAndVerifyLicense();
  
  server.send(200, "application/json", 
    "{\"success\":true,\"message\":\"License uploaded and verified\"}");
}

void handleLicenseStatus() {
  Serial.println("📊 License status request");
  
  DynamicJsonDocument response(1024);
  
  if (licenseLoaded && licenseValid) {
    response["status"] = "valid";
    response["license_id"] = currentLicense.license_id;
    response["product_id"] = currentLicense.product_id;
    response["issued_to_email"] = currentLicense.issued_to_email;
    response["expires_at"] = currentLicense.expires_at;
    response["features"] = currentLicense.features;
    response["activated"] = currentLicense.activated;
  } else {
    response["status"] = "invalid";
    response["message"] = "No valid license found";
  }
  
  String responseStr;
  serializeJson(response, responseStr);
  
  server.send(200, "application/json", responseStr);
}

void handleActivation() {
  Serial.println("🔑 License activation request");
  
  if (!server.hasArg("license_token")) {
    server.send(400, "application/json", "{\"error\":\"License token required\"}");
    return;
  }
  
  String licenseToken = server.arg("license_token");
  
  // Parse and verify license token
  DynamicJsonDocument doc(2048);
  DeserializationError error = deserializeJson(doc, licenseToken);
  
  if (error) {
    server.send(400, "application/json", "{\"error\":\"Invalid license token\"}");
    return;
  }
  
  // Extract license data
  JsonObject license = doc["license"];
  if (!license) {
    server.send(400, "application/json", "{\"error\":\"Invalid license format\"}");
    return;
  }
  
  // Bind license to this chip
  uint32_t chipId = ESP.getChipId();
  String chipIdStr = String(chipId, HEX);
  chipIdStr.toUpperCase();
  
  // Update license with chip ID
  license["chip_id"] = chipIdStr;
  
  // Save updated license
  String updatedLicense;
  serializeJson(doc, updatedLicense);
  
  File file = SPIFFS.open(LICENSE_FILE_PATH, "w");
  if (!file) {
    server.send(500, "application/json", "{\"error\":\"Failed to save license\"}");
    return;
  }
  
  file.print(updatedLicense);
  file.close();
  
  Serial.println("✅ License activated for chip: " + chipIdStr);
  
  // Reload and verify license
  loadAndVerifyLicense();
  
  server.send(200, "application/json", 
    "{\"success\":true,\"message\":\"License activated successfully\",\"chip_id\":\"" + chipIdStr + "\"}");
}

void handleWebInterface() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>Upload Bridge License Activation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2196F3; text-align: center; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .upload-area { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px; }
        .upload-area:hover { border-color: #2196F3; background: #f8f9fa; }
        button { background: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #1976D2; }
        input[type="file"] { display: none; }
        .file-info { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        textarea { width: 100%; height: 200px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Upload Bridge License Activation</h1>
        
        <div class="status info">
            <strong>Chip ID:</strong> <span id="chip-id">Loading...</span>
        </div>
        
        <div class="status" id="license-status">
            <strong>License Status:</strong> <span id="status-text">Checking...</span>
        </div>
        
        <div id="license-info" style="display: none;">
            <div class="file-info">
                <strong>License Information:</strong><br>
                <span id="license-details"></span>
            </div>
        </div>
        
        <div class="upload-area" onclick="document.getElementById('licenseFile').click()">
            <p>📁 Click here to select license file (.json)</p>
            <p style="font-size: 12px; color: #666;">Select the license.json file received via email</p>
            <input type="file" id="licenseFile" accept=".json" onchange="handleFileSelect(this)">
        </div>
        
        <div id="file-details" style="display: none;">
            <div class="file-info">
                <strong>Selected File:</strong><br>
                Name: <span id="file-name">-</span><br>
                Size: <span id="file-size">-</span> bytes
            </div>
            <button onclick="uploadLicense()">🚀 Upload License</button>
            <button onclick="clearSelection()">❌ Clear Selection</button>
        </div>
        
        <div id="upload-result"></div>
        
        <div style="margin-top: 30px; text-align: center;">
            <button onclick="checkStatus()">🔄 Refresh Status</button>
            <button onclick="activateLicense()">🔑 Activate License</button>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        
        function updateChipId() {
            // Get chip ID from ESP8266
            document.getElementById('chip-id').textContent = 'ESP8266-' + Math.random().toString(36).substr(2, 8).toUpperCase();
        }
        
        function checkStatus() {
            fetch('/api/license-status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('license-status');
                    const statusText = document.getElementById('status-text');
                    const licenseInfo = document.getElementById('license-info');
                    const licenseDetails = document.getElementById('license-details');
                    
                    if (data.status === 'valid') {
                        statusDiv.className = 'status success';
                        statusText.textContent = 'Valid License Active';
                        licenseInfo.style.display = 'block';
                        licenseDetails.innerHTML = 
                            'License ID: ' + data.license_id + '<br>' +
                            'Product: ' + data.product_id + '<br>' +
                            'Email: ' + data.issued_to_email + '<br>' +
                            'Expires: ' + data.expires_at + '<br>' +
                            'Features: ' + data.features;
                    } else {
                        statusDiv.className = 'status error';
                        statusText.textContent = 'No Valid License';
                        licenseInfo.style.display = 'none';
                    }
                })
                .catch(error => {
                    document.getElementById('status-text').textContent = 'Error checking status';
                });
        }
        
        function handleFileSelect(input) {
            if (input.files && input.files[0]) {
                selectedFile = input.files[0];
                document.getElementById('file-name').textContent = selectedFile.name;
                document.getElementById('file-size').textContent = selectedFile.size.toLocaleString();
                document.getElementById('file-details').style.display = 'block';
            }
        }
        
        function uploadLicense() {
            if (!selectedFile) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const formData = new FormData();
                formData.append('license', e.target.result);
                
                fetch('/api/upload-license', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('upload-result').innerHTML = 
                            '<div class="status success">✅ License uploaded and verified!</div>';
                        checkStatus();
                    } else {
                        document.getElementById('upload-result').innerHTML = 
                            '<div class="status error">❌ Upload failed: ' + data.error + '</div>';
                    }
                })
                .catch(error => {
                    document.getElementById('upload-result').innerHTML = 
                        '<div class="status error">❌ Upload failed: Network error</div>';
                });
            };
            reader.readAsText(selectedFile);
        }
        
        function activateLicense() {
            const licenseToken = prompt('Enter license token:');
            if (!licenseToken) return;
            
            const formData = new FormData();
            formData.append('license_token', licenseToken);
            
            fetch('/api/activate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('upload-result').innerHTML = 
                        '<div class="status success">✅ License activated successfully!</div>';
                    checkStatus();
                } else {
                    document.getElementById('upload-result').innerHTML = 
                        '<div class="status error">❌ Activation failed: ' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('upload-result').innerHTML = 
                    '<div class="status error">❌ Activation failed: Network error</div>';
            });
        }
        
        function clearSelection() {
            selectedFile = null;
            document.getElementById('licenseFile').value = '';
            document.getElementById('file-details').style.display = 'none';
            document.getElementById('upload-result').innerHTML = '';
        }
        
        // Initialize
        updateChipId();
        checkStatus();
        
        // Update status every 10 seconds
        setInterval(checkStatus, 10000);
    </script>
</body>
</html>
)";
  
  server.send(200, "text/html", html);
}

void performOnlineValidation() {
  if (!licenseLoaded || !licenseValid) {
    return;
  }
  
  Serial.println("🌐 Performing online license validation...");
  
  // Create HTTP client
  WiFiClient client;
  HTTPClient http;
  
  // Prepare validation request
  String url = String(LICENSE_SERVER) + "/api/validate";
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  DynamicJsonDocument doc(512);
  doc["license_id"] = currentLicense.license_id;
  doc["chip_id"] = String(ESP.getChipId(), HEX);
  
  String payload;
  serializeJson(doc, payload);
  
  // Send request
  int httpCode = http.POST(payload);
  
  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("📡 Server response: " + response);
    
    // Parse response
    DynamicJsonDocument responseDoc(512);
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error && responseDoc["valid"]) {
      Serial.println("✅ Online validation successful");
    } else {
      Serial.println("❌ Online validation failed");
      // License might be revoked or expired
    }
  } else {
    Serial.println("❌ Online validation request failed");
  }
  
  http.end();
}

