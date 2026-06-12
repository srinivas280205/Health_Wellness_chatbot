import streamlit as st
import jwt, datetime, json, os, re
from hashlib import sha256
from collections import defaultdict, Counter
import pandas as pd
import plotly.express as px

# ══════════════════════════════════════════════════════════════
# CONFIGURATION  (set these in Streamlit Cloud → App Settings → Secrets)
# ══════════════════════════════════════════════════════════════
SECRET_KEY     = st.secrets.get("SECRET_KEY",     "mysecretkey")
ADMIN_EMAIL    = st.secrets.get("ADMIN_EMAIL",    "admin@wellbot.com")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")
KB_FILE        = "kb.json"
# JSON fallback paths (used only when MONGO_URI is NOT in secrets)
_DB_FILE       = "users.json"
_LOG_FILE      = "chat_logs.json"

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="Health Wellness Chatbot", layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ══════════════════════════════════════════════════════════════
# THEME CSS
# ══════════════════════════════════════════════════════════════
def get_theme_css(theme):
    if theme == "light":
        return """
        <style>
        body { background: #E0E0E0; }
        .stApp { background-color: #E0E0E0; color: #001A3A; }
        h1, h2, h3, h4, h5, h6, label { color: #003366 !important; }
        h1 { color: #001A3A !important; text-align: center; }
        h2, h3 { border-bottom-color: #80BFFF; color: #001A3A !important; }
        .stSidebar { background-color: #FFFFFF !important; border-right: 1px solid #80BFFF; }
        .stSidebar .stButton>button { background-color: #E0E0E0; color: #003366; border: 1px solid #003366; }
        .stSidebar .stButton>button:hover { background-color: #003366; color: #FFFFFF; border-color: #003366; }
        .stTextInput>div>div>input, div[data-testid="stForm"] input[type="text"],
        div[data-testid="stForm"] input[type="password"], div[data-testid="stForm"] textarea {
            background-color: #FFFFFF; color: #001A3A; border: 1px solid #003366; }
        .stButton>button { background-color: #E0E0E0; color: #003366; border: 1px solid #003366; }
        .stButton>button:hover { background-color: #003366; color: #FFFFFF; border-color: #003366; }
        .chat-bubble { border: 1px solid #003366; }
        .bot-msg { background-color: #FFFFFF; color: #001A3A; }
        .user-msg { background-color: #003366; color: #FFFFFF; }
        .status-online { background-color: #28a745 !important; }
        .status-offline { background-color: #DC3545 !important; }
        div[data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #003366; }
        div[data-testid="stMetric"] label { color: #003366 !important; }
        div.admin-list-container { background-color: #FFFFFF; border: 1px solid #003366; color: #001A3A; }
        div.admin-list-container li { border-bottom-color: #E0E0E0; color: #001A3A; }
        </style>"""
    else:
        return """
        <style>
        body { background: #001A3A; }
        .stApp { background-color: #001A3A; color: #FFFFFF; }
        h1, h2, h3, h4, h5, h6, label { color: #80BFFF !important; }
        h1 { color: #FFFFFF !important; text-align: center; }
        h2, h3 { border-bottom: 2px solid #003366; padding-bottom: 5px; color: #FFFFFF !important; margin-top: 1.5rem; }
        .stSidebar { background-color: #001024 !important; border-right: 1px solid #003366; }
        .stSidebar .stButton>button {
            background-color: #003366; color: #FFFFFF; border: 1px solid #80BFFF;
            width: 100%; margin-bottom: 5px; border-radius: 4px;
            text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .stSidebar .stButton>button:hover { background-color: #80BFFF; color: #001A3A; border-color: #FFFFFF; }
        .stTextInput>div>div>input, div[data-testid="stForm"] input[type="text"],
        div[data-testid="stForm"] input[type="password"], div[data-testid="stForm"] textarea {
            background-color: #003366; color: #FFFFFF; border: 1px solid #80BFFF;
            border-radius: 4px; padding: 10px; }
        .stButton>button { background-color: #003366; color: #FFFFFF; font-weight: bold;
            border-radius: 4px; border: 1px solid #80BFFF; padding: 8px 18px; }
        .stButton>button:hover { background-color: #80BFFF; color: #001A3A; border-color: #FFFFFF; }
        .chat-bubble { padding: 10px 15px; margin: 8px 0; border-radius: 15px;
            max-width: 80%; word-wrap: break-word; font-size: 16px; line-height: 1.5; }
        .bot-msg { background-color: #003366; color: #FFFFFF; border-top-left-radius: 0; float: left; clear: both; }
        .user-msg { background-color: #80BFFF; color: #001A3A; border-top-right-radius: 0; float: right; clear: both; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status-online  { background-color: #80BFFF !important; }
        .status-offline { background-color: #DC3545 !important; }
        .bot-header { font-size: 1.5rem; font-weight: 600; color: #FFFFFF !important;
            display: flex; align-items: center; margin-bottom: 1rem; }
        div.feedback-button-container { margin-top: -10px; margin-left: 10px; margin-bottom: 10px; float: left; clear: both; }
        div.feedback-button-container .stButton>button { background-color: transparent; border: none; height: 30px; width: 30px; font-size: 1.3em; }
        span.feedback-received { color: #80BFFF; font-size: 0.9em; float: left; clear: both; margin-left: 10px; margin-top: 5px; }
        div[data-testid="stMetric"] { background-color: #003366; border-radius: 8px; padding: 1rem; border: 1px solid #80BFFF; }
        div[data-testid="stMetric"] label { color: #AAAAAA !important; }
        div[data-testid="stMetric"] div.st-emotion-cache-1gfitym { color: #FFFFFF !important; }
        div.admin-list-container { background-color: #003366; padding: 1rem; border-radius: 8px;
            border: 1px solid #80BFFF; max-height: 250px; overflow-y: auto; }
        div.admin-list-container h3 { margin-top: 0; color: #FFFFFF !important; }
        div.admin-list-container ul { list-style: none; padding: 0; margin: 0; }
        div.admin-list-container li { padding: 0.3rem 0; border-bottom: 1px solid #001A3A;
            display: flex; justify-content: space-between; align-items: center; color: #FFFFFF; }
        div.admin-list-container li:last-child { border-bottom: none; }
        div.admin-list-container span.feedback-icon-up   { color: #28a745; font-weight: bold; }
        div.admin-list-container span.feedback-icon-down { color: #DC3545; font-weight: bold; }
        .plotly-graph-div { background: transparent !important; }
        div[data-testid="stTabs"] { background-color: #001A3A; border-radius: 8px; padding: 5px; }
        .stTabs [data-baseweb="tab-list"] { background-color: #001A3A; }
        .stTabs [data-baseweb="tab"] { background-color: #003366; color: #FFFFFF; border-radius: 4px; margin-right: 5px; }
        .stTabs [data-baseweb="tab--selected"] { background-color: #80BFFF; color: #001A3A; font-weight: bold; }
        hr { border-top: 1px solid #003366; margin: 1rem 0; }
        </style>"""

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PROFILE SCHEMA
# ══════════════════════════════════════════════════════════════
PROFILE_SCHEMA = {
    "name":     {"type": "text",   "label": "Full Name",         "default": ""},
    "age":      {"type": "select", "label": "Age Group",         "options": ["18–25","25–35","35–45","45+"],   "default": "18–25"},
    "gender":   {"type": "select", "label": "Gender",            "options": ["Male","Female","Other"],         "default": "Male"},
    "language": {"type": "select", "label": "Preferred Language","options": ["English","Hindi"],               "default": "English"},
}

