import http.server
import socketserver
import json
import urllib.request
import urllib.error
import base64
import os
import webbrowser
import math

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# -------------------------------------------------------------
# In-Memory Incident Store (Pre-seeded with realistic data)
# -------------------------------------------------------------
incidents = [
    {
        "id": "TKT-1001",
        "title": "Severe Deep Pothole on Commuter Highway Lane",
        "category": "Road Infrastructure",
        "severity_score": 5,
        "severity_label": "Critical Hazard",
        "department": "Public Works Department (PWD)",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "address": "Outer Ring Road, Near Gate 3",
        "status": "In Progress",
        "upvotes": 8,
        "reported_time": "2 hours ago",
        "hazard_rationale": "High-speed lane crater (~10 inch depth) causing abrupt braking and high rollover risk.",
        "recommended_action": "Emergency cold asphalt patching and warning barricades."
    },
    {
        "id": "TKT-1002",
        "title": "Overflowing Public Waste Bin Blocking Walkway",
        "category": "Sanitation & Waste",
        "severity_score": 3,
        "severity_label": "Moderate",
        "department": "Municipal Solid Waste Corp",
        "latitude": 28.6280,
        "longitude": 77.2200,
        "address": "Market Complex Pedestrian Zone",
        "status": "Reported",
        "upvotes": 3,
        "reported_time": "4 hours ago",
        "hazard_rationale": "Solid waste overflow blocking pedestrian sidewalk, attracting pests and creating public health risk.",
        "recommended_action": "Deploy 2-man compact waste truck for collection and disinfection."
    },
    {
        "id": "TKT-1003",
        "title": "High-Pressure Potable Water Main Burst",
        "category": "Water & Drainage",
        "severity_score": 4,
        "severity_label": "High Urgency",
        "department": "City Water Board",
        "latitude": 28.6350,
        "longitude": 77.2120,
        "address": "Sector 4 Junction",
        "status": "Dispatched",
        "upvotes": 14,
        "reported_time": "1 hour ago",
        "hazard_rationale": "Continuous water loss undermining sub-road asphalt, creating risk of sinkhole collapse.",
        "recommended_action": "Isolate valve sector 4 and replace breached cast iron conduit."
    }
]

