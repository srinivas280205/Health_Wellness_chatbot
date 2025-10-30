import streamlit as st
import jwt, datetime, json, os, re
from hashlib import sha256
from collections import defaultdict, Counter
import pandas as pd
import plotly.express as px # Import Plotly for Pie Chart

# --- CONFIGURATION ---
SECRET_KEY = "mysecretkey"
DB_FILE = "users.json"
KB_FILE = "kb.json" # KB is now external
LOG_FILE = "chat_logs.json" # For feedback and analytics
ADMIN_EMAIL = "admin@app.com" # Designate your admin email

# Use wide layout for dashboard
st.set_page_config(page_title="Health Wellness Chatbot", layout="wide")

# --- Initialize Theme in Session State ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark" # Default to dark

# --- NEW THEME: Red / Dark Blue / Light Blue / White ---
# This CSS block now includes both Dark and a new Light theme.
# It also includes fixes for chat history alignment and feedback thumbs.
def get_theme_css(theme):
    if theme == "light":
        return """
        <style>
        /* --- LIGHT THEME --- */
        body { background: #E0E0E0; } /* Light Grey BG */
        .stApp { background-color: #E0E0E0; color: #001A3A; } /* Dark Blue Text */
        h1, h2, h3, h4, h5, h6, label { color: #003366 !important; } /* Mid Blue */
        h1 { color: #001A3A !important; text-align: center; }
        h2, h3 { border-bottom-color: #80BFFF; color: #001A3A !important; }
        .stSidebar { background-color: #FFFFFF !important; border-right: 1px solid #80BFFF; }
        .stSidebar .stButton>button { background-color: #E0E0E0; color: #003366; border: 1px solid #003366; }
        .stSidebar .stButton>button:hover { background-color: #003366; color: #FFFFFF; border-color: #003366; }
        .stTextInput>div>div>input, div[data-testid="stForm"] input[type="text"], div[data-testid="stForm"] input[type="password"], div[data-testid="stForm"] textarea {
            background-color: #FFFFFF; color: #001A3A; border: 1px solid #003366;
        }
        .stButton>button { background-color: #E0E0E0; color: #003366; border: 1px solid #003366; }
        .stButton>button:hover { background-color: #003366; color: #FFFFFF; border-color: #003366; }
        .stButton>button[kind="primary"], div[data-testid="stForm"] button.st-emotion-cache-19rxjzo { background-color: #003366 !important; color: #FFFFFF !important; border-color: #003366 !important; }
        button.st-emotion-cache-1uj9mc { background-color: #DC3545 !important; color: #FFFFFF !important; } /* Delete */
        .chat-bubble { border: 1px solid #003366; }
        .bot-msg { background-color: #FFFFFF; color: #001A3A; }
        .user-msg { background-color: #003366; color: #FFFFFF; }
        div[data-testid="stForm"] button.st-emotion-cache-uss2im { background-color: #FFFFFF !important; color: #003366 !important; border-color: #003366 !important; }
        div[data-testid="stForm"] button.st-emotion-cache-uss2im:hover { background-color: #003366 !important; color: #FFFFFF !important; }
        .status-online { background-color: #28a745 !important; } /* Green */
        .status-offline { background-color: #DC3545 !important; } /* Red */
        div[data-testid="stHorizontalBlock"] .stButton>button { background-color: #FFFFFF; color: #003366; border: 1px solid #003366; }
        div[data-testid="stHorizontalBlock"] .stButton>button:hover { background-color: #003366; color: #FFFFFF; }
        div[data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #003366; }
        div[data-testid="stMetric"] label { color: #003366 !important; }
        div[data-testid="stMetric"] div.st-emotion-cache-1gfitym { color: #001A3A !important; }
        div.admin-list-container { background-color: #FFFFFF; border: 1px solid #003366; color: #001A3A; }
        div.admin-list-container li { border-bottom-color: #E0E0E0; color: #001A3A; }
        div[data-testid="stJson"] pre code { color: #001A3A !important; } /* Dark text for JSON */
        </style>
        """
    else: # Dark Theme
        return """
        <style>
        /* --- DARK THEME (BMW Inspired) --- */
        body { background: #001A3A; } /* Dark Blue */
        .stApp { background-color: #001A3A; color: #FFFFFF; } /* White Text */
        h1, h2, h3, h4, h5, h6, label { color: #80BFFF !important; } /* Light Blue Accent */
        h1 { color: #FFFFFF !important; text-align: center; }
        h2, h3 { border-bottom: 2px solid #003366; padding-bottom: 5px; color: #FFFFFF !important; margin-top: 1.5rem; }
        .stSidebar { background-color: #001024 !important; border-right: 1px solid #003366; } /* Even Darker Blue */
        .stSidebar .stButton>button {
            background-color: #003366; color: #FFFFFF; border: 1px solid #80BFFF;
            width: 100%; margin-bottom: 5px; border-radius: 4px;
            /* CHAT HISTORY ALIGNMENT FIX */
            text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .stSidebar .stButton>button:hover { background-color: #80BFFF; color: #001A3A; border-color: #FFFFFF; }
        /* Logout Button */
        .stSidebar .stButton>button.st-emotion-cache-q91vdp { /* Specific selector for logout */
            background-color: #DC3545; border-color: #DC3545; color: #FFFFFF;
        }
        .stSidebar .stButton>button.st-emotion-cache-q91vdp:hover {
            background-color: #F87979; border-color: #F87979;
        }

        .stTextInput>div>div>input, div[data-testid="stForm"] input[type="text"], div[data-testid="stForm"] input[type="password"], div[data-testid="stForm"] textarea {
            background-color: #003366; color: #FFFFFF; border: 1px solid #80BFFF;
            border-radius: 4px; padding: 10px;
        }
        div[data-testid="stForm"] div[data-testid="stTextInput"] > div:nth-child(2) > div:nth-child(1) > input { height: 48px; }
        .stTextInput>div>div>input:focus, div[data-testid="stForm"] input[type="text"]:focus,
        div[data-testid="stForm"] input[type="password"]:focus, div[data-testid="stForm"] textarea:focus {
            border-color: #FFFFFF; box-shadow: 0 0 0 1px #FFFFFF;
        }
        .stButton>button { background-color: #003366; color: #FFFFFF; font-weight: bold; border-radius: 4px; border: 1px solid #80BFFF; padding: 8px 18px; height: 38px; line-height: 20px; }
        .stButton>button:hover { background-color: #80BFFF; color: #001A3A; border-color: #FFFFFF; }
        .stButton>button[kind="primary"], div[data-testid="stForm"] button.st-emotion-cache-19rxjzo { /* Save buttons */
             background-color: #80BFFF !important; color: #001A3A !important; border: 1px solid #80BFFF !important;
        }
        .stButton>button[kind="primary"]:hover, div[data-testid="stForm"] button.st-emotion-cache-19rxjzo:hover {
              background-color: #AAD4FF !important; border-color: #FFFFFF !important; color: #001A3A !important;
        }
        button.st-emotion-cache-1uj9mc { background-color: #DC3545 !important; color: #FFFFFF !important; border: none !important; } /* Delete */
        button.st-emotion-cache-1uj9mc:hover { background-color: #F87979 !important; }
        .chat-bubble { padding: 10px 15px; margin: 8px 0; border-radius: 15px; max-width: 80%; word-wrap: break-word; font-size: 16px; line-height: 1.5; }
        .bot-msg { background-color: #003366; color: #FFFFFF; border-top-left-radius: 0; float: left; clear: both; }
        .user-msg { background-color: #80BFFF; color: #001A3A; border-top-right-radius: 0; float: right; clear: both; }
        div[data-testid="stForm"] button.st-emotion-cache-uss2im { /* Chat Send */
            background-color: #003366 !important; color: #FFFFFF !important; height: 48px !important; width: 100% !important;
            border-radius: 4px !important; border: 1px solid #80BFFF !important; font-size: 20px !important; padding: 0 !important; margin-top: -1px;
        }
        div[data-testid="stForm"] button.st-emotion-cache-uss2im:hover { background-color: #80BFFF !important; border-color: #FFFFFF !important; color: #001A3A !important; }
        div[data-testid="column"] { padding-top: 0 !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        div[data-testid="stVerticalBlock"] > div { margin-bottom: 1rem; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status-online { background-color: #80BFFF !important; } /* Light Blue online */
        .status-offline { background-color: #DC3545 !important; } /* Red offline */
        .bot-header { font-size: 1.5rem; font-weight: 600; color: #FFFFFF !important; display: flex; align-items: center; margin-bottom: 1rem; }
        div[data-testid="stHorizontalBlock"] .stButton>button { background-color: #003366; color: #FFFFFF; border: 1px solid #80BFFF; height: 40px; font-weight: normal; width: 100%; }
        div[data-testid="stHorizontalBlock"] .stButton>button:hover { background-color: #80BFFF; color: #001A3A; border: 1px solid #FFFFFF; }
        div.feedback-button-container { margin-top: -10px; margin-left: 10px; margin-bottom: 10px; float: left; clear: both; }
        div.feedback-button-container .stButton>button { background-color: transparent; border: none; height: 30px; width: 30px; font-weight: bold; padding: 0; font-size: 1.3em; }
        div.feedback-button-container .stButton:nth-child(1)>button { color: #28a745 !important; } /* Green Thumb */
        div.feedback-button-container .stButton:nth-child(1)>button:hover { color: #34D399 !important; }
        div.feedback-button-container .stButton:nth-child(2)>button { color: #DC3545 !important; } /* Red Thumb */
        div.feedback-button-container .stButton:nth-child(2)>button:hover { color: #F87979 !important; }
        span.feedback-received { color: #80BFFF; font-size: 0.9em; float: left; clear: both; margin-left: 10px; margin-top: 5px; } /* Accent color */
        div[data-testid="stMetric"] { background-color: #003366; border-radius: 8px; padding: 1rem; border: 1px solid #80BFFF; }
        div[data-testid="stMetric"] label { color: #AAAAAA !important; }
        div[data-testid="stMetric"] div.st-emotion-cache-1gfitym { color: #FFFFFF !important; }
        div[data-testid="stMetric"] div.st-emotion-cache-1gfitym > div { color: #FFFFFF !important; }
        div.admin-list-container { background-color: #003366; padding: 1rem; border-radius: 8px; border: 1px solid #80BFFF; max-height: 250px; overflow-y: auto; }
        div.admin-list-container h3 { margin-top: 0; margin-bottom: 0.5rem; color: #FFFFFF !important; }
        div.admin-list-container ul { list-style: none; padding: 0; margin: 0; }
        div.admin-list-container li { padding: 0.3rem 0; border-bottom: 1px solid #001A3A; display: flex; justify-content: space-between; align-items: center; color: #FFFFFF; }
        div.admin-list-container li:last-child { border-bottom: none; }
        div.admin-list-container span.feedback-icon-up { color: #28a745; font-weight: bold; } /* Green thumb */
        div.admin-list-container span.feedback-icon-down { color: #DC3545; font-weight: bold; } /* Red thumb */
        div.admin-list-container button { margin-top: 10px; }
        .plotly-graph-div { background: transparent !important; }
        div[data-testid="stJson"] pre code { color: #FFFFFF !important; }
        /* Tab Styles */
        div[data-testid="stTabs"] { background-color: #001A3A; border-radius: 8px; padding: 5px; }
        .stTabs [data-baseweb="tab-list"] { background-color: #001A3A; } /* Dark blue tab header */
        .stTabs [data-baseweb="tab"] { background-color: #003366; color: #FFFFFF; border-radius: 4px; margin-right: 5px; }
        .stTabs [data-baseweb="tab--selected"] { background-color: #80BFFF; color: #001A3A; font-weight: bold; }
        div[data-testid="stExpander"] div[role="button"] { padding: 0.5rem; } /* Tighter expander */
        hr { border-top: 1px solid #003366; margin: 1rem 0; } /* Divider color */
        </style>
        """
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


