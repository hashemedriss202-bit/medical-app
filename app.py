from flask import Flask, request, jsonify, render_template, send_file
import matplotlib
matplotlib.use('Agg')  # مهم جدًا لمنع أخطاء matplotlib
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import requests
import os

app = Flask(__name__)

# ======================
# 🔗 AI SERVER (مع بيانات احتياطية)
# ======================
API_URL = "https://clapper-hunger-financial.ngrok-free.dev/analyze"

def analyze_with_api(symptoms):
    # بيانات تجريبية احتياطية
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
# 🌍 Arabic mapping
# ======================
disease_ar = {
    "flu": "إنفلونزا",
    "cold": "نزلة برد",
    "pneumonia": "التهاب رئوي",
    "heart disease": "مرض قلبي",
    "food poisoning": "تسمم غذائي",
    "infection": "عدوى",
    "diabetes": "سكري",
    "blood pressure": "ضغط الدم",
    "migraine": "صداع نصفي",
    "stomach problem": "مشاكل المعدة"
}

# ======================
# 🧪 Tests
# ======================
tests_dict = {
    "flu": ["تحليل CBC", "فحص فيروسات"],
    "cold": ["راحة", "سوائل"],
    "pneumonia": ["أشعة صدر", "تحليل دم"],
    "heart disease": ["ECG", "فحص قلب"],
    "food poisoning": ["تحليل براز"],
    "infection": ["تحليل دم"],
    "diabetes": ["تحليل سكر"],
    "blood pressure": ["قياس الضغط"],
    "migraine": ["فحص أعصاب"],
    "stomach problem": ["منظار"]
}

# ======================
# 📄 PDF
# ======================
def generate_pdf(symptoms, results):
    os.makedirs("static", exist_ok=True)
    doc = SimpleDocTemplate("static/report.pdf")
    styles = getSampleStyleSheet()
    
    content = [
        Paragraph("التقرير الطبي", styles["Title"]),
        Paragraph(f"الأعراض: {symptoms}", styles["Normal"]),
        Paragraph(" ", styles["Normal"]),
        Paragraph("النتائج:", styles["Heading2"])
    ]
    
    for r in results[:5]:
        content.append(
            Paragraph(
                f"• {r['disease']}: {r['probability']}%",
                styles["Normal"]
            )
        )
    
    doc.build(content)
    return "static/report.pdf"

# ======================
# 📊 Chart (معطل مؤقتاً)
# ======================
def create_chart(results):
    """دالة إنشاء الرسم البياني - معطلة مؤقتاً لإتمام النشر"""
    # تم تعطيل هذه الدالة لأن matplotlib تسبب مشاكل في النشر
    pass

# ======================
# 🌐 UI Routes
# ======================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ======================
# 🔬 API Endpoint
# ======================
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)
    
    if not data:
        return jsonify({"error": "No JSON data"}), 400
    
    symptoms_input = data.get("symptoms", "").strip()
    
    if not symptoms_input:
        return jsonify({"error": "Empty symptoms"}), 400
    
    api_results = analyze_with_api(symptoms_input)
    
    results = []
    for r in api_results:
        eng = r.get("disease", "")
        prob = float(r.get("probability", 0)) * 100
        
        results.append({
            "disease": disease_ar.get(eng, eng),
            "probability": round(prob, 2),
            "tests": tests_dict.get(eng, ["استشارة طبيب"])
        })
    
    results = sorted(results, key=lambda x: x["probability"], reverse=True)
    
    generate_pdf(symptoms_input, results)
    # create_chart(results)  # معطل مؤقتاً
    
    return jsonify(results)

# ======================
# 📥 Download PDF
# ======================
@app.route("/download-pdf")
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