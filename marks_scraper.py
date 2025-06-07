from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import json
import os

def scrape_and_generate_pdfs(prn, day, month, year, include_marks=True, include_attendance=True):
    # Setup headless Chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://crce-students.contineo.in/parents/index.php")
        wait = WebDriverWait(driver, 10)

        # Fill PRN
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(prn)

        # Select day
        day_select = Select(driver.find_element(By.ID, "dd"))
        for option in day_select.options:
            if option.text.strip() == day:
                option.click()
                break

        # Convert month to 3-letter abbreviation capitalized
        month_abbr = month[:3].capitalize()
        month_select = Select(driver.find_element(By.ID, "mm"))
        for option in month_select.options:
            if option.text.strip().lower() == month_abbr.lower():
                option.click()
                break

        # Select year
        Select(driver.find_element(By.ID, "yyyy")).select_by_value(year)

        # Submit form
        driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "input[type='submit']"))

        # Wait for the page to load dashboard data
        time.sleep(5)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all("script")

        cie_marks = {}
        attendance = {}
        subjects = ["CSC601", "CSC602", "CSC603", "CSC604", "CSL601", "CSL602", "CSL603", "CSL604", "CSL605", "CSM601", "CSDL06013"]

        for script in scripts:
            text = script.text.strip()

            # Parse CIE marks JSON from script text
            if include_marks and "stackedBarChart_1" in text and "columns" in text:
                try:
                    match = re.search(r'columns\s*:\s*(\[\[.*?\]\])', text, re.DOTALL)
                    if match:
                        raw_json = match.group(1)
                        json_ready = raw_json.replace("'", '"')
                        cie_list = json.loads(json_ready)

                        for row in cie_list:
                            label = row[0]
                            values = [float(v) if v is not None else None for v in row[1:]]
                            cie_marks[label] = values
                except Exception as e:
                    print("Error parsing CIE JSON:", e)

            # Parse Attendance data from script text
            if include_attendance and "gaugeTypeMulti" in text and "columns" in text:
                try:
                    att_data = re.findall(r'\["(.*?)",(\d+)\]', text)
                    for subject, percent in att_data:
                        attendance[subject] = int(percent)
                except Exception as e:
                    print("Error parsing attendance data:", e)

        # Create CIE DataFrame if marks requested
        cie_df = None
        if include_marks and cie_marks:
            cie_df = pd.DataFrame({"Subject": subjects})
            for label, scores in cie_marks.items():
                padded = (scores + [None] * len(subjects))[:len(subjects)]
                cie_df[label] = padded
            cie_df = cie_df.dropna(axis=1, how='all')
            numeric_cols = cie_df.columns.drop("Subject")
            cie_df[numeric_cols] = cie_df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            cie_df["Total"] = cie_df[numeric_cols].sum(axis=1)

        # Create Attendance DataFrame if attendance requested
        att_df = None
        if include_attendance and attendance:
            att_df = pd.DataFrame(list(attendance.items()), columns=["Subject", "Attendance (%)"])

        # Create output directory if needed
        os.makedirs("output", exist_ok=True)

        marks_pdf = None
        attendance_pdf = None
        combined_pdf = None

        # If both marks and attendance are requested, create a combined PDF
        if include_marks and include_attendance and cie_df is not None and att_df is not None and cie_df.shape[1] > 1 and not att_df.empty:
            combined_pdf = "output/marks_and_attendance.pdf"
            with PdfPages(combined_pdf) as pdf:

                # Page 1: Marks Table
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.axis('off')
                table_data = cie_df.fillna("").astype(str)
                table = ax.table(cellText=table_data.values,
                                 colLabels=table_data.columns,
                                 cellLoc='center',
                                 loc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1.2, 1.2)
                plt.title("CIE Marks", fontsize=14)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

                # Page 2: Attendance Table
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.axis('off')
                table_data = att_df.fillna("").astype(str)
                table = ax.table(cellText=table_data.values,
                                 colLabels=table_data.columns,
                                 cellLoc='center',
                                 loc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1.2, 1.2)
                plt.title("Attendance (%)", fontsize=14)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        else:
            # Generate separate PDFs if only one or none is requested

            # Marks PDF
            if include_marks and cie_df is not None and cie_df.shape[1] > 1:
                marks_pdf = "output/marks.pdf"
                with PdfPages(marks_pdf) as pdf:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.axis('off')
                    table_data = cie_df.fillna("").astype(str)
                    table = ax.table(cellText=table_data.values,
                                     colLabels=table_data.columns,
                                     cellLoc='center',
                                     loc='center')
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1.2, 1.2)
                    plt.title("CIE Marks", fontsize=14)
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)

            # Attendance PDF
            if include_attendance and att_df is not None and not att_df.empty:
                attendance_pdf = "output/attendance.pdf"
                with PdfPages(attendance_pdf) as pdf:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.axis('off')
                    table_data = att_df.fillna("").astype(str)
                    table = ax.table(cellText=table_data.values,
                                     colLabels=table_data.columns,
                                     cellLoc='center',
                                     loc='center')
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1.2, 1.2)
                    plt.title("Attendance (%)", fontsize=14)
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)

        # Return paths
        if combined_pdf:
            return {"combined": combined_pdf}
        else:
            return {
                "marks": marks_pdf if marks_pdf else None,
                "attendance": attendance_pdf if attendance_pdf else None
            }

    finally:
        driver.quit()
