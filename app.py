from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import PyPDF2
import google.generativeai as genai
import os
import json
import re

# ---------------- Flask App ----------------
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Gemini Config ----------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- PDF Text Extraction ----------------
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

# ---------------- Safe JSON Extraction ----------------
def extract_json(text):
    """
    Extracts JSON object from Gemini response safely
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError("No valid JSON found")

# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_resume():
    # Check file
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Save file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Extract text
    resume_text = extract_text_from_pdf(file_path)

    if not resume_text.strip():
        return jsonify({"error": "Unable to extract text from PDF"}), 400

    # Prompt
    prompt = f"""
You are an ATS resume analyzer.

Analyze the resume and return ONLY valid JSON.
Do not include explanations or extra text.

Required JSON format:
{{
  "score": number,
  "found_keywords": [],
  "missing_keywords": [],
  "strengths": [],
  "improvements": []
}}

Resume:
{resume_text}
"""

    # Gemini Call
    response = model.generate_content(prompt)

    # Parse Response
    try:
        data = extract_json(response.text)
        return jsonify(data)

    except Exception:
        return jsonify({
            "error": "Failed to parse AI response",
            "raw_response": response.text
        }), 500

# ---------------- Run Server ----------------
if __name__ == "__main__":
    app.run(debug=True, port=8080)


