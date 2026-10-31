import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Set UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

print("=== Generating Multilingual Test Documents ===")

# Locate fonts
FONT_DIR = "/usr/share/fonts/truetype"
noto_dir = os.path.join(FONT_DIR, "noto")

font_paths = {
    "latin_reg": os.path.join(noto_dir, "NotoSans-Regular.ttf"),
    "latin_bold": os.path.join(noto_dir, "NotoSans-Bold.ttf"),
    "telugu_reg": os.path.join(noto_dir, "NotoSansTelugu-Regular.ttf"),
    "telugu_bold": os.path.join(noto_dir, "NotoSansTelugu-Bold.ttf"),
    "deva_reg": os.path.join(noto_dir, "NotoSansDevanagari-Regular.ttf"),
    "deva_bold": os.path.join(noto_dir, "NotoSansDevanagari-Bold.ttf"),
}

# Fallback check
for k, p in list(font_paths.items()):
    if not os.path.exists(p):
        print(f"Warning: {p} not found, searching alternative...")
        if "telugu" in k:
            alt = os.path.join(noto_dir, "NotoSerifTelugu-Regular.ttf")
            if os.path.exists(alt):
                font_paths[k] = alt
        elif "deva" in k:
            alt = os.path.join(noto_dir, "NotoSerifDevanagari-Regular.ttf")
            if os.path.exists(alt):
                font_paths[k] = alt

print("Resolved Font Paths:")
for k, p in font_paths.items():
    print(f"  {k}: {p} (exists={os.path.exists(p)})")


def create_telugu_prescription(output_pdf_path, output_png_path):
    width, height = 1654, 2338  # ~200 DPI A4
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    f_header = ImageFont.truetype(font_paths["latin_bold"], 42)
    f_sub = ImageFont.truetype(font_paths["latin_reg"], 26)
    f_label = ImageFont.truetype(font_paths["latin_bold"], 30)
    f_body = ImageFont.truetype(font_paths["latin_reg"], 28)
    f_telugu = ImageFont.truetype(font_paths["telugu_reg"], 28)
    f_telugu_bold = ImageFont.truetype(font_paths["telugu_bold"], 32)
    f_small = ImageFont.truetype(font_paths["latin_reg"], 22)

    # Decorative header banner
    draw.rectangle([(60, 60), (width - 60, 240)], fill=(240, 246, 255), outline=(37, 99, 235), width=3)
    draw.text((90, 85), "APOLLO CLINIC & HEALTHCARE", fill=(30, 58, 138), font=f_header)
    draw.text((90, 140), "Dr. K. Srinivas, MBBS, MD (Internal Medicine) | Reg No: TS-45920", fill=(55, 65, 81), font=f_sub)
    draw.text((90, 180), "Road No 36, Jubilee Hills, Hyderabad, Telangana | Ph: +91 40 2345 6789", fill=(100, 116, 139), font=f_small)

    # Patient info box
    draw.rectangle([(60, 260), (width - 60, 410)], fill=(248, 250, 252), outline=(203, 213, 225), width=2)
    draw.text((90, 280), "Patient Name: Ramesh Rao", fill=(15, 23, 42), font=f_label)
    draw.text((650, 280), "Age: 52 Yrs", fill=(15, 23, 42), font=f_body)
    draw.text((950, 280), "Gender: Male", fill=(15, 23, 42), font=f_body)
    draw.text((1250, 280), "Date: 12-Oct-2026", fill=(15, 23, 42), font=f_body)
    draw.text((90, 340), "ABHA ID: 91-4432-8891-2011", fill=(30, 64, 175), font=f_label)
    draw.text((650, 340), "Contact: +91 98480 12345", fill=(15, 23, 42), font=f_body)

    # Vitals & Diagnosis
    y = 440
    draw.text((90, y), "CLINICAL OBSERVATIONS & LAB VALUES", fill=(30, 58, 138), font=f_label)
    y += 50
    draw.line([(90, y), (width - 90, y)], fill=(203, 213, 225), width=2)
    y += 20
    draw.text((90, y), "Diagnosis: Type 2 Diabetes Mellitus with Essential Hypertension", fill=(185, 28, 28), font=f_label)
    y += 45
    draw.text((90, y), "Blood Pressure: 140/90 mmHg  |  Pulse: 76 bpm  |  BMI: 26.4 kg/m2", fill=(15, 23, 42), font=f_body)
    y += 45
    draw.text((90, y), "Fasting Blood Sugar (FBS): 162 mg/dL  |  HbA1c: 7.8%  |  Serum Creatinine: 0.9 mg/dL", fill=(15, 23, 42), font=f_body)

    # Prescription Section (Rx) - Telugu & English mixed
    y += 90
    draw.text((90, y), "PRESCRIPTION (మందుల వివరాలు) [Rx]", fill=(30, 58, 138), font=f_telugu_bold)
    y += 50
    draw.line([(90, y), (width - 90, y)], fill=(37, 99, 235), width=3)
    y += 30

    rx_items = [
        ("1. Tab Metformin 500mg", "రోజుకు రెండుసార్లు భోజనం తర్వాత తీసుకోండి (1 - 0 - 1)"),
        ("2. Tab Telmisartan 40mg", "ఉదయం ఖాళీ కడుపుతో ఒకసారి వేసుకోండి (1 - 0 - 0)"),
        ("3. Tab Glimepiride 1mg", "ఉదయం అల్పాహారానికి 15 నిమిషాల ముందు తీసుకోండి (1 - 0 - 0)"),
        ("4. Cap Vitamin D3 60k", "వారానికి ఒకసారి భోజనం తర్వాత వేసుకోండి (శనివారం)")
    ]

    for med, telugu_inst in rx_items:
        # Med name (English)
        draw.text((100, y), med, fill=(15, 23, 42), font=f_label)
        y += 45
        # Telugu instructions
        draw.text((140, y), f"మోతాదు: {telugu_inst}", fill=(30, 41, 59), font=f_telugu)
        y += 65

    # Instructions & Precautions (Telugu)
    y += 30
    draw.rectangle([(80, y), (width - 80, y + 260)], fill=(254, 252, 232), outline=(234, 179, 8), width=2)
    y_box = y + 20
    draw.text((110, y_box), "వైద్యుల సలహాలు మరియు సూచనలు (Patient Instructions):", fill=(161, 98, 7), font=f_telugu_bold)
    y_box += 50
    draw.text((110, y_box), "• ప్రతిరోజు 30 నిమిషాలు ఉదయం నడక వ్యాయామం తప్పనిసరిగా చేయండి.", fill=(15, 23, 42), font=f_telugu)
    y_box += 45
    draw.text((110, y_box), "• తీపి పదార్థాలు, వేపుళ్ళు మరియు ఉప్పు వినియోగాన్ని పూర్తిగా తగ్గించండి.", fill=(15, 23, 42), font=f_telugu)
    y_box += 45
    draw.text((110, y_box), "• నీరసం లేదా మైకం వచ్చినట్లయితే వెంటనే రక్తంలో చక్కెర పరీక్షించి గ్లూకోజ్ తీసుకోండి.", fill=(15, 23, 42), font=f_telugu)
    y_box += 45
    draw.text((110, y_box), "• 15 రోజుల తర్వాత ఖాళీ కడుపుతో షుగర్ పరీక్ష చేయించి డాక్టర్‌ను సంప్రదించండి.", fill=(15, 23, 42), font=f_telugu)

    # Footer & Signature
    y = 2050
    draw.line([(90, y), (width - 90, y)], fill=(203, 213, 225), width=2)
    y += 40
    draw.text((90, y), "Next Follow-up Date: 27-Oct-2026", fill=(100, 116, 139), font=f_body)
    draw.text((1050, y), "డాక్టర్ సంతకం / Doctor Signature:", fill=(30, 58, 138), font=f_telugu)
    y += 60
    draw.text((1150, y), "Dr. K. Srinivas, MD", fill=(15, 23, 42), font=f_label)

    # Save PNG and PDF
    img.save(output_png_path, "PNG", quality=95)
    img.save(output_pdf_path, "PDF", resolution=200.0)
    print(f"Generated Telugu Prescription: {output_pdf_path} & {output_png_path}")