# --- PROFILE SCHEMA (Unchanged) ---
PROFILE_SCHEMA = { "name": {"type": "text", "label": "Full Name", "default": ""}, "age": {"type": "select", "label": "Age Group", "options": ["18–25", "25–35", "35–45", "45+"], "default": "18–25"}, "gender": {"type": "select", "label": "Gender", "options": ["Male", "Female", "Other"], "default": "Male"}, "language": {"type": "select", "label": "Preferred Language", "options": ["English", "Hindi"], "default": "English"}, }

# --- KNOWLEDGE BASE (External) ---
@st.cache_data(ttl=600) # Cache KB for 10 minutes
def load_kb():
    if not os.path.exists(KB_FILE): st.error(f"{KB_FILE} not found!"); return {}
    try:
        with open(KB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e: st.error(f"Error loading KB: {e}."); return {}
@st.cache_data
def build_entity_map(kb_data):
    entity_map = defaultdict(list)
    if kb_data:
        for cond, data in kb_data.items():
            for sym in data.get("symptoms", []): entity_map["symptom"].append(sym)
            for part in data.get("body_parts", []): entity_map["body_part"].append(part)
    return entity_map
KB = load_kb()
ENTITY_MAP = build_entity_map(KB)
if not KB: st.warning("Knowledge Base empty/not loaded.")

# --- LOGGING & ANALYTICS ---
def load_logs():
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0: return []
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError: st.warning(f"Bad {LOG_FILE}. Starting empty."); return []
def save_logs(logs):
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f: json.dump(logs, f, indent=4, ensure_ascii=False)
    except Exception as e: st.error(f"Failed to save logs: {e}")
def log_chat(email, query, response, resp_id):
    logs = load_logs(); main_resp = response.split("<br><br>---<br>")[0]
    logs.append({"id": resp_id, "email": email, "query": query, "response": main_resp, "feedback": "none", "comment": "", "timestamp": datetime.datetime.utcnow().isoformat()})
    save_logs(logs)
def log_feedback(resp_id, fb_type, comment=""):
    logs = load_logs(); found = False
    for log in logs:
        if log.get("id") == resp_id: log["feedback"] = fb_type; log["comment"] = comment if comment else log["comment"]; found = True; break
    if found: save_logs(logs)
    else: st.error("Error logging feedback: Log ID not found.")
def get_frequent_keywords(email):
    logs = load_logs(); queries = [log['query'] for log in logs if log['email'] == email]
    defaults = ["🤒 Headache", "🤢 Flu", "🔥 Burns", "😴 Sleep", "🧘 Anxiety"]
    if not queries: return defaults
    words = [w for q in queries for w in re.findall(r'\b\w{4,}\b', q.lower())]
    stops = {"what", "when", "tell", "about", "have", "with", "from", "mein", "kya", "kaise", "this", "that"}
    filtered = [w for w in words if w not in stops]
    if not filtered: return defaults
    top_5 = [w for w, c in Counter(filtered).most_common(5)]
    emojis = {"headache": "🤒", "flu": "🤢", "burns": "🔥", "sleep": "😴", "anxiety": "🧘", "cough": "💨", "cold": "🤧", "fever": "🌡️", "pain": "💥", "cut": "🩹"}
    formatted = [f"{emojis.get(w, '🔍')} {w.title()}" for w in top_5]
    if len(formatted) < 5:
        existing = {kw.split(" ", 1)[-1].lower() for kw in formatted}
        needed = 5 - len(formatted); added = 0
        for d_kw in defaults:
             if added >= needed: break
             if d_kw.split(" ", 1)[-1].lower() not in existing: formatted.append(d_kw); added += 1
    return formatted[:5]

# --- AUTH & USER HELPERS ---
@st.cache_resource(ttl=600) # Cache user data for 10 mins
def load_users():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        print(f"User file {DB_FILE} not found. Creating admin."); admin_hash = hash_pw("admin123"); prof = {k: v["default"] for k, v in PROFILE_SCHEMA.items()}
        users = {ADMIN_EMAIL: {"password": admin_hash, "profile": prof}}; save_users(users); return users
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except json.JSONDecodeError: st.error("User DB error."); return {}
def save_users(users):
    try:
        with open(DB_FILE, 'w') as f: json.dump(users, f, indent=4)
        load_users.clear() # Clear cache after saving
    except Exception as e: st.error(f"Failed save users: {e}")
def hash_pw(pw): return sha256(pw.encode()).hexdigest()
def create_token(email): payload = {"email": email,"exp": datetime.datetime.utcnow()+datetime.timedelta(hours=8)}; return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
def get_user_from_token():
    token = st.session_state.get("token")
    if not token: return None
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": True}); return decoded["email"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        st.error(f"Session Error: {e}. Please log in."); keys = list(st.session_state.keys())
        [st.session_state.pop(k, None) for k in keys]; st.rerun(); return None

# --- NLU & RESPONSE LOGIC ---
def extract_entities(text, msg):
    text_lower = text.lower(); extracted = {"symptom": set(), "body_part": set()}
    global ENTITY_MAP;
    if not ENTITY_MAP: return extracted
    for etype, kwds in ENTITY_MAP.items():
        for kwd in kwds:
            kp = False
            if kwd.isascii():
                if re.search(r'\b' + re.escape(kwd) + r'\b', text_lower): kp = True
            elif kwd in msg: kp = True
            if kp: extracted[etype].add(kwd)
    if not extracted["body_part"]:
        for sym in extracted["symptom"]:
            if sym in ["fever", "dehydration", "insomnia", "bukhar", "paani ki kami", "anidra", "बुखार", "पानी की कमी", "अनिद्रा", "sleep", "नींद", "anxiety", "चिंता", "तनाव"]:
                extracted["body_part"].add("body"); break
    return extracted
def generate_disclaimer(name_en, name_hi, is_hindi):
    hr = "border-top: 1px dashed #80BFFF; margin: 10px 0;"
    note_hi = f"Note: यह **{name_hi}** जानकारी केवल बुनियादी मार्गदर्शन के लिए है।<br>यदि लक्षण बने रहते हैं या बिगड़ जाते हैं तो डॉक्टर से सलाह लें."
    note_en = f"Note: This **{name_en.title().replace('/', ' or ')}** information is for basic guidance only.<br>Consult a healthcare provider if symptoms persist or worsen."
    return f"<hr style='{hr}'>{note_hi}" if is_hindi else f"<hr style='{hr}'>{note_en}"
def get_bot_response(msg):
    global KB, ENTITY_MAP
    KB = load_kb(); # Refresh KB
    if not KB: return "🤖 Sorry, KB unavailable."
    ENTITY_MAP = build_entity_map(KB) # Rebuild map
    msg_lower = msg.lower()
    HINDI_KW = ["namaste", "hindi", "sir dard", "bukhar", "khansi", "pet", "dard", "moch", "matli", "ulti", "jaln", "kamar", "peeth", "jukaam", "sardi", "gala", "khujli", "dast", "kabz", "pyas", "chot", "sujan", "daant", "tanaav", "chinta", "नमस्ते", "नमस्कार", "हिंदी", "सिरदर्द", "माथा दर्द", "सिर में दर्द", "सिर", "गर्दन", "माइग्रेन", "तेज सिरदर्द", "आंख", "बुखार", "तापमान", "ज्वर", "तेज़ बुखार", "शरीर", "खांसी", "सूखी खांसी", "गीली खांसी", "सर्दी", "जुकाम", "नाक बहना", "बंद नाक", "गला", "सीना", "नाक", "गले में दर्द", "खराश", "गला खराब", "एलर्जी", "छींक", "खुजली", "आंख में खुजली", "त्वचा", "मतली", "उल्टी", "पेट खराब", "जी मचलना", "पेट दर्द", "पेट", "दस्त", "पेट में मरोड़", "लूज मोशन", "कब्ज", "पेट साफ नहीं होना", "प्यास", "पानी की कमी", "सूखा मुंह", "चक्कर", "मुंह", "धूप से जलन", "जलना", "छाले", "लाल त्वचा", "चोट", "ज़ख्म", "खून बहना", "कटना", "उंगली", "हाथ", "पैर", "सिर पर चोट", "चक्कर आना", "दर्द", "मोच", "सूजन", "टखना", "घुटना", "कलाई", "जोड़", "मांसपेशी", "कमर दर्द", "पीठ में दर्द", "कमर", "पीठ", "नींद नहीं आना", "अनिद्रा", "थकान", "दांत दर्द", "मसूड़ों में दर्द", "दांत", "मसूड़ा", "चकत्ते", "लाल दाने", "कीड़े ने काटा", "मच्छर काटा", "डंक", "कान", "फ्लू", "नींद", "चिंता", "तनाव"]
    is_hindi = any(h in msg_lower for h in HINDI_KW if h.isascii()) or any(h in msg for h in HINDI_KW if not h.isascii())
    greetings = {"नमस्ते", "नमस्कार", "hi", "hello", "hey", "namaste", "start"}; farewells = {"bye", "goodbye", "thanks", "thank you", "dhanyawad", "shukriya", "धन्यवाद", "शुक्रिया"}
    if msg_lower in greetings or any(g in msg for g in greetings if not g.isascii()): return "🤖 नमस्ते! मैं आपका कल्याण सहायक हूँ।" if is_hindi else "🤖 Hello! I’m your Wellness Assistant."
    if msg_lower in farewells or any(f in msg for f in farewells if not f.isascii()): return "🤖 आपका स्वागत है! सुरक्षित रहें!" if is_hindi else "🤖 You're welcome! Stay safe!"
    not_found = "🤖 क्षमा करें, मेरे पास इस बारे में जानकारी नहीं है..." if is_hindi else "🤖 Sorry, I don't have information on that..."
    res_key = "hindi_responses" if is_hindi else "responses"
    entities = extract_entities(msg_lower, msg); found = entities["symptom"].union(entities["body_part"])
    match, score = None, 0
    q_map = {"burns": "sunburn/burn", "sleep": "insomnia", "anxiety": "anxiety", "flu": "cough/cold"}; mapped_key = q_map.get(msg_lower)
    if mapped_key and mapped_key in KB: match, score = mapped_key, 100
    else:
        for c, d in KB.items():
            kwds = set(d.get("symptoms", []) + d.get("body_parts", [])); s = len(found.intersection(kwds))
            if s > score: score, match = s, c
            elif s == score and match:
                if c in ["migraine", "minor head injury"] and match in ["headache", "fever"]: match = c
                elif len(c) > len(match) and match not in ["migraine", "minor head injury"]: match = c
    if match and res_key in KB[match]:
        s_list=list(entities['symptom']); p_list=list(entities['body_part'])
        nlu_p = f"Part(s): **{', '.join(p for p in p_list if p != 'body')}**" if p_list and p_list != ["body"] else "Part(s): *None*"
        nlu_s = f"Symptom(s): **{', '.join(s_list)}**" if s_list else "Symptom(s): *None*"
        nlu = f"<br><br>---<br>**🔍 Analysis:**<br>{nlu_s}<br>{nlu_p}"
        r_list = KB[match].get(res_key, []); r_txt = r_list[0] if r_list else not_found
        disc = generate_disclaimer(KB[match]["condition_name_en"], KB[match]["condition_name_hi"], is_hindi)
        return r_txt + nlu + disc
    return not_found

# --- VALIDATION ---
def validate_email(e): return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e)
def validate_password(p): return len(p) >= 6

