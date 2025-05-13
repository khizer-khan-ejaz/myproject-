import os
from flask import Flask, request, render_template, jsonify
from groq import Groq
from gtts import gTTS
import base64
import io
import logging # Added for better debugging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure Groq client
# Replace with your actual API key when using
# It's better practice to use environment variables for API keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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") # Use your key here or set env var
if not GROQ_API_KEY:
    logging.error("GROQ_API_KEY not found. Please set the environment variable or hardcode it (not recommended for production).")
    # Optionally, exit or handle the missing key error
    # exit() # Or return an error page/response

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logging.error(f"Failed to initialize Groq client: {e}")
    # Handle client initialization failure appropriately
    # exit()

# --- IMPORTANT: Define the System Prompt ---
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
# --- ---

@app.route('/')
def home():
    # Make sure you have an index.html in a 'templates' folder
    return render_template('index.html')

@app.route('/text_chat', methods=['POST'])
def text_chat():
    data = request.json
    user_input = data.get('message', '')
    logging.info(f"Received text chat request: {user_input}")

    if not user_input:
        logging.warning("Text chat request received with no message.")
        return jsonify({'error': 'No message provided'}), 400

    # Process the message with Groq API
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Using the more capable model
            messages=[
                {"role": "system", "content": HMS_SYSTEM_PROMPT}, # Use the specific HMS prompt
                {"role": "user", "content": user_input}
            ],
            max_tokens=1500 # Increased slightly for potentially more detailed medical info
        )

        bot_response = response.choices[0].message.content
        logging.info(f"Groq text response generated successfully.")
        return jsonify({'response': bot_response})

    except Exception as e:
        logging.error(f"Error during Groq API call (text_chat): {e}", exc_info=True) # Log full traceback
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

@app.route('/voice_chat', methods=['POST'])
def voice_chat():
    # Expect JSON payload with text from Speech-to-Text on the client-side
    data = request.json
    if not data or 'text' not in data:
        logging.warning("Voice chat request received without text.")
        return jsonify({'error': 'No text provided in voice chat request'}), 400

    text = data['text']
    logging.info(f"Received voice chat request (text): {text}")

    # Process text with Groq
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Using the more capable model
            messages=[
                {"role": "system", "content": HMS_SYSTEM_PROMPT}, # Use the specific HMS prompt
                {"role": "user", "content": text}
            ],
            max_tokens=1500 # Increased slightly
        )

        bot_response = response.choices[0].message.content
        logging.info(f"Groq voice response generated successfully.")

        # Convert text response to speech using gTTS
        try:
            tts = gTTS(text=bot_response, lang='en')

            # Save to a bytes buffer
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            # Encode to base64 for sending to the client
            audio_base64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
            logging.info(f"TTS audio generated and encoded successfully.")

            return jsonify({
                'text': text,              # What the user said (from client STT)
                'response': bot_response,  # LLM's text response
                'audio': audio_base64      # LLM's audio response (TTS)
            })

        except Exception as e_tts:
            logging.error(f"Error during gTTS processing: {e_tts}", exc_info=True)
            # Fallback: return text response only if TTS fails
            return jsonify({
                'text': text,
                'response': bot_response,
                'audio': None, # Indicate audio generation failed
                'warning': 'Could not generate audio response.'
            })


    except Exception as e_groq:
        logging.error(f"Error during Groq API call (voice_chat): {e_groq}", exc_info=True)
        return jsonify({'error': f'An internal error occurred: {str(e_groq)}'}), 500

if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible on your network, or keep 127.0.0.1 for local only
    # Turn off debug mode for anything resembling production or shared use
    app.run(host='0.0.0.0', port=8080, debug=False) # Turn Debug OFF for production


i want to connect with mongo  db 
client = MongoClient('mongodb+srv://khizerkhan495:X1q35w6AvoyJZvab@cluster0.iy7ew.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['hospital_db']  # Creating database named hospital_db

# Collections (equivalents of tables in SQL)
patients_collection = db['patients']
doctors_collection = db['doctors']
scans_collection = db['scans']
surgeries_collection = db['surgeries']

connect with this mongo db also suggestion of doctor and registration form to chabot
html create in backend 
def create_patient(ssn, username, fullname, email, password, birthdate):
    print(f"--- CREATE_PATIENT CALLED ---") # DEBUG
    print(f"Received data: SSN={ssn}, Username={username}, Fullname={fullname}, Email={email}, Birthdate={birthdate}") # DEBUG

    # Basic validation (example)
    if not all([ssn, username, fullname, email, password, birthdate]):
        print("--- ERROR: Missing data in create_patient ---") # DEBUG
        raise ValueError("All fields are required for patient creation.")

    # Check for existing user (example using your patients_collection)
    if patients_collection.find_one({"ssn": ssn}):
        print(f"--- ERROR: SSN {ssn} already exists ---") # DEBUG
        raise ValueError("Patient with this SSN already exists.")
    if patients_collection.find_one({"username": username}): # Assuming 'username' is the key in DB
        print(f"--- ERROR: Username {username} already exists ---") # DEBUG
        raise ValueError("Username already taken.")

    try:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        patient_data = {
            "ssn": ssn,
            "username": username, # Ensure this matches your DB schema (e.g., username or user_name)
            "full_name": fullname,
            "email": email,
            "password": hashed_password,
            "birthdate": birthdate,
            # "role": "patient" # Good to add a role if you distinguish users
        }
        print(f"--- Inserting into DB: {patient_data} ---") # DEBUG
        result = patients_collection.insert_one(patient_data)
        print(f"--- DB Insert Result: {result.inserted_id} ---") # DEBUG
        return result.inserted_id
    except Exception as e:
        print(f"--- DATABASE ERROR in create_patient: {str(e)} ---") # DEBUG
        import traceback
        traceback.print_exc()
        raise # Re-raise to be caught by the route or let Flask handle as 500