import re
import pandas as pd
# import pyttsx3 # Not used for web audio generation, gTTS is.
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier,_tree
import numpy as np
from sklearn.model_selection import train_test_split
# from sklearn.model_selection import cross_val_score # If used, ensure y_test_encoded_global
from sklearn.svm import SVC
import csv
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from gtts import gTTS
import base64
import io

# --- Declare global variables for ML components and data ---
# These will be populated by initialize_symptom_data_on_startup()
training_df = None
testing_df = None
cols = None
x_features = None
y_prognosis_str = None
reduced_data = None
le = None
y_prognosis_encoded = None
x_train_global, x_test_global, y_train_global, y_test_encoded_global = None, None, None, None
clf = None  # Main Decision Tree classifier
svc_model = None # SVM model
rf_clf_sec_global = None # Secondary Decision Tree for sec_predict

symptoms_dict = {}
severityDictionary = dict()
description_list = dict()
precautionDictionary = dict()
chk_dis = []
# feature_names_for_tree = [] # Corresponds to 'features' in original script, same as cols
# tree_internal_representation = None # Corresponds to 'tree_' in original script

# Initialize Flask app
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Groq Chatbot Setup ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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") # Replace with your key or env var
if GROQ_API_KEY == "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" and "GROQ_API_KEY" not in os.environ:
    print("WARNING: Using a hardcoded Groq API key. For production, set the GROQ_API_KEY environment variable.")
elif not GROQ_API_KEY:
    print("ERROR: GROQ_API_KEY not set. Please set it as an environment variable. Groq features will fail.")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
if not groq_client:
    print("WARNING: Groq client not initialized due to missing API key. AI chat features will be limited/fail.")

GENERAL_SYSTEM_PROMPT = """
You are an AI Medical Information Assistant. You are NOT a real doctor and CANNOT provide medical diagnoses or prescribe medication.
Your goal is to:
1. Engage in helpful conversation about health-related topics.
2. If the user indicates they want to discuss symptoms for a potential disease, acknowledge this and the system will guide them through a separate process. Do not try to diagnose them yourself.
3. If asked about appointments, provide information based on the context given (e.g., clinic hours, booking procedures).
4. For general health questions, provide general information and resources.
5. ALWAYS include a clear disclaimer in ALL your responses: "Remember, I am an AI assistant and not a real doctor. This information is for general knowledge only and not a substitute for professional medical advice. Please consult a qualified healthcare professional for any health concerns or before making any decisions related to your health."
6. If symptoms discussed (outside the specialized symptom checker) sound serious or like an emergency (e.g., chest pain, difficulty breathing, severe bleeding, sudden weakness), URGENTLY advise the user to seek immediate medical attention from a doctor or emergency services.
"""

APPOINTMENT_CONTEXT_FOR_GROQ = """
[CONTEXT FOR APPOINTMENT QUERIES]
Our clinic's operational hours are Monday to Friday, from 9:00 AM to 5:00 PM. Saturday hours are 10:00 AM to 2:00 PM for urgent queries, by appointment only. We are closed on Sundays.
Appointments can be scheduled by calling our reception at (555) 123-4567 during business hours.
Alternatively, you can request an appointment through our website at www.exampleclinic.com/appointments.
Please have your personal details and preferred date/time ready. We also offer telehealth consultations for certain conditions.
For emergencies, please dial 911 or go to the nearest emergency room.
"""

# --- Global state for conversation and symptom checking ---
conversation_history = []
current_symptom_check_data = {}


