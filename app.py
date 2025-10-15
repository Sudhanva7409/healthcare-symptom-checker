from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Groq client
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")
    
client = Groq(api_key=api_key)

# Database setup
def init_db():
    conn = sqlite3.connect('symptom_checker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS queries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  symptoms TEXT NOT NULL,
                  response TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Save query to database
def save_query(symptoms, response):
    conn = sqlite3.connect('symptom_checker.db')
    c = conn.cursor()
    c.execute("INSERT INTO queries (symptoms, response) VALUES (?, ?)",
              (symptoms, response))
    conn.commit()
    conn.close()

# Get query history
def get_history(limit=10):
    conn = sqlite3.connect('symptom_checker.db')
    c = conn.cursor()
    c.execute("SELECT * FROM queries ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# LLM prompt for symptom analysis
def analyze_symptoms(symptoms):
    prompt = f"""Based on these symptoms, suggest possible conditions and next steps with educational disclaimer.

Symptoms: {symptoms}

Please provide:
1. Possible conditions (ranked by likelihood)
2. Recommended next steps
3. When to seek immediate medical attention
4. Educational disclaimer

Format your response clearly with sections."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical education assistant. Provide informative analysis of symptoms for educational purposes only. Be as accurate as possible. Always include disclaimers that this is not medical advice and users should consult healthcare professionals."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error analyzing symptoms: {str(e)}"

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    symptoms = data.get('symptoms', '')
    
    if not symptoms:
        return jsonify({'error': 'No symptoms provided'}), 400
    
    # Get LLM analysis
    response = analyze_symptoms(symptoms)
    
    # Save to database
    save_query(symptoms, response)
    
    return jsonify({
        'symptoms': symptoms,
        'analysis': response,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/history', methods=['GET'])
def history():
    limit = request.args.get('limit', 10, type=int)
    rows = get_history(limit)
    
    history_data = []
    for row in rows:
        history_data.append({
            'id': row[0],
            'symptoms': row[1],
            'response': row[2],
            'timestamp': row[3]
        })
    
    return jsonify(history_data)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'message': 'Symptom Checker API is running'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
