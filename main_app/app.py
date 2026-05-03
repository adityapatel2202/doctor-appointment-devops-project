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
