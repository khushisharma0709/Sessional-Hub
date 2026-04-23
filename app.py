from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

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


# Dashboard Page
@app.route('/dashboard')
def dashboard():

    total_questions = len(df)
    total_subjects = df['subject_name'].nunique()
    total_units = df['unit_number'].nunique()

    return render_template(
        "dashboard.html",
        total_questions=total_questions,
        total_subjects=total_subjects,
        total_units=total_units
    )


if __name__ == '__main__':
    app.run(debug=True)