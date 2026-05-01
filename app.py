from flask import Flask, request, jsonify, render_template, send_file
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
# 🧠 SMART ANALYSIS (قاعدة أمراض موسعة)
# ======================
def smart_diagnosis(symptoms):
    """تحليل ذكي للأعراض باستخدام قاعدة معرفة موسعة"""
    symptoms_lower = symptoms.lower()
    results = []
    
    # قاعدة المعرفة الموسعة (مرض -> كلمات مفتاحية)
    rules = {
        "flu": {
            "keywords": ["حمى", "سعال", "احتقان", "إنفلونزا", "رشح", "زكام", "عطس", "تعب", "آلام جسم"],
            "ar_name": "إنفلونزا",
            "tests": ["تحليل CBC", "فحص فيروسات", "مسحة أنف"]
        },
        "cold": {
            "keywords": ["زكام", "رشح", "عطس", "احتقان أنف", "سعال بسيط", "حمى خفيفة"],
            "ar_name": "نزلة برد",
            "tests": ["راحة", "سوائل دافئة", "فيتامين C"]
        },
        "pneumonia": {
            "keywords": ["التهاب رئوي", "ضيق تنفس", "كحة شديدة", "بلغم", "حمى عالية", "ألم صدر"],
            "ar_name": "التهاب رئوي",
            "tests": ["أشعة صدر", "تحليل دم", "زراعة بلغم"]
        },
        "allergy": {
            "keywords": ["حساسية", "عطس", "حكة", "عيون دامعة", "طفح جلدي", "احمرار", "تورم"],
            "ar_name": "حساسية",
            "tests": ["اختبار حساسية", "فحص IgE", "تجنب مسببات الحساسية"]
        },
        "asthma": {
            "keywords": ["ربو", "ضيق تنفس", "صوت صفير", "كحة ليلية", "صعوبة تنفس"],
            "ar_name": "ربو",
            "tests": ["وظائف تنفسية", "تصوير الصدر", "اختبار ميثاكولين"]
        },
        "sinusitis": {
            "keywords": ["جيوب أنفية", "صداع", "ضغط وجه", "احتقان أنف", "مخاط سميك", "ألم أسنان"],
            "ar_name": "التهاب الجيوب الأنفية",
            "tests": ["منظار الأنف", "أشعة مقطعية", "مضادات حيوية"]
        },
        "arthritis": {
            "keywords": ["التهاب مفاصل", "ألم مفاصل", "تورم مفاصل", "تيبس صباحي", "احمرار مفصل"],
            "ar_name": "التهاب المفاصل",
            "tests": ["تحليل الروماتويد", "أشعة مفاصل", "فحص CRP"]
        },
        "urinary infection": {
            "keywords": ["التهاب بول", "حرقة بول", "تبول متكرر", "ألم أسفل البطن", "بول عكر"],
            "ar_name": "التهاب المسالك البولية",
            "tests": ["تحليل بول", "زراعة بول", "موجات فوق صوتية"]
        },
        "anemia": {
            "keywords": ["فقر دم", "تعب", "شحوب", "دوخة", "ضيق نفس", "تساقط شعر", "برودة أطراف"],
            "ar_name": "فقر الدم",
            "tests": ["صورة دم كاملة", "حديد serum", "فيتامين B12"]
        },
        "thyroid": {
            "keywords": ["غدة درقية", "تعب", "تغير وزن", "خفقان", "تساقط شعر", "برودة", "عصبية"],
            "ar_name": "مشاكل الغدة الدرقية",
            "tests": ["تحليل هرمونات الغدة", "موجات فوق صوتية", "فحص T3,T4,TSH"]
        },
        "liver disease": {
            "keywords": ["كبد", "يرقان", "اصفرار", "تعب", "استفراغ", "غثيان", "ألم بطن", "فقدان شهية"],
            "ar_name": "أمراض الكبد",
            "tests": ["إنزيمات الكبد", "الموجات فوق الصوتية", "تحليل وظائف الكبد"]
        },
        "kidney disease": {
            "keywords": ["كلية", "تورم قدم", "تعب", "تبول قليل", "رغوة في البول", "ضغط مرتفع"],
            "ar_name": "أمراض الكلى",
            "tests": ["وظائف الكلى", "تحليل كرياتينين", "يوريا", "موجات فوق صوتية"]
        },
        "migraine": {
            "keywords": ["صداع نصفي", "شقيقة", "صداع شديد", "غثيان", "حساسية ضوء", "ألم خافق"],
            "ar_name": "صداع نصفي",
            "tests": ["فحص أعصاب", "رنين مغناطيسي", "مسكنات"]
        },
        "stomach problem": {
            "keywords": ["معدة", "حرقة", "عسر هضم", "غثيان", "انتفاخ", "ألم بطن", "قرحة"],
            "ar_name": "مشاكل المعدة",
            "tests": ["منظار", "تحليل جرثومة المعدة", "مضادات حموضة"]
        },
        "diabetes": {
            "keywords": ["سكري", "عطش شديد", "تبول كثير", "جوع", "تعب", "زغللة عيون", "تنميل"],
            "ar_name": "سكري",
            "tests": ["تحليل سكر صائم", "سكر تراكمي", "اختبار تحمل الجلوكوز"]
        },
        "blood pressure": {
            "keywords": ["ضغط دم", "ضغط مرتفع", "صداع", "دوخة", "احمرار وجه", "خفقان"],
            "ar_name": "ضغط الدم",
            "tests": ["قياس الضغط", "تحليل دهون", "فحص قلب"]
        },
        "heart disease": {
            "keywords": ["قلب", "ألم صدر", "خفقان", "ضيق نفس", "تعب", "انتفاخ قدمين"],
            "ar_name": "مرض قلبي",
            "tests": ["ECG", "إيكو قلب", "تحليل إنزيمات القلب"]
        },
        "food poisoning": {
            "keywords": ["تسمم غذائي", "استفراغ", "إسهال", "غثيان", "ألم بطن", "حمى", "طعام فاسد"],
            "ar_name": "تسمم غذائي",
            "tests": ["تحليل براز", "زراعة براز", "سوائل وريدية"]
        }
    }
    
    # تحليل الأعراض
    for disease, info in rules.items():
        keywords = info["keywords"]
        matches = sum(1 for keyword in keywords if keyword in symptoms_lower)
        
        if matches > 0:
            # حساب نسبة الاحتمال بناءً على عدد الكلمات المتطابقة
            probability = min(0.95, 0.20 + (matches / len(keywords)) * 0.75)
            results.append({
                "disease": disease,
                "ar_name": info["ar_name"],
                "probability": round(probability * 100, 1),
                "tests": info["tests"],
                "matches": matches
            })
    
    # ترتيب النتائج حسب الاحتمالية
    results.sort(key=lambda x: x["probability"], reverse=True)
    
    # إضافة بيانات احتياطية إذا لم يتم العثور على نتائج
    if not results:
        results = [
            {"disease": "unknown", "ar_name": "غير محدد", "probability": 30.0, 
             "tests": ["استشارة طبيب متخصص", "فحص سريري"], "matches": 0}
        ]
    
    return results[:5]  # إرجاع أفضل 5 نتائج

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
# 🔬 API Endpoint (لـ Flutter أو التطبيقات الأخرى)
# ======================
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)
    
    if not data:
        return jsonify({"error": "No JSON data"}), 400
    
    symptoms_input = data.get("symptoms", "").strip()
    
    if not symptoms_input:
        return jsonify({"error": "Empty symptoms"}), 400
    
    # استخدام التحليل الذكي بدلاً من API الخارجي
    results = smart_diagnosis(symptoms_input)
    
    # تنسيق النتائج
    formatted_results = []
    for r in results:
        formatted_results.append({
            "disease": r["ar_name"],
            "probability": r["probability"],
            "tests": r["tests"]
        })
    
    generate_pdf(symptoms_input, formatted_results)
    
    return jsonify(formatted_results)

# ======================
# 🖥️ HTML Form Endpoint (للواجهة الأمامية)
# ======================
@app.route("/analyze-form", methods=["POST"])
def analyze_form():
    symptoms_input = request.form.get("symptoms", "").strip()
    
    if not symptoms_input:
        return "الرجاء إدخال الأعراض", 400
    
    # استخدام التحليل الذكي
    results = smart_diagnosis(symptoms_input)
    
    # تنسيق النتائج للعرض
    formatted_results = []
    for r in results:
        formatted_results.append({
            "disease": r["ar_name"],
            "probability": r["probability"],
            "tests": r["tests"]
        })
    
    generate_pdf(symptoms_input, formatted_results)
    
    return render_template("index.html", results=formatted_results, input_text=symptoms_input)

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
        tests_text = "الفحوصات: " + "، ".join(r['tests'])
        content.append(Paragraph(tests_text, styles["Normal"]))
        content.append(Paragraph(" ", styles["Normal"]))
    
    doc.build(content)
    return "static/report.pdf"

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