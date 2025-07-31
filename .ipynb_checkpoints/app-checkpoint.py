from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF
import qrcode
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "generated/receipts"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

class UniversityReceiptPDF(FPDF):
    def header(self):
        self.image(f"{STATIC_FOLDER}/logo.jpg", x=10, y=8, w=25)

        self.set_font("Arial", "U", 16)
        self.set_text_color(220, 0, 0)
        self.cell(0, 10, "OFFICE OF THE BURSAR", ln=True, align='L')

        self.set_font("Arial", "B", 18)
        self.set_text_color(0, 102, 0)
        self.cell(0, 12, "UNIVERSITY OF UYO", ln=True, align='C')

        self.set_font("Arial", "", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, "P.M.B 1017, UYO, AKWA IBOM STATE, NIGERIA", ln=True, align='C')
        self.ln(3)

    def draw_top_right_block(self, qr_path, passport_path, data):
        self.image(qr_path, x=170, y=20, w=25)
        self.image(passport_path, x=170, y=50, w=25, h=30)

        self.set_xy(130, 85)
        self.set_font("Arial", "", 9)
        block = [
            ("Gender:", data["gender"]),
            ("Session:", data["session"]),
            ("Level:", data["level"]),
            ("Date:", data["date"])
        ]
        for label, val in block:
            self.cell(25, 6, label, 0)
            self.cell(40, 6, val, ln=True)

    def draw_student_info(self, data):
        self.set_xy(10, 95)
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
            self.cell(50, 8, f"{label}:", 1)
            self.cell(140, 8, val, 1, ln=True)

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
def index():
    if request.method == "POST":
        form = request.form
        passport = request.files["passport"]
        passport_path = f"{STATIC_FOLDER}/passport_{uuid.uuid4().hex}.jpg"
        passport.save(passport_path)

        qr_path = generate_qr(f"{form['regno']} - {form['fullname']}")

        pdf = UniversityReceiptPDF()
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        pdf.draw_top_right_block(qr_path, passport_path, form)
        pdf.draw_student_info(form)
        pdf.draw_payment_table()
        pdf.draw_footer()

        filename = f"{form['regno'].replace('/', '_')}_{uuid.uuid4().hex}.pdf"
        path = os.path.join(UPLOAD_FOLDER, filename)
        pdf.output(path)

        return send_file(path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
