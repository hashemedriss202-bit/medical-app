from flask import Flask, request, jsonify, render_template, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import ml_model

app = Flask(__name__)

# تحميل نموذج الذكاء الاصطناعي
model, symptom_to_idx, symptom_list = ml_model.model, ml_model.symptom_to_idx, ml_model.symptom_list

# ======================
# 📄 PDF
# ======================
def generate_pdf(symptoms, results):
    os.makedirs("static", exist_ok=True)
    
    doc = SimpleDocTemplate("static/report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    
    # إنشاء نمط عربي
    styles.add(ParagraphStyle(name='Arabic', fontName='Helvetica', alignment=TA_RIGHT, fontSize=12))
    styles.add(ParagraphStyle(name='Centered', alignment=TA_CENTER, fontSize=14, textColor='#2E86AB'))
    
    content = [
        Paragraph("<b>🏥 التقرير الطبي</b>", styles['Centered']),
        Spacer(1, 20),
        Paragraph(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Arabic']),
        Paragraph(f"🩺 الأعراض المدخلة: {symptoms}", styles['Arabic']),
        Spacer(1, 15),
        Paragraph("<b>📊 نتائج التحليل:</b>", styles['Arabic']),
        Spacer(1, 10)
    ]
    
    # إضافة النتائج
    for r in results:
        content.append(Paragraph(f"• <b>{r['disease']}</b> - {r['probability']}%", styles['Arabic']))
        if r.get('tests'):
            tests_text = "🧪 الفحوصات الموصى بها: " + "، ".join(r['tests'])
            content.append(Paragraph(tests_text, styles['Arabic']))
        content.append(Spacer(1, 10))
    
    # تذييل
    content.append(Spacer(1, 30))
    content.append(Paragraph("هذا التقرير هو لأغراض استشارية فقط، وليس بديلاً عن استشارة الطبيب.", styles['Arabic']))
    
    doc.build(content)
    return "static/report.pdf"

# ======================
# 🌐 Routes
# ======================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    """واجهة API للتحليل (JSON)"""
    data = request.get_json(silent=True)
    
    if not data:
        return jsonify({"error": "No JSON data"}), 400
    
    symptoms_input = data.get("symptoms", "").strip()
    
    if not symptoms_input:
        return jsonify({"error": "Empty symptoms"}), 400
    
    # استخدام نموذج الذكاء الاصطناعي
    prediction = ml_model.predict_disease(symptoms_input, model, symptom_to_idx, symptom_list)
    
    result = [{
        "disease": prediction['disease_ar'],
        "probability": prediction['confidence'],
        "tests": prediction['suggested_tests'],
        "recommendations": prediction['recommendations']
    }]
    
    generate_pdf(symptoms_input, result)
    
    return jsonify(result)

@app.route("/analyze-form", methods=["POST"])
def analyze_form():
    """واجهة HTML للتحليل"""
    symptoms_input = request.form.get("symptoms", "").strip()
    
    if not symptoms_input:
        return "الرجاء إدخال الأعراض", 400
    
    # استخدام نموذج الذكاء الاصطناعي
    prediction = ml_model.predict_disease(symptoms_input, model, symptom_to_idx, symptom_list)
    
    results = [{
        "disease": prediction['disease_ar'],
        "probability": prediction['confidence'],
        "tests": prediction['suggested_tests'],
        "recommendations": prediction['recommendations']
    }]
    
    # إضافة التشخيصات البديلة
    for alt_disease, alt_prob in prediction['alternatives']:
        if alt_disease != prediction['disease_ar']:
            results.append({
                "disease": alt_disease,
                "probability": alt_prob,
                "tests": ml_model.tests_dict.get(alt_disease, ["استشارة طبيب"]),
                "recommendations": ml_model.get_recommendations(alt_disease)
            })
    
    generate_pdf(symptoms_input, results)
    
    return render_template("index.html", 
                          results=results[:5], 
                          input_text=symptoms_input,
                          matched_symptoms=prediction['matched_symptoms'])

@app.route("/download-pdf")
def download_pdf():
    pdf_path = "static/report.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name="report.pdf")
    return jsonify({"error": "PDF not found"}), 404

@app.route("/diseases")
def diseases_list():
    """عرض قائمة الأمراض المدعومة"""
    diseases = [{"en": k, "ar": ml_model.disease_ar.get(k, k), "symptoms": v} 
                for k, v in ml_model.symptoms_database.items()]
    return jsonify(diseases)

# ======================
# ▶️ RUN
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)