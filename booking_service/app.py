from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///booking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Use environment variable or default to Docker service name
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:5000")


class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, nullable=False)
    slot_date = db.Column(db.String(20), nullable=False)
    slot_time = db.Column(db.String(20), nullable=False)
    is_booked = db.Column(db.Boolean, default=False)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, nullable=False)
    doctor_id = db.Column(db.Integer, nullable=False)
    appointment_date = db.Column(db.String(20), nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="Pending")


@app.route("/")
def home():
    return jsonify({"message": "Booking Service Running"})


# Doctor adds available slot
@app.route("/slots", methods=["POST"])
def add_slot():
    data = request.json

    slot = Slot(
        doctor_id=data["doctor_id"],
        slot_date=data["slot_date"],
        slot_time=data["slot_time"],
        is_booked=False
    )

    db.session.add(slot)
    db.session.commit()

    return jsonify({"message": "Slot added successfully"}), 201


# Patient views available slots for selected doctor
@app.route("/slots/<int:doctor_id>", methods=["GET"])
def get_available_slots(doctor_id):
    slots = Slot.query.filter_by(
        doctor_id=doctor_id,
        is_booked=False
    ).all()

    result = []
    for slot in slots:
        result.append({
            "id": slot.id,
            "doctor_id": slot.doctor_id,
            "slot_date": slot.slot_date,
            "slot_time": slot.slot_time,
            "is_booked": slot.is_booked
        })

    return jsonify(result), 200


# Doctor views all slots
@app.route("/doctor/<int:doctor_id>/slots", methods=["GET"])
def get_doctor_slots(doctor_id):
    slots = Slot.query.filter_by(doctor_id=doctor_id).all()

    result = []
    for slot in slots:
        result.append({
            "id": slot.id,
            "doctor_id": slot.doctor_id,
            "slot_date": slot.slot_date,
            "slot_time": slot.slot_time,
            "is_booked": slot.is_booked
        })

    return jsonify(result), 200


# Delete slot
@app.route("/slots/<int:slot_id>", methods=["DELETE"])
def delete_slot(slot_id):
    slot = Slot.query.get_or_404(slot_id)

    db.session.delete(slot)
    db.session.commit()

    return jsonify({"message": "Slot deleted successfully"}), 200


# Patient books appointment using available slot
@app.route("/appointments", methods=["POST"])
def book_appointment():
    data = request.json

    slot = Slot.query.get(data["slot_id"])

    if not slot:
        return jsonify({"message": "Slot not found"}), 404

    if slot.is_booked:
        return jsonify({"message": "Slot already booked"}), 400

    appointment = Appointment(
        patient_id=data["patient_id"],
        doctor_id=slot.doctor_id,
        appointment_date=slot.slot_date,
        appointment_time=slot.slot_time,
        status="Pending"
    )

    slot.is_booked = True

    db.session.add(appointment)
    db.session.commit()

    return jsonify({"message": "Appointment booked successfully"}), 201


# Patient views own appointments
@app.route("/appointments/patient/<int:patient_id>", methods=["GET"])
def patient_appointments(patient_id):
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()

    result = []
    for appointment in appointments:
        # Fetch doctor name and specialization from auth service
        doctor_name = "Unknown"
        doctor_specialization = "Unknown"
        try:
            response = requests.get(f"{AUTH_SERVICE_URL}/doctor/{appointment.doctor_id}")
            if response.status_code == 200:
                doctor_data = response.json()
                doctor_name = doctor_data.get("name", "Unknown")
                doctor_specialization = doctor_data.get("specialization", "Unknown")
        except:
            pass
        
        result.append({
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "doctor_name": doctor_name,
            "specialization": doctor_specialization,
            "appointment_date": appointment.appointment_date,
            "appointment_time": appointment.appointment_time,
            "status": appointment.status
        })

    return jsonify(result), 200


# Doctor views own appointments
@app.route("/appointments/doctor/<int:doctor_id>", methods=["GET"])
def doctor_appointments(doctor_id):
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()

    result = []
    for appointment in appointments:
        # Fetch patient name from auth service
        patient_name = "Unknown"
        try:
            response = requests.get(f"{AUTH_SERVICE_URL}/patient/{appointment.patient_id}")
            if response.status_code == 200:
                patient_data = response.json()
                patient_name = patient_data.get("name", "Unknown")
        except:
            pass
        
        result.append({
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "patient_name": patient_name,
            "doctor_id": appointment.doctor_id,
            "appointment_date": appointment.appointment_date,
            "appointment_time": appointment.appointment_time,
            "status": appointment.status
        })

    return jsonify(result), 200


# Doctor updates appointment status
@app.route("/appointments/<int:appointment_id>/status", methods=["PUT"])
def update_appointment_status(appointment_id):
    data = request.json
    new_status = data["status"]

    allowed_status = ["Pending", "Accepted", "Rejected", "Cancelled", "Completed"]

    if new_status not in allowed_status:
        return jsonify({"message": "Invalid status"}), 400

    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = new_status

    # If cancelled, make slot available again
    if new_status == "Cancelled":
        slot = Slot.query.filter_by(
            doctor_id=appointment.doctor_id,
            slot_date=appointment.appointment_date,
            slot_time=appointment.appointment_time
        ).first()

        if slot:
            slot.is_booked = False

    db.session.commit()

    return jsonify({"message": "Appointment status updated successfully"}), 200


# Patient cancels appointment
@app.route("/appointments/<int:appointment_id>/cancel", methods=["PUT"])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    appointment.status = "Cancelled"

    slot = Slot.query.filter_by(
        doctor_id=appointment.doctor_id,
        slot_date=appointment.appointment_date,
        slot_time=appointment.appointment_time
    ).first()

    if slot:
        slot.is_booked = False

    db.session.commit()

    return jsonify({"message": "Appointment cancelled successfully"}), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)