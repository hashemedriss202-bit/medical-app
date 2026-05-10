import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# بيانات الأمراض بالعربية والفحوصات
disease_ar = {
    "Influenza": "إنفلونزا",
    "Common Cold": "نزلة برد",
    "Pneumonia": "التهاب رئوي",
    "Allergy": "حساسية",
    "Asthma": "ربو",
    "Sinusitis": "التهاب الجيوب الأنفية",
    "Urinary Tract Infection": "التهاب المسالك البولية",
    "Anemia": "فقر الدم",
    "Migraine": "صداع نصفي",
    "Gastritis": "التهاب المعدة",
    "Diabetes": "سكري",
    "Hypertension": "ضغط الدم",
    "Arthritis": "التهاب المفاصل",
    "Bronchitis": "التهاب شعبي",
    "Tonsillitis": "التهاب اللوزتين",
    "Conjunctivitis": "التهاب الملتحمة",
    "Dermatitis": "التهاب الجلد",
    "Food Poisoning": "تسمم غذائي",
    "Hepatitis": "التهاب الكبد",
    "Kidney Disease": "أمراض الكلى"
}

tests_dict = {
    "Influenza": ["تحليل CBC", "فحص فيروسات", "مسحة أنف"],
    "Common Cold": ["راحة", "سوائل دافئة", "فيتامين C"],
    "Pneumonia": ["أشعة صدر", "تحليل دم", "زراعة بلغم"],
    "Allergy": ["اختبار حساسية", "فحص IgE", "تجنب مسببات الحساسية"],
    "Asthma": ["وظائف تنفسية", "تصوير الصدر", "اختبار ميثاكولين"],
    "Sinusitis": ["منظار الأنف", "أشعة مقطعية", "مضادات حيوية"],
    "Urinary Tract Infection": ["تحليل بول", "زراعة بول", "موجات فوق صوتية"],
    "Anemia": ["صورة دم كاملة", "حديد serum", "فيتامين B12"],
    "Migraine": ["فحص أعصاب", "رنين مغناطيسي", "مسكنات"],
    "Gastritis": ["منظار", "تحليل جرثومة المعدة", "مضادات حموضة"],
    "Diabetes": ["تحليل سكر صائم", "سكر تراكمي", "اختبار تحمل الجلوكوز"],
    "Hypertension": ["قياس الضغط", "تحليل دهون", "فحص قلب"],
    "Arthritis": ["تحليل الروماتويد", "أشعة مفاصل", "فحص CRP"],
    "Bronchitis": ["أشعة صدر", "تحليل بلغم", "وظائف تنفسية"],
    "Tonsillitis": ["فحص سريري", "مسحة حلق", "تحليل دم"],
    "Conjunctivitis": ["فحص عيون", "مسحة عين", "قطرات مضادة"],
    "Dermatitis": ["فحص جلد", "اختبار حساسية", "مرطبات"],
    "Food Poisoning": ["تحليل براز", "زراعة براز", "سوائل وريدية"],
    "Hepatitis": ["إنزيمات الكبد", "تحليل فيروسات", "موجات فوق صوتية"],
    "Kidney Disease": ["وظائف الكلى", "تحليل كرياتينين", "موجات فوق صوتية"]
}

# قاعدة معرفة للأعراض
symptoms_database = {
    "Influenza": ["حمى", "سعال", "احتقان", "إنفلونزا", "رشح", "تعب", "آلام جسم", "صداع"],
    "Common Cold": ["زكام", "رشح", "عطس", "احتقان أنف", "سعال بسيط", "حمى خفيفة"],
    "Pneumonia": ["التهاب رئوي", "ضيق تنفس", "كحة شديدة", "بلغم", "حمى عالية", "ألم صدر"],
    "Allergy": ["حساسية", "عطس", "حكة", "عيون دامعة", "طفح جلدي", "احمرار", "تورم"],
    "Asthma": ["ربو", "ضيق تنفس", "صوت صفير", "كحة ليلية", "صعوبة تنفس"],
    "Sinusitis": ["جيوب أنفية", "صداع", "ضغط وجه", "احتقان أنف", "مخاط سميك", "ألم أسنان"],
    "Urinary Tract Infection": ["التهاب بول", "حرقة بول", "تبول متكرر", "ألم أسفل البطن", "بول عكر"],
    "Anemia": ["فقر دم", "تعب", "شحوب", "دوخة", "ضيق نفس", "تساقط شعر", "برودة أطراف"],
    "Migraine": ["صداع نصفي", "شقيقة", "صداع شديد", "غثيان", "حساسية ضوء", "ألم خافق"],
    "Gastritis": ["معدة", "حرقة", "عسر هضم", "غثيان", "انتفاخ", "ألم بطن", "قرحة"],
    "Diabetes": ["سكري", "عطش شديد", "تبول كثير", "جوع", "تعب", "زغللة عيون", "تنميل"],
    "Hypertension": ["ضغط دم", "ضغط مرتفع", "صداع", "دوخة", "احمرار وجه", "خفقان"],
    "Arthritis": ["التهاب مفاصل", "ألم مفاصل", "تورم مفاصل", "تيبس صباحي", "احمرار مفصل"],
    "Bronchitis": ["التهاب شعبي", "كحة", "بلغم", "ضيق تنفس", "حمى"],
    "Tonsillitis": ["التهاب لوزتين", "ألم حلق", "صعوبة بلع", "حمى", "تضخم لوزات"],
    "Conjunctivitis": ["التهاب عين", "احمرار عين", "حكة عين", "إفرازات عين", "تورم جفن"],
    "Dermatitis": ["التهاب جلد", "حكة جلد", "احمرار جلد", "طفح جلدي", "جفاف جلد"],
    "Food Poisoning": ["تسمم غذائي", "استفراغ", "إسهال", "غثيان", "ألم بطن", "حمى"],
    "Hepatitis": ["التهاب كبد", "يرقان", "تعب", "استفراغ", "ألم بطن", "فقدان شهية"],
    "Kidney Disease": ["أمراض كلى", "تورم قدم", "تعب", "تبول قليل", "رغوة في البول"]
}

