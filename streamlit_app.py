# streamlit_app.py
# RUN THIS FILE FROM: CRISIS_CHATBOT/rasa_project/
# Command: streamlit run streamlit_app.py

import streamlit as st
import requests
import time
import re
from datetime import datetime

# ---------------------------
# Rasa endpoints (local)
# ---------------------------
RASA_BASE_URL = "http://localhost:5005"
RASA_REST_WEBHOOK = f"{RASA_BASE_URL}/webhooks/rest/webhook"
RASA_STATUS_URL = f"{RASA_BASE_URL}/status"  # usually available
RASA_ROOT_URL = f"{RASA_BASE_URL}/"          # fallback ping

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="Crisis Response Assistant",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# HARD SAFETY CSS: prevent "all black" page
# (forces readable background even if theme / browser changes)
# ---------------------------
st.markdown(
    """
<style>
.stApp {
  background: #F8FAFC !important;
  color: #0F172A !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Custom CSS (improved button contrast + non-faded UI)
# ---------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --emergency-red: #DC2626;
  --emergency-red-dark: #B91C1C;
  --warning-orange: #EA580C;
  --safe-green: #059669;
  --info-blue: #0284C7;
  --info-blue-dark: #0369A1;
  --critical-dark: #7F1D1D;
  --bg-emergency: #FEF2F2;
  --bg-safe: #F0FDF4;
  --text-emergency: #991B1B;
  --border-emergency: #FCA5A5;
}

/* Reduce default Streamlit padding */
.main .block-container {
  padding-top: 1rem !important;
  padding-bottom: 1rem !important;
}

/* Header */
.main-header {
  background: linear-gradient(135deg, var(--emergency-red) 0%, var(--critical-dark) 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-radius: 0.75rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 10px 25px rgba(220, 38, 38, 0.2);
}
.emergency-title {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 2.25rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}
.emergency-subtitle {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 1.1rem;
  font-weight: 400;
  margin-top: 0.5rem;
  opacity: 0.95;
}

/* Alerts compact */
.stAlert {
  margin-top: 0 !important;
  margin-bottom: 0.5rem !important;
}

/* Chat container */
.chat-container {
  background: white;
  border-radius: 1rem;
  padding: 0.8rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  border: 2px solid #E5E7EB;
  height: 350px;
  overflow-y: auto;
  overflow-x: hidden;
  margin-bottom: 1rem;
  margin-top: 0 !important;
  scroll-behavior: smooth;
  position: relative;
}

/* Scrollbar */
.chat-container::-webkit-scrollbar { width: 6px; }
.chat-container::-webkit-scrollbar-track { background: transparent; }
.chat-container::-webkit-scrollbar-thumb {
  background: #CBD5E1; border-radius: 3px; transition: background 0.2s ease;
}
.chat-container::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* Messages */
.user-message, .bot-message { margin-bottom: 0.5rem; }

.user-message {
  background: var(--info-blue);
  color: white;
  padding: 1rem 1.25rem;
  border-radius: 1rem 1rem 0.25rem 1rem;
  margin: 0.75rem 0 0.75rem auto;
  max-width: 80%;
  font-family: 'IBM Plex Sans', sans-serif;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(2, 132, 199, 0.2);
}

.bot-message {
  background: #F8FAFC;
  color: #334155;
  padding: 1rem 1.25rem;
  border-radius: 1rem 1rem 1rem 0.25rem;
  margin: 0.75rem auto 0.75rem 0;
  max-width: 85%;
  border-left: 4px solid var(--info-blue);
  font-family: 'IBM Plex Sans', sans-serif;
  line-height: 1.6;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.emergency-message {
  background: var(--bg-emergency) !important;
  border-left: 4px solid var(--emergency-red) !important;
  color: var(--text-emergency) !important;
  font-weight: 700;
  animation: pulse-border 2s infinite;
}

.critical-message {
  background: linear-gradient(135deg, #DC2626 0%, #7F1D1D 100%) !important;
  color: white !important;
  border: none !important;
  font-weight: 800;
  box-shadow: 0 4px 20px rgba(220, 38, 38, 0.3) !important;
}

@keyframes pulse-border {
  0%, 100% { border-left-color: var(--emergency-red); }
  50% { border-left-color: var(--warning-orange); }
}

/* Risk panel */
.risk-panel {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  border: 2px solid #E5E7EB;
  box-shadow: 0 4px 15px rgba(0,0,0,0.06);
}
.risk-critical {
  background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
  border: 2px solid var(--emergency-red);
  box-shadow: 0 4px 20px rgba(220, 38, 38, 0.15);
}
.risk-high {
  background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
  border: 2px solid var(--warning-orange);
}
.risk-medium {
  background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
  border: 2px solid #D97706;
}
.risk-low {
  background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
  border: 2px solid var(--safe-green);
}

/* Emergency contacts */
.emergency-contacts {
  background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 1rem;
  margin-top: 1rem;
}
.contact-number {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

/* Status */
.status-connected { color: var(--safe-green); font-weight: 700; }
.status-disconnected { color: var(--emergency-red); font-weight: 800; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Inputs */
.stTextInput > div > div > input {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 1rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 2px solid #D1D5DB;
  transition: all 0.2s ease;
}
.stTextInput > div > div > input:focus {
  border-color: var(--info-blue);
  box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.12);
}

/* ----------------------------
   BUTTON FIX: prevent "faded" look
   Streamlit renders buttons with opacity/filters depending on theme.
   We force strong colors + clear hover/active states.
   ---------------------------- */
.stButton > button {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-weight: 800 !important;
  background: var(--info-blue) !important;
  color: #FFFFFF !important;
  border-radius: 0.6rem !important;
  border: 0 !important;
  padding: 0.75rem 1.25rem !important;
  line-height: 1.1 !important;
  opacity: 1 !important;
  filter: none !important;
  box-shadow: 0 6px 14px rgba(2, 132, 199, 0.22) !important;
  transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease !important;
}

.stButton > button:hover {
  background: var(--info-blue-dark) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 10px 18px rgba(2, 132, 199, 0.30) !important;
}

.stButton > button:active {
  transform: translateY(0px) !important;
  box-shadow: 0 6px 12px rgba(2, 132, 199, 0.22) !important;
}

/* Ensure disabled buttons still look visibly disabled but not "washed out" */
.stButton > button:disabled {
  background: #94A3B8 !important;
  color: #0F172A !important;
  opacity: 0.85 !important;
  box-shadow: none !important;
  transform: none !important;
}

/* Make chat_input send arrow / widget colors readable in dark/light */
div[data-testid="stChatInput"] textarea {
  font-family: 'IBM Plex Sans', sans-serif !important;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

@media (max-width: 768px) {
  .emergency-title { font-size: 1.75rem; }
  .user-message, .bot-message { max-width: 95%; }
  .main-header { padding: 1rem; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Session state init
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "risk_data" not in st.session_state:
    st.session_state.risk_data = None
if "crisis_active" not in st.session_state:
    st.session_state.crisis_active = False


# ---------------------------
# Helpers
# ---------------------------
def check_rasa_connection() -> bool:
    """Check if Rasa server is reachable."""
    try:
        r = requests.get(RASA_STATUS_URL, timeout=2)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    try:
        r = requests.get(RASA_ROOT_URL, timeout=2)
        return r.status_code in (200, 404)  # some rasa returns 404 on root
    except Exception:
        return False


def send_message_to_rasa(message: str):
    """Send a message to Rasa REST webhook and return list of bot responses."""
    clean_message = str(message).strip()
    if not clean_message:
        return [{"text": "Please enter a message."}]

    payload = {"sender": st.session_state.session_id, "message": clean_message}

    try:
        resp = requests.post(
            RASA_REST_WEBHOOK,
            json=payload,
            timeout=15,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code == 200:
            data = resp.json() or []
            valid = [r for r in data if r.get("text", "").strip()]
            return valid if valid else [{"text": "Response received but was empty."}]
        return [{"text": f"❌ Connection error (Status: {resp.status_code}). Check Rasa server."}]
    except requests.exceptions.Timeout:
        return [{"text": "⏱️ Request timeout. Please try again."}]
    except requests.exceptions.ConnectionError:
        return [{"text": "❌ Unable to connect to Rasa on port 5005. Start `rasa run` first."}]
    except Exception as e:
        return [{"text": f"❌ System error: {str(e)}"}]


def extract_risk_data(bot_response: dict):
    """Extract risk level + score from the bot response text."""
    text = bot_response.get("text", "") or ""
    t_upper = text.upper()

    if "RISK" not in t_upper:
        return None

    risk = {}
    if "RISK LEVEL: CRITICAL" in t_upper:
        risk["level"], risk["color"] = "CRITICAL", "critical"
    elif "RISK LEVEL: HIGH" in t_upper:
        risk["level"], risk["color"] = "HIGH", "high"
    elif "RISK LEVEL: MEDIUM" in t_upper:
        risk["level"], risk["color"] = "MEDIUM", "medium"
    elif "RISK LEVEL: LOW" in t_upper:
        risk["level"], risk["color"] = "LOW", "low"

    m = re.search(r"Risk Score:\s*(\d+)/100", text, re.IGNORECASE)
    if m:
        risk["score"] = m.group(1)

    return risk if risk else None


def get_current_context(messages):
    """Infer the current flow step from recent bot messages."""
    if not messages:
        return "initial"

    recent_bot = [m["text"].lower() for m in messages[-4:] if m["sender"] == "bot"]

    for bot_msg in reversed(recent_bot):
        if "which type of emergency" in bot_msg:
            return "crisis_selection"
        if "current location" in bot_msg or "city + nearby landmark" in bot_msg:
            return "location_input"
        if "how many people" in bot_msg:
            return "people_count"
        if "vulnerable people" in bot_msg or "children / elderly" in bot_msg:
            return "vulnerability_input"
        if "can you move to a safer place" in bot_msg:
            return "mobility_input"
        if "injured" in bot_msg and ("yes / no" in bot_msg):
            return "injury_input"
        if "what would you like to do next" in bot_msg:
            return "next_action"

    return "general"


def render_quick_buttons(context, rasa_connected):
    """Render quick reply buttons and return message text if clicked."""
    if not rasa_connected:
        return None

    if context == "crisis_selection":
        st.markdown("**🚨 Emergency Type:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("🏠 Earthquake", key="btn_earthquake"):
                return "/report_earthquake"
        with c2:
            if st.button("🌊 Flood", key="btn_flood"):
                return "/report_flood"
        with c3:
            if st.button("🔥 Fire", key="btn_fire"):
                return "/report_fire"
        with c4:
            if st.button("⚡ Power Out", key="btn_power"):
                return "/report_power_outage"

    elif context == "location_input":
        st.markdown("**📍 Common Locations:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("Berlin", key="btn_berlin"):
                return "Berlin, Germany"
        with c2:
            if st.button("Munich", key="btn_munich"):
                return "Munich, Germany"
        with c3:
            if st.button("Frankfurt", key="btn_frankfurt"):
                return "Frankfurt am Main, Germany"
        with c4:
            if st.button("Hamburg", key="btn_hamburg"):
                return "Hamburg, Germany"

    elif context == "people_count":
        st.markdown("**👥 How many people:**")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("1", key="btn_p1"):
                return "1"
        with c2:
            if st.button("2", key="btn_p2"):
                return "2"
        with c3:
            if st.button("3", key="btn_p3"):
                return "3"
        with c4:
            if st.button("4", key="btn_p4"):
                return "4"
        with c5:
            if st.button("5+", key="btn_p5"):
                return "5"

    elif context == "vulnerability_input":
        st.markdown("**⚠️ Vulnerable People:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("None", key="btn_vuln_none"):
                return "none"
        with c2:
            if st.button("Children", key="btn_vuln_child"):
                return "children"
        with c3:
            if st.button("Elderly", key="btn_vuln_elderly"):
                return "elderly"
        with c4:
            if st.button("Pregnant", key="btn_vuln_pregnant"):
                return "pregnant"

    elif context == "mobility_input":
        st.markdown("**🚶 Can you move safely?**")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Yes", key="btn_mob_yes"):
                return "yes"
        with c2:
            if st.button("No", key="btn_mob_no"):
                return "no"
        with c3:
            if st.button("Unsure", key="btn_mob_unsure"):
                return "unsure"

    elif context == "injury_input":
        st.markdown("**🩹 Anyone injured?**")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Yes", key="btn_inj_yes"):
                return "yes"
        with c2:
            if st.button("No", key="btn_inj_no"):
                return "no"
        with c3:
            if st.button("Unsure", key="btn_inj_unsure"):
                return "unsure"

    elif context == "next_action":
        st.markdown("**🎯 What to do next:**")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🆘 Emergency Services", key="btn_emergency_services"):
                return "/request_human"
        with c2:
            if st.button("📋 Safety Guide", key="btn_safety"):
                return "/more_steps_yes"
        with c3:
            if st.button("ℹ️ Info Only", key="btn_info"):
                return "/more_steps_no"

    else:
        st.markdown("**⚡ Quick Actions:**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚨 Start Emergency", key="btn_start_emergency"):
                return "emergency"
        with c2:
            if st.button("🔄 Restart Chat", key="btn_restart_general"):
                return "restart"

    return None


def format_message(message: dict, sender: str) -> str:
    """Return HTML for a chat bubble. Also formats safety protocols into readable lines."""
    text = message.get("text", "") or ""

    # Pretty formatting for "1) ... 2) ..." etc
    if "SAFETY PROTOCOL" in text.upper():
        text = re.sub(r"(\d+\))\s+", r"\1\n", text)
        text = re.sub(r"PROTOCOL:\s*", "PROTOCOL:\n", text, flags=re.IGNORECASE)

    if sender == "bot":
        if any(k in text.lower() for k in ["immediate danger", "critical", "call 112", "call 911"]):
            css_class = "bot-message critical-message"
        elif any(k in text.lower() for k in ["emergency", "dispatch", "connecting"]):
            css_class = "bot-message emergency-message"
        else:
            css_class = "bot-message"
    else:
        css_class = "user-message"

    safe_html = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")).replace("\n", "<br>")
    return f'<div class="{css_class}">{safe_html}</div>'


def auto_format_location(text: str, context: str) -> str:
    """Auto-format city-only inputs into 'City, Germany' to satisfy your location validator."""
    if context != "location_input":
        return text

    location = text.strip().lower()
    city_formats = {
        "berlin": "Berlin, Germany",
        "munich": "Munich, Germany",
        "muenchen": "Munich, Germany",
        "frankfurt": "Frankfurt am Main, Germany",
        "hamburg": "Hamburg, Germany",
        "cologne": "Cologne, Germany",
        "koeln": "Cologne, Germany",
        "stuttgart": "Stuttgart, Germany",
        "dusseldorf": "Düsseldorf, Germany",
        "dortmund": "Dortmund, Germany",
        "essen": "Essen, Germany",
        "leipzig": "Leipzig, Germany",
        "bremen": "Bremen, Germany",
        "dresden": "Dresden, Germany",
        "hannover": "Hannover, Germany",
        "nuremberg": "Nuremberg, Germany",
        "nurnberg": "Nuremberg, Germany",
    }

    if location in city_formats:
        return city_formats[location]

    for city, formatted in city_formats.items():
        if location.startswith(city) and len(location) > len(city):
            extra = location[len(city):].strip().strip(",").strip()
            if extra:
                city_name = formatted.split(",")[0]
                return f"{city_name}, {extra.title()}"

    if "," in text and len(text.strip()) > 8:
        parts = [p.strip().title() for p in text.split(",")]
        return ", ".join(parts)

    return text


def process_message_and_respond(message_text: str):
    """Add user message, call Rasa, append bot replies, update risk panel, rerun."""
    if not message_text or not str(message_text).strip():
        return

    context = get_current_context(st.session_state.messages)
    outgoing = auto_format_location(str(message_text).strip(), context)

    # Append user bubble (show what user typed, not necessarily the auto-formatted text)
    st.session_state.messages.append(
        {"text": str(message_text).strip(), "sender": "user", "timestamp": datetime.now()}
    )

    bot_responses = send_message_to_rasa(outgoing)

    for br in bot_responses:
        txt = br.get("text", "")
        if txt and txt.strip():
            st.session_state.messages.append(
                {"text": txt, "sender": "bot", "timestamp": datetime.now()}
            )

            risk_info = extract_risk_data(br)
            if risk_info:
                st.session_state.risk_data = risk_info
                st.session_state.crisis_active = True

    st.rerun()


# ---------------------------
# Main app
# ---------------------------
def main():
    # Header
    st.markdown(
        """
<div class="main-header">
  <h1 class="emergency-title">🚨 Crisis Response Assistant</h1>
  <p class="emergency-subtitle">Professional Emergency Assessment & Guidance System</p>
</div>
""",
        unsafe_allow_html=True,
    )

    rasa_connected = check_rasa_connection()

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.markdown("### 💬 Emergency Communication")

        status_class = "status-connected" if rasa_connected else "status-disconnected"
        status_text = "🟢 System Online" if rasa_connected else "🔴 System Offline"
        st.markdown(f'<p class="{status_class}">{status_text}</p>', unsafe_allow_html=True)

        if not st.session_state.messages:
            st.info(
                """
🚨 **Crisis Response Assistant**

I'm here to help assess emergency situations and provide professional guidance.

⚡ **For Immediate Emergencies:** 🇪🇺 Call 112 | 🇺🇸 Call 911

📋 **For Assessment:** Click **EMERGENCY** or describe your situation below.
"""
            )

        # Chat window
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.messages:
            sender = "user" if msg["sender"] == "user" else "bot"
            chat_html += format_message(msg, sender)
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # Auto-scroll to bottom
        if st.session_state.messages:
            st.markdown(
                """
<script>
setTimeout(function() {
  var containers = document.querySelectorAll('.chat-container');
  containers.forEach(function(c) { c.scrollTop = c.scrollHeight; });
}, 80);
</script>
""",
                unsafe_allow_html=True,
            )

        # Quick buttons
        context = get_current_context(st.session_state.messages)
        quick = render_quick_buttons(context, rasa_connected)
        if quick:
            process_message_and_respond(quick)

        placeholders = {
            "crisis_selection": "Or type: earthquake, flood, fire, power outage...",
            "location_input": "Type your location: e.g., 'Berlin, Alexanderplatz' or 'Munich, Main Street 123'...",
            "people_count": "Type number of people: e.g., 1, 2, 3...",
            "vulnerability_input": "Type vulnerabilities: e.g., '2 children', '1 elderly', 'none'...",
            "mobility_input": "Type: yes, no, or unsure...",
            "injury_input": "Type: yes, no, or unsure...", 
            "next_action": "Type: safety guide, emergency services, or info only...",
            "general": "Type your emergency situation or 'emergency' to begin...",
            "initial": "Type 'hi' or 'emergency' to begin...",
        }

        user_input = st.chat_input(
            placeholders.get(context, "Type your emergency message here...") if rasa_connected else "System offline",
            disabled=not rasa_connected,
            key="chat_input",
        )
        if user_input:
            process_message_and_respond(user_input)

        # Buttons row
        c_em, c_rs = st.columns(2)
        with c_em:
            if st.button(
                "🚨 EMERGENCY",
                disabled=not rasa_connected,
                help="Quick emergency assessment",
                key="main_emergency_btn",
            ):
                process_message_and_respond("emergency")

        with c_rs:
            if st.button(
                "🔄 Restart",
                disabled=not rasa_connected,
                help="Start new conversation",
                key="main_restart_btn",
            ):
                # Tell rasa + clear UI
                send_message_to_rasa("restart")
                st.session_state.messages = []
                st.session_state.risk_data = None
                st.session_state.crisis_active = False
                st.rerun()

    with col2:
        st.markdown("### 📊 Risk Assessment")

        if st.session_state.risk_data:
            risk = st.session_state.risk_data
            risk_class = f"risk-panel risk-{risk.get('color', 'low')}"
            risk_html = f"""
<div class="{risk_class}">
  <h3 style="margin-top: 0; font-family: 'IBM Plex Sans', sans-serif;">
    🎯 Risk Level: <strong>{risk.get('level', 'UNKNOWN')}</strong>
  </h3>
  <p style="font-size: 1.2rem; margin: 0.5rem 0;">
    📊 Score: <strong>{risk.get('score', 'N/A')}/100</strong>
  </p>
  <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #E5E7EB;">
    <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">
      Assessment updated: {datetime.now().strftime('%H:%M:%S')}
    </p>
  </div>
</div>
"""
            st.markdown(risk_html, unsafe_allow_html=True)
        else:
            st.markdown(
                """
<div class="risk-panel">
  <h3 style="margin-top: 0; color: #6B7280;">🎯 No Active Assessment</h3>
  <p style="color: #9CA3AF;">Risk assessment will appear here during emergency evaluation.</p>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown("### 📞 Emergency Contacts")
        st.markdown(
            """
<div class="emergency-contacts">
  <h4 style="margin-top: 0; font-family: 'IBM Plex Sans', sans-serif;">🚨 Immediate Emergency</h4>
  <div style="margin: 1rem 0;">
    <div class="contact-number">🇪🇺 Europe: 112</div>
    <div class="contact-number">🇺🇸 US/Canada: 911</div>
  </div>
  <p style="margin: 0; font-size: 0.9rem; opacity: 0.95;">
    Call immediately for life-threatening situations
  </p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("### ⚙️ System Status")
        status_html = f"""
<div class="risk-panel">
  <h4 style="margin-top: 0;">Connection Status</h4>
  <p class="{'status-connected' if rasa_connected else 'status-disconnected'}">
    {'🟢 Rasa Server: Online' if rasa_connected else '🔴 Rasa Server: Offline'}
  </p>
  <p style="font-size: 0.9rem; color: #6B7280; margin: 0.5rem 0;">
    Session: {st.session_state.session_id}
  </p>
  <p style="font-size: 0.9rem; color: #6B7280; margin: 0;">
    Messages: {len(st.session_state.messages)}
  </p>
</div>
"""
        st.markdown(status_html, unsafe_allow_html=True)

        with st.expander("📋 How to Use", expanded=False):
            st.markdown(
                """
**Quick Start**
1. 🚨 Click **EMERGENCY**
2. 💬 Or type your situation
3. 📊 Risk assessment appears automatically
4. 🔄 Use **Restart** for new conversation

**Crisis Types Supported**
- 🏠 Earthquake/Shaking
- 🌊 Flood/Water Rising
- 🔥 Fire/Smoke
- ⚡ Power Outage

**Important**
- If your bot uses custom actions, you must run the action server too:
  - `rasa run actions -p 5055`
- And run the main Rasa server:
  - `rasa run -m models --enable-api --cors "*" -p 5005`
"""
            )


if __name__ == "__main__":
    main()