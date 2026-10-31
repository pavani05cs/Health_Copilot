import sqlite3

conn = sqlite3.connect('/home/ubuntu/health_copilot.db')
c = conn.cursor()

# 1. Insert Vineetha if not exists
c.execute("""
INSERT OR IGNORE INTO patients (patient_id, abha_id, full_name, age, gender, contact_phone, created_at)
VALUES ('PAT-VINEETHA-21F', '91-8842-1920-2026', 'Vineetha', 21, 'Female', '+91 97012 34567', datetime('now'));
""")

# 2. Re-assign Thyrocare encounters to Vineetha
thyrocare_encs = [r[0] for r in c.execute("SELECT encounter_id FROM encounters WHERE hospital_name LIKE '%Thyrocare%' OR doctor_name LIKE '%Praveen%'").fetchall()]
print('Found Thyrocare encounters to link to Vineetha:', thyrocare_encs)

for enc_id in thyrocare_encs:
    c.execute("UPDATE encounters SET patient_id = 'PAT-VINEETHA-21F' WHERE encounter_id = ?;", (enc_id,))
    c.execute("UPDATE lab_observations SET patient_id = 'PAT-VINEETHA-21F' WHERE encounter_id = ?;", (enc_id,))
    c.execute("UPDATE medications SET patient_id = 'PAT-VINEETHA-21F' WHERE encounter_id = ?;", (enc_id,))
    c.execute("UPDATE vitals SET patient_id = 'PAT-VINEETHA-21F' WHERE encounter_id = ?;", (enc_id,))
    c.execute("UPDATE diagnoses SET patient_id = 'PAT-VINEETHA-21F' WHERE encounter_id = ?;", (enc_id,))
    c.execute("UPDATE clinical_instructions SET patient_id = 'PAT-VINEETHA-21F' WHERE encounter_id = ?;", (enc_id,))

conn.commit()

print('\nUpdated patients list in database:')
for p in c.execute("SELECT patient_id, full_name, age, gender, abha_id FROM patients").fetchall():
    enc_count = c.execute("SELECT count(*) FROM encounters WHERE patient_id = ?", (p[0],)).fetchone()[0]
    lab_count = c.execute("SELECT count(*) FROM lab_observations WHERE patient_id = ?", (p[0],)).fetchone()[0]
    print(f"Patient {p[1]} ({p[0]}, {p[3]}, {p[2]}y): {enc_count} encounters, {lab_count} lab tests")

conn.close()