# --- Initialization Function for All Data and Models ---
def initialize_symptom_data_on_startup():
    global training_df, testing_df, cols, x_features, y_prognosis_str, reduced_data, le
    global y_prognosis_encoded, x_train_global, x_test_global, y_train_global, y_test_encoded_global
    global clf, svc_model, rf_clf_sec_global
    global symptoms_dict, severityDictionary, description_list, precautionDictionary, chk_dis
    # global feature_names_for_tree, tree_internal_representation

    print("Starting comprehensive system initialization...")

    # 1. Load Main Data
    training_df = pd.read_csv('Data/Training.csv')
    testing_df = pd.read_csv('Data/Testing.csv') # For testing/evaluation
    
    cols = training_df.columns[:-1].tolist() # Ensure it's a list of column names
    x_features = training_df[cols]
    y_prognosis_str = training_df['prognosis']

    # 2. Create reduced_data (for finding related symptoms)
    reduced_data = training_df.groupby(training_df['prognosis']).max()

    # 3. Label Encoding for Prognosis
    le = preprocessing.LabelEncoder()
    le.fit(y_prognosis_str)
    y_prognosis_encoded = le.transform(y_prognosis_str)

    # 4. Train/Test Split for Main Classifiers
    x_train_global, x_test_global, y_train_global, y_test_encoded_global = train_test_split(
        x_features, y_prognosis_encoded, test_size=0.33, random_state=42
    )

    # 5. Train Main Decision Tree Classifier (clf)
    dt_classifier = DecisionTreeClassifier()
    clf = dt_classifier.fit(x_train_global, y_train_global)
    print(f"Main Decision Tree (clf) trained. Score on test set: {clf.score(x_test_global, y_test_encoded_global):.4f}")
    
    # --- Optional: Tree internals (if ever needed, though current flow doesn't rely on direct traversal) ---
    # tree_internal_representation = clf.tree_
    # feature_names_for_tree = [
    #     cols[i] if i != _tree.TREE_UNDEFINED else "undefined!"
    #     for i in tree_internal_representation.feature
    # ]


    # 6. Train SVM Classifier (svc_model)
    svm_classifier = SVC()
    svc_model = svm_classifier.fit(x_train_global, y_train_global)
    print(f"SVM model (svc_model) trained. Score on test set: {svc_model.score(x_test_global, y_test_encoded_global):.4f}")

    # 7. Train Secondary Decision Tree Classifier (rf_clf_sec_global) for sec_predict
    # This model is trained on the full training data with string labels for prognosis
    df_full_for_sec_predict = pd.read_csv('Data/Training.csv') # Re-read or use training_df
    x_full_sec_features = df_full_for_sec_predict.iloc[:, :-1]
    y_full_sec_prognosis_str = df_full_for_sec_predict['prognosis']
    
    sec_dt_classifier = DecisionTreeClassifier()
    rf_clf_sec_global = sec_dt_classifier.fit(x_full_sec_features, y_full_sec_prognosis_str)
    print("Secondary prediction model (rf_clf_sec_global) trained.")

    # 8. Populate symptoms_dict (symptom name to feature index)
    symptoms_dict.clear() # Ensure it's empty if re-initializing
    for index, symptom_name in enumerate(cols): # cols is list of symptom names
        symptoms_dict[symptom_name] = index
    
    # 9. Load Auxiliary Data Files (Severity, Description, Precaution)
    # These functions populate their respective global dictionaries
    getSeverityDict()
    getDescription()
    getprecautionDict()

    # 10. Setup chk_dis (list of all symptoms for pattern checking)
    chk_dis.clear()
    chk_dis.extend(cols) # cols should be the list of symptom names (features)

    print("Comprehensive system initialization complete.")