def calculate_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000 # Radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def call_gemini_api(api_key, parts_data):
    """Direct standard library HTTPS call to Google Gemini with automatic model fallback."""
    # List of reliable production models in order of trial
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro"
    ]
    
    clean_key = api_key.strip().strip('"').strip("'")
    last_error = None

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
        payload = {
            "contents": [
                {
                    "parts": parts_data
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                text_response = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_response)
        except urllib.error.HTTPError as he:
            err_body = he.read().decode('utf-8', errors='ignore')
            last_error = f"Model {model_name} HTTP {he.code}: {err_body}"
            # If 404 (model not found), continue loop and try next model
            if he.code == 404:
                continue
            else:
                # Other errors (e.g. 400 bad API key, 403 quota)
                raise Exception(f"Google API Error ({he.code}): {err_body}")
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"All models failed. Last error: {last_error}")

class CivicLensHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
            return super().do_GET()
        elif self.path == "/api/incidents":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(incidents).encode('utf-8'))
            return
        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        if self.path == "/api/analyze":
            api_key = req_data.get("api_key", "").strip()
            image_b64 = req_data.get("image_base64", "")
            mime_type = req_data.get("mime_type", "image/jpeg")
            citizen_note = req_data.get("note", "")
            lat = float(req_data.get("latitude", 28.6315))
            lon = float(req_data.get("longitude", 77.2167))
            address = req_data.get("address", "Civic Zone")

            if not api_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Gemini API key is required."}).encode('utf-8'))
                return

            prompt = f"""
You are an expert Certified Municipal Civil Engineer and AI Triage Inspector.
Analyze this submitted photo for civic or municipal infrastructure issues.

Citizen Additional Note: "{citizen_note}"

Return STRICT JSON format ONLY with this schema:
{{
  "is_civic_issue": true,
  "rejection_reason": "string (only if is_civic_issue is false, explaining why)",
  "title": "Short 5-8 word punchy title of the defect",
  "category": "One of ['Road Infrastructure', 'Sanitation & Waste', 'Water & Drainage', 'Electrical & Lighting', 'Public Safety & Parks']",
  "severity_score": integer from 1 (minor) to 5 (critical danger to life/traffic),
  "severity_label": "One of ['Low', 'Moderate', 'High', 'Critical Hazard', 'Emergency']",
  "assigned_department": "Municipal department responsible",
  "hazard_rationale": "2-3 sentences explaining the danger to vehicles, pedestrians, or public health",
  "recommended_action": "Specific repair crew action",
  "estimated_fix_time_hours": 24
}}
"""
            # Clean image data
            if "," in image_b64:
                image_b64 = image_b64.split(",", 1)[1]

            parts = [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_b64
                    }
                },
                {"text": prompt}
            ]

            try:
                ai_result = call_gemini_api(api_key, parts)

                duplicate_found = False
                matched_ticket = None

                if ai_result.get("is_civic_issue", False):
                    # Check for duplicates within 75 meters
                    for existing in incidents:
                        dist = calculate_distance_meters(lat, lon, existing["latitude"], existing["longitude"])
                        if dist <= 75 and existing["category"] == ai_result.get("category"):
                            duplicate_found = True
                            matched_ticket = existing
                            existing["upvotes"] += 1
                            if existing["severity_score"] < 5:
                                existing["severity_score"] += 1
                                existing["severity_label"] = "Escalated by Citizens"
                            break

                    if not duplicate_found:
                        new_ticket = {
                            "id": f"TKT-{len(incidents) + 1001}",
                            "title": ai_result.get("title", "Civic Infrastructure Defect"),
                            "category": ai_result.get("category", "Road Infrastructure"),
                            "severity_score": int(ai_result.get("severity_score", 3)),
                            "severity_label": ai_result.get("severity_label", "Moderate"),
                            "department": ai_result.get("assigned_department", "Public Works"),
                            "latitude": lat,
                            "longitude": lon,
                            "address": address,
                            "status": "Reported",
                            "upvotes": 1,
                            "reported_time": "Just now",
                            "hazard_rationale": ai_result.get("hazard_rationale", ""),
                            "recommended_action": ai_result.get("recommended_action", "")
                        }
                        incidents.insert(0, new_ticket)

                response_obj = {
                    "ai_result": ai_result,
                    "duplicate_found": duplicate_found,
                    "matched_ticket": matched_ticket,
                    "all_incidents": incidents
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_obj).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

        elif self.path == "/api/audit":
            api_key = req_data.get("api_key", "").strip()
            before_b64 = req_data.get("before_image", "")
            after_b64 = req_data.get("after_image", "")
            title = req_data.get("title", "Infrastructure Repair")

            if "," in before_b64:
                before_b64 = before_b64.split(",", 1)[1]
            if "," in after_b64:
                after_b64 = after_b64.split(",", 1)[1]

            prompt = f"""
You are a Municipal Quality Assurance Auditor.
Original Problem: "{title}"

Audit these TWO images:
Image 1: The 'BEFORE' photo showing original reported defect.
Image 2: The 'AFTER' photo claiming work is complete.

Return STRICT JSON ONLY:
{{
  "is_resolved": true,
  "confidence_percentage": 95,
  "quality_grade": "One of ['Excellent', 'Acceptable', 'Substandard', 'Incomplete', 'Fraudulent']",
  "audit_verdict": "Detailed summary of whether the repair is acceptable or rejected."
}}
"""
            parts = [
                {"inline_data": {"mime_type": "image/jpeg", "data": before_b64}},
                {"inline_data": {"mime_type": "image/jpeg", "data": after_b64}},
                {"text": prompt}
            ]

            try:
                audit_res = call_gemini_api(api_key, parts)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(audit_res).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

        elif self.path == "/api/update_status":
            tkt_id = req_data.get("id")
            new_status = req_data.get("status")
            for inc in incidents:
                if inc["id"] == tkt_id:
                    inc["status"] = new_status
                    break
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "incidents": incidents}).encode('utf-8'))

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    server_address = ('', PORT)
    with socketserver.TCPServer(server_address, CivicLensHandler) as httpd:
        print(f"==================================================")
        print(f"🚀 CivicLens AI Server Running!")
        print(f"👉 Open in your browser: http://localhost:{PORT}")
        print(f"==================================================")
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass
        httpd.serve_forever()