# ══════════════════════════════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════════════════════════════
def hash_pw(pw):
    return sha256(pw.encode()).hexdigest()

def create_token(email):
    payload = {"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_user_from_token():
    token = st.session_state.get("token")
    if not token:
        return None
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": True})
        return decoded["email"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        st.error(f"Session expired: {e}. Please log in again.")
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        st.rerun()
        return None

def validate_email(e):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e)

def validate_password(p):
    return len(p) >= 6

# ══════════════════════════════════════════════════════════════
# JSON FALLBACK HELPERS  (used when MongoDB is not configured)
# ══════════════════════════════════════════════════════════════
def _load_json(path, default):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Failed to save {path}: {e}")

# ══════════════════════════════════════════════════════════════
# MONGODB CONNECTION
# ══════════════════════════════════════════════════════════════
@st.cache_resource
def get_db():
    """Returns MongoDB database, or None if MONGO_URI not configured."""
    if "MONGO_URI" not in st.secrets:
        return None
    try:
        import pymongo
        client = pymongo.MongoClient(st.secrets["MONGO_URI"], serverSelectionTimeoutMS=5000)
        client.server_info()  # Raises if connection fails
        db = client.get_database("wellbot")
        # Create indexes for fast lookups
        db["users"].create_index("_id")
        db["chat_logs"].create_index("id")
        db["chat_logs"].create_index("email")
        # Ensure admin user exists
        if not db["users"].find_one({"_id": ADMIN_EMAIL}):
            prof = {k: v["default"] for k, v in PROFILE_SCHEMA.items()}
            db["users"].insert_one({
                "_id": ADMIN_EMAIL,
                "password": hash_pw(ADMIN_PASSWORD),
                "profile": prof,
                "is_admin": True,
                "created_at": datetime.datetime.utcnow()
            })
        return db
    except Exception as e:
        st.sidebar.warning(f"⚠️ MongoDB: {e}\nUsing local storage.")
        return None

# ══════════════════════════════════════════════════════════════
# DATA LAYER — USERS
# ══════════════════════════════════════════════════════════════
def get_user(email):
    """Return user dict {password, profile} or None."""
    db = get_db()
    if db is not None:
        doc = db["users"].find_one({"_id": email})
        if doc:
            return {"password": doc["password"], "profile": doc.get("profile", {})}
        return None
    users = _load_json(_DB_FILE, {})
    return users.get(email)

def register_user(email, password):
    """Register new user. Returns (success, message)."""
    prof = {k: v["default"] for k, v in PROFILE_SCHEMA.items()}
    db = get_db()
    if db is not None:
        if db["users"].find_one({"_id": email}):
            return False, "An account with this email already exists."
        db["users"].insert_one({
            "_id": email,
            "password": hash_pw(password),
            "profile": prof,
            "is_admin": False,
            "created_at": datetime.datetime.utcnow()
        })
        return True, "✅ Registered successfully! You can now log in."
    # JSON fallback
    users = _load_json(_DB_FILE, {})
    if not users:
        admin_prof = {k: v["default"] for k, v in PROFILE_SCHEMA.items()}
        users[ADMIN_EMAIL] = {"password": hash_pw(ADMIN_PASSWORD), "profile": admin_prof}
    if email in users:
        return False, "An account with this email already exists."
    users[email] = {"password": hash_pw(password), "profile": prof}
    _save_json(_DB_FILE, users)
    return True, "✅ Registered successfully! You can now log in."

def update_user_profile(email, profile):
    """Update profile for existing user."""
    db = get_db()
    if db is not None:
        db["users"].update_one({"_id": email}, {"$set": {"profile": profile}})
        return
    users = _load_json(_DB_FILE, {})
    if email in users:
        users[email]["profile"] = profile
        _save_json(_DB_FILE, users)

def get_all_users():
    """Return dict of all users {email: {password, profile}}."""
    db = get_db()
    if db is not None:
        return {u["_id"]: {"password": u["password"], "profile": u.get("profile", {})}
                for u in db["users"].find()}
    return _load_json(_DB_FILE, {})

def delete_user(email):
    """Delete a user and all their chat logs. Admin cannot be deleted."""
    if email == ADMIN_EMAIL:
        st.error("Admin account cannot be deleted.")
        return False
    db = get_db()
    if db is not None:
        db["users"].delete_one({"_id": email})
        db["chat_logs"].delete_many({"email": email})
        return True
    users = _load_json(_DB_FILE, {})
    users.pop(email, None)
    _save_json(_DB_FILE, users)
    logs = _load_json(_LOG_FILE, [])
    logs = [l for l in logs if l.get("email") != email]
    _save_json(_LOG_FILE, logs)
    return True

# ══════════════════════════════════════════════════════════════
# DATA LAYER — CHAT LOGS
# ══════════════════════════════════════════════════════════════
def load_logs():
    db = get_db()
    if db is not None:
        return list(db["chat_logs"].find({}, {"_id": 0}))
    return _load_json(_LOG_FILE, [])

def log_chat(email, query, response, resp_id):
    main_resp = response.split("<br><br>---<br>")[0]
    db = get_db()
    if db is not None:
        db["chat_logs"].insert_one({
            "id": resp_id, "email": email, "query": query,
            "response": main_resp, "feedback": "none", "comment": "",
            "timestamp": datetime.datetime.utcnow()
        })
        return
    logs = _load_json(_LOG_FILE, [])
    logs.append({"id": resp_id, "email": email, "query": query, "response": main_resp,
                 "feedback": "none", "comment": "",
                 "timestamp": datetime.datetime.utcnow().isoformat()})
    _save_json(_LOG_FILE, logs)

def log_feedback(resp_id, fb_type, comment=""):
    db = get_db()
    if db is not None:
        result = db["chat_logs"].update_one(
            {"id": resp_id},
            {"$set": {"feedback": fb_type, "comment": comment}}
        )
        if result.matched_count == 0:
            st.error("Feedback error: log entry not found.")
        return
    logs = _load_json(_LOG_FILE, [])
    found = False
    for log in logs:
        if log.get("id") == resp_id:
            log["feedback"] = fb_type
            log["comment"] = comment if comment else log.get("comment", "")
            found = True
            break
    if found:
        _save_json(_LOG_FILE, logs)
    else:
        st.error("Feedback error: Log ID not found.")

def get_frequent_keywords(email):
    logs = load_logs()
    queries = [log['query'] for log in logs if log.get('email') == email]
    defaults = ["🤒 Headache", "🤢 Flu", "🔥 Burns", "😴 Sleep", "🧘 Anxiety"]
    if not queries:
        return defaults
    words = [w for q in queries for w in re.findall(r'\b\w{4,}\b', q.lower())]
    stops = {"what","when","tell","about","have","with","from","mein","kya","kaise","this","that"}
    filtered = [w for w in words if w not in stops]
    if not filtered:
        return defaults
    emojis = {"headache":"🤒","flu":"🤢","burns":"🔥","sleep":"😴","anxiety":"🧘",
              "cough":"💨","cold":"🤧","fever":"🌡️","pain":"💥","cut":"🩹"}
    top_5 = [w for w, _ in Counter(filtered).most_common(5)]
    formatted = [f"{emojis.get(w,'🔍')} {w.title()}" for w in top_5]
    if len(formatted) < 5:
        existing = {kw.split(" ",1)[-1].lower() for kw in formatted}
        for d_kw in defaults:
            if len(formatted) >= 5:
                break
            if d_kw.split(" ",1)[-1].lower() not in existing:
                formatted.append(d_kw)
    return formatted[:5]

# ══════════════════════════════════════════════════════════════
# KNOWLEDGE BASE  (stays file-based — it's static config)
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=600)
def load_kb():
    if not os.path.exists(KB_FILE):
        st.error(f"{KB_FILE} not found!")
        return {}
    try:
        with open(KB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading KB: {e}")
        return {}

def save_kb(kb_data):
    try:
        with open(KB_FILE, 'w', encoding='utf-8') as f:
            json.dump(kb_data, f, indent=4, ensure_ascii=False)
        load_kb.clear()
        return True
    except Exception as e:
        st.error(f"Failed to save KB: {e}")
        return False

@st.cache_data
def build_entity_map(kb_data):
    entity_map = defaultdict(list)
    if kb_data:
        for cond, data in kb_data.items():
            for sym in data.get("symptoms", []):   entity_map["symptom"].append(sym)
            for part in data.get("body_parts", []): entity_map["body_part"].append(part)
    return entity_map

KB         = load_kb()
ENTITY_MAP = build_entity_map(KB)
if not KB:
    st.warning("Knowledge Base is empty or not loaded.")

# ══════════════════════════════════════════════════════════════
# NLU & RESPONSE LOGIC
# ══════════════════════════════════════════════════════════════
def extract_entities(text, msg):
    text_lower = text.lower()
    extracted  = {"symptom": set(), "body_part": set()}
    global ENTITY_MAP
    if not ENTITY_MAP:
        return extracted
    for etype, kwds in ENTITY_MAP.items():
        for kwd in kwds:
            kp = False
            if kwd.isascii():
                if re.search(r'\b' + re.escape(kwd) + r'\b', text_lower): kp = True
            elif kwd in msg: kp = True
            if kp: extracted[etype].add(kwd)
    if not extracted["body_part"]:
        for sym in extracted["symptom"]:
            if sym in ["fever","dehydration","insomnia","bukhar","paani ki kami","anidra",
                       "बुखार","पानी की कमी","अनिद्रा","sleep","नींद","anxiety","चिंता","तनाव"]:
                extracted["body_part"].add("body"); break
    return extracted

def generate_disclaimer(name_en, name_hi, is_hindi):
    hr = "border-top: 1px dashed #80BFFF; margin: 10px 0;"
    note_hi = f"Note: यह **{name_hi}** जानकारी केवल बुनियादी मार्गदर्शन के लिए है।<br>यदि लक्षण बने रहते हैं तो डॉक्टर से सलाह लें."
    note_en = f"Note: This **{name_en.title().replace('/', ' or ')}** information is for basic guidance only.<br>Consult a healthcare provider if symptoms persist or worsen."
    return f"<hr style='{hr}'>{note_hi}" if is_hindi else f"<hr style='{hr}'>{note_en}"

def get_bot_response(msg):
    global KB, ENTITY_MAP
    KB = load_kb()
    if not KB: return "🤖 Sorry, knowledge base unavailable."
    ENTITY_MAP = build_entity_map(KB)
    msg_lower  = msg.lower()
    HINDI_KW   = ["namaste","hindi","sir dard","bukhar","khansi","pet","dard","moch","matli","ulti",
                  "jaln","kamar","peeth","jukaam","sardi","gala","khujli","dast","kabz","pyas","chot",
                  "sujan","daant","tanaav","chinta",
                  "नमस्ते","नमस्कार","हिंदी","सिरदर्द","माथा दर्द","सिर में दर्द","सिर","गर्दन","माइग्रेन",
                  "तेज सिरदर्द","आंख","बुखार","तापमान","ज्वर","तेज़ बुखार","शरीर","खांसी","सूखी खांसी",
                  "गीली खांसी","सर्दी","जुकाम","नाक बहना","बंद नाक","गला","सीना","नाक","गले में दर्द",
                  "खराश","गला खराब","एलर्जी","छींक","खुजली","आंख में खुजली","त्वचा","मतली","उल्टी",
                  "पेट खराब","जी मचलना","पेट दर्द","पेट","दस्त","पेट में मरोड़","लूज मोशन","कब्ज",
                  "पेट साफ नहीं होना","प्यास","पानी की कमी","सूखा मुंह","चक्कर","मुंह","धूप से जलन",
                  "जलना","छाले","लाल त्वचा","चोट","ज़ख्म","खून बहना","कटना","उंगली","हाथ","पैर",
                  "सिर पर चोट","चक्कर आना","दर्द","मोच","सूजन","टखना","घुटना","कलाई","जोड़","मांसपेशी",
                  "कमर दर्द","पीठ में दर्द","कमर","पीठ","नींद नहीं आना","अनिद्रा","थकान","दांत दर्द",
                  "मसूड़ों में दर्द","दांत","मसूड़ा","चकत्ते","लाल दाने","कीड़े ने काटा","मच्छर काटा",
                  "डंक","कान","फ्लू","नींद","चिंता","तनाव"]
    is_hindi  = any(h in msg_lower for h in HINDI_KW if h.isascii()) or \
                any(h in msg       for h in HINDI_KW if not h.isascii())
    greetings = {"नमस्ते","नमस्कार","hi","hello","hey","namaste","start"}
    farewells = {"bye","goodbye","thanks","thank you","dhanyawad","shukriya","धन्यवाद","शुक्रिया"}
    if msg_lower in greetings or any(g in msg for g in greetings if not g.isascii()):
        return "🤖 नमस्ते! मैं आपका कल्याण सहायक हूँ।" if is_hindi else "🤖 Hello! I'm your Wellness Assistant. How can I help you today?"
    if msg_lower in farewells or any(f in msg for f in farewells if not f.isascii()):
        return "🤖 आपका स्वागत है! सुरक्षित रहें!" if is_hindi else "🤖 You're welcome! Stay safe!"
    not_found = "🤖 क्षमा करें, मेरे पास इस बारे में जानकारी नहीं है..." if is_hindi else "🤖 Sorry, I don't have information on that. Try describing your symptoms differently."
    res_key  = "hindi_responses" if is_hindi else "responses"
    entities = extract_entities(msg_lower, msg)
    found    = entities["symptom"].union(entities["body_part"])
    match, score = None, 0
    q_map  = {"burns":"sunburn/burn","sleep":"insomnia","anxiety":"anxiety","flu":"cough/cold"}
    mapped_key = q_map.get(msg_lower)
    if mapped_key and mapped_key in KB:
        match, score = mapped_key, 100
    else:
        for c, d in KB.items():
            kwds = set(d.get("symptoms",[]) + d.get("body_parts",[]))
            s    = len(found.intersection(kwds))
            if s > score:
                score, match = s, c
            elif s == score and match:
                if c in ["migraine","minor head injury"] and match in ["headache","fever"]:
                    match = c
                elif len(c) > len(match) and match not in ["migraine","minor head injury"]:
                    match = c
    if match and res_key in KB[match]:
        s_list = list(entities['symptom']); p_list = list(entities['body_part'])
        nlu_p  = f"Part(s): **{', '.join(p for p in p_list if p != 'body')}**" if p_list and p_list != ["body"] else "Part(s): *None*"
        nlu_s  = f"Symptom(s): **{', '.join(s_list)}**" if s_list else "Symptom(s): *None*"
        nlu    = f"<br><br>---<br>**🔍 Analysis:**<br>{nlu_s}<br>{nlu_p}"
        r_list = KB[match].get(res_key, [])
        r_txt  = r_list[0] if r_list else not_found
        disc   = generate_disclaimer(KB[match]["condition_name_en"], KB[match]["condition_name_hi"], is_hindi)
        return r_txt + nlu + disc
    return not_found

# ══════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════
def show_main_dashboard_layout():
    logs_data = load_logs()
    df = pd.DataFrame(logs_data) if logs_data else pd.DataFrame()
    if not df.empty and 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)
        except Exception:
            df = pd.DataFrame()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📊 Usage Statistics")
        global KB
        t_queries = len(df)
        f_counts  = df['feedback'].value_counts() if 'feedback' in df.columns else pd.Series()
        pos_fb    = f_counts.get('up', 0); neg_fb = f_counts.get('down', 0); t_rated = pos_fb + neg_fb
        fb_score  = (pos_fb / t_rated * 100) if t_rated > 0 else 0
        t_users   = len(get_all_users()); t_kb = len(KB)
        m1, m2 = st.columns(2)
        with m1: st.metric("Total Users", t_users); st.metric("Health Topics (KB)", t_kb)
        with m2: st.metric("Queries Handled", t_queries); st.metric("Positive Feedback", f"{fb_score:.1f}%", f"{t_rated} rated")
        db = get_db()
        if db is not None:
            st.caption("🟢 MongoDB Atlas — data persists across restarts")
        else:
            st.caption("🟡 Local JSON storage — data resets on redeploy")
    with col2:
        st.subheader("📚 Knowledge Base")
        st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
        if not KB:
            st.caption("KB empty.")
        else:
            items = list(KB.keys())
            st.markdown("<ul>", unsafe_allow_html=True)
            for k in items[:6]:
                name = KB.get(k, {}).get('condition_name_en', k)
                st.markdown(f"<li>{name}</li>", unsafe_allow_html=True)
            if len(items) > 6:
                st.markdown(f"<li>...+{len(items)-6} more</li>", unsafe_allow_html=True)
            st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("Manage KB", key="goto_kb", use_container_width=True):
            st.session_state.admin_tab = "KB"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    col3, col4 = st.columns([2, 1])
    with col3:
        st.subheader("📈 Query Trends")
        if df.empty or 'timestamp' not in df.columns or df['timestamp'].isnull().all():
            st.caption("No trend data yet.")
        else:
            try:
                trends = df.set_index('timestamp').resample('D')['query'].count()
                if not trends.empty: st.line_chart(trends, color="#80BFFF")
                else: st.caption("No queries logged.")
            except Exception as e:
                st.caption(f"Chart error: {e}")
    with col4:
        st.subheader("💬 Recent Feedback")
        st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
        if df.empty or 'feedback' not in df.columns:
            st.caption("No feedback yet.")
        else:
            fb_df = df[df['feedback'] != 'none'].sort_values('timestamp', ascending=False).head(5)
            if fb_df.empty:
                st.caption("No rated feedback.")
            else:
                st.markdown("<ul>", unsafe_allow_html=True)
                for _, r in fb_df.iterrows():
                    icon = "👍" if r['feedback'] == 'up' else "👎"
                    cls  = "up" if r['feedback'] == 'up' else "down"
                    q    = (r['query'][:30] + '...') if len(str(r['query'])) > 30 else r['query']
                    st.markdown(f"<li><span>'{q}'</span> <span class='feedback-icon-{cls}'>{icon}</span></li>", unsafe_allow_html=True)
                st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("View All Feedback", key="goto_fb", use_container_width=True):
            st.session_state.admin_tab = "FB"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    col5, col6 = st.columns([2, 1])
    with col5:
        st.subheader("🥧 Query Categories")
        if df.empty or 'query' not in df.columns:
            st.caption("No category data.")
        else:
            def cat_q(q):
                q = str(q).lower()
                if any(s in q for s in ["headache","fever","cough","cold","pain","sore"]): return "Symptoms"
                if any(s in q for s in ["cut","burn","sprain","injury","bite"]):           return "First Aid"
                if any(s in q for s in ["sleep","anxiety","stress","diet","hydrate","constipation"]): return "Wellness"
                return "Other"
            df['category'] = df['query'].apply(cat_q)
            cat_counts = df['category'].value_counts()
            if not cat_counts.empty:
                pie_df = cat_counts.reset_index(); pie_df.columns = ['category','count']
                fig = px.pie(pie_df, names='category', values='count', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  font_color="#FFFFFF", showlegend=False)
                fig.update_traces(textinfo='percent+label', textfont_size=14,
                                  marker=dict(line=dict(color='#001A3A', width=2)))
                st.plotly_chart(fig, use_container_width=True)
    with col6:
        st.subheader("👥 Users Quick View")
        st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
        all_u = get_all_users()
        st.markdown("<ul>", unsafe_allow_html=True)
        for email in list(all_u.keys())[:5]:
            name = all_u[email].get("profile", {}).get("name", "—")
            label = "👑" if email == ADMIN_EMAIL else "👤"
            st.markdown(f"<li>{label} {email}</li>", unsafe_allow_html=True)
        if len(all_u) > 5:
            st.markdown(f"<li>...+{len(all_u)-5} more</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        if st.button("Manage Users", key="goto_users", use_container_width=True):
            st.session_state.admin_tab = "USERS"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def show_user_management():
    st.subheader("👥 User Management")
    if st.button("← Back to Dashboard", key="back_from_users"):
        st.session_state.admin_tab = None; st.rerun()

    all_users = get_all_users()
    st.info(f"Total registered users: **{len(all_users)}**")

    # Search filter
    search = st.text_input("🔍 Search by email", key="user_search", placeholder="type to filter...")
    filtered = {e: d for e, d in all_users.items()
                if not search or search.lower() in e.lower()}

    if not filtered:
        st.warning("No users found.")
        return

    for email, data in filtered.items():
        profile = data.get("profile", {})
        name    = profile.get("name", "—") or "—"
        age     = profile.get("age",  "—")
        lang    = profile.get("language", "English")
        is_admin_user = (email == ADMIN_EMAIL)

        with st.expander(f"{'👑 ADMIN' if is_admin_user else '👤'} {email} — {name}", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1: st.write(f"**Name:** {name}"); st.write(f"**Age:** {age}")
            with c2: st.write(f"**Language:** {lang}")
            with c3:
                if not is_admin_user:
                    if st.button(f"🗑️ Delete User", key=f"del_{email}", type="primary"):
                        if delete_user(email):
                            st.success(f"Deleted {email}")
                            st.rerun()
                else:
                    st.caption("Admin — cannot delete")

def show_kb_management():
    st.subheader("✍️ Knowledge Base Management")
    if st.button("← Back to Dashboard", key="back_from_kb"):
        st.session_state.admin_tab = None; st.rerun()
    with st.expander("Edit Knowledge Base (JSON)", expanded=True):
        kb_edit  = load_kb()
        kb_json  = json.dumps(kb_edit, indent=4, ensure_ascii=False)
        new_json = st.text_area("KB JSON", value=kb_json, height=600, key="kb_edit")
        col_k1, _ = st.columns([1, 5])
        with col_k1:
            if st.button("💾 Save KB", type="primary", key="save_kb", use_container_width=True):
                try:
                    new_kb = json.loads(new_json)
                    if save_kb(new_kb):
                        global KB, ENTITY_MAP
                        KB = new_kb; ENTITY_MAP = defaultdict(list)
                        for c, d in KB.items():
                            for s in d.get("symptoms",  []): ENTITY_MAP["symptom"].append(s)
                            for p in d.get("body_parts",[]): ENTITY_MAP["body_part"].append(p)
                        st.success("✅ KB updated!"); st.session_state.admin_tab = None; st.rerun()
                    else:
                        st.error("Failed to save KB.")
                except Exception as e:
                    st.error(f"JSON Error: {e}")

def show_feedback_management():
    st.subheader("💬 All Feedback & Comments")
    if st.button("← Back to Dashboard", key="back_from_fb"):
        st.session_state.admin_tab = None; st.rerun()
    logs_data = load_logs()
    df = pd.DataFrame(logs_data) if logs_data else pd.DataFrame()
    if df.empty or 'feedback' not in df.columns:
        st.warning("No logs found.")
        return
    fb_all = df[df['feedback'] != 'none'][['timestamp','email','query','feedback','comment']].sort_values('timestamp', ascending=False)
    if fb_all.empty:
        st.info("No rated feedback yet.")
    else:
        st.dataframe(fb_all, use_container_width=True,
                     column_config={
                         "timestamp": st.column_config.DatetimeColumn("Time", format="YY-MM-DD HH:mm"),
                         "email":"User","query":"Query","feedback":"Rating","comment":"Comment"})

def show_admin_dashboard():
    st.header("✨ Admin Dashboard")
    admin_tab = st.session_state.get("admin_tab", None)
    if   admin_tab == "KB":    show_kb_management()
    elif admin_tab == "FB":    show_feedback_management()
    elif admin_tab == "USERS": show_user_management()
    else:                      show_main_dashboard_layout()

# ══════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════
st.title("🪄 Health & Wellness Assistant")

user_email = get_user_from_token()

for key, default_val in {"chat_archive": [], "show_admin": False,
                         "feedback_submitted": {}, "admin_tab": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default_val

# ── LOGGED-IN VIEW ────────────────────────────────────────────
if user_email:
    with st.sidebar:
        st.header("Controls & History")
        if user_email == ADMIN_EMAIL:
            st.markdown("---"); st.subheader("👑 Admin")
            if st.button("Admin Dashboard", use_container_width=True):
                st.session_state.show_admin = True; st.session_state.admin_tab = None; st.rerun()
            st.markdown("---")

        is_online = st.toggle("Bot Status", value=True, key="bot_status")
        if st.button("➕ New Chat", key="new_chat", use_container_width=True):
            if "chat_history" in st.session_state and len(st.session_state.chat_history) > 1:
                st.session_state.chat_archive.insert(0, st.session_state.chat_history)
            st.session_state.pop("chat_history", None)
            st.session_state.pop("feedback_submitted", None)
            st.rerun()

        st.markdown("---"); st.subheader("Chat History")
        if st.session_state.chat_archive:
            for i, chat in enumerate(st.session_state.chat_archive[:10]):
                first = next((m for r, m in chat if r == 'user'), "Chat")
                title = first[:50] + ("..." if len(first) > 50 else "")
                if st.button(f"📜 {title}", key=f"chat_{i}"):
                    st.session_state.chat_history = chat
                    st.session_state.feedback_submitted = {}
                    st.session_state.show_admin = False; st.rerun()
        else:
            st.caption("No past chats.")

        st.markdown("---")
        if st.button("🚪 Logout", key="logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                st.session_state.pop(k, None)
            st.success("Logged out successfully.")
            st.rerun()

    # ── Main Area ────────────────────────────────────────────
    if st.session_state.get("show_admin", False) and user_email == ADMIN_EMAIL:
        show_admin_dashboard()
    else:
        st.success(f"✅ Logged in as **{user_email}**")
        user_data = get_user(user_email) or {}
        profile   = user_data.get("profile", {})

        st.divider()
        with st.expander("👤 User Profile & Settings", expanded=False):
            prof_tab1, prof_tab2 = st.tabs(["Update Profile", "⚙️ Settings"])
            with prof_tab1:
                st.markdown("### 📌 Update Profile")
                with st.form("profile_form"):
                    new_profile = {}
                    for key, config in PROFILE_SCHEMA.items():
                        current_value = profile.get(key, config["default"])
                        if config["type"] == "text":
                            new_profile[key] = st.text_input(config["label"], current_value, key=f"p_{key}")
                        elif config["type"] == "select":
                            options = config["options"]
                            index   = options.index(current_value) if current_value in options else 0
                            new_profile[key] = st.selectbox(config["label"], options, index=index, key=f"p_{key}")
                    if st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True):
                        update_user_profile(user_email, new_profile)
                        st.success("✅ Profile saved!"); st.rerun()
            with prof_tab2:
                st.markdown("### ⚙️ App Settings")
                current_theme = st.session_state.theme
                if st.button(f"Switch to {'Light' if current_theme == 'dark' else 'Dark'} Mode", use_container_width=True):
                    st.session_state.theme = "light" if current_theme == "dark" else "dark"; st.rerun()
                st.markdown("---")
                st.markdown("### 📌 Current Profile")
                st.json({k: v for k, v in profile.items() if k in PROFILE_SCHEMA})
        st.divider()

        # ── CHAT INTERFACE ────────────────────────────────
        status_class = "status-online" if is_online else "status-offline"
        status_text  = "Online" if is_online else "Offline"
        st.markdown(f'<div class="bot-header"><span class="status-indicator {status_class}"></span>'
                    f'<span>Chatbot ({status_text})</span></div>', unsafe_allow_html=True)

        if "chat_history" not in st.session_state:
            lang       = profile.get("language", "English")
            init_greet = "🤖 नमस्ते! मैं आपका स्वास्थ्य सहायक हूँ। आज आप कैसे हैं?" if lang == "Hindi" \
                         else "🤖 Hello! I'm your Health & Wellness Assistant. How can I help you today?"
            st.session_state.chat_history = [("bot", init_greet)]

        chat_display_cont = st.container(height=400)
        with chat_display_cont:
            for i, (role, text) in enumerate(list(st.session_state.chat_history)):
                resp_id = f"msg_{i}_{hash_pw(text)[:8]}"
                if role == "user":
                    st.markdown(f'<div class="chat-bubble user-msg">{text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble bot-msg">{text}</div>', unsafe_allow_html=True)
                    if i > 0:
                        fb_state = st.session_state.feedback_submitted.get(resp_id)
                        if fb_state is None:
                            st.markdown('<div class="feedback-button-container">', unsafe_allow_html=True)
                            fb_c1, fb_c2, _ = st.columns([1, 1, 10])
                            with fb_c1:
                                if st.button("👍", key=f"up_{resp_id}", help="Helpful"):
                                    log_feedback(resp_id, "up")
                                    st.session_state.feedback_submitted[resp_id] = True
                                    st.toast("✅ Thanks for your feedback!"); st.rerun()
                            with fb_c2:
                                if st.button("👎", key=f"dn_{resp_id}", help="Not Helpful"):
                                    st.session_state.feedback_submitted[resp_id] = "pending"; st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif fb_state == "pending":
                            st.markdown('<div class="feedback-button-container">', unsafe_allow_html=True)
                            with st.form(key=f"comm_{resp_id}"):
                                comm = st.text_input("Reason (optional):", key=f"comm_in_{resp_id}")
                                if st.form_submit_button("Submit"):
                                    log_feedback(resp_id, "down", comm)
                                    st.session_state.feedback_submitted[resp_id] = True
                                    st.toast("Thanks for the feedback! 👎"); st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif fb_state is True:
                            st.markdown("<span class='feedback-received'>✅ Feedback received!</span>", unsafe_allow_html=True)
            st.markdown("<div id='end-of-chat'></div>", unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([6, 1])
            with col1:
                user_in = st.text_input("Type...", key="chat_in", label_visibility="collapsed",
                                        placeholder="Describe your symptoms or ask a health question…")
            with col2:
                send = st.form_submit_button("➤", help="Send")
            if send and user_in.strip():
                st.session_state.chat_history.append(("user", user_in))
                resp    = "🤖 Bot is currently offline." if not is_online else get_bot_response(user_in)
                resp_id = f"msg_{len(st.session_state.chat_history)}_{hash_pw(resp)[:8]}"
                log_chat(user_email, user_in, resp, resp_id)
                st.session_state.chat_history.append(("bot", resp))
                st.rerun()
            elif send:
                st.warning("Please type a message first.")

        st.divider()
        st.write("**Quick suggestions:**")
        dyn_kw = get_frequent_keywords(user_email)
        cols   = st.columns(5)
        for i, kw in enumerate(dyn_kw):
            with cols[i]:
                if st.button(kw, use_container_width=True, key=f"kw_{i}"):
                    u_click = kw.split(" ", 1)[-1].strip()
                    st.session_state.chat_history.append(("user", u_click))
                    resp    = "🤖 Bot is offline." if not is_online else get_bot_response(u_click)
                    resp_id = f"msg_{len(st.session_state.chat_history)}_{hash_pw(resp)[:8]}"
                    log_chat(user_email, u_click, resp, resp_id)
                    st.session_state.chat_history.append(("bot", resp))
                    st.rerun()

# ── LOGIN / REGISTER VIEW ─────────────────────────────────────
else:
    db = get_db()
    db_status = "🟢 MongoDB Atlas connected" if db is not None else "🟡 Local JSON storage"
    st.caption(db_status)

    st.subheader("Welcome to WellBot 🤖")
    st.write("Register a new account or log in below.")

    with st.form("auth_form"):
        em = st.text_input("Email Address", key="em_in", placeholder="your@email.com")
        pw = st.text_input("Password", type="password", key="pw_in",
                           placeholder="Minimum 6 characters")
        c1, c2 = st.columns(2)
        with c1: reg = st.form_submit_button("📝 Register", use_container_width=True)
        with c2: log = st.form_submit_button("🔑 Login",    use_container_width=True)

        if reg:
            if not em or not pw:
                st.error("Please enter both email and password.")
            elif not validate_email(em):
                st.error("Please enter a valid email address.")
            elif not validate_password(pw):
                st.error("Password must be at least 6 characters.")
            else:
                ok, msg = register_user(em, pw)
                if ok: st.success(msg)
                else:  st.error(msg)

        if log:
            if not em or not pw:
                st.error("Please enter both email and password.")
            elif not validate_email(em):
                st.error("Please enter a valid email address.")
            else:
                user = get_user(em)
                if user and user["password"] == hash_pw(pw):
                    st.session_state["token"] = create_token(em)
                    st.success("✅ Logged in successfully!"); st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")

    st.markdown("---")
    st.caption(f"Admin login: use the email configured in Streamlit secrets (`ADMIN_EMAIL`)")