def create_hindi_prescription(output_pdf_path, output_png_path):
    width, height = 1654, 2338  # ~200 DPI A4
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    f_header = ImageFont.truetype(font_paths["latin_bold"], 42)
    f_sub = ImageFont.truetype(font_paths["latin_reg"], 26)
    f_label = ImageFont.truetype(font_paths["latin_bold"], 30)
    f_body = ImageFont.truetype(font_paths["latin_reg"], 28)
    f_hindi = ImageFont.truetype(font_paths["deva_reg"], 28)
    f_hindi_bold = ImageFont.truetype(font_paths["deva_bold"], 32)
    f_small = ImageFont.truetype(font_paths["latin_reg"], 22)

    # Decorative header banner
    draw.rectangle([(60, 60), (width - 60, 240)], fill=(240, 253, 250), outline=(13, 148, 136), width=3)
    draw.text((90, 85), "MAX SUPER SPECIALITY HOSPITAL", fill=(17, 94, 89), font=f_header)
    draw.text((90, 140), "Dr. Rajesh Verma, MBBS, DNB (Internal Medicine) | Reg No: DMC-68421", fill=(55, 65, 81), font=f_sub)
    draw.text((90, 180), "Press Enclave Road, Saket, New Delhi - 110017 | Ph: +91 11 4123 4567", fill=(100, 116, 139), font=f_small)

    # Patient info box
    draw.rectangle([(60, 260), (width - 60, 410)], fill=(248, 250, 252), outline=(203, 213, 225), width=2)
    draw.text((90, 280), "Patient Name: Sunita Sharma", fill=(15, 23, 42), font=f_label)
    draw.text((650, 280), "Age: 46 Yrs", fill=(15, 23, 42), font=f_body)
    draw.text((950, 280), "Gender: Female", fill=(15, 23, 42), font=f_body)
    draw.text((1250, 280), "Date: 12-Oct-2026", fill=(15, 23, 42), font=f_body)
    draw.text((90, 340), "ABHA ID: 14-8821-3341-9920", fill=(17, 94, 89), font=f_label)
    draw.text((650, 340), "Contact: +91 98110 54321", fill=(15, 23, 42), font=f_body)

    # Vitals & Diagnosis
    y = 440
    draw.text((90, y), "CLINICAL OBSERVATIONS & LAB VALUES", fill=(17, 94, 89), font=f_label)
    y += 50
    draw.line([(90, y), (width - 90, y)], fill=(203, 213, 225), width=2)
    y += 20
    draw.text((90, y), "Diagnosis: Acute Febrile Illness / Viral Fever with Mild Dehydration", fill=(185, 28, 28), font=f_label)
    y += 45
    draw.text((90, y), "Temperature: 101.4 F  |  Pulse: 92 bpm  |  SpO2: 98% on room air", fill=(15, 23, 42), font=f_body)
    y += 45
    draw.text((90, y), "Platelet Count: 185,000 /mcL  |  Hemoglobin (Hb): 12.2 g/dL  |  TLC: 6,400 /mcL", fill=(15, 23, 42), font=f_body)

    # Prescription Section (Rx) - Hindi & English mixed
    y += 90
    draw.text((90, y), "PRESCRIPTION (दवाओं का विवरण) [Rx]", fill=(17, 94, 89), font=f_hindi_bold)
    y += 50
    draw.line([(90, y), (width - 90, y)], fill=(13, 148, 136), width=3)
    y += 30

    rx_items = [
        ("1. Tab Paracetamol 650mg", "दिन में तीन बार खाने के बाद बुखार होने पर लें (1 - 1 - 1)"),
        ("2. Tab Pantoprazole 40mg", "सुबह खाली पेट एक गोली नाश्ते से 30 मिनट पहले लें (1 - 0 - 0)"),
        ("3. Tab Cetirizine 10mg", "रात को सोने से पहले एक गोली लें (0 - 0 - 1)"),
        ("4. ORS घोल (Electrolyte)", "एक पैकेट 1 लीटर उबले पानी में मिलाकर दिनभर घूंट-घूंट पिएं")
    ]

    for med, hindi_inst in rx_items:
        draw.text((100, y), med, fill=(15, 23, 42), font=f_label)
        y += 45
        draw.text((140, y), f"खुराक / निर्देश: {hindi_inst}", fill=(30, 41, 59), font=f_hindi)
        y += 65

    # Instructions & Precautions (Hindi)
    y += 30
    draw.rectangle([(80, y), (width - 80, y + 260)], fill=(254, 242, 242), outline=(239, 68, 68), width=2)
    y_box = y + 20
    draw.text((110, y_box), "चिकित्सक के महत्वपूर्ण निर्देश (Patient Care Instructions):", fill=(185, 28, 28), font=f_hindi_bold)
    y_box += 50
    draw.text((110, y_box), "• भरपूर मात्रा में पानी, नारियल पानी और ताजा तरल पदार्थ का सेवन करें।", fill=(15, 23, 42), font=f_hindi)
    y_box += 45
    draw.text((110, y_box), "• पूरी तरह आराम करें तथा तैलीय एवं भारी भोजन से परहेज रखें।", fill=(15, 23, 42), font=f_hindi)
    y_box += 45
    draw.text((110, y_box), "• बुखार 102 डिग्री से अधिक होने पर माथे पर ठंडे पानी की पट्टी रखें।", fill=(15, 23, 42), font=f_hindi)
    y_box += 45
    draw.text((110, y_box), "• यदि 3 दिन बाद भी बुखार जारी रहे तो तुरंत प्लेटलेट जांच कराएं।", fill=(15, 23, 42), font=f_hindi)

    # Footer & Signature
    y = 2050
    draw.line([(90, y), (width - 90, y)], fill=(203, 213, 225), width=2)
    y += 40
    draw.text((90, y), "Next Follow-up Date: 15-Oct-2026", fill=(100, 116, 139), font=f_body)
    draw.text((1050, y), "चिकित्सक हस्ताक्षर / Doctor Signature:", fill=(17, 94, 89), font=f_hindi)
    y += 60
    draw.text((1150, y), "Dr. Rajesh Verma, DNB", fill=(15, 23, 42), font=f_label)

    # Save PNG and PDF
    img.save(output_png_path, "PNG", quality=95)
    img.save(output_pdf_path, "PDF", resolution=200.0)
    print(f"Generated Hindi Prescription: {output_pdf_path} & {output_png_path}")


if __name__ == "__main__":
    out_dir = "/home/ubuntu/multilingual_test"
    os.makedirs(out_dir, exist_ok=True)
    
    tel_pdf = os.path.join(out_dir, "dummy_telugu_rx.pdf")
    tel_png = os.path.join(out_dir, "dummy_telugu_rx.png")
    create_telugu_prescription(tel_pdf, tel_png)

    hin_pdf = os.path.join(out_dir, "dummy_hindi_rx.pdf")
    hin_png = os.path.join(out_dir, "dummy_hindi_rx.png")
    create_hindi_prescription(hin_pdf, hin_png)

    print("Dummy PDFs and high-res images created successfully!")
