"""
Flask Server for Exam Proctoring System
=======================================
Serves the exam application and provides API endpoints for
dynamic question generation using Google Gemini.
"""

import os
import json
from flask import Flask, send_from_directory, jsonify, request, make_response
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='.')

# Configure Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# ==========================================
# CORS Support
# ==========================================
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    # Security headers for camera/mic access (SharedArrayBuffer requirements)
    response.headers.add("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.add("Cross-Origin-Embedder-Policy", "require-corp")
    return response

# ==========================================
# Routes
# ==========================================

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

@app.route('/api/questions', methods=['GET', 'OPTIONS'])
def get_questions():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    # Fallback questions (Standard set)
    fallback_questions = [
        {
            "id": 1,
            "text": "Explain the concept of Object-Oriented Programming (OOP) and list its four main principles with brief descriptions.",
            "topic": "OOP Principles"
        },
        {
            "id": 2,
            "text": "What is the difference between a stack and a queue data structure? Provide examples of real-world applications for each.",
            "topic": "Data Structures"
        },
        {
            "id": 3,
            "text": "Describe what an API (Application Programming Interface) is and explain the difference between REST and GraphQL APIs.",
            "topic": "APIs"
        },
        {
            "id": 4,
            "text": "What is machine learning? Explain the difference between supervised and unsupervised learning with examples.",
            "topic": "Machine Learning"
        },
        {
            "id": 5,
            "text": "Explain the concept of database normalization. What are the benefits and when might you choose to denormalize?",
            "topic": "Databases"
        }
    ]

    if not API_KEY:
        print("[API] No Gemini API Key found. Serving fallback questions.")
        return _corsify_actual_response(jsonify(fallback_questions))

    try:
        print("[API] Generating questions with Gemini...")
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        prompt = """
        Generate 5 unique, challenging exam questions for a Computer Science exam.
        Topics should cover: OOP, Data Structures, Web Development, Machine Learning, and Databases.
        
        Return ONLY a raw JSON array with no markdown formatting.
        Each object in the array must have: 'id' (number), 'text' (string), and 'topic' (string).
        """
        
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # Clean up markdown code blocks if present
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        questions = json.loads(text_response)
        
        # Ensure IDs are correct
        for i, q in enumerate(questions):
            q['id'] = i + 1
            
        print("[API] Successfully generated questions.")
        return _corsify_actual_response(jsonify(questions))

    except Exception as e:
        print(f"[API] Error generating questions: {e}")
        return _corsify_actual_response(jsonify(fallback_questions))

@app.after_request
def after_request(response):
    return _corsify_actual_response(response)

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 EXAM PROCTORING SERVER (FLASK)")
    print("=" * 60)
    print("✅ Server running on http://localhost:8000")
    if API_KEY:
        print("✨ Gemini API Enabled")
    else:
        print("⚠️  Gemini API Key missing (using offline questions)")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)