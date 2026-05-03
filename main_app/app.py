from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = "secret123"

AUTH_SERVICE_URL = "http://auth-service:5000"
BOOKING_SERVICE_URL = "http://booking-service:5000"


@app.route("/")
def home():
    return render_template("index.html")


# ---------------- PATIENT AUTH ----------------

@app.route("/patient/register", methods=["GET", "POST"])
def patient_register():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"]
        }

        response = requests.post(f"{AUTH_SERVICE_URL}/patient/register", json=data)

        if response.status_code == 201:
            flash("Patient registered successfully. Please login.")
            return redirect(url_for("patient_login"))

        flash(response.json().get("message", "Registration failed."))

    return render_template("patient_register.html")


@app.route("/patient/login", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        data = {
            "email": request.form["email"],
            "password": request.form["password"]
        }

        response = requests.post(f"{AUTH_SERVICE_URL}/patient/login", json=data)

        if response.status_code == 200:
            user = response.json()
            session.clear()
            session["role"] = "patient"
            session["patient_id"] = user["patient_id"]
            session["patient_name"] = user["name"]
            return redirect(url_for("patient_dashboard"))

        flash("Invalid patient email or password.")

    return render_template("patient_login.html")


# ---------------- DOCTOR AUTH ----------------

@app.route("/doctor/register", methods=["GET", "POST"])
def doctor_register():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "specialization": request.form["specialization"],
            "email": request.form["email"],
            "password": request.form["password"],
            "phone": request.form.get("phone"),
            "qualification": request.form.get("qualification"),
            "experience": request.form.get("experience")
        }

        response = requests.post(f"{AUTH_SERVICE_URL}/doctor/register", json=data)

        if response.status_code == 201:
            flash("Doctor registered successfully. Please login.")
            return redirect(url_for("doctor_login"))

        flash(response.json().get("message", "Doctor registration failed."))

    return render_template("doctor_register.html")


@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        data = {
            "email": request.form["email"],
            "password": request.form["password"]
        }

        response = requests.post(f"{AUTH_SERVICE_URL}/doctor/login", json=data)

        if response.status_code == 200:
            doctor = response.json()
            session.clear()
            session["role"] = "doctor"
            session["doctor_id"] = doctor["doctor_id"]
            session["doctor_name"] = doctor["name"]
            return redirect(url_for("doctor_dashboard"))

        flash("Invalid doctor email or password.")

    return render_template("doctor_login.html")

# ---------------- PATIENT DASHBOARD ----------------

@app.route("/patient/dashboard")
def patient_dashboard():
    if session.get("role") != "patient":
        return redirect(url_for("patient_login"))

    response = requests.get(f"{AUTH_SERVICE_URL}/doctors")
    doctors = response.json() if response.status_code == 200 else []

    return render_template("patient_dashboard.html", doctors=doctors)


@app.route("/book/<int:doctor_id>", methods=["GET", "POST"])
def book_appointment(doctor_id):
    if session.get("role") != "patient":
        return redirect(url_for("patient_login"))

    doctors_response = requests.get(f"{AUTH_SERVICE_URL}/doctors")
    doctors = doctors_response.json() if doctors_response.status_code == 200 else []

    doctor = None
    for d in doctors:
        if d["id"] == doctor_id:
            doctor = d

    slots_response = requests.get(f"{BOOKING_SERVICE_URL}/slots/{doctor_id}")
    slots = slots_response.json() if slots_response.status_code == 200 else []

    if request.method == "POST":
        data = {
            "patient_id": session["patient_id"],
            "slot_id": int(request.form["slot_id"])
        }

        response = requests.post(f"{BOOKING_SERVICE_URL}/appointments", json=data)

        if response.status_code == 201:
            flash("Appointment booked successfully.")
            return redirect(url_for("my_appointments"))

        flash(response.json().get("message", "Booking failed."))

    return render_template("book_appointment.html", doctor=doctor, slots=slots)


@app.route("/my-appointments")
def my_appointments():
    if session.get("role") != "patient":
        return redirect(url_for("patient_login"))

    patient_id = session["patient_id"]

    response = requests.get(f"{BOOKING_SERVICE_URL}/appointments/patient/{patient_id}")
    appointments = response.json() if response.status_code == 200 else []

    return render_template("my_appointments.html", appointments=appointments)


@app.route("/cancel-appointment/<int:appointment_id>")
def cancel_appointment(appointment_id):
    if session.get("role") != "patient":
        return redirect(url_for("patient_login"))

    requests.put(f"{BOOKING_SERVICE_URL}/appointments/{appointment_id}/cancel")
    flash("Appointment cancelled successfully.")

    return redirect(url_for("my_appointments"))


# ---------------- DOCTOR DASHBOARD ----------------

@app.route("/doctor/dashboard")
def doctor_dashboard():
    if session.get("role") != "doctor":
        return redirect(url_for("doctor_login"))

    doctor_id = session["doctor_id"]

    appointments_response = requests.get(f"{BOOKING_SERVICE_URL}/appointments/doctor/{doctor_id}")
    appointments = appointments_response.json() if appointments_response.status_code == 200 else []

    slots_response = requests.get(f"{BOOKING_SERVICE_URL}/doctor/{doctor_id}/slots")
    slots = slots_response.json() if slots_response.status_code == 200 else []

    return render_template(
        "doctor_dashboard.html",
        appointments=appointments,
        slots=slots
    )


@app.route("/doctor/add-slot", methods=["GET", "POST"])
def add_slot():
    if session.get("role") != "doctor":
        return redirect(url_for("doctor_login"))

    if request.method == "POST":
        data = {
            "doctor_id": session["doctor_id"],
            "slot_date": request.form["slot_date"],
            "slot_time": request.form["slot_time"]
        }

        response = requests.post(f"{BOOKING_SERVICE_URL}/slots", json=data)

        if response.status_code == 201:
            flash("Slot added successfully.")
            return redirect(url_for("doctor_dashboard"))

        flash("Slot could not be added.")

    return render_template("manage_slots.html")


@app.route("/doctor/delete-slot/<int:slot_id>")
def delete_slot(slot_id):
    if session.get("role") != "doctor":
        return redirect(url_for("doctor_login"))

    requests.delete(f"{BOOKING_SERVICE_URL}/slots/{slot_id}")
    flash("Slot deleted successfully.")

    return redirect(url_for("doctor_dashboard"))


@app.route("/doctor/update-appointment/<int:appointment_id>/<string:new_status>")
def update_appointment_status(appointment_id, new_status):
    if session.get("role") != "doctor":
        return redirect(url_for("doctor_login"))

    data = {"status": new_status}

    requests.put(
        f"{BOOKING_SERVICE_URL}/appointments/{appointment_id}/status",
        json=data
    )

    flash(f"Appointment {new_status.lower()} successfully.")
    return redirect(url_for("doctor_dashboard"))


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)