def train_model():
    """بناء وتدريب نموذج التعلم الآلي"""
    all_diseases = []
    all_symptoms_set = set()
    
    # تحضير البيانات من قاعدة المعرفة
    data = []
    for disease, symptoms in symptoms_database.items():
        all_diseases.append(disease)
        for symptom in symptoms:
            all_symptoms_set.add(symptom)
        data.append({"disease": disease, "symptoms": symptoms})
    
    # إنشاء قاموس لترميز الأعراض
    symptom_list = sorted(list(all_symptoms_set))
    symptom_to_idx = {symptom: i for i, symptom in enumerate(symptom_list)}
    
    # إنشاء مصفوفة الميزات
    X = []
    y = []
    
    for disease, symptoms in symptoms_database.items():
        row = [0] * len(symptom_list)
        for symptom in symptoms:
            if symptom in symptom_to_idx:
                row[symptom_to_idx[symptom]] = 1
        X.append(row)
        y.append(disease)
    
    X = np.array(X)
    y = np.array(y)
    
    # تدريب النموذج
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # حفظ النموذج والأدوات
    joblib.dump(model, 'disease_model.pkl')
    joblib.dump(symptom_to_idx, 'symptom_idx.pkl')
    joblib.dump(symptom_list, 'symptom_list.pkl')
    
    print(f"✅ تم تدريب النموذج بنجاح على {len(symptoms_database)} مرض")
    return model, symptom_to_idx, symptom_list

def load_model():
    """تحميل النموذج المدرب"""
    if os.path.exists('disease_model.pkl'):
        model = joblib.load('disease_model.pkl')
        symptom_to_idx = joblib.load('symptom_idx.pkl')
        symptom_list = joblib.load('symptom_list.pkl')
        print("✅ تم تحميل النموذج بنجاح")
        return model, symptom_to_idx, symptom_list
    else:
        print("⚠️ لم يتم العثور على نموذج مدرب، جارٍ التدريب...")
        return train_model()

def predict_disease(symptoms_text, model, symptom_to_idx, symptom_list):
    """التنبؤ بالمرض بناءً على الأعراض المدخلة"""
    symptoms_list = [s.strip().lower() for s in symptoms_text.replace('،', ',').split(',')]
    
    # إنشاء متجه الأعراض
    input_vector = [0] * len(symptom_list)
    for symptom in symptoms_list:
        if symptom in symptom_to_idx:
            input_vector[symptom_to_idx[symptom]] = 1
    
    # التنبؤ
    prediction = model.predict([input_vector])[0]
    probabilities = model.predict_proba([input_vector])[0]
    confidence = max(probabilities) * 100
    
    # الحصول على أفضل 3 أمراض محتملة
    top_3_indices = np.argsort(probabilities)[-3:][::-1]
    alternatives = [(model.classes_[i], probabilities[i] * 100) for i in top_3_indices]
    
    # الحصول على الأعراض المتطابقة
    matched_symptoms = []
    for symptom in symptoms_list:
        if symptom in symptom_to_idx and input_vector[symptom_to_idx[symptom]] == 1:
            matched_symptoms.append(symptom)
    
    return {
        "disease_en": prediction,
        "disease_ar": disease_ar.get(prediction, prediction),
        "confidence": round(confidence, 2),
        "alternatives": [(disease_ar.get(d, d), round(prob, 2)) for d, prob in alternatives],
        "matched_symptoms": matched_symptoms,
        "suggested_tests": tests_dict.get(prediction, ["استشارة طبيب متخصص"]),
        "recommendations": get_recommendations(prediction)
    }

def get_recommendations(disease):
    """توصيات عامة للمرض"""
    recommendations = {
        "Influenza": ["الراحة التامة", "شرب سوائل كثيرة", "تناول مسكنات للحرارة"],
        "Common Cold": ["الراحة", "سوائل دافئة", "غرغرة بالماء والملح"],
        "Pneumonia": ["مراجعة طبيب فوراً", "الراحة التامة", "متابعة التنفس"],
        "Allergy": ["تجنب مسببات الحساسية", "استخدام مضادات الهيستامين", "شرب الماء"],
        "Asthma": ["استخدام البخاخ", "تجنب المهيجات", "مراجعة طبيب"],
        "Urinary Tract Infection": ["شرب ماء بكثرة", "تجنب المنبهات", "مراجعة طبيب"],
        "Anemia": ["زيادة الحديد في الطعام", "تناول فيتامين C", "مراجعة طبيب"],
        "Migraine": ["الراحة في غرفة مظلمة", "تجنب الضوضاء", "شرب ماء"],
        "Diabetes": ["مراقبة السكر", "اتباع نظام غذائي", "ممارسة رياضة"],
        "Hypertension": ["تقليل الملح", "ممارسة رياضة", "مراقبة الضغط"]
    }
    return recommendations.get(disease, ["استشارة طبيب متخصص", "مراجعة الحالة بدقة"])

# تدريب النموذج عند استيراد الملف
model, symptom_to_idx, symptom_list = load_model()