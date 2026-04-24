import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request
import pandas as pd
import os
import PyPDF2
from werkzeug.utils import secure_filename

# -------------------- SETUP --------------------
app = Flask(__name__)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Folders
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "generated_paper_result"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Dataset
DATASET_PATH = "database/os_250_full_real_clean.csv"
df = pd.read_csv(DATASET_PATH)


# -------------------- ROUTES --------------------

# Home Page
@app.route('/')
def home():
    subjects = df['subject_name'].unique()
    return render_template("index.html", subjects=subjects)


# Generate Page
@app.route('/generate')
def generate():
    subjects = df['subject_name'].unique()
    return render_template("generate.html", subjects=subjects)


# Generate Paper
@app.route('/generate_paper', methods=['POST'])
def generate_paper():

    subject = request.form['subject']
    unit = request.form['unit']
    difficulty = request.form['difficulty']
    total_questions = int(request.form['total_questions'])

    filtered = df[
        (df['subject_name'] == subject) &
        (df['unit_number'].astype(str) == unit) &
        (df['difficulty_level'] == difficulty)
    ]

    questions = filtered.sample(
        min(total_questions, len(filtered))
    )

    return render_template(
        "generate.html",
        subjects=df['subject_name'].unique(),
        questions=questions.to_dict(orient='records')
    )


# Evaluate Page
@app.route('/evaluate')
def evaluate():
    return render_template("evaluate.html")


# -------------------- AI EVALUATION --------------------
@app.route('/evaluate_answer', methods=['POST'])
def evaluate_answer():

    student_answer = request.form.get('student_answer', '').strip()
    max_marks = int(request.form.get('max_marks', 10))

    # -------- PDF Upload --------
    uploaded_text = ''
    file = request.files.get('answer_pdf')

    if file and file.filename.endswith('.pdf'):
        fname = secure_filename(file.filename)
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        file.save(fpath)

        with open(fpath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            uploaded_text = ' '.join(
                page.extract_text() or '' for page in reader.pages
            )

    # Final text
    text_to_eval = uploaded_text or student_answer

    if not text_to_eval:
        return render_template(
            "evaluate.html",
            error="Please type an answer or upload a PDF."
        )

    # -------- Gemini AI --------
    prompt = f"""
Evaluate this student's answer.

Give:
- Score out of {max_marks}
- Strengths
- Weaknesses
- Final feedback

Answer:
{text_to_eval}
"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    try:
        response = requests.post(url, json={
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        })

        data = response.json()

        ai_output = data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        ai_output = f"Error: {str(e)}"

    # Result send to frontend
    result = {
        "ai_result": ai_output
    }

    return render_template("evaluate.html", result=result)


# -------------------- DASHBOARD --------------------
@app.route('/dashboard')
def dashboard():

    total_questions = len(df)
    total_subjects = df['subject_name'].nunique()
    total_units = df['unit_number'].nunique()

    papers_generated = len([
        f for f in os.listdir(RESULTS_FOLDER) if f.endswith('.txt')
    ])

    diff_counts = df['difficulty_level'].value_counts().to_dict()
    unit_counts = df['unit_number'].value_counts().sort_index().to_dict()

    return render_template(
        "dashboard.html",
        total_questions=total_questions,
        total_subjects=total_subjects,
        total_units=total_units,
        papers_generated=papers_generated,
        diff_counts=diff_counts,
        unit_counts=unit_counts
    )


# -------------------- RUN --------------------
if __name__ == '__main__':
    app.run(debug=True)