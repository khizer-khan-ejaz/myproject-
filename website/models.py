from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import os
import secrets
from PIL import Image
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

# Initialize MongoDB connection
client = MongoClient('mongodb+srv://khizerkhan495:X1q35w6AvoyJZvab@cluster0.iy7ew.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['hospital_db']  # Creating database named hospital_db

# Collections (equivalents of tables in SQL)
patients_collection = db['patients']
doctors_collection = db['doctors']
scans_collection = db['scans']
surgeries_collection = db['surgeries']

views = Blueprint('views', __name__)

# Utility function to save a picture
def save_picture(form_picture):
    if form_picture and form_picture.filename:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(views.root_path, 'static/profile_pics', picture_fn)

        output_size = (125, 125)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        return picture_fn
    else:
        return 'default.jpg'    

def save_scan(form_picture):
    if form_picture and form_picture.filename:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(views.root_path, 'static/scans', picture_fn)

        output_size = (500, 500)  # Adjust the size as needed
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        return picture_fn
    else:
        return 'default.jpg'

# Utility function to create a new patient
# In models.py
from werkzeug.security import generate_password_hash # Or your chosen hashing library

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
from werkzeug.security import check_password_hash, generate_password_hash
# Utility function to authenticate a user and render the appropriate template
def authenticate_user(user_type, username_attempt, password_attempt):
    print(f"--- AUTHENTICATE_USER called with UserType: {user_type}, Username: {username_attempt} ---")
    
    if user_type == 'patient':
        user_document = patients_collection.find_one({"username": username_attempt.strip()})

        if user_document:
            print(f"Found patient: {user_document.get('username')}")
            if check_password_hash(user_document['password'], password_attempt):
                return {"user_type": "patient", "id": str(user_document["_id"])}
            else:
                print("Password mismatch for patient.")
                return None
        print("Patient not found.")
        return None

    elif user_type == 'doctor':
        user_document = doctors_collection.find_one({"user_name": username_attempt})
        if user_document:
            print(f"Found doctor: {user_document.get('user_name')}")
            if check_password_hash(user_document['password'], password_attempt):
                return {"user_type": "doctor", "id": str(user_document["_id"])}
            else:
                print("Password mismatch for doctor.")
                return None
        print("Doctor not found.")
        return None

    elif user_type == 'admin':
        ADMIN_USERNAME = "admin"
        ADMIN_HASHED_PASSWORD = generate_password_hash("adminpassword")  # Better to store securely

        if username_attempt == ADMIN_USERNAME and check_password_hash(ADMIN_HASHED_PASSWORD, password_attempt):
            print("Admin authenticated successfully.")
            return {"user_type": "admin"}
        else:
            print("Admin authentication failed.")
            return None

    print("Invalid user type.")
    return None

def book_scan(scan_type, test_type, appointment_date, additional_notes, patient_id, time):
    message = None
    
    if scan_type:
        # Convert patient_id to ObjectId if it's a string
        if isinstance(patient_id, str):
            patient_id = ObjectId(patient_id)
            
        # Get surgeries for time conflict check
        surgeries = list(surgeries_collection.find({'patient_id': patient_id}))
        surgery_registered_dates = [str(surgery['date']) for surgery in surgeries]
        surgery_registered_hours = [int(surgery['hour_minute'].split(':')[0]) for surgery in surgeries]
        
        # Get scans for time conflict check
        scans = list(scans_collection.find({'patient_id': patient_id}))
        scan_registered_dates = [str(scan['date']) for scan in scans]
        scan_registered_hours = [
            int(scan['time'].split(':')[0]) if isinstance(scan['time'], str) 
            else int(scan['time']) if scan['time'] is not None 
            else None 
            for scan in scans
        ]
        
        # Convert time to int for comparison
        time = int(time)
        appointment_date_str = str(appointment_date)
        
        # Check for conflicts
        scan_conflict = any(time == registered_hour and appointment_date_str == date1 
                           for registered_hour, date1 in zip(scan_registered_hours, scan_registered_dates))
        
        surgery_conflict = any(time == registered_hour and appointment_date_str == date1 
                              for registered_hour, date1 in zip(surgery_registered_hours, surgery_registered_dates))
        
        if not scan_conflict and not surgery_conflict:
            if 8 <= time <= 18:
                # MongoDB document for scan
                scan_data = {
                    'machine': scan_type,
                    'category': test_type,
                    'date': appointment_date,
                    'patient_notes': additional_notes,
                    'patient_id': patient_id,
                    'time': time,
                    'created_at': datetime.now()
                }
                
                scans_collection.insert_one(scan_data)
                message = 'Scan is successfully registered'
                return message
            else:
                message = 'Scanning department is closed at this time. Please choose time from 8 to 18'
                return message
        elif surgery_conflict:
            message = 'You already registered a surgery at the same time'
            return message
        else:
            message = 'You already registered a scan at the same time'
            return message

def book_surgery(surgery_type, doctor_name, date, hour_minute, additional_notes, patient_id):
    message = None
    
    if surgery_type:
        # Convert patient_id to ObjectId if it's a string
        if isinstance(patient_id, str):
            patient_id = ObjectId(patient_id)
            
        # Get doctor information
        doctor = doctors_collection.find_one({'full_name': doctor_name})
        
        if not doctor:
            message = f"Doctor {doctor_name} not found"
            return message
        
        doctor_id = doctor['_id']
        start_work = int(doctor.get('start_work', 8))  # Default to 8 if not set
        end_work = int(doctor.get('end_work', 17))     # Default to 17 if not set
        
        # Get surgeries by doctor for conflict checking
        doctor_surgeries = list(surgeries_collection.find({'doctor_id': doctor_id}))
        doctor_registered_hours = [int(s['hour_minute'].split(':')[0]) for s in doctor_surgeries]
        doctor_registered_dates = [str(s['date']) for s in doctor_surgeries]
        
        # Get patient surgeries for conflict checking
        patient_surgeries = list(surgeries_collection.find({'patient_id': patient_id}))
        surgery_registered_hours = [int(s['hour_minute'].split(':')[0]) for s in patient_surgeries]
        surgery_registered_dates = [str(s['date']) for s in patient_surgeries]
        
        # Get patient scans for conflict checking
        patient_scans = list(scans_collection.find({'patient_id': patient_id}))
        scan_registered_dates = [str(s['date']) for s in patient_scans]
        scan_registered_hours = [
            int(s['time'].split(':')[0]) if isinstance(s['time'], str) 
            else int(s['time']) if s['time'] is not None 
            else None 
            for s in patient_scans
        ]
        
        # Convert hour to int for comparison
        hour = int(hour_minute.split(':')[0]) if isinstance(hour_minute, str) else int(hour_minute)
        date_str = str(date)
        
        # Check if time is within doctor's working hours
        if start_work <= hour <= end_work:
            # Check for conflicts
            patient_surgery_conflict = any(hour == h and date_str == d 
                                        for h, d in zip(surgery_registered_hours, surgery_registered_dates))
            
            patient_scan_conflict = any(hour == h and date_str == d 
                                     for h, d in zip(scan_registered_hours, scan_registered_dates))
            
            doctor_conflict = any(hour == h and date_str == d 
                               for h, d in zip(doctor_registered_hours, doctor_registered_dates))
            
            if not patient_surgery_conflict and not patient_scan_conflict and not doctor_conflict:
                # MongoDB document for surgery
                surgery_data = {
                    'type': surgery_type,
                    'date': date,
                    'hour_minute': hour_minute,
                    'additional_notes': additional_notes,
                    'patient_id': patient_id,
                    'doctor_name': doctor_name,
                    'doctor_id': doctor_id,
                    'created_at': datetime.now()
                }
                
                surgeries_collection.insert_one(surgery_data)
                message = f'Surgery is successfully registered with Dr {doctor_name}'
                return message
            elif doctor_conflict:
                message = f'Dr {doctor_name} is not available at this time'
                return message
            elif patient_scan_conflict:
                message = 'You already registered a scan at the same time'
                return message
            else:
                message = 'You already registered a surgery at the same time'
                return message
        else:
            message = f'Dr is only available between {start_work} and {end_work}'
            return message
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
def get_doctor_by_id(doctor_id):
    print(f"Input doctor_id: {doctor_id} (type: {type(doctor_id)})")
    try:
        if isinstance(doctor_id, str):
            try:
                doctor_id = ObjectId(doctor_id)
                print(f"Converted to ObjectId: {doctor_id}")
            except Exception as e:
                print(f"Invalid ObjectId string: {doctor_id}, error: {e}")
                return None
        elif not isinstance(doctor_id, ObjectId):
            print(f"Unsupported doctor_id type: {type(doctor_id)}")
            return None

        doctor = doctors_collection.find_one({'_id': doctor_id})
        if doctor:
            print(f"Doctor found: {doctor['full_name']} (ID: {doctor['_id']})")
        else:
            print(f"No doctor found for ID: {doctor_id}")
        return doctor
    except PyMongoError as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
def get_patient_by_id(patient_id):
    # Convert patient_id to ObjectId if it's a string
    if isinstance(patient_id, str):
        patient_id = ObjectId(patient_id)
        
    return patients_collection.find_one({'_id': patient_id})

def get_scans_by_doctor_id(doctor_id):
    # Convert doctor_id to ObjectId if it's a string
    if isinstance(doctor_id, str):
        doctor_id = ObjectId(doctor_id)
        
    return list(scans_collection.find({'doctor_id': doctor_id}))

def get_unassigned_scans():
    return list(scans_collection.find({'doctor_id': None}))

def update_doctor_profile(doctor_id, data):
    # Convert doctor_id to ObjectId if it's a string
    if isinstance(doctor_id, str):
        doctor_id = ObjectId(doctor_id)
        
    # Prepare update data
    update_data = {
        'full_name': data['full_name'],
        'working_hours': data['working_hours'],
        'salary': data['salary'],
        'phone': data['phone'][:11] if data['phone'] else '',
        'address': data['address'],
        'photo': data['photo'],
        'start_work': data['start_work'],
        'end_work': data['end_work'],
        'updated_at': datetime.now()
    }
    
    doctors_collection.update_one(
        {'_id': doctor_id},
        {'$set': update_data}
    )

def update_scan(doctor_id, data):
    # Convert IDs to ObjectId if they're strings
    if isinstance(doctor_id, str):
        doctor_id = ObjectId(doctor_id)
        
    scan_id = data['scan_id']
    if isinstance(scan_id, str):
        scan_id = ObjectId(scan_id)
    
    # Prepare update data
    update_data = {
        'price': data['price'],
        'report': data['report'],
        'doctor_id': doctor_id,
        'updated_at': datetime.now()
    }
    
    scans_collection.update_one(
        {'_id': scan_id},
        {'$set': update_data}
    )

def delete_doctor(doctor_id):
    # Convert doctor_id to ObjectId if it's a string
    if isinstance(doctor_id, str):
        doctor_id = ObjectId(doctor_id)
    
    # Update scans to remove doctor_id reference
    scans_collection.update_many(
        {'doctor_id': doctor_id},
        {'$set': {'doctor_id': None}}
    )
    
    # Delete surgeries associated with the doctor
    surgeries_collection.delete_many({'doctor_id': doctor_id})
    
    # Delete the doctor
    doctors_collection.delete_one({'_id': doctor_id})

def create_doctor(data):
    # MongoDB document for doctor
    doctor_data = {
        'ssn': data['ssn'],
        'email': data['email'],
        'password': data['password'],
        'user_name': data['user_name'],
        'full_name': data['full_name'],
        'specialty': data['specialty'],
        'department': data['department'],
        'gender': data['gender'],
        'created_at': datetime.now()
    }
    
    result = doctors_collection.insert_one(doctor_data)
    return result.inserted_id