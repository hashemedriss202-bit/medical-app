from flask import Flask, request, jsonify, render_template, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from datetime import datetime
import os
import numpy as np
import joblib

app = Flask(__name__)

# ======================
# تحميل النموذج والبيانات
# ======================
model = None
label_encoder = None
symptom_list = None
diseases_database = None

try:
    model = joblib.load("models/disease_model.pkl")
    label_encoder = joblib.load("models/label_encoder.pkl")
    symptom_list = joblib.load("models/symptom_list.pkl")
    diseases_database = joblib.load("models/diseases_database.pkl")
    print(f"✅ تم تحميل النموذج: {len(label_encoder.classes_)} مرض")
except Exception as e:
    print(f"⚠️ خطأ في تحميل النموذج: {e}")

# ======================
# قاموس الفحوصات والتوصيات لكل مرض
# ======================
tests_dict = {
    "إنفلونزا": ["تحليل CBC", "فحص فيروسات", "مسحة أنف", "راحة تامة"],
    "نزلة برد": ["راحة", "سوائل دافئة", "فيتامين C", "غرغرة بالماء والملح"],
    "التهاب رئوي": ["أشعة صدر", "تحليل دم", "زراعة بلغم", "مضادات حيوية"],
    "كورونا": ["مسحة PCR", "تحليل أضداد", "صورة صدر", "عزل منزلي"],
    "صداع نصفي": ["فحص أعصاب", "رنين مغناطيسي", "مسكنات", "راحة في مكان مظلم"],
    "حساسية": ["اختبار حساسية", "فحص IgE", "مضادات هيستامين", "تجنب المسببات"],
    "ربو": ["وظائف تنفسية", "تصوير الصدر", "بخاخ موسع", "تجنب المهيجات"],
    "سكري": ["تحليل سكر صائم", "سكر تراكمي", "تحليل بول", "نظام غذائي"],
    "ضغط الدم": ["قياس الضغط", "تحليل دهون", "تخطيط قلب", "تقليل الملح"],
    "التهاب المعدة": ["منظار", "تحليل جرثومة المعدة", "مضادات حموضة", "تجنب المنبهات"],
    "التهاب المسالك": ["تحليل بول", "زراعة بول", "مضادات حيوية", "شرب ماء"],
    "فقر الدم": ["صورة دم كاملة", "حديد serum", "مكملات حديد", "تغذية متوازنة"],
    "التهاب المفاصل": ["تحليل الروماتويد", "أشعة مفاصل", "علاج طبيعي", "مسكنات"],
    "التهاب شعبي": ["أشعة صدر", "تحليل بلغم", "موسعات شعب", "راحة"],
    "التهاب الجيوب": ["منظار الأنف", "أشعة مقطعية", "مضادات حيوية", "بخاخات أنف"],
    "التهاب اللوزتين": ["فحص سريري", "مسحة حلق", "مضادات حيوية", "سوائل دافئة"],
    "تسمم غذائي": ["تحليل براز", "زراعة براز", "سوائل وريدية", "راحة"],
    "التهاب الكبد": ["إنزيمات الكبد", "تحليل فيروسات", "راحة", "تجنب الكحول"],
    "ملاريا": ["مسحة دم", "اختبار سريع", "مضادات ملاريا", "راحة"],
    "تيفوئيد": ["اختبار فيدال", "زراعة دم", "مضادات حيوية", "سوائل"],
    "حمى الضنك": ["تحليل NS1", "تحليل IgM", "سوائل", "راحة", "مراقبة الصفائح"],
    "السل": ["اختبار الجلد", "أشعة صدر", "علاج رباعي", "عزل"],
    "اليرقان": ["إنزيمات الكبد", "تحليل بول", "راحة", "سوائل"],
    "جدري الماء": ["فحص سريري", "مضادات فيروس", "راحة", "تجنب الخدش"],
    "عدوى فطرية": ["فحص الجلد", "زراعة فطرية", "مضادات فطرية", "نظافة"],
    "حب الشباب": ["فحص جلد", "كريمات موضعية", "نظافة", "تجنب الدهون"],
    "بواسير": ["فحص شرجي", "كريمات", "ملينات", "ماء دافئ"],
    "قرحة المعدة": ["منظار", "تحليل جرثومة", "مضادات حيوية", "مضادات حموضة"],
    "انزلاق غضروفي": ["رنين مغناطيسي", "علاج طبيعي", "مسكنات", "راحة"],
    "فرط الدرقية": ["تحليل هرمونات", "موجات فوق صوتية", "أدوية", "متابعة"],
    "قصور الدرقية": ["تحليل هرمونات", "علاج تعويضي", "متابعة", "غذاء متوازن"]
}

