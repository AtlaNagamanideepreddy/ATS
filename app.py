from flask import Flask, render_template, jsonify
import PyPDF2
import google.generativeai as genai
import os
app = Flask(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")
def extract_text_from_pdf(pdf_path):
    extracted_text = ""

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text

    return extracted_text


# -------------------- Routes --------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_resume():
    pdf_path = "Resume (3).pdf"
    resume_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
    Here is my resume text:
    {resume_text}

    I am a 3rd year B.Tech CSE student.

    Please provide:
    1. ATS score out of 100
    2. Pros
    3. Cons
    4. Improvement suggestions
    """

    response = model.generate_content(prompt)

    return jsonify({"result": response.text})


# -------------------- Run Server --------------------
if __name__ == "__main__":
    app.run(port=8080, debug=True)