# ==================================================================
# --- ADMIN DASHBOARD FUNCTION (FIXED & IMPROVED) ---
# ==================================================================
def show_main_dashboard_layout():
    """Displays the main dashboard with metrics and charts."""
    logs_data = load_logs()
    df = pd.DataFrame(logs_data) if logs_data else pd.DataFrame()
    if not df.empty and 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)
        except Exception: df = pd.DataFrame()

    # --- Row 1: Metrics & KB ---
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📊 Usage Statistics")
        global KB # Access global KB
        t_queries = len(df); f_counts = df['feedback'].value_counts() if 'feedback' in df.columns else pd.Series()
        pos_fb = f_counts.get('up', 0); neg_fb = f_counts.get('down', 0); t_rated = pos_fb + neg_fb
        fb_score = (pos_fb / t_rated * 100) if t_rated > 0 else 0
        t_users = len(load_users()); t_kb = len(KB)
        m_col1, m_col2 = st.columns(2)
        with m_col1: st.metric("Total Users", t_users); st.metric("Health Topics (KB)", t_kb)
        with m_col2: st.metric("Queries Handled", t_queries); st.metric("Positive Feedback", f"{fb_score:.1f}%", f"{t_rated} rated")
    with col2:
        st.subheader("📚 Knowledge Base"); st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
        if not KB: st.caption("KB empty.")
        else:
            items = list(KB.keys()); st.markdown("<ul>", unsafe_allow_html=True)
            for k in items[:6]: name = KB.get(k, {}).get('condition_name_en', k); st.markdown(f"<li>{name}</li>", unsafe_allow_html=True)
            if len(items) > 6: st.markdown("<li>...</li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("Manage KB", key="goto_kb", use_container_width=True): st.session_state.admin_tab = "KB"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Row 2: Trends & Feedback ---
    col3, col4 = st.columns([2, 1])
    with col3:
        st.subheader("📈 Query Trends");
        if df.empty or 'timestamp' not in df.columns or df['timestamp'].isnull().all(): st.caption("No trend data.")
        else:
            try:
                 trends = df.set_index('timestamp').resample('D')['query'].count()
                 if not trends.empty: st.line_chart(trends, color="#80BFFF") # Light Blue line
                 else: st.caption("No queries logged.")
            except Exception as e: st.caption(f"Chart error: {e}")
    with col4:
        st.subheader("💬 Recent Feedback"); st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
        if df.empty or 'feedback' not in df.columns: st.caption("No feedback.")
        else:
            fb_df = df[df['feedback'] != 'none'].sort_values('timestamp', ascending=False).head(5)
            if fb_df.empty: st.caption("No rated feedback.")
            else:
                st.markdown("<ul>", unsafe_allow_html=True)
                for i, r in fb_df.iterrows():
                    icon = "👍" if r['feedback'] == 'up' else "👎"; cls = "up" if r['feedback'] == 'up' else "down"
                    q = (r['query'][:30] + '...') if len(r['query']) > 30 else r['query']
                    st.markdown(f"<li><span>'{q}'</span> <span class='feedback-icon-{cls}'>{icon}</span></li>", unsafe_allow_html=True)
                st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("Manage Feedback", key="goto_fb", use_container_width=True): st.session_state.admin_tab = "FB"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Row 3: Categories (Pie) & Deployment ---
    col5, col6 = st.columns([2, 1])
    with col5:
        st.subheader("🥧 Query Categories")
        if df.empty or 'query' not in df.columns: st.caption("No category data.")
        else:
            # --- CORRECTED FUNCTION DEFINITION ---
            def cat_q(q):
                q = str(q).lower()
                if any(s in q for s in ["headache", "fever", "cough", "cold", "pain", "sore"]):
                    return "Symptoms"
                if any(s in q for s in ["cut", "burn", "sprain", "injury", "bite"]):
                    return "First Aid"
                if any(s in q for s in ["sleep", "anxiety", "stress", "diet", "hydrate", "constipation"]):
                    return "Wellness"
                return "Other"
            # --- END CORRECTION ---

            df['category'] = df['query'].apply(cat_q) if 'query' in df.columns else 'Other'; cat_counts = df['category'].value_counts()
            if not cat_counts.empty:
                 pie_df = cat_counts.reset_index(); pie_df.columns = ['category', 'count']
                 fig = px.pie(pie_df, names='category', values='count', hole=0.4,
                              color_discrete_sequence=px.colors.qualitative.Pastel) # Multi-colored
                 fig.update_layout(legend_title_text='Categories', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FFFFFF", showlegend=False)
                 fig.update_traces(textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#001A3A', width=2)))
                 st.plotly_chart(fig, use_container_width=True)
            else: st.caption("Could not categorize.")
    with col6:
        st.subheader("🚀 Deployment Status"); st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
        st.markdown("<ul><li><span style='color:#28a745;'>✅</span> Docker ready</li><li><span style='color:#28a745;'>✅</span> Cloud ready</li><li><span style='color:#FFA500;'>⏳</span> Docs pending</li></ul>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_kb_management():
    st.subheader("✍️ Knowledge Base Management")
    if st.button("Back to Dashboard", key="back_from_kb"): st.session_state.admin_tab = None; st.rerun()
    with st.expander("Edit Knowledge Base (JSON)", expanded=True):
        kb_edit = load_kb(); kb_json = json.dumps(kb_edit, indent=4, ensure_ascii=False)
        new_json = st.text_area("KB JSON", value=kb_json, height=600, key="kb_edit")
        col_k1, col_k2 = st.columns([1,5])
        with col_k1:
            if st.button("Save KB", type="primary", key="save_kb", use_container_width=True):
                try:
                    new_kb = json.loads(new_json)
                    if save_kb(new_kb):
                        global KB, ENTITY_MAP; KB = new_kb; ENTITY_MAP = defaultdict(list)
                        for c, d in KB.items():
                            for s in d.get("symptoms", []): ENTITY_MAP["symptom"].append(s)
                            for p in d.get("body_parts", []): ENTITY_MAP["body_part"].append(p)
                        st.success("KB updated!"); st.session_state.admin_tab = None; st.rerun()
                    else: st.error("Failed save KB.")
                except Exception as e: st.error(f"Error: {e}")
        with col_k2: st.empty() # Placeholder

def show_feedback_management():
    st.subheader("💬 All Feedback & Comments")
    if st.button("Back to Dashboard", key="back_from_fb"): st.session_state.admin_tab = None; st.rerun()
    logs_data = load_logs(); df = pd.DataFrame(logs_data) if logs_data else pd.DataFrame()
    if df.empty or 'feedback' not in df.columns: st.warning("No logs.")
    else:
        fb_all = df[df['feedback'] != 'none'][['timestamp', 'email', 'query', 'feedback', 'comment']].sort_values('timestamp', ascending=False)
        if fb_all.empty: st.info("No rated feedback.")
        else: st.dataframe(fb_all, use_container_width=True, column_config={"timestamp": st.column_config.DatetimeColumn("Time", format="YY-MM-DD HH:mm"), "email":"User", "query":"Query", "feedback":"Rating", "comment":"Comment"})

def show_admin_dashboard():
    st.header("✨ Admin Dashboard")
    admin_tab = st.session_state.get("admin_tab", None)

    if admin_tab == "KB":
        show_kb_management()
    elif admin_tab == "FB":
        show_feedback_management()
    else:
        # Show main dashboard layout by default
        show_main_dashboard_layout()

# ==================================================================
# --- MAIN APP LOGIC ---
# ==================================================================
st.title("🪄 Health & Wellness Assistant")
users = load_users(); user_email = get_user_from_token()
keys_to_init = {"chat_archive": [], "show_admin": False, "feedback_submitted": {}, "admin_tab": None}
for key, default_val in keys_to_init.items():
    if key not in st.session_state: st.session_state[key] = default_val

# --- LOGGED-IN VIEW ---
if user_email:
    with st.sidebar:
        st.header("Controls & History")
        if user_email == ADMIN_EMAIL:
            st.markdown("---"); st.subheader("👑 Admin")
            if st.button("Admin Dashboard"): st.session_state.show_admin=True; st.session_state.admin_tab=None; st.rerun()
            st.markdown("---")
        is_online = st.toggle("Bot Status", value=True, key="bot_status")
        if st.button("➕ New Chat", key="new_chat"):
            if "chat_history" in st.session_state and len(st.session_state.chat_history)>1: st.session_state.chat_archive.insert(0, st.session_state.chat_history)
            st.session_state.pop("chat_history", None); st.session_state.pop("feedback_submitted", None); st.rerun()
        st.markdown("---"); st.subheader("Chat History")
        if st.session_state.chat_archive:
            for i, chat in enumerate(st.session_state.chat_archive[:10]):
                first = next((m for r, m in chat if r == 'user'), "Chat"); title = first[:50] + ("..." if len(first)>50 else "")
                if st.button(f"📜 {title}", key=f"chat_{i}"): st.session_state.chat_history=chat; st.session_state.feedback_submitted={}; st.session_state.show_admin=False; st.rerun()
        else: st.caption("No past chats.")
        st.markdown("---")
        # Red Logout Button
        if st.button(" Logout", key="logout", type="primary"):
             keys = list(st.session_state.keys()); [st.session_state.pop(k, None) for k in keys]; st.success("Logged out."); st.rerun()
        # Custom CSS for red logout button
        st.markdown("""<style> button.st-emotion-cache-q91vdp { background-color: #DC3545; border-color: #DC3545; }
                           button.st-emotion-cache-q91vdp:hover { background-color: #F87979; border-color: #F87979; } </style>""", unsafe_allow_html=True)


    # --- Main Area ---
    if st.session_state.get("show_admin", False) and user_email == ADMIN_EMAIL: show_admin_dashboard()
    else: # --- Standard Chat Interface ---
        if not st.session_state.get("show_admin", False): st.success(f"✅ Logged in as {user_email}")
        profile = users.get(user_email, {}).get("profile", {})

        # --- NEW: Tabbed Profile Section ---
        st.divider()
        with st.expander("👤 User Profile & Settings", expanded=False):
             prof_tab1, prof_tab2 = st.tabs(["Update Profile", "⚙️ Settings"])
             with prof_tab1:
                 st.markdown("### 📌 Update Profile Data")
                 with st.form("profile_form"):
                     new_profile = {}
                     for key, config in PROFILE_SCHEMA.items():
                         current_value = profile.get(key, config["default"])
                         if config["type"] == "text": new_profile[key] = st.text_input(config["label"], current_value, key=f"profile_{key}")
                         elif config["type"] == "select":
                             options = config["options"]; index = options.index(current_value) if current_value in options else 0
                             new_profile[key] = st.selectbox(config["label"], options, index=index, key=f"profile_{key}")
                     save_prof = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)
                     if save_prof:
                         if user_email in users: users[user_email]["profile"] = new_profile; save_users(users); st.success("Profile saved!"); st.rerun()
                         else: st.error("User not found.")
             with prof_tab2:
                 st.markdown("### ⚙️ App Settings")
                 st.write("Manage your application preferences here.")
                 # Light/Dark Mode Toggle
                 current_theme = st.session_state.theme
                 if st.button(f"Switch to {'Light' if current_theme == 'dark' else 'Dark'} Mode", use_container_width=True):
                     st.session_state.theme = "light" if current_theme == "dark" else "dark"
                     st.rerun()

                 st.markdown("---")
                 st.markdown("### 📌 Current Profile (Read-Only)")
                 current_profile_display = users.get(user_email, {}).get("profile", {})
                 st.json({k:v for k,v in current_profile_display.items() if k in PROFILE_SCHEMA})
        st.divider()

        # --- CHATBOT INTERFACE ---
        status_class = "status-online" if is_online else "status-offline"; status_text = "Online" if is_online else "Offline"
        st.markdown(f'<div class="bot-header"><span class="status-indicator {status_class}"></span><span>Chatbot ({status_text})</span></div>', unsafe_allow_html=True)
        if "chat_history" not in st.session_state:
            lang = profile.get("language", "English"); init_greet = "🤖 नमस्ते!..." if lang == "Hindi" else "🤖 Hello! Ask me..."
            st.session_state.chat_history = [("bot", init_greet)]

        chat_display_cont = st.container(height=400) # Fixed height chat area
        with chat_display_cont:
            chat_hist = list(st.session_state.chat_history)
            for i, (role, text) in enumerate(chat_hist):
                resp_id = f"msg_{i}_{hash_pw(text)[:8]}"
                if role == "user": st.markdown(f'<div class="chat-bubble user-msg">{text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble bot-msg">{text}</div>', unsafe_allow_html=True)
                    if i > 0:
                        fb_state = st.session_state.feedback_submitted.get(resp_id)
                        if fb_state is None:
                            st.markdown('<div class="feedback-button-container">', unsafe_allow_html=True)
                            fb_c1, fb_c2, _ = st.columns([1, 1, 10])
                            with fb_c1: # Green Thumb UP
                                if st.button("👍", key=f"up_{resp_id}", help="Helpful"): log_feedback(resp_id, "up"); st.session_state.feedback_submitted[resp_id] = True; st.toast("✅ Thanks for your feedback!"); st.rerun()
                            with fb_c2: # Red Thumb DOWN
                                if st.button("👎", key=f"down_{resp_id}", help="Not Helpful"): st.session_state.feedback_submitted[resp_id] = "pending"; st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif fb_state == "pending": # Show comment form for DOWN vote
                             st.markdown('<div class="feedback-button-container">', unsafe_allow_html=True)
                             with st.form(key=f"comm_{resp_id}"):
                                comm = st.text_input("Reason (opt):", key=f"comm_{resp_id}")
                                if st.form_submit_button("Submit"): log_feedback(resp_id, "down", comm); st.session_state.feedback_submitted[resp_id] = True; st.toast("Thanks for the feedback! 👎"); st.rerun()
                             st.markdown('</div>', unsafe_allow_html=True)
                        elif fb_state == True: st.markdown("<span class='feedback-received'>✅ Feedback received!</span>", unsafe_allow_html=True)
            st.markdown("<div id='end-of-chat'></div>", unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True): # Chat Input Form
            col1, col2 = st.columns([6, 1])
            with col1: user_in = st.text_input("Type...", key="chat_in", label_visibility="collapsed", placeholder="Ask symptoms...")
            with col2: send = st.form_submit_button("➤", help="Send")
            if send and user_in.strip():
                st.session_state.chat_history.append(("user", user_in))
                resp = "🤖 Offline..." if not is_online else get_bot_response(user_in)
                resp_id = f"msg_{len(st.session_state.chat_history)}_{hash_pw(resp)[:8]}"
                log_chat(user_email, user_in, resp, resp_id)
                st.session_state.chat_history.append(("bot", resp))
                st.rerun()
            elif send: st.warning("Please type.")

        st.divider()
        st.write("Or try:")
        dyn_kw = get_frequent_keywords(user_email)
        cols = st.columns(5) # Use exactly 5 columns for keyword buttons
        for i, kw in enumerate(dyn_kw):
            with cols[i]:
                if st.button(kw, use_container_width=True, key=f"kw_{i}"):
                    u_click = kw.split(" ", 1)[-1].strip()
                    st.session_state.chat_history.append(("user", u_click))
                    resp = "🤖 Offline..." if not is_online else get_bot_response(u_click)
                    resp_id = f"msg_{len(st.session_state.chat_history)}_{hash_pw(resp)[:8]}"
                    log_chat(user_email, u_click, resp, resp_id)
                    st.session_state.chat_history.append(("bot", resp))
                    st.rerun()

# --- LOGIN / REGISTER VIEW ---
else:
    st.subheader("Register / Login")
    with st.form("login_reg_form"):
        em = st.text_input("Email", key="em_in", placeholder=f"Use '{ADMIN_EMAIL}' / 'admin123'")
        pw = st.text_input("Password", type="password", key="pw_in")
        c1, c2 = st.columns(2)
        with c1: reg = st.form_submit_button("Register")
        with c2: log = st.form_submit_button("Login")
        if reg:
            if not validate_email(em): st.error("Invalid Email")
            elif not validate_password(pw): st.error("Pwd >= 6 chars")
            elif em in users: st.error("User exists")
            else: users[em]={"password":hash_pw(pw),"profile":{k:v["default"] for k,v in PROFILE_SCHEMA.items()}}; save_users(users); st.success("Registered! Login.")
        if log:
            if not validate_email(em) or not pw: st.error("Email/Pwd required")
            elif em in users and users[em]["password"] == hash_pw(pw): st.session_state["token"] = create_token(em); st.success("Login ok!"); st.rerun()
            else: st.error("Invalid credentials.")
