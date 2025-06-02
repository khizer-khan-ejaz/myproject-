from flask import render_template, redirect, url_for, request, jsonify
from bson.objectid import ObjectId
from .models import *
# views.py

# ... other imports and code ...

@views.route('/scan_detail/<scan_id>') # Ensure this line exists and is not commented out
def scan_detail(scan_id):             # Ensure the function name is scan_detail
    try:
        scan_id_obj = ObjectId(scan_id)
        scan = scans_collection.find_one({'_id': scan_id_obj})

        if not scan:
            flash(f"Scan with ID {scan_id} not found.", "error")
            # Redirect to a relevant page, maybe patient's dashboard?
            # You might need the patient_id here, which isn't directly available.
            # Redirecting to index or login might be safer if patient context is lost.
            return redirect(url_for('views.index')) # Or redirect back if you can get patient_id

        # Assuming you have a template named 'scan_detail.html'
        return render_template('scan_detail.html', scan=scan)

    except InvalidId:
        flash("Invalid Scan ID format.", "error")
        return redirect(url_for('views.index')) # Or appropriate error page
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        print(f"Error in scan_detail route: {e}") # Log error
        return redirect(url_for('views.index'))
@views.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
@views.route('/login', methods=['GET', 'POST'])
def login():
    print(f"--- LOGIN ROUTE HIT --- METHOD: {request.method} ---")  # DEBUG
    if request.method == 'POST':
        print(f"FORM DATA: {request.form}")  # DEBUG
        if 'submit_sign_in' in request.form:
            print("--- Entering sign-in block ---")  # DEBUG
            username = request.form.get('username2', '').strip()
            password = request.form.get('password2', '').strip()
            user_type = request.form.get('userType', '')
            print(f"User type: {user_type}")
            print(f"Username entered: {username}")  # DEBUG
            if user_type == 'patient':
                user = db.patients.find_one({"username": username})
                if user and check_password_hash(user['password'], password):
                    print("--- Password correct ---")  # DEBUG
                    return redirect(url_for('views.patient', patient_id=str(user['_id'])))
                elif user:
                    print("--- Incorrect password ---")  # DEBUG
                    return render_template('login.html', error="Incorrect password.")
                else:
                    print("--- User not found ---")  # DEBUG
                    return render_template('login.html', error="User not found.")
            elif user_type == 'doctor':
                print("--- Entering doctor login block ---")
                user = db.doctors.find_one({"user_name": username})
                if user and user['password'] == password:
                    print("--- Password correct ---")  # DEBUG
                    return redirect(url_for('views.doctor', doctor_id=str(user['_id'])))
                elif user:
                    print("--- Incorrect password ---")  # DEBUG
                    return render_template('login.html', error="Incorrect password.")
                else:
                    print("--- User not found ---")  # DEBUG
                    return render_template('login.html', error="User not found.")
            else:
                print("--- Invalid user type ---")  # DEBUG
                return render_template('login.html', error="Invalid user type.")
        elif 'submit_create_patient' in request.form:
            print("--- Entering patient creation block ---")  # DEBUG
            try:
                ssn = request.form['ssn']
                username = request.form['username1']
                fullname = request.form['fullname']
                email = request.form['email']
                password = request.form['password1']
                birthdate = request.form['birthdate']
                print(f"Data for create_patient: {ssn}, {username}, {fullname}, {email}, (password hidden), {birthdate}")  # DEBUG
                create_patient(ssn, username, fullname, email, password, birthdate)
                print("--- Patient creation successful (from route perspective) ---")  # DEBUG
                return render_template('login.html', message="Patient created successfully!")
            except ValueError as e:
                print(f"--- ValueError in patient creation: {str(e)} ---")  # DEBUG
                return render_template('login.html', error=f"Error: {str(e)}")
            except KeyError as e:
                print(f"--- KeyError - Missing form field: {str(e)} ---")  # DEBUG
                return render_template('login.html', error=f"Missing required field: {str(e)}. Please fill all fields.")
            except Exception as e:
                print(f"--- UNEXPECTED ERROR in patient creation: {str(e)} ---")  # DEBUG
                import traceback
                traceback.print_exc()  # Prints full stack trace to terminal
                return render_template('login.html', error="An unexpected error occurred while creating the patient.")
        else:
            print("--- POST request but no recognized submit button name. ---")  # DEBUG
            return render_template('login.html', error="Form submission error. Please try again.")
    return render_template('login.html')
