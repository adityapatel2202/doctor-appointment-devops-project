from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///auth.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(100))
    experience = db.Column(db.String(50))


@app.route("/")
def home():
    return jsonify({"message": "Auth Service Running"})


@app.route("/patient/register", methods=["POST"])
def patient_register():
    data = request.json

    existing_patient = Patient.query.filter_by(email=data["email"]).first()
    if existing_patient:
        return jsonify({"message": "Patient email already exists"}), 400

    patient = Patient(
        name=data["name"],
        email=data["email"],
        password=generate_password_hash(data["password"])
    )

    db.session.add(patient)
    db.session.commit()

    return jsonify({"message": "Patient registered successfully"}), 201


@app.route("/patient/login", methods=["POST"])
def patient_login():
    data = request.json

    patient = Patient.query.filter_by(email=data["email"]).first()

    if patient and check_password_hash(patient.password, data["password"]):
        return jsonify({
            "message": "Patient login successful",
            "patient_id": patient.id,
            "name": patient.name
        }), 200

    return jsonify({"message": "Invalid patient email or password"}), 401


@app.route("/doctor/register", methods=["POST"])
def doctor_register():
    data = request.json

    existing_doctor = Doctor.query.filter_by(email=data["email"]).first()
    if existing_doctor:
        return jsonify({"message": "Doctor email already exists"}), 400

    doctor = Doctor(
        name=data["name"],
        specialization=data["specialization"],
        email=data["email"],
        password=generate_password_hash(data["password"]),
        phone=data.get("phone"),
        qualification=data.get("qualification"),
        experience=data.get("experience")
    )

    db.session.add(doctor)
    db.session.commit()

    return jsonify({"message": "Doctor registered successfully"}), 201


@app.route("/doctor/login", methods=["POST"])
def doctor_login():
    data = request.json

    doctor = Doctor.query.filter_by(email=data["email"]).first()

    if doctor and check_password_hash(doctor.password, data["password"]):
        return jsonify({
            "message": "Doctor login successful",
            "doctor_id": doctor.id,
            "name": doctor.name
        }), 200

    return jsonify({"message": "Invalid doctor email or password"}), 401


@app.route("/doctors", methods=["GET"])
def get_doctors():
    doctors = Doctor.query.all()

    result = []
    for doctor in doctors:
        result.append({
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization,
            "phone": doctor.phone,
            "qualification": doctor.qualification,
            "experience": doctor.experience
        })

    return jsonify(result), 200


@app.route("/patient/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    return jsonify({
        "id": patient.id,
        "name": patient.name,
        "email": patient.email
    }), 200


@app.route("/doctor/<int:doctor_id>", methods=["GET"])
def get_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    return jsonify({
        "id": doctor.id,
        "name": doctor.name,
        "specialization": doctor.specialization,
        "phone": doctor.phone,
        "qualification": doctor.qualification,
        "experience": doctor.experience
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)