# --- Helper functions to load auxiliary data (populate global dictionaries) ---
def getSeverityDict():
    global severityDictionary
    severityDictionary.clear()
    try:
        with open('MasterData/symptom_severity.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                try:
                    if len(row) >= 2 and row[0].strip(): # Ensure symptom name is not empty
                        severityDictionary[row[0].strip()] = int(row[1])
                except ValueError:
                    print(f"Warning: Skipping malformed severity row (ValueError): {row}")
                except IndexError:
                    print(f"Warning: Skipping incomplete severity row (IndexError): {row}")
    except FileNotFoundError:
        print("ERROR: MasterData/symptom_severity.csv not found.")
    # print(f"Severity dictionary loaded with {len(severityDictionary)} entries.")


def getDescription():
    global description_list
    description_list.clear()
    try:
        with open('MasterData/symptom_Description.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row and row[0].strip(): # Ensure row is not empty and has a disease name
                    description_list[row[0].strip()] = row[1].strip() if len(row) > 1 else "No description available."
    except FileNotFoundError:
        print("ERROR: MasterData/symptom_Description.csv not found.")
    # print(f"Description list loaded with {len(description_list)} entries.")


def getprecautionDict():
    global precautionDictionary
    precautionDictionary.clear()
    try:
        with open('MasterData/symptom_precaution.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row and row[0].strip() and len(row) >= 5:
                    precautionDictionary[row[0].strip()] = [p.strip() for p in row[1:5]] # Take first 4 precautions
                # elif row and row[0].strip(): # Log if row is present but not matching format
                    # print(f"Warning: Skipping malformed precaution row (expected 5+ elements): {row}")
    except FileNotFoundError:
        print("ERROR: MasterData/symptom_precaution.csv not found.")
    # print(f"Precaution dictionary loaded with {len(precautionDictionary)} entries.")


# --- Core Logic Functions (using global models and data) ---
def calc_condition(exp, days):
    sum_severity = 0
    for item in exp:
        sum_severity += severityDictionary.get(item, 0) # Use .get for safety
    
    if not exp or not isinstance(days, (int, float)) or days <= 0 or len(exp) == 0:
        return "Could not assess severity due to missing or invalid (days/symptoms) information."
    
    # Original logic: (sum_severity * days) / (len(exp) + 1)
    # Ensure this logic is appropriate for your severity scale and interpretation of 'days'
    # Adding 1 to len(exp) in denominator might be to avoid div by zero if exp was 1 item,
    # but it also skews the average. If len(exp) is guaranteed > 0 by checks, len(exp) might be better.
    # Let's stick to original for now, but highlight as a point of review.
    calculated_value = (sum_severity * days) / (len(exp) + 1) # Original logic used +1
    
    if calculated_value > 13:
        return "Based on the severity and duration, you should consider consulting a doctor."
    else:
        return "It might not be that severe, but please take precautions."


def check_pattern(dis_list_symptoms, inp_symptom): # dis_list_symptoms is chk_dis
    pred_list=[]
    inp_symptom_normalized = inp_symptom.replace(' ','_').lower().strip()
    # Escape special characters for regex and ensure whole word match or partial match as intended
    # The original just used the input as pattern, let's make it more robust for substring
    patt = f"{re.escape(inp_symptom_normalized)}" # Looks for exact substring after normalization
    
    # For a more flexible search (e.g., "head ache" matching "headache"):
    # patt = inp_symptom.lower().strip().replace(" ", ".*") # Allows anything between words
    # Or, more simply, check if each word of input is in symptom:
    # input_words = set(inp_symptom.lower().strip().split())
    # pred_list = [
    #     item for item in dis_list_symptoms
    #     if input_words.issubset(set(item.replace('_', ' ').lower().split()))
    # ]
    
    # Using original regex logic for now:
    regexp = re.compile(patt)
    pred_list=[item for item in dis_list_symptoms if regexp.search(item.replace(' ','_').lower())]
    
    if pred_list:
        return 1, pred_list
    else:
        return 0, []


def sec_predict(symptoms_exp):
    global rf_clf_sec_global, symptoms_dict # Uses globally trained model and symptoms_dict
    
    if not rf_clf_sec_global or not symptoms_dict:
        print("Error: Secondary model or symptoms_dict not initialized for sec_predict.")
        return np.array([]) # Return empty or handle error appropriately

    input_vector = np.zeros(len(symptoms_dict))
    for item in symptoms_exp:
        if item in symptoms_dict:
            input_vector[symptoms_dict[item]] = 1
        # else:
            # print(f"Warning: Symptom '{item}' not in symptoms_dict for sec_predict.")
            
    if np.sum(input_vector) == 0 and symptoms_exp: # If symptoms were provided but none matched dict
        print("Warning: No known symptoms provided to sec_predict after filtering.")
        # Depending on desired behavior, could return empty or a default prediction
    
    return rf_clf_sec_global.predict([input_vector])


def initialize_chat_session():
    global conversation_history, current_symptom_check_data
    print("Initializing chat session...")
    conversation_history = [
        {"role": "system", "content": GENERAL_SYSTEM_PROMPT}
    ]
    current_symptom_check_data = {
        "active": False,
        "stage": "", 
        "main_symptom": "",
        "ambiguous_symptoms": [],
        "days": 0,
        "symptoms_for_confirmation": [],
        "current_confirmation_index": 0,
        "collected_symptoms": [],
        "primary_disease_guess": None,
    }
    
    initial_bot_message = "Hello! I'm an AI Medical Information Assistant. Do you want to discuss symptoms for a potential disease, or ask about appointments? Remember, I am an AI assistant and not a real doctor. This information is for general knowledge only and not a substitute for professional medical advice. Please consult a qualified healthcare professional for any health concerns or before making any decisions related to your health."
    conversation_history.append({"role": "assistant", "content": initial_bot_message})
    print("Chat session initialized.")
    return initial_bot_message


def _generate_final_diagnosis_response_text(collected_symptoms, num_days, primary_disease_guess_from_clf_str):
    s_exp = collected_symptoms
    n_days = num_days
    
    disease1_name_str = primary_disease_guess_from_clf_str # This is already a string
    
    # sec_predict returns an array of predicted disease strings
    second_pred_list_raw_str = sec_predict(s_exp) 

    condition_advice = calc_condition(s_exp, n_days)
    
    disease1_desc = description_list.get(disease1_name_str, "No description available.")
    disease1_precautions = precautionDictionary.get(disease1_name_str, [])

    response_parts = [f"Thank you for providing all the information. Based on your symptoms:"]
    if disease1_name_str:
        response_parts.append(f"\nOne possibility (based on your initial main symptom) is: {disease1_name_str.replace('_', ' ')}")
        response_parts.append(f"Description: {disease1_desc}")

    disease2_name_from_sec_predict_str = None
    if second_pred_list_raw_str is not None and second_pred_list_raw_str.size > 0:
        disease2_name_from_sec_predict_str = second_pred_list_raw_str[0] # sec_predict now returns string prognosis
        if disease2_name_from_sec_predict_str != disease1_name_str:
            disease2_desc = description_list.get(disease2_name_from_sec_predict_str, "No description available.")
            response_parts.append(f"\nConsidering all symptoms, another possibility could be: {disease2_name_from_sec_predict_str.replace('_', ' ')}")
            response_parts.append(f"Description: {disease2_desc}")
        # else:
            # print(f"Secondary prediction matched primary: {disease1_name_str}")
    
    response_parts.append(f"\n{condition_advice}")

    if disease1_precautions:
        response_parts.append(f"\nFor {disease1_name_str.replace('_', ' ')}, general precautions include:")
        for i, p in enumerate(disease1_precautions):
            response_parts.append(f"{i+1}) {p.strip()}")
            
    final_response_text = "\n".join(response_parts)
    final_response_text += "\n\nRemember, I am an AI assistant and not a real doctor. This information is for general knowledge only and not a substitute for professional medical advice. Please consult a qualified healthcare professional for any health concerns or before making any decisions related to your health."
    final_response_text += "\n\nIs there anything else I can help you with today?"
    return final_response_text


# --- Flask Routes ---
@app.route('/')
def home():
    return "HealthCare ChatBot and Symptom Checker API is running!"

@app.route('/reset_chat_interaction', methods=['POST'])
def reset_chat_interaction_endpoint():
    print("Endpoint /reset_chat_interaction called.")
    initial_message = initialize_chat_session()
    audio_base64 = None
    try:
        tts = gTTS(text=initial_message, lang='en', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_base64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
    except Exception as e:
        print(f"Error generating TTS for reset: {e}")

    return jsonify({
        'bot_response_text': initial_message,
        'bot_audio_base64': audio_base64,
        'state_reset': True
    })

@app.route('/chat_interaction', methods=['POST'])
def chat_interaction_endpoint():
    global conversation_history, current_symptom_check_data, clf, le, reduced_data, symptoms_dict, chk_dis
    
    data = request.json
    user_input = data.get('message', '').strip()
    speak_response = data.get('speak', False)

    print(f"\n--- New Interaction ---")
    print(f"User Input: '{user_input}'")
    print(f"Symptom Check State (before processing): active={current_symptom_check_data.get('active')}, stage='{current_symptom_check_data.get('stage')}'")


    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    conversation_history.append({"role": "user", "content": user_input})
    bot_response_text = ""

    if len(conversation_history) == 3 and not current_symptom_check_data.get("active"): 
        current_symptom_check_data["stage"] = "awaiting_initial_choice"

    # --- Symptom Checker Logic ---
    if current_symptom_check_data.get("stage") == "awaiting_initial_choice":
        # ... (rest of the chat_interaction_endpoint remains largely the same) ...
        # Ensure it uses the globally initialized 'clf', 'le', 'reduced_data', 'symptoms_dict', 'chk_dis'
        print("Processing stage: awaiting_initial_choice")
        if "disease" in user_input.lower() or "symptom" in user_input.lower():
            print("User wants to discuss symptoms.")
            current_symptom_check_data["active"] = True
            current_symptom_check_data["stage"] = "awaiting_symptom"
            bot_response_text = "Okay, let's talk about your symptoms. What is the main symptom you are experiencing?"
        elif "appointment" in user_input.lower() or "schedule" in user_input.lower() or "timing" in user_input.lower():
            print("User is asking about appointments (initial query).")
            current_symptom_check_data["active"] = False 
            current_symptom_check_data["stage"] = "done" 
            
            if not groq_client:
                bot_response_text = "I'm sorry, I can't process appointment queries at the moment (AI service not available)."
            else:
                groq_query = f"{APPOINTMENT_CONTEXT_FOR_GROQ}\nUser wants to know about appointments. Their query is: \"{user_input}\". Please respond based on the provided clinic context and their query, and include the standard disclaimer."
                temp_history_for_groq = [
                    {"role": "system", "content": GENERAL_SYSTEM_PROMPT},
                    {"role": "user", "content": groq_query}
                ]
                try:
                    response = groq_client.chat.completions.create(
                        model="llama3-8b-8192", messages=temp_history_for_groq, max_tokens=600, temperature=0.7)
                    bot_response_text = response.choices[0].message.content
                except Exception as e:
                    bot_response_text = f"Sorry, I encountered an error trying to get appointment information: {str(e)}"
        else: 
            print("User's first query is general. Will pass to general Groq handler.")
            current_symptom_check_data["active"] = False
            current_symptom_check_data["stage"] = "done"

    elif current_symptom_check_data.get("active", False):
        stage = current_symptom_check_data["stage"]
        print(f"Processing active symptom check stage: {stage}")

        if stage == "awaiting_symptom":
            symptom_input_raw = user_input
            # chk_dis should be populated by initialize_symptom_data_on_startup
            conf, cnf_dis_list = check_pattern(chk_dis, symptom_input_raw)

            if conf == 1:
                if len(cnf_dis_list) > 1:
                    current_symptom_check_data["stage"] = "clarifying_symptom"
                    current_symptom_check_data["ambiguous_symptoms"] = cnf_dis_list
                    options_text = "\n".join([f"{i+1}) {s.replace('_', ' ')}" for i, s in enumerate(cnf_dis_list)])
                    bot_response_text = f"I found a few matches for '{symptom_input_raw}'. Which one did you mean?\n{options_text}\nPlease reply with the number."
                else:
                    confirmed_symptom = cnf_dis_list[0]
                    current_symptom_check_data["main_symptom"] = confirmed_symptom
                    current_symptom_check_data["stage"] = "awaiting_days"
                    bot_response_text = f"Okay, you mentioned '{confirmed_symptom.replace('_', ' ')}'. For how many days have you been experiencing this?"
            else:
                bot_response_text = "I'm sorry, I couldn't find that symptom. Please try describing it differently or check for typos. What is your main symptom?"

        elif stage == "clarifying_symptom":
            try:
                choice_index = int(user_input) - 1
                ambiguous_symptoms = current_symptom_check_data["ambiguous_symptoms"]
                if 0 <= choice_index < len(ambiguous_symptoms):
                    confirmed_symptom = ambiguous_symptoms[choice_index]
                    current_symptom_check_data["main_symptom"] = confirmed_symptom
                    current_symptom_check_data["stage"] = "awaiting_days"
                    bot_response_text = f"Got it: '{confirmed_symptom.replace('_', ' ')}'. For how many days have you been experiencing this?"
                else:
                    options_text = "\n".join([f"{i+1}) {s.replace('_', ' ')}" for i, s in enumerate(ambiguous_symptoms)])
                    bot_response_text = f"Invalid selection. Please enter a number from the list:\n{options_text}"
            except ValueError:
                options_text = "\n".join([f"{i+1}) {s.replace('_', ' ')}" for i, s in enumerate(current_symptom_check_data["ambiguous_symptoms"])])
                bot_response_text = f"Please enter a number to select the symptom from the list:\n{options_text}"

        elif stage == "awaiting_days":
            try:
                num_days = int(user_input)
                if num_days <= 0:
                    bot_response_text = "Please enter a positive number for days (e.g., 1, 2, 3)."
                else:
                    current_symptom_check_data["days"] = num_days
                    main_symptom = current_symptom_check_data["main_symptom"]
                    current_symptom_check_data["collected_symptoms"] = [main_symptom]

                    input_vector_clf = np.zeros(len(symptoms_dict)) # symptoms_dict from global
                    if main_symptom in symptoms_dict:
                         input_vector_clf[symptoms_dict[main_symptom]] = 1
                    
                    # clf and le from global
                    predicted_prognosis_indices = clf.predict([input_vector_clf])
                    primary_disease_guess_array_str = le.inverse_transform(predicted_prognosis_indices) # Result is string
                    
                    if primary_disease_guess_array_str.size > 0:
                        primary_disease_str = primary_disease_guess_array_str[0]
                        current_symptom_check_data["primary_disease_guess"] = primary_disease_str
                        
                        symptoms_to_ask_about = []
                        # reduced_data from global
                        if primary_disease_str in reduced_data.index:
                            symptoms_series = reduced_data.loc[primary_disease_str]
                            symptoms_to_ask_about = list(symptoms_series[symptoms_series > 0].index)
                            symptoms_to_ask_about = [s for s in symptoms_to_ask_about if s != main_symptom and s in symptoms_dict] 
                        
                        if symptoms_to_ask_about:
                            current_symptom_check_data["symptoms_for_confirmation"] = symptoms_to_ask_about
                            current_symptom_check_data["current_confirmation_index"] = 0
                            current_symptom_check_data["stage"] = "confirming_symptoms"
                            next_symptom_to_ask = symptoms_to_ask_about[0].replace('_', ' ')
                            bot_response_text = f"Okay. To help me understand better, are you also experiencing '{next_symptom_to_ask}'? (yes/no)"
                        else: 
                            bot_response_text = _generate_final_diagnosis_response_text(
                                current_symptom_check_data["collected_symptoms"],
                                current_symptom_check_data["days"],
                                current_symptom_check_data["primary_disease_guess"] # This is a string
                            )
                            current_symptom_check_data["active"] = False
                            current_symptom_check_data["stage"] = "done"
                    else:
                        bot_response_text = "I couldn't make an initial assessment with that symptom. Let's try again. What is your main symptom?"
                        current_symptom_check_data["stage"] = "awaiting_symptom"
            except ValueError:
                bot_response_text = "Please enter a valid number for days (e.g., 1, 2, 3)."

        elif stage == "confirming_symptoms":
            symptoms_to_confirm = current_symptom_check_data["symptoms_for_confirmation"]
            current_index = current_symptom_check_data["current_confirmation_index"]

            if "yes" in user_input.lower():
                current_symptom_check_data["collected_symptoms"].append(symptoms_to_confirm[current_index])
            elif "no" not in user_input.lower(): # If not 'yes' and not 'no'
                bot_response_text = f"Please answer 'yes' or 'no'. Are you experiencing '{symptoms_to_confirm[current_index].replace('_', ' ')}'?"
                conversation_history.append({"role": "assistant", "content": bot_response_text})
                audio_base64_confirm = None
                if speak_response:
                    try:
                        tts_confirm = gTTS(text=bot_response_text, lang='en', slow=False)
                        mp3_fp_confirm = io.BytesIO()
                        tts_confirm.write_to_fp(mp3_fp_confirm)
                        mp3_fp_confirm.seek(0)
                        audio_base64_confirm = base64.b64encode(mp3_fp_confirm.read()).decode('utf-8')
                    except Exception as e_tts: print(f"TTS error: {e_tts}")
                return jsonify({
                    'bot_response_text': bot_response_text, 'bot_audio_base64': audio_base64_confirm,
                    'symptom_check_active': current_symptom_check_data.get("active", False),
                    'current_stage': current_symptom_check_data.get("stage", "")
                })

            current_index += 1
            current_symptom_check_data["current_confirmation_index"] = current_index

            if current_index < len(symptoms_to_confirm):
                next_symptom_to_ask = symptoms_to_confirm[current_index].replace('_', ' ')
                bot_response_text = f"Okay. And are you experiencing '{next_symptom_to_ask}'? (yes/no)"
            else: 
                bot_response_text = _generate_final_diagnosis_response_text(
                    current_symptom_check_data["collected_symptoms"],
                    current_symptom_check_data["days"],
                    current_symptom_check_data["primary_disease_guess"] # String
                )
                current_symptom_check_data["active"] = False
                current_symptom_check_data["stage"] = "done"
    
    # --- Groq General Chat Handling ---
    if not bot_response_text: 
        if not groq_client:
            bot_response_text = "I'm sorry, I'm currently unable to process general chat requests. My AI capabilities are limited. If you wanted to discuss symptoms or appointments, please try again or be more specific."
            if "Remember, I am an AI assistant" not in bot_response_text:
                 bot_response_text += "\n\nRemember, I am an AI assistant and not a real doctor. This information is for general knowledge only and not a substitute for professional medical advice. Please consult a qualified healthcare professional for any health concerns or before making any decisions related to your health."
        else:
            try:
                max_history_len = 10 
                temp_history_for_groq = [conversation_history[0]] 
                if len(conversation_history) > 1:
                    temp_history_for_groq.extend(conversation_history[-max_history_len:])
                
                final_history_for_groq = []
                seen_roles_content = set()
                for msg in reversed(temp_history_for_groq):
                    identifier = (msg['role'], msg['content'])
                    if identifier not in seen_roles_content:
                        final_history_for_groq.append(msg)
                        seen_roles_content.add(identifier)
                final_history_for_groq.reverse()

                response = groq_client.chat.completions.create(
                    model="llama3-8b-8192", messages=final_history_for_groq,
                    max_tokens=1000, temperature=0.7 )
                bot_response_content = response.choices[0].message.content
                
                is_emergency_warning = "seek immediate medical attention" in bot_response_content.lower()
                has_disclaimer = "consult a qualified healthcare professional" in bot_response_content or \
                                "Remember, I am an AI assistant and not a real doctor" in bot_response_content
                
                if not is_emergency_warning and not has_disclaimer:
                    bot_response_content += "\n\nRemember, I am an AI assistant and not a real doctor. This information is for general knowledge only and not a substitute for professional medical advice. Please consult a qualified healthcare professional for any health concerns or before making any decisions related to your health."
                bot_response_text = bot_response_content
            except Exception as e:
                bot_response_text = f"AI: Sorry, I encountered an error: {str(e)}"
                bot_response_text += "\n\nRemember, I am an AI assistant and not a real doctor. Please consult a healthcare professional for medical advice."

    conversation_history.append({"role": "assistant", "content": bot_response_text})
    audio_base64 = None
    if speak_response and bot_response_text:
        try:
            tts = gTTS(text=bot_response_text, lang='en', slow=False)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_base64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
        except Exception as e: print(f"Error generating TTS: {e}")

    print(f"Final bot_response_text to be sent: {bot_response_text[:100]}...")
    print(f"Symptom Check State (after processing): active={current_symptom_check_data.get('active')}, stage='{current_symptom_check_data.get('stage')}'")
    print(f"--- End Interaction ---")

    return jsonify({
        'bot_response_text': bot_response_text, 'bot_audio_base64': audio_base64,
        'symptom_check_active': current_symptom_check_data.get("active", False),
        'current_stage': current_symptom_check_data.get("stage", "")
    })


if __name__ == '__main__':
    initialize_symptom_data_on_startup() # This now does all data/model setup
    initialize_chat_session() 
    app.run(debug=True, port=5000)