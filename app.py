from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from fpdf import FPDF
from PIL import Image
import qrcode
import os
import uuid
import io

app = Flask(__name__)
app.secret_key = "super-secret-key"

# Paths
UPLOAD_FOLDER = "generated/receipts"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)

# Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# PDF Generator
class UniversityReceiptPDF(FPDF):
    def header(self):
        self.image(f"{STATIC_FOLDER}/logo.jpg", x=15, y=10, w=25)
        self.set_font("Arial", "BU", 18)
        self.set_x(56)
        self.set_text_color(220, 0, 0)
        self.cell(0, 5, "OFFICE OF THE BURSAR", ln=True, align='L')

        self.set_font("Arial", "B", 30)
        self.set_x(40)
        self.set_text_color(69, 160, 113)
        self.cell(0, 13, "UNIVERSITY OF UYO", ln=True, align='L')

        self.set_font("Arial", "B", 10)
        self.set_x(51)
        self.set_text_color(0, 0, 0)
        self.cell(0, 4, "P.M.B 1017, UYO, AKWA IBOM STATE, NIGERIA", ln=True, align='L')
        self.ln(4)
        self.set_draw_color(169, 169, 169)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(9, y, 153, y)
        self.ln(6)

        self.set_draw_color(0)
        self.set_line_width(0.2)
        self.rect(x=7, y=5, w=195, h=100)
        self.line(x1=155, y1=5, x2=155, y2=105)
        self.line(x1=7, y1=40, x2=155, y2=40)
        self.rect(x=157, y=7, w=43, h=96)
        self.line(x1=157, y1=43, x2=200, y2=43)
        self.line(x1=157, y1=73, x2=200, y2=73)
        self.line(x1=157, y1=81, x2=200, y2=81)
        self.line(x1=157, y1=87, x2=200, y2=87)
        self.line(x1=157, y1=94, x2=200, y2=94)

    def draw_top_right_block(self, qr_path, passport_path, data):
        self.image(qr_path, x=158.8, y=9, w=38, h=31)
        self.image(passport_path, x=159, y=45, w=39.8, h=25)
        self.set_xy(170, 75)
        self.set_font("Arial", "B", 9)
        block = [
            ("Gender:", data["gender"]),
            ("Session:", data["session"]),
            ("Level:", data["level"]),
            ("Date:", data["date"])
        ]
        for label, val in block:
            self.set_xy(158, self.get_y())
            self.set_font("Arial", "B", 9)
            self.cell(22, 6.5, label, 0)
            self.set_font("Arial", "", 9)
            self.cell(76, 6.5, val, ln=True)

    def draw_student_info(self, data):
        self.set_xy(10, 39)
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, "STUDENT'S INFORMATION DETAILS", ln=True)
        self.set_font("Arial", "", 10)
        fields = [
            ("RegNo", data["regno"]),
            ("FullName", data["fullname"]),
            ("Dept./Faculty", data["dept"]),
            ("Programme", data["programme"]),
            ("ProgType", data["progtype"]),
            ("Phone#", data["phone"]),
            ("RRR", data["rrr"])
        ]
        for label, val in fields:
            self.set_font("Arial", "B", 10)
            self.cell(50, 8, f"{label}:", 1)
            self.set_font("Arial", "", 10)
            self.cell(93, 8, val, 1, ln=True)

    def draw_payment_table(self):
        self.ln(5)
        self.set_font("Arial", "B", 10)
        self.set_fill_color(230, 230, 250)
        self.cell(0, 8, "SECOND SEMESTER PAYMENT FOR 2024/2025 SESSION - 100L", 1, ln=True, fill=True)
        self.set_font("Arial", "B", 9)
        self.cell(10, 8, "#", 1)
        self.cell(140, 8, "ITEM", 1)
        self.cell(0, 8, "Amount(N)", 1, ln=True)
        self.set_font("Arial", "", 9)
        items = [
            ("1", "Examination", "1,250"),
            ("2", "Medical/Student Health Insurance Scheme", "1,000"),
            ("3", "Library", "1,000"),
            ("4", "Utilities/Services", "10,000"),
            ("5", "Finance Charge", "500"),
            ("6", "Database Charge", "1,000"),
            ("7", "ICT Project", "1,000"),
            ("8", "Facility Management", "2,500"),
            ("9", "Development Levy", "20,000"),
            ("10", "Professional Accreditation", "15,000")
        ]
        for num, desc, amt in items:
            self.cell(10, 7, num, 1)
            self.cell(140, 7, desc, 1)
            self.cell(0, 7, amt, 1, ln=True)
        self.set_font("Arial", "B", 9)
        self.cell(150, 8, "Total(N): Fifty Three Thousand Two Hundred Fifty Naira Only", 1)
        self.cell(0, 8, "N53,250", 1, ln=True)

    def draw_footer(self):
        self.ln(5)
        self.set_font("Arial", "", 8)
        self.multi_cell(0, 5, "Useful Information:\nYou are expected to present this e-Receipt to your Finance Officer for confirmation and documentation. This e-receipt is valid ONLY upon confirmation.")
        self.ln(3)
        self.set_font("Arial", "I", 8)
        self.cell(0, 6, "Authorised Stamp & Signatory", ln=True, align='R')
        self.cell(0, 6, "For University of Uyo", align='R')

def generate_qr(text):
    qr_path = f"{STATIC_FOLDER}/qr_{uuid.uuid4().hex}.png"
    qrcode.make(text).save(qr_path)
    return qr_path

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        form = request.form
        passport = request.files["passport"]

        if not passport or not passport.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            flash("Only JPG/PNG passport image required.")
            return redirect(url_for("index"))

        passport_path = f"{STATIC_FOLDER}/passport_{uuid.uuid4().hex}.jpg"
        image = Image.open(passport).convert("RGB").resize((180, 220))
        image.save(passport_path, format="JPEG", quality=85)

        qr_path = generate_qr(f"{form['regno']} - {form['fullname']}")
        pdf_buffer = io.BytesIO()

        pdf = UniversityReceiptPDF()
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        pdf.draw_top_right_block(qr_path, passport_path, form)
        pdf.draw_student_info(form)
        pdf.draw_payment_table()
        pdf.draw_footer()

        pdf_output = pdf.output(dest='S').encode('latin1')
        pdf_buffer.write(pdf_output)
        pdf_buffer.seek(0)

        os.remove(qr_path)
        os.remove(passport_path)

        filename = f"{form['regno'].replace('/', '_')}_receipt.pdf"
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    return render_template("index.html", user=current_user.username)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("signup"))
        hashed = generate_password_hash(password)
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created. Please login.")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))

with app.app_context():
    db.create_all()

