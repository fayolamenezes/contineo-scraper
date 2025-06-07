from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from marks_scraper import scrape_and_generate_pdfs
import os
import traceback

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with actual secure key

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Get form data
        prn = request.form.get('prn', '').strip()
        day = request.form.get('day', '').strip()
        month = request.form.get('month', '').strip()
        year = request.form.get('year', '').strip()
        include_marks = request.form.get('include_marks') == 'on'
        include_attendance = request.form.get('include_attendance') == 'on'

        # Validation
        if not (prn and day and month and year):
            flash("All fields are required.", "error")
            return redirect(url_for('index'))
        if not (include_marks or include_attendance):
            flash("Please select at least one: Marks or Attendance.", "error")
            return redirect(url_for('index'))

        # Scrape and generate PDF
        pdf_paths = scrape_and_generate_pdfs(prn, day, month, year, include_marks, include_attendance)
        combined_pdf = pdf_paths.get("combined")

        # Serve the PDF
        if combined_pdf and os.path.exists(combined_pdf):
            return send_file(combined_pdf,
                             as_attachment=True,
                             download_name=f"{prn}_report.pdf")
        else:
            flash("PDF could not be generated. Try again.", "error")
            return redirect(url_for('index'))

    except Exception as e:
        print("Error during PDF generation:")
        traceback.print_exc()
        flash("Something went wrong. Please verify your details and try again.", "error")
        return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)