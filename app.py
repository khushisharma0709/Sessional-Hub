from flask import Flask, render_template, request
import pandas as pd
import os
import re
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Upload & Results Folders
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "generated_paper_result"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Dataset Path
DATASET_PATH = "database/os_250_full_real_clean.csv"

# Load Dataset
df = pd.read_csv(DATASET_PATH)


# Home Page
@app.route('/')
def home():
    subjects = df['subject_name'].unique()
    return render_template("index.html", subjects=subjects)


# Generate Paper Page
@app.route('/generate')
def generate():
    subjects = df['subject_name'].unique()
    return render_template("generate.html", subjects=subjects)


# Generate Question Paper
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


# Evaluate Answer
@app.route('/evaluate_answer', methods=['POST'])
def evaluate_answer():

    student_answer = request.form.get('student_answer', '').strip()
    max_marks = int(request.form.get('max_marks', 10))

    # PDF upload support
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

    text_to_eval = uploaded_text or student_answer

    if not text_to_eval:
        return render_template("evaluate.html",
                               error="Please type an answer or upload a PDF.")

    # Keyword similarity scoring
    def tokenize(t):
        return set(re.sub(r'[^a-z0-9 ]', '', t.lower()).split())

    student_words = tokenize(text_to_eval)
    reference = request.form.get('reference_answer', '').strip()

    if reference:
        ref_words = tokenize(reference)
        overlap = len(student_words & ref_words)
        similarity = min(100, int((overlap / max(len(ref_words), 1)) * 100 * 2))
    else:
        word_count = len(text_to_eval.split())
        similarity = min(100, word_count * 2)

    marks = round((similarity / 100) * max_marks, 1)

    if similarity >= 75:
        feedback = "Excellent! The answer covers most key points thoroughly."
        grade = "A"
    elif similarity >= 55:
        feedback = "Good answer. Some key concepts are present but could be expanded."
        grade = "B"
    elif similarity >= 35:
        feedback = "Average. Several important points are missing. Review the topic."
        grade = "C"
    else:
        feedback = "Needs improvement. The answer lacks key concepts. Please revise."
        grade = "D"

    result = {
        'marks': marks,
        'max_marks': max_marks,
        'similarity': similarity,
        'feedback': feedback,
        'grade': grade
    }

    return render_template("evaluate.html", result=result)


# Dashboard Page
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


if __name__ == '__main__':
    app.run(debug=True)