@views.route('/doctor/<doctor_id>', methods=['GET', 'POST'])
def doctor(doctor_id):
    doctor_id_obj = ObjectId(doctor_id)
    doctor = get_doctor_by_id(doctor_id_obj)
    scans = get_scans_by_doctor_id(doctor_id_obj)
    scans2 = get_unassigned_scans()
    surgeries = list(surgeries_collection.find({'doctor_id': doctor_id_obj}))
    
    if request.method == 'POST':
        scan_data = {
            'price': int(request.form.get('price')) if request.form.get('price') else 0,
            'report': save_scan(request.files.get('report')),
            'scan_id': ObjectId(request.form.get('scan_id'))
        }
        update_scan(doctor_id_obj, scan_data)
        return redirect(url_for('views.doctor', doctor_id=doctor_id))
        
    if doctor.get('department') == 'Radiology':
        return render_template('Radiologydoctor.html', doctor=doctor, scans=scans, scans2=scans2)
    if doctor.get('department') == 'Surgery':
        return render_template('Surgerydoctor.html', doctor=doctor, surgerys=surgeries)
    
    return render_template('Radiologydoctor.html', doctor=doctor, scans=scans, scans2=scans2)

# model.py - book_scan (Example with more debugging and assuming date is YYYY-MM-DD string)

