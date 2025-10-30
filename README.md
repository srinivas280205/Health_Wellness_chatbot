# 🩺 Health Chatbot

An **AI-powered Health & Wellness Assistant** built with **Streamlit** that helps users understand possible conditions and wellness tips based on their symptoms — available in **English** and **Hindi**.

---

## 🚀 Features
- 🧠 Symptom-based health guidance  
- 🔐 User login & registration (with admin access)  
- 🌍 Multilingual (English + Hindi)  
- 📊 Admin analytics & feedback dashboard  
- 🐳 Docker + ngrok support for easy deployment  

---

## ⚙️ Setup

### 1️⃣ Install Requirements
```bash
pip install -r requirements.txt
2️⃣ Initialize Database
bash
Copy code
python database.py
(Admin credentials: admin@app.com / admin123)

3️⃣ Run App
bash
Copy code
streamlit run app.py
Visit: http://localhost:8501

🌐 Optional: Public Access (ngrok)
bash
Copy code
python run_with_ngrok.py
Edit your ngrok token inside run_with_ngrok.py before running.

🐳 Run with Docker
bash
Copy code
docker build -t health_chatbot .
docker run -p 8501:8501 health_chatbot
🧩 Tech Stack
Python, Streamlit, pyjwt, pyngrok, pandas, plotly

👨‍💻 Admin Details
Email	Password
admin@app.com	admin123

📜 License
Licensed under the MIT License — free to use and modify.

💬 “Your health is your greatest wealth — stay informed, stay well.”
