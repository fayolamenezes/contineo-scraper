from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from marks_scraper import scrape_and_generate_pdfs
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        prn = request.form.get('prn', '').strip()
        day = request.form.get('day', '').strip()
        month = request.form.get('month', '').strip()
        year = request.form.get('year', '').strip()
        
        include_marks = request.form.get('include_marks') == 'on'
        include_attendance = request.form.get('include_attendance') == 'on'

        # Basic validation
        if not (prn and day and month and year):
            flash("All fields are required.", "error")
            return redirect(url_for('index'))
        if not (include_marks or include_attendance):
            flash("Select at least one: Marks or Attendance.", "error")
            return redirect(url_for('index'))

        # Call updated function which returns paths to PDFs in a dict
        pdf_paths = scrape_and_generate_pdfs(prn, day, month, year, include_marks, include_attendance)

        # If both selected, check for combined PDF first
        combined_pdf = pdf_paths.get("combined")
        if combined_pdf and os.path.exists(combined_pdf):
            return send_file(combined_pdf, as_attachment=True)

        # Otherwise send marks PDF if requested
        if include_marks:
            marks_pdf = pdf_paths.get("marks")
            if marks_pdf and os.path.exists(marks_pdf):
                return send_file(marks_pdf, as_attachment=True)
            else:
                flash("Marks PDF not found.", "error")
                return redirect(url_for('index'))

        # Or send attendance PDF if requested
        if include_attendance:
            attendance_pdf = pdf_paths.get("attendance")
            if attendance_pdf and os.path.exists(attendance_pdf):
                return send_file(attendance_pdf, as_attachment=True)
            else:
                flash("Attendance PDF not found.", "error")
                return redirect(url_for('index'))

        # If none sent, fallback error
        flash("PDF could not be generated. Try again.", "error")
        return redirect(url_for('index'))

    except Exception as e:
        print(f"Error: {e}")
        flash("Something went wrong while generating the PDF. Please check your inputs.", "error")
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