# ======================
# دالة التشخيص الرئيسية
# ======================
def predict_disease(symptoms_text):
    """تشخيص المرض بناءً على الأعراض المدخلة"""
    if model is None:
        return {"disease": "إنفلونزا", "confidence": 50, "tests": ["فحص سريري"]}
    
    # تنظيف الأعراض المدخلة
    symptoms_input = [s.strip() for s in symptoms_text.replace('،', ',').split(',')]
    
    # إنشاء متجه الأعراض
    input_vector = [0] * len(symptom_list)
    matched_symptoms = []
    
    for i, symptom in enumerate(symptom_list):
        if symptom in symptoms_input:
            input_vector[i] = 1
            matched_symptoms.append(symptom)
    
    # التنبؤ بالمرض
    prediction = model.predict([input_vector])[0]
    disease = label_encoder.inverse_transform([prediction])[0]
    
    # حساب نسبة الثقة
    probabilities = model.predict_proba([input_vector])[0]
    confidence = max(probabilities) * 100
    
    # الحصول على الفحوصات
    tests = tests_dict.get(disease, ["فحص سريري", "استشارة طبيب"])
    
    # الحصول على الأعراض المميزة للمرض
    disease_symptoms = diseases_database.get(disease, [])
    
    return {
        "disease": disease,
        "confidence": round(confidence, 1),
        "matched_symptoms": matched_symptoms,
        "matched_count": len(matched_symptoms),
        "total_symptoms": len(symptoms_input),
        "tests": tests,
        "disease_symptoms": disease_symptoms
    }

# ======================
# إنشاء تقرير PDF
# ======================
def generate_pdf(symptoms, result):
    os.makedirs("static", exist_ok=True)
    doc = SimpleDocTemplate("static/report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    
    content = [
        Paragraph("<b>🏥 التقرير الطبي</b>", styles['Title']),
        Spacer(1, 20),
        Paragraph(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']),
        Paragraph(f"🩺 الأعراض المدخلة: {symptoms}", styles['Normal']),
        Spacer(1, 15),
        Paragraph(f"<b>📊 التشخيص المحتمل:</b> {result['disease']} - {result['confidence']}%", styles['Normal']),
        Spacer(1, 10),
        Paragraph("<b>🧪 الفحوصات الموصى بها:</b>", styles['Normal'])
    ]
    
    for test in result.get('tests', []):
        content.append(Paragraph(f"• {test}", styles['Normal']))
    
    doc.build(content)
    return "static/report.pdf"

# ======================
# Routes
# ======================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze-form", methods=["POST"])
def analyze_form():
    symptoms_input = request.form.get("symptoms", "").strip()
    
    if not symptoms_input:
        return "الرجاء إدخال الأعراض", 400
    
    result = predict_disease(symptoms_input)
    generate_pdf(symptoms_input, result)
    
    results_display = [{
        "disease": result['disease'],
        "probability": result['confidence'],
        "tests": result.get('tests', [])
    }]
    
    return render_template("index.html", 
                          results=results_display, 
                          input_text=symptoms_input,
                          matched_count=result.get('matched_count', 0))

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON data"}), 400
    
    symptoms_input = data.get("symptoms", "").strip()
    if not symptoms_input:
        return jsonify({"error": "Empty symptoms"}), 400
    
    result = predict_disease(symptoms_input)
    return jsonify(result)

@app.route("/download-pdf")
def download_pdf():
    pdf_path = "static/report.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name="medical_report.pdf")
    return jsonify({"error": "PDF not found"}), 404

@app.route("/diseases")
def get_diseases():
    """عرض قائمة جميع الأمراض المدعومة"""
    if diseases_database:
        return jsonify({
            "diseases": list(diseases_database.keys()),
            "total": len(diseases_database)
        })
    return jsonify({"error": "No data"}), 500
@app.route('/service-worker.js')
def service_worker():
    return send_file('static/service-worker.js')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)