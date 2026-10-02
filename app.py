import streamlit as st
import os
import json
import io
import math
import pandas as pd
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="CivicLens AI | Intelligent Civic Issue Triage",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern hackathon presentation
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .severity-badge-5 { background-color: #EF4444; color: white; padding: 4px 10px; border-radius: 9999px; font-weight: 700; }
    .severity-badge-4 { background-color: #F97316; color: white; padding: 4px 10px; border-radius: 9999px; font-weight: 700; }
    .severity-badge-3 { background-color: #F59E0B; color: white; padding: 4px 10px; border-radius: 9999px; font-weight: 700; }
    .severity-badge-2 { background-color: #10B981; color: white; padding: 4px 10px; border-radius: 9999px; font-weight: 700; }
    .severity-badge-1 { background-color: #3B82F6; color: white; padding: 4px 10px; border-radius: 9999px; font-weight: 700; }
    .duplicate-alert {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        color: #92400E;
        padding: 12px;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Initialize Session State Database (Simulated persistence)
# -------------------------------------------------------------
if "incidents" not in st.session_state:
    st.session_state.incidents = [
        {
            "id": "TKT-1001",
            "title": "Massive Crater Pothole on Connaught Outer Circle",
            "category": "Road Infrastructure",
            "severity_score": 5,
            "severity_label": "Critical Hazard",
            "department": "Public Works Department (PWD)",
            "latitude": 28.6315,
            "longitude": 77.2167,
            "address": "Connaught Place, New Delhi",
            "status": "In Progress",
            "upvotes": 7,
            "reported_time": "2 hours ago",
            "rationale": "High-speed lane pothole (~12 inch depth) posing immediate motorcycle wipeout risk."
        },
        {
            "id": "TKT-1002",
            "title": "Overflowing Municipal Dumpster Blocking Sidewalk",
            "category": "Sanitation & Waste",
            "severity_score": 3,
            "severity_label": "Moderate",
            "department": "Municipal Solid Waste Corp",
            "latitude": 28.6280,
            "longitude": 77.2200,
            "address": "Barakhamba Road",
            "status": "Reported",
            "upvotes": 3,
            "reported_time": "4 hours ago",
            "rationale": "Garbage spill on pedestrian footpath causing public health and pedestrian overflow onto road."
        },
        {
            "id": "TKT-1003",
            "title": "High-Pressure Main Water Pipe Leak",
            "category": "Water & Drainage",
            "severity_score": 4,
            "severity_label": "High Urgency",
            "department": "Delhi Jal Board",
            "latitude": 28.6350,
            "longitude": 77.2120,
            "address": "Shivaji Stadium Lane",
            "status": "Dispatched",
            "upvotes": 12,
            "reported_time": "1 hour ago",
            "rationale": "Severe potable water wastage and road base erosion risking asphalt collapse."
        }
    ]

# -------------------------------------------------------------
# Helper: Distance Calculation (Haversine in meters)
# -------------------------------------------------------------
def calculate_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# -------------------------------------------------------------
# Helper: Gemini AI Vision Analysis
# -------------------------------------------------------------
def analyze_civic_image(image: Image.Image, api_key: str, citizen_note: str = ""):
    """Analyzes an image with Google Gemini to extract structured civic triage metadata."""
    prompt = f"""
You are an expert Certified Municipal Civil Engineer and AI Triage Inspector.
Analyze this submitted photo for civic or municipal infrastructure issues.

Citizen Additional Note: "{citizen_note}"

Return STRICT JSON format ONLY (no markdown fences, no extra text) with the following structure:
{{
  "is_civic_issue": true or false,
  "rejection_reason": "string (only if is_civic_issue is false, explaining why)",
  "title": "Concise 5-8 word title of the problem",
  "category": "One of ['Road Infrastructure', 'Sanitation & Waste', 'Water & Drainage', 'Electrical & Lighting', 'Public Parks & Footpaths', 'General Hazard']",
  "severity_score": integer from 1 (minor cosmetic) to 5 (imminent danger to life/traffic),
  "severity_label": "One of ['Low', 'Moderate', 'High', 'Critical Hazard', 'Emergency']",
  "assigned_department": "Name of the government municipal department responsible",
  "hazard_rationale": "2-3 sentences explaining the danger to vehicles, pedestrians, or public health",
  "recommended_action": "Specific repair instructions (e.g. cold asphalt patching, 4-man sanitation team)",
  "estimated_fix_time_hours": integer number of hours expected to fix
}}
"""
    try:
        # Try modern google-genai SDK first
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image, prompt]
            )
            raw_text = response.text.strip()
        except ImportError:
            # Fallback to google-generativeai
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content([image, prompt])
            raw_text = response.text.strip()

        # Clean JSON formatting if wrapped in codeblocks
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        return json.loads(raw_text.strip()), None

    except Exception as e:
        return None, str(e)

# -------------------------------------------------------------
# Helper: Gemini AI Before-and-After Resolution Verification
# -------------------------------------------------------------
def verify_resolution_ai(before_img: Image.Image, after_img: Image.Image, issue_title: str, api_key: str):
    prompt = f"""
You are a Municipal Quality Assurance Auditor.
Original Problem: "{issue_title}"

You are provided with TWO images:
Image 1: The 'BEFORE' image showing the reported civic defect.
Image 2: The 'AFTER' image submitted by the municipal field crew claiming the issue is resolved.

Audit both images and verify if the reported issue has been genuinely and properly resolved.

Return STRICT JSON format ONLY:
{{
  "is_resolved": true or false,
  "confidence_percentage": integer 0-100,
  "audit_verdict": "Clear summary of whether the repair is acceptable, incomplete, or fraudulent",
  "quality_grade": "One of ['Excellent', 'Acceptable', 'Substandard', 'Incomplete', 'Rejected']"
}}
"""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[before_img, after_img, prompt]
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        return json.loads(raw_text.strip()), None
    except Exception as e:
        return None, str(e)


# -------------------------------------------------------------
# Sidebar Configuration
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.markdown("### ⚙️ System Configuration")
    
    # API Key retrieval (from env or input)
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=env_key,
        type="password",
        help="Get a free key at https://aistudio.google.com"
    )
    api_key = api_key_input.strip()

    if api_key:
        st.success("✅ AI Engine Connected", icon="🟢")
    else:
        st.warning("⚠️ Enter Gemini API Key to enable live vision analysis", icon="🔑")

    st.markdown("---")
    st.markdown("### 📍 Simulated City Location")
    city_zone = st.selectbox(
        "Target Municipal Zone",
        ["Central City (Delhi/CP)", "South Tech Corridor", "North Industrial District"]
    )
    
    st.markdown("---")
    st.markdown("### 🏆 Hackathon Quick Features")
    st.info("""
    - **Vision Triage**: Auto-detects defect & severity
    - **Smart Deduplication**: Merges reports within 75m
    - **AI Resolution Audit**: Before & after verification
    """)

# -------------------------------------------------------------
# Main Header
# -------------------------------------------------------------
st.markdown('<div class="main-header">🏛️ CivicLens AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous Civic Intelligence, Geo-Clustered Triage & Resolution Verification</div>', unsafe_allow_html=True)

# Tabs
tab_report, tab_admin, tab_audit = st.tabs([
    "📸 1. Citizen Report & AI Triage",
    "🗺️ 2. Municipal Command Center",
    "✅ 3. AI Resolution Auditor"
])

# =============================================================
# TAB 1: Citizen Report
# =============================================================
with tab_report:
    st.markdown("#### Report an Urban Infrastructure Issue")
    st.caption("Snap a photo of potholes, trash heaps, broken streetlights, or water leaks. AI handles classification and municipal routing.")

    col1, col2 = st.columns([1.1, 1], gap="medium")

    with col1:
        input_mode = st.radio("Choose Input Method:", ["📁 Upload Photo", "📸 Live Camera Snap"], horizontal=True)
        uploaded_image = None

        if input_mode == "📁 Upload Photo":
            uploaded_file = st.file_uploader("Select an image from your device", type=["jpg", "jpeg", "png", "webp"])
            if uploaded_file:
                uploaded_image = Image.open(uploaded_file)
        else:
            camera_file = st.camera_input("Take a photo of the civic issue")
            if camera_file:
                uploaded_image = Image.open(camera_file)

        if uploaded_image:
            st.image(uploaded_image, caption="Submitted Photo Preview", use_container_width=True)

    with col2:
        st.markdown("##### 📍 Location & Context")
        
        # Coordinates input (defaults to city center)
        geo_col1, geo_col2 = st.columns(2)
        with geo_col1:
            lat = st.number_input("Latitude", value=28.6315, format="%.5f")
        with geo_col2:
            lon = st.number_input("Longitude", value=77.2167, format="%.5f")

        address = st.text_input("Landmark / Street Address", value="Connaught Outer Circle, Near Metro Gate 3")
        citizen_note = st.text_area("Optional Notes / Voice Transcript", placeholder="e.g. Pothole appeared after heavy rain yesterday. Cars are swerving abruptly.")

        submit_btn = st.button("🚀 Analyze & Submit with AI", type="primary", use_container_width=True, disabled=(uploaded_image is None))

    # Processing AI Analysis
    if submit_btn and uploaded_image:
        if not api_key:
            st.error("Please provide a Gemini API Key in the left sidebar to analyze the image.")
        else:
            with st.spinner("🤖 CivicLens AI is inspecting infrastructure hazards and severity..."):
                result, error = analyze_civic_image(uploaded_image, api_key, citizen_note)

            if error:
                st.error(f"AI Analysis Failed: {error}")
            elif not result.get("is_civic_issue", False):
                st.warning(f"🚫 **Not a Civic Issue**: {result.get('rejection_reason', 'No municipal infrastructure hazard was identified in this image. Please upload a clear photo of public roads, sanitation, or utilities.')}")
            else:
                st.success("✅ Issue Successfully Classified & Verified!")
                
                # Check for Duplicates in proximity (within 75 meters)
                duplicate_found = False
                matched_ticket_id = None
                
                for existing in st.session_state.incidents:
                    dist = calculate_distance_meters(lat, lon, existing["latitude"], existing["longitude"])
                    if dist <= 75 and existing["category"] == result.get("category"):
                        duplicate_found = True
                        matched_ticket_id = existing["id"]
                        existing["upvotes"] += 1
                        # If multiple reports, elevate severity if moderate
                        if existing["severity_score"] < 5:
                            existing["severity_score"] += 1
                            existing["severity_label"] = "Escalated by Citizens"
                        break

                if duplicate_found:
                    st.markdown(f"""
                    <div class="duplicate-alert">
                        ⚡ <b>Smart Geo-Deduplication Triggered:</b><br/>
                        An active ticket (<b>{matched_ticket_id}</b>) already exists within 75 meters for this issue.<br/>
                        Rather than cluttering city staff with duplicate tickets, your report was <b>merged as an Urgency Upvote (+1)</b>. Priority elevated!
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Create new ticket
                    new_id = f"TKT-{len(st.session_state.incidents) + 1001}"
                    new_ticket = {
                        "id": new_id,
                        "title": result.get("title", "Reported Civic Hazard"),
                        "category": result.get("category", "General Hazard"),
                        "severity_score": int(result.get("severity_score", 3)),
                        "severity_label": result.get("severity_label", "Moderate"),
                        "department": result.get("assigned_department", "Public Works Department"),
                        "latitude": lat,
                        "longitude": lon,
                        "address": address,
                        "status": "Reported",
                        "upvotes": 1,
                        "reported_time": "Just now",
                        "rationale": result.get("hazard_rationale", "Under evaluation.")
                    }
                    st.session_state.incidents.insert(0, new_ticket)

                # Show Result Card
                st.markdown("### 📋 AI Triage Incident Sheet")
                sev_score = result.get("severity_score", 3)
                badge_class = f"severity-badge-{sev_score}"

                triage_col1, triage_col2, triage_col3 = st.columns(3)
                triage_col1.metric("Category", result.get("category"))
                triage_col2.metric("Hazard Severity", f"{sev_score}/5 ({result.get('severity_label')})")
                triage_col3.metric("Assigned Dept", result.get("assigned_department"))

                with st.expander("🔍 View AI Civil Engineering Analysis", expanded=True):
                    st.write(f"**Hazard Rationale:** {result.get('hazard_rationale')}")
                    st.write(f"**Recommended Repair Action:** {result.get('recommended_action')}")
                    st.write(f"**Target SLA Resolution:** Within {result.get('estimated_fix_time_hours', 24)} hours")

# =============================================================
# TAB 2: Municipal Command Center
# =============================================================
with tab_admin:
    st.markdown("#### 🏛️ Municipal Official Operations Dashboard")
    st.caption("City-wide visibility, AI-ranked priority triage queue, and field crew dispatch.")

    # KPI Bar
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_incidents = len(st.session_state.incidents)
    critical_count = sum(1 for inc in st.session_state.incidents if inc["severity_score"] >= 4)
    resolved_count = sum(1 for inc in st.session_state.incidents if inc["status"] == "Resolved")
    open_count = total_incidents - resolved_count

    kpi1.metric("Total Incident Pool", total_incidents)
    kpi2.metric("Critical Hazards (Lv 4-5)", critical_count, delta="High Priority", delta_color="inverse")
    kpi3.metric("Active Work Orders", open_count)
    kpi4.metric("Audited Resolutions", resolved_count, delta="+1 Today")

    st.markdown("---")

    # Map View
    st.markdown("##### 📍 Interactive Incident Heatmap")
    map_data = pd.DataFrame([
        {
            "lat": inc["latitude"],
            "lon": inc["longitude"],
            "title": inc["title"]
        } for inc in st.session_state.incidents
    ])
    st.map(map_data, zoom=13)

    st.markdown("---")
    st.markdown("##### 🚨 Priority Triage Queue (Ranked by AI Severity & Citizen Votes)")

    # Sort tickets by severity (desc) and upvotes (desc)
    sorted_incidents = sorted(
        st.session_state.incidents,
        key=lambda x: (x["severity_score"], x["upvotes"]),
        reverse=True
    )

    for inc in sorted_incidents:
        with st.container():
            card_col1, card_col2, card_col3 = st.columns([0.6, 2.5, 1])
            with card_col1:
                st.markdown(f"**{inc['id']}**")
                st.markdown(f"<span class='severity-badge-{inc['severity_score']}'>Lvl {inc['severity_score']} Severity</span>", unsafe_allow_html=True)
                st.caption(f"👥 {inc['upvotes']} Citizen Reports")
            with card_col2:
                st.markdown(f"**{inc['title']}**")
                st.markdown(f"📍 *{inc['address']}* | 🏛️ **{inc['department']}**")
                st.caption(f"⚠️ {inc['rationale']}")
            with card_col3:
                status_color = {"Reported": "red", "In Progress": "orange", "Dispatched": "blue", "Resolved": "green"}.get(inc['status'], "gray")
                st.markdown(f"Status: **:{status_color}[{inc['status']}]**")
                
                # Action Buttons
                btn_cols = st.columns(2)
                if inc['status'] != "Resolved":
                    if btn_cols[0].button("🚜 Dispatch", key=f"disp_{inc['id']}"):
                        inc['status'] = "Dispatched"
                        st.rerun()
                    if btn_cols[1].button("✅ Close", key=f"close_{inc['id']}"):
                        inc['status'] = "Resolved"
                        st.rerun()
            st.divider()

# =============================================================
# TAB 3: AI Resolution Auditor
# =============================================================
with tab_audit:
    st.markdown("#### 🔍 AI-Powered Before & After Verification Audit")
    st.caption("Prevent fraudulent ticket closures. When field staff mark an issue as fixed, CivicLens AI compares before/after photos.")

    audit_col1, audit_col2 = st.columns(2)

    with audit_col1:
        st.markdown("##### 1. Select Incident to Audit")
        selected_ticket = st.selectbox(
            "Select Open Ticket",
            options=[inc["id"] + " - " + inc["title"] for inc in st.session_state.incidents]
        )
        st.markdown("##### 2. Upload Original Before Image")
        before_file = st.file_uploader("Upload BEFORE Photo", type=["jpg", "png", "jpeg"], key="audit_before")

    with audit_col2:
        st.markdown("##### 3. Upload Field Crew 'Repaired' Photo")
        after_file = st.file_uploader("Upload AFTER Photo (Work Completion)", type=["jpg", "png", "jpeg"], key="audit_after")

    if before_file and after_file:
        col_prev1, col_prev2 = st.columns(2)
        before_img = Image.open(before_file)
        after_img = Image.open(after_file)
        col_prev1.image(before_img, caption="Before (Reported Defect)", use_container_width=True)
        col_prev2.image(after_img, caption="After (Claimed Fix)", use_container_width=True)

        if st.button("🔎 Run AI Verification Audit", type="primary", use_container_width=True):
            if not api_key:
                st.error("Please provide your Gemini API Key in the left sidebar.")
            else:
                with st.spinner("🤖 Comparing before and after structural features..."):
                    audit_res, audit_err = verify_resolution_ai(before_img, after_img, selected_ticket, api_key)
                
                if audit_err:
                    st.error(f"Audit failed: {audit_err}")
                else:
                    if audit_res.get("is_resolved", False):
                        st.success(f"🎉 **RESOLUTION VERIFIED ({audit_res.get('confidence_percentage')}% Confidence)**")
                        st.markdown(f"**Quality Grade:** {audit_res.get('quality_grade')}")
                        st.markdown(f"**Verdict:** {audit_res.get('audit_verdict')}")
                    else:
                        st.error(f"❌ **RESOLUTION REJECTED ({audit_res.get('confidence_percentage')}% Confidence)**")
                        st.markdown(f"**Quality Grade:** {audit_res.get('quality_grade')}")
                        st.markdown(f"**Audit Findings:** {audit_res.get('audit_verdict')}")
                        st.warning("Action: Ticket remains open. Escalation notice sent to municipal contractor.")

# Footer
st.markdown("---")
st.markdown(
    "<center><small>Built with ❤️ for Civic Hackathons • Powered by Google Gemini Multimodal AI & Streamlit</small></center>",
    unsafe_allow_html=True
)
