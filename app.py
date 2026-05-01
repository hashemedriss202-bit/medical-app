from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for, flash
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from functools import wraps
import requests
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "medical_app_secret_key_2026")

# ======================
# 👤 USER DATABASE (قاعدة بيانات المستخدمين المؤقتة)
# ======================
# في التطبيق الحقيقي، استخدم قاعدة بيانات حقيقية
users_db = {
    "doctor": {
        "password": "doctor123",
        "name": "دكتور أحمد",
        "role": "doctor"
    },
    "patient": {
        "password": "patient123",
        "name": "مريض",
        "role": "patient"
    },
    "admin": {
        "password": "admin123",
        "name": "مدير النظام",
        "role": "admin"
    }
}

# ======================
# 🔐 DECORATOR FOR LOGIN REQUIRED
# ======================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('الرجاء تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ======================
# 📄 LOGIN & REGISTER ROUTES
# ======================
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username in users_db and users_db[username]['password'] == password:
            session['username'] = username
            session['user_name'] = users_db[username]['name']
            session['role'] = users_db[username]['role']
            flash(f'مرحباً {users_db[username]["name"]}！', 'success')
            
            # تسجيل دخول الطبيب يذهب للوحة التحكم
            if users_db[username]['role'] == 'doctor':
                return redirect(url_for('dashboard'))
            return redirect(url_for('home'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template("login.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        
        if username in users_db:
            flash('اسم المستخدم موجود بالفعل', 'danger')
        elif len(password) < 4:
            flash('كلمة المرور يجب أن تكون 4 أحرف على الأقل', 'danger')
        else:
            users_db[username] = {
                "password": password,
                "name": name,
                "role": "patient"
            }
            flash('تم التسجيل بنجاح！يمكنك تسجيل الدخول الآن', 'success')
            return redirect(url_for('login'))
    
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

# ======================
# 🔗 AI SERVER (مع بيانات احتياطية)
# ======================
API_URL = "https://clapper-hunger-financial.ngrok-free.dev/analyze"

def analyze_with_api(symptoms):
    mock_data = [
        {"disease": "flu", "probability": 0.82},
        {"disease": "cold", "probability": 0.67},
        {"disease": "infection", "probability": 0.43},
        {"disease": "pneumonia", "probability": 0.31},
        {"disease": "stomach problem", "probability": 0.25}
    ]
    
    try:
        response = requests.post(API_URL, json={"symptoms": symptoms}, timeout=10)
        if response.status_code == 200:
            return response.json()
        return mock_data
    except Exception as e:
        print(f"API error: {e}")
        return mock_data

# ======================
# 🧠 SMART ANALYSIS
# ======================
def smart_diagnosis(symptoms):
    symptoms_lower = symptoms.lower()
    results = []
    
    rules = {
        "flu": {
            "keywords": ["حمى", "سعال", "احتقان", "إنفلونزا", "رشح", "تعب"],
            "ar_name": "إنفلونزا",
            "tests": ["تحليل CBC", "فحص فيروسات"]
        },
        "cold": {
            "keywords": ["زكام", "رشح", "عطس", "احتقان أنف", "سعال بسيط"],
            "ar_name": "نزلة برد",
            "tests": ["راحة", "سوائل دافئة", "فيتامين C"]
        },
        "pneumonia": {
            "keywords": ["التهاب رئوي", "ضيق تنفس", "كحة شديدة", "بلغم", "حمى عالية"],
            "ar_name": "التهاب رئوي",
            "tests": ["أشعة صدر", "تحليل دم", "زراعة بلغم"]
        },
        "allergy": {
            "keywords": ["حساسية", "عطس", "حكة", "عيون دامعة", "طفح جلدي"],
            "ar_name": "حساسية",
            "tests": ["اختبار حساسية", "فحص IgE"]
        },
        "asthma": {
            "keywords": ["ربو", "ضيق تنفس", "صوت صفير", "كحة ليلية"],
            "ar_name": "ربو",
            "tests": ["وظائف تنفسية", "تصوير الصدر"]
        },
        "sinusitis": {
            "keywords": ["جيوب أنفية", "صداع", "ضغط وجه", "احتقان أنف"],
            "ar_name": "التهاب الجيوب الأنفية",
            "tests": ["منظار الأنف", "أشعة مقطعية"]
        },
        "urinary infection": {
            "keywords": ["التهاب بول", "حرقة بول", "تبول متكرر", "ألم أسفل البطن"],
            "ar_name": "التهاب المسالك البولية",
            "tests": ["تحليل بول", "زراعة بول"]
        },
        "anemia": {
            "keywords": ["فقر دم", "تعب", "شحوب", "دوخة", "ضيق نفس"],
            "ar_name": "فقر الدم",
            "tests": ["صورة دم كاملة", "حديد serum"]
        },
        "migraine": {
            "keywords": ["صداع نصفي", "شقيقة", "صداع شديد", "غثيان", "حساسية ضوء"],
            "ar_name": "صداع نصفي",
            "tests": ["فحص أعصاب", "رنين مغناطيسي"]
        },
        "stomach problem": {
            "keywords": ["معدة", "حرقة", "عسر هضم", "غثيان", "انتفاخ", "ألم بطن"],
            "ar_name": "مشاكل المعدة",
            "tests": ["منظار", "تحليل جرثومة المعدة"]
        }
    }
    
    for disease, info in rules.items():
        keywords = info["keywords"]
        matches = sum(1 for keyword in keywords if keyword in symptoms_lower)
        
        if matches > 0:
            probability = min(0.95, 0.20 + (matches / len(keywords)) * 0.75)
            results.append({
                "disease": disease,
                "ar_name": info["ar_name"],
                "probability": round(probability * 100, 1),
                "tests": info["tests"]
            })
    
    results.sort(key=lambda x: x["probability"], reverse=True)
    
    if not results:
        results = [
            {"disease": "unknown", "ar_name": "غير محدد", "probability": 30.0, 
             "tests": ["استشارة طبيب متخصص", "فحص سريري"]}
        ]
    
    return results[:5]

# ======================
# 📄 PDF
# ======================
def generate_pdf(symptoms, results, username=None):
    os.makedirs("static", exist_ok=True)
    doc = SimpleDocTemplate("static/report.pdf")
    styles = getSampleStyleSheet()
    
    content = [
        Paragraph("التقرير الطبي", styles["Title"]),
        Paragraph(f"المستخدم: {username or 'زائر'}", styles["Normal"]),
        Paragraph(f"التاريخ: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Paragraph(f"الأعراض: {symptoms}", styles["Normal"]),
        Paragraph(" ", styles["Normal"]),
        Paragraph("النتائج:", styles["Heading2"])
    ]
    
    for r in results[:5]:
        content.append(Paragraph(f"• {r['ar_name']}: {r['probability']}%", styles["Normal"]))
        tests_text = "الفحوصات: " + "، ".join(r['tests'])
        content.append(Paragraph(tests_text, styles["Normal"]))
        content.append(Paragraph(" ", styles["Normal"]))
    
    doc.build(content)
    return "static/report.pdf"

# ======================
# 🌐 UI ROUTES (Protected)
# ======================
@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session.get('user_name'))

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get('role') != 'doctor':
        flash('هذه الصفحة مخصصة للأطباء فقط', 'danger')
        return redirect(url_for('home'))
    return render_template("dashboard.html", username=session.get('user_name'))

# ======================
# 🔬 API Endpoint
# ======================
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    data = request.get_json(silent=True)
    
    if not data:
        return jsonify({"error": "No JSON data"}), 400
    
    symptoms_input = data.get("symptoms", "").strip()
    
    if not symptoms_input:
        return jsonify({"error": "Empty symptoms"}), 400
    
    results = smart_diagnosis(symptoms_input)
    
    formatted_results = []
    for r in results:
        formatted_results.append({
            "disease": r["ar_name"],
            "probability": r["probability"],
            "tests": r["tests"]
        })
    
    generate_pdf(symptoms_input, formatted_results, session.get('username'))
    
    return jsonify(formatted_results)

# ======================
# 🖥️ HTML Form Endpoint
# ======================
@app.route("/analyze-form", methods=["POST"])
@login_required
def analyze_form():
    symptoms_input = request.form.get("symptoms", "").strip()
    
    if not symptoms_input:
        return "الرجاء إدخال الأعراض", 400
    
    results = smart_diagnosis(symptoms_input)
    
    formatted_results = []
    for r in results:
        formatted_results.append({
            "disease": r["ar_name"],
            "probability": r["probability"],
            "tests": r["tests"]
        })
    
    generate_pdf(symptoms_input, formatted_results, session.get('username'))
    
    return render_template("index.html", results=formatted_results, input_text=symptoms_input, username=session.get('user_name'))

# ======================
# 📥 Download PDF
# ======================
@app.route("/download-pdf")
@login_required
def download_pdf():
    pdf_path = "static/report.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return jsonify({"error": "PDF not found"}), 404

# ======================
# ▶️ RUN
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)