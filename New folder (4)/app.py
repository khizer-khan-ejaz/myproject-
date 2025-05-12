import os
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from groq import Groq
from gtts import gTTS
import base64
import io
import logging
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

# Configure logging
logging.basicConfig(level=logging.INFO)

# MongoDB Configuration
client = MongoClient('mongodb+srv://khizerkhan495:X1q35w6AvoyJZvab@cluster0.iy7ew.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['hospital_db']
patients_collection = db['patients']
doctors_collection = db['doctors']
scans_collection = db['scans']
surgeries_collection = db['surgeries']

# Configure Groq client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
if not GROQ_API_KEY:
    logging.error("GROQ_API_KEY not found. Please set the environment variable or hardcode it (not recommended for production).")

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logging.error(f"Failed to initialize Groq client: {e}")

HMS_SYSTEM_PROMPT = """
You are an AI assistant designed to support healthcare professionals within a simulated hospital management system context.
Your role is to provide general information and potential suggestions regarding medical conditions, standard treatment pathways, and common diagnostic tests based on the input provided (e.g., symptoms, suspected conditions).

**Key Instructions & Limitations:**
1.  **Professional Audience:** Assume you are interacting with doctors, nurses, or medical administrators. Use appropriate medical terminology where relevant, but explain concepts clearly.
2.  **Informational Only:** Your responses are strictly informational and suggestive. They are NOT diagnoses, treatment plans, or medical advice.
3.  **Emphasize Professional Judgment:** ALWAYS state that your suggestions are potential options and that final decisions MUST be based on a qualified healthcare provider's assessment, patient history, clinical examination, and specific institutional protocols.
4.  **Suggest, Don't Prescribe:** When asked about treatments or tests, list common options, their general purpose, and potential considerations. Do NOT present any single option as definitive or required. Use phrases like "Common approaches include...", "Tests often considered are...", "Factors to consider might be...".
5.  **Refuse Diagnosis:** If asked to provide a specific diagnosis for a patient, politely refuse and state that diagnosis requires a qualified professional's direct evaluation.
6.  **No Patient Data:** Do not ask for or store any real patient-identifiable information. Base your responses solely on the general information provided in the prompt.
7.  **Cite General Knowledge:** Frame your knowledge as based on general medical literature and standard practices, not specific patient cases.
8.  **Safety Disclaimer:** Include a brief reminder in your responses that this is an AI tool and professional validation is essential. Example: "Remember to correlate this information with the full clinical picture and institutional guidelines."
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            ssn = request.form.get('ssn')
            username = request.form.get('username')
            fullname = request.form.get('fullname')
            email = request.form.get('email')
            password = request.form.get('password')
            birthdate = request.form.get('birthdate')
            
            # Basic validation
            if not all([ssn, username, fullname, email, password, birthdate]):
                return render_template('register.html', error="All fields are required")
            
            # Check if user already exists
            if patients_collection.find_one({"ssn": ssn}):
                return render_template('register.html', error="Patient with this SSN already exists")
            if patients_collection.find_one({"username": username}):
                return render_template('register.html', error="Username already taken")
            
            # Hash password and create patient
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            patient_data = {
                "ssn": ssn,
                "username": username,
                "full_name": fullname,
                "email": email,
                "password": hashed_password,
                "birthdate": datetime.strptime(birthdate, '%Y-%m-%d'),
                "created_at": datetime.now(),
                "role": "patient"
            }
            
            patients_collection.insert_one(patient_data)
            return redirect(url_for('login'))
        
        except Exception as e:
            logging.error(f"Error during registration: {e}")
            return render_template('register.html', error="An error occurred during registration")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        patient = patients_collection.find_one({"username": username})
        if patient and check_password_hash(patient['password'], password):
            session['user_id'] = str(patient['_id'])
            session['username'] = patient['username']
            session['role'] = patient.get('role', 'patient')
            return redirect(url_for('home'))
        
        return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/text_chat', methods=['POST'])
def text_chat():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_input = data.get('message', '')
    logging.info(f"Received text chat request from {session['username']}: {user_input}")

    if not user_input:
        logging.warning("Text chat request received with no message.")
        return jsonify({'error': 'No message provided'}), 400

    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": HMS_SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1500
        )

        bot_response = response.choices[0].message.content
        logging.info(f"Groq text response generated successfully.")
        return jsonify({'response': bot_response})

    except Exception as e:
        logging.error(f"Error during Groq API call (text_chat): {e}", exc_info=True)
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

@app.route('/voice_chat', methods=['POST'])
def voice_chat():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    if not data or 'text' not in data:
        logging.warning("Voice chat request received without text.")
        return jsonify({'error': 'No text provided in voice chat request'}), 400

    text = data['text']
    logging.info(f"Received voice chat request (text): {text}")

    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": HMS_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            max_tokens=1500
        )

        bot_response = response.choices[0].message.content
        logging.info(f"Groq voice response generated successfully.")

        try:
            tts = gTTS(text=bot_response, lang='en')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_base64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
            logging.info(f"TTS audio generated and encoded successfully.")

            return jsonify({
                'text': text,
                'response': bot_response,
                'audio': audio_base64
            })

        except Exception as e_tts:
            logging.error(f"Error during gTTS processing: {e_tts}", exc_info=True)
            return jsonify({
                'text': text,
                'response': bot_response,
                'audio': None,
                'warning': 'Could not generate audio response.'
            })

    except Exception as e_groq:
        logging.error(f"Error during Groq API call (voice_chat): {e_groq}", exc_info=True)
        return jsonify({'error': f'An internal error occurred: {str(e_groq)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)