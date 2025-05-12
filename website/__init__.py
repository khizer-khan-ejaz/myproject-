from flask import Flask
from flask_login import LoginManager
from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb+srv://khizerkhan495:X1q35w6AvoyJZvab@cluster0.iy7ew.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['hospital_db']

# Collections
patients_collection = db['patients']
doctors_collection = db['doctors']
scans_collection = db['scans']
surgeries_collection = db['surgeries']

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    
    # Import and register blueprints
    from .views import views
    app.register_blueprint(views, url_prefix='/')
    
    # MongoDB client is already established
    
    login_manager = LoginManager()
    login_manager.login_view = 'views.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        # Convert string ID to ObjectId if necessary
        from bson.objectid import ObjectId
        
        # Try to find user in patients collection
        patient = patients_collection.find_one({'_id': ObjectId(id)})
        if patient:
            # Create a User-like object with the necessary attributes
            return type('User', (), {
                'id': str(patient['_id']),
                'is_authenticated': True,
                'is_active': True,
                'is_anonymous': False,
                'get_id': lambda: str(patient['_id'])
            })
        
        # Try to find user in doctors collection
        doctor = doctors_collection.find_one({'_id': ObjectId(id)})
        if doctor:
            return type('User', (), {
                'id': str(doctor['_id']),
                'is_authenticated': True,
                'is_active': True,
                'is_anonymous': False,
                'get_id': lambda: str(doctor['_id'])
            })
        
        return None
    
    return app