def book_scan(scan_type, test_type, appointment_date_str, additional_notes, patient_id, time_str):
    print(f"\n--- book_scan called ---")
    print(f"Inputs: scan_type={scan_type}, test_type={test_type}, date={appointment_date_str}, notes={additional_notes}, patient_id={patient_id}, time={time_str}")

    try:
        # Ensure patient_id is ObjectId
        if isinstance(patient_id, str):
            patient_id = ObjectId(patient_id)

        # Ensure time is an integer hour
        try:
            time_hour = int(time_str) # Assumes time_str is just the hour like '9' or '14'
        except (ValueError, TypeError) as e:
            print(f"Error converting time '{time_str}' to int: {e}")
            return "Invalid time format. Please provide the hour (e.g., 8, 14)."

        # Validate time range
        if not (8 <= time_hour <= 18):
            return 'Scanning department is closed at this time. Please choose time from 8 to 18'

        # --- Conflict Checking ---
        # Get potentially conflicting appointments for this patient on this day
        conflicting_surgeries = list(surgeries_collection.find({
            'patient_id': patient_id,
            'date': appointment_date_str # Assumes date stored as 'YYYY-MM-DD' string
        }))
        conflicting_scans = list(scans_collection.find({
            'patient_id': patient_id,
            'date': appointment_date_str # Assumes date stored as 'YYYY-MM-DD' string
        }))

        print(f"Found {len(conflicting_surgeries)} potentially conflicting surgeries on {appointment_date_str}")
        print(f"Found {len(conflicting_scans)} potentially conflicting scans on {appointment_date_str}")

        # Check surgery conflict
        surgery_conflict = False
        for surgery in conflicting_surgeries:
            try:
                surgery_hour = int(surgery.get('hour_minute', 'N/A').split(':')[0])
                print(f"Comparing requested hour {time_hour} with surgery hour {surgery_hour}")
                if surgery_hour == time_hour:
                    surgery_conflict = True
                    break
            except: # Catch errors splitting/converting time
                 print(f"Warning: Could not parse hour from surgery {surgery.get('_id')}")
                 continue # Skip this surgery if time is invalid

        # Check scan conflict
        scan_conflict = False
        for scan in conflicting_scans:
            try:
                scan_db_time = scan.get('time') # Could be int or string 'HH:MM' or None
                if scan_db_time is not None:
                    if isinstance(scan_db_time, str):
                        scan_hour = int(scan_db_time.split(':')[0])
                    else: # Assume int
                        scan_hour = int(scan_db_time)
                    print(f"Comparing requested hour {time_hour} with scan hour {scan_hour}")
                    if scan_hour == time_hour:
                        scan_conflict = True
                        break
            except:
                 print(f"Warning: Could not parse hour from scan {scan.get('_id')}")
                 continue # Skip this scan if time is invalid

        print(f"Surgery conflict: {surgery_conflict}, Scan conflict: {scan_conflict}")

        # --- Decision and Insertion ---
        if surgery_conflict:
            return 'You already registered a surgery at the same time'
        elif scan_conflict:
            return 'You already registered a scan at the same time'
        else:
            # MongoDB document for scan
            scan_data = {
                'machine': scan_type,
                'category': test_type,
                'date': appointment_date_str, # Store consistent date format
                'patient_notes': additional_notes,
                'patient_id': patient_id,
                'time': time_hour, # Store hour as integer
                'doctor_id': None, # Explicitly set to None initially
                'price': None,
                'report': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            scans_collection.insert_one(scan_data)
            print(f"--- Scan registered successfully ---")
            return 'Scan is successfully registered'

    except InvalidId:
         print("Error: Invalid Patient ID format.")
         return "Error processing request (Invalid ID)."
    except Exception as e:
        print(f"--- DATABASE/LOGIC ERROR in book_scan: {str(e)} ---")
        import traceback
        traceback.print_exc()
        return "An unexpected error occurred while booking the scan."

# --- Apply similar debugging/refinement to book_surgery ---

# view.py - /patient route POST handler (using flash)


@views.route('/view_patient_info/<patient_id>')
def view_patient_info(patient_id):
    patient_id_obj = ObjectId(patient_id)
    patient_info = patients_collection.find_one({'_id': patient_id_obj})
    return render_template('view_patient_info.html', patient_info=patient_info)

@views.route('/patient/<patient_id>', methods=['GET', 'POST'])
def patient(patient_id):
    try:
        # Validate and convert ID early
        patient_id_obj = ObjectId(patient_id)
    except InvalidId:
        flash("Invalid patient ID.", "error")
        # Redirect to a safe page, maybe login or index
        return redirect(url_for('views.login'))

    # --- POST Request Handling ---
    if request.method == 'POST':
        print(f"Patient POST form data: {request.form}") # Debug form data

        # Check which form was submitted (using button name or key fields)
        if 'submit_scan' in request.form or 'scanType' in request.form: # Check scan form submission
            scan_type = request.form.get('scanType')
            test_type = request.form.get('testType')
            appointment_date = request.form.get('appointmentDate') # e.g., 'YYYY-MM-DD'
            additional_notes = request.form.get('additionalNotes')
            hour_str = request.form.get('appointmentHour1') # e.g., '9' or '14'

            # Basic validation
            if not all([scan_type, test_type, appointment_date, hour_str]):
                 flash("Missing required fields for scan booking.", "warning")
            else:
                # Call the booking function (ensure it returns messages for flashing)
                scan_message = book_scan(
                    scan_type,
                    test_type,
                    appointment_date,
                    additional_notes,
                    patient_id_obj, # Pass ObjectId
                    hour_str # Pass hour string
                )
                # Flash the result
                if scan_message and 'success' in scan_message.lower():
                     flash(scan_message, 'success')
                else:
                     flash(scan_message or "Failed to book scan.", 'error')

        elif 'submit_surgery' in request.form or 'SurgeryType' in request.form: # Check surgery form
            surgery_type = request.form.get('SurgeryType') # This is the specialty
            doctor_name = request.form.get('DoctorName')
            date = request.form.get('appointmentDate2') # e.g., 'YYYY-MM-DD'
            # Get time HH:MM string (adjust model if needed)
            hour_minute_str = request.form.get('appointmentHour') # e.g., '09:30'
            patient_notes = request.form.get('additionalNotes2')

            if not all([surgery_type, doctor_name, date, hour_minute_str]):
                 flash("Missing required fields for surgery booking.", "warning")
            else:
                 # Call the booking function
                 surgery_message = book_surgery(
                     surgery_type,
                     doctor_name,
                     date,
                     hour_minute_str, # Pass HH:MM string
                     patient_notes,
                     patient_id_obj # Pass ObjectId
                 )
                 # Flash the result
                 if surgery_message and 'success' in surgery_message.lower():
                     flash(surgery_message, 'success')
                 else:
                     flash(surgery_message or "Failed to book surgery.", 'error')
        else:
             flash("Unknown form submission.", "warning")


        # Redirect after POST to prevent re-submission on refresh
        # Pass the original patient_id string
        return redirect(url_for('views.patient', patient_id=patient_id))

    # --- GET Request Logic ---
    # Fetch data using model functions which should return dictionaries
    patient_data = get_patient_by_id(patient_id_obj)

    if not patient_data:
         flash("Patient not found.", "error")
         return redirect(url_for('views.login'))

    # Fetch related data as lists of dictionaries
    # Add sorting if desired, e.g., .sort('date', 1) for ascending date
    surgeries_data = list(surgeries_collection.find({'patient_id': patient_id_obj}).sort('date', 1))
    scans_data = list(scans_collection.find({'patient_id': patient_id_obj}).sort('date', 1))

    # Fetch distinct specialties for the surgery dropdown
    specialties = doctors_collection.distinct('specialty')


    # Pass dictionaries and lists to the template
    return render_template(
        'patient.html',
        patient=patient_data,        # Pass the patient dictionary
        surgeries=surgeries_data,    # Pass the list of surgery dictionaries
        scans=scans_data,            # Pass the list of scan dictionaries
        specialties=specialties      # Pass the list of specialties
    )
@views.route('/get_doctors', methods=['POST'])
def get_doctors():
    try:
        # Use the key name expected from your HTML/JS ('SurgeryType' or 'specialty')
        # Let's assume it's 'specialty' based on common practice, adjust if needed
        requested_specialty = request.form.get('specialty')
        print(f"get_doctors called with specialty: {requested_specialty}") # Debug

        if not requested_specialty:
            print("Missing 'specialty' parameter") # Debug
            return jsonify({'error': 'Missing required parameter: specialty'}), 400

        # Define Projection - Use actual field names from your MongoDB collection
        projection = {
            '_id': 1,
            'full_name': 1, # Use 'full_name' if that's your field name
            'specialty': 1,
            # 'photo': 1, # Add 'photo' if you want to display doctor picture in dropdown
            # Add other fields needed by the frontend
        }

        # Query MongoDB
        filtered_doctors_cursor = doctors_collection.find(
            {'specialty': requested_specialty}, # Filter criteria
            projection
        )

        doctors_list = []
        for doctor in filtered_doctors_cursor:
            doctor['_id'] = str(doctor['_id']) # Convert ObjectId to string
            doctors_list.append(doctor)

        print(f"Found {len(doctors_list)} doctors for specialty '{requested_specialty}'") # Debug
        return jsonify(doctors_list)

    except Exception as e:
        print(f"Error fetching doctors: {e}") # Log the error
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An internal server error occurred while fetching doctors.'}), 500
@views.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        create_doctor({
            'ssn': request.form['ssn'],
            'email': request.form['email'],
            'password': request.form['password'],
            'user_name': request.form['user_name'],
            'full_name': request.form['full_name'],
            'department': request.form['department'],
            'specialty': request.form['specialty'],
            'gender': request.form['Gender'][0]
        })

    doctors = list(doctors_collection.find())
    doctors_count = doctors_collection.count_documents({})
    patients_count = patients_collection.count_documents({})
    scans_count = scans_collection.count_documents({})
    surgeries_count = surgeries_collection.count_documents({})
    app_count = scans_count + surgeries_count

    return render_template('admin2.html', doctors=doctors, doctors_count=doctors_count, patient_count=patients_count, app_count=app_count)

from flask import render_template, request, redirect, url_for, flash
from bson import ObjectId
from bson.errors import InvalidId

# view.py - Corrected /edit_doctor route

@views.route('/edit_doctor/<doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    try:
        print(f"Attempting to edit doctor with ID: {doctor_id}")
        
        doctor_id_obj = ObjectId(doctor_id)
        doctor = get_doctor_by_id(doctor_id_obj) # Use your model function

        if not doctor:
            flash('Doctor not found', 'error')
            print(f"Doctor not found for ID: {doctor_id}")
            return redirect(url_for('views.admin'))

        if request.method == 'POST':
            print(f"Edit doctor POST form data: {request.form}") # Debug form
            print(f"Edit doctor POST files: {request.files}") # Debug files
            try:
                # Prepare data dictionary from form for the model function
                doctor_update_data = {
                    'full_name': request.form.get('full_name', doctor.get('full_name')), # Keep old value if not provided
                    # Convert numeric fields safely
                    'working_hours': int(request.form.get('working_hours')) if request.form.get('working_hours') else doctor.get('working_hours', 0),
                    'salary': int(request.form.get('salary')) if request.form.get('salary') else doctor.get('salary', 0),
                    'phone': request.form.get('phone', doctor.get('phone', ''))[:11], # Limit length
                    'address': request.form.get('address', doctor.get('address', '')),
                    # Ensure start/end work times are strings if stored that way
                    'start_work': request.form.get('start', doctor.get('start_work', '8')),
                    'end_work': request.form.get('end', doctor.get('end_work', '17')),
                    # 'photo' is handled separately below
                }

                # Handle file upload
                if 'photo' in request.files:
                    photo_file = request.files['photo']
                    if photo_file and photo_file.filename:
                         print(f"Attempting to save photo: {photo_file.filename}")
                         saved_filename = save_picture(photo_file)
                         if saved_filename != 'default.jpg': # Check if save was successful (optional check)
                             doctor_update_data['photo'] = saved_filename
                             print(f"Photo saved as: {saved_filename}")
                         else:
                              print("Photo saving returned default or failed, keeping old photo.")
                              # Optionally keep the old photo: doctor_update_data['photo'] = doctor.get('photo', 'default.jpg')
                    else:
                        print("No new photo file selected or file has no name.")
                        # Keep the old photo if none is uploaded
                        doctor_update_data['photo'] = doctor.get('photo', 'default.jpg')
                else:
                     print("Photo field not in request.files")
                     # Keep the old photo if 'photo' input wasn't present
                     doctor_update_data['photo'] = doctor.get('photo', 'default.jpg')


                # --- USE YOUR MODEL FUNCTION ---
                update_doctor_profile(doctor_id_obj, doctor_update_data)

                flash('Doctor updated successfully!', 'success')
                return redirect(url_for('views.admin'))

            except ValueError as e: # Catch potential int conversion errors
                flash(f'Invalid input value: {str(e)}', 'error')
                print(f"Update ValueError: {str(e)}")
            except Exception as e:
                flash(f'Error updating doctor: {str(e)}', 'error')
                print(f"Update error: {str(e)}")
                import traceback
                traceback.print_exc()
                # Re-render edit form with error message? Or redirect to admin?
                # return render_template('edit_doctor.html', doctor=doctor, error=str(e)) # Example re-render
        doctors = list(doctors_collection.find())
        # GET Request
        print(f"Rendering template with doctor data: {doctor}")
        return render_template('edit_doctor.html', doctor=doctor)

    except InvalidId:
        flash('Invalid doctor ID format.', 'error')
        print(f"Invalid ObjectId: {doctor_id}")
        return redirect(url_for('views.admin'))
    except Exception as e:
        flash(f'An unexpected server error occurred: {str(e)}', 'error')
        print(f"Route error in edit_doctor GET/Pre-POST: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('views.admin'))
@views.route('/delete_doctor/<doctor_id>', methods=['POST'])
def delete_doctor_route(doctor_id):
    doctor_id_obj = ObjectId(doctor_id)
    delete_doctor(doctor_id_obj)
    return redirect(url_for('views.admin'))