from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import json
import os

def create_pdf_table(dataframe, title, size=(10, 5)):
    fig, ax = plt.subplots(figsize=size)
    ax.axis('off')
    table = ax.table(cellText=dataframe.fillna("").astype(str).values,
                     colLabels=dataframe.columns,
                     cellLoc='center',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.2)
    plt.title(title, fontsize=12)
    return fig

def scrape_and_generate_pdfs(prn, day, month, year, include_marks=True, include_attendance=True):
    # Setup headless Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://crce-students.contineo.in/parents/index.php")
        wait = WebDriverWait(driver, 15)

        # Login form
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(prn)

        Select(driver.find_element(By.ID, "dd")).select_by_visible_text(day)
        Select(driver.find_element(By.ID, "mm")).select_by_visible_text(month[:3].capitalize())
        Select(driver.find_element(By.ID, "yyyy")).select_by_value(year)

        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        # Wait for dashboard to load (can optimize with a better element)
        wait.until(EC.presence_of_element_located((By.XPATH, "//script[contains(text(),'columns')]")))

        # Parse page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        scripts = soup.find_all("script")

        cie_marks, attendance = {}, {}
        subjects = ["CSC601", "CSC602", "CSC603", "CSC604", "CSL601", "CSL602", "CSL603", "CSL604", "CSL605", "CSM601", "CSDL06013"]

        for script in scripts:
            text = script.text.strip()
            if include_marks and "stackedBarChart_1" in text and "columns" in text:
                match = re.search(r'columns\s*:\s*(\[\[.*?\]\])', text, re.DOTALL)
                if match:
                    try:
                        cie_list = json.loads(match.group(1).replace("'", '"'))
                        for row in cie_list:
                            cie_marks[row[0]] = [float(v) if v is not None else None for v in row[1:]]
                    except:
                        continue
            if include_attendance and "gaugeTypeMulti" in text and "columns" in text:
                att_data = re.findall(r'\["(.*?)",(\d+)\]', text)
                for subject, percent in att_data:
                    attendance[subject] = int(percent)

        # DataFrames
        cie_df = att_df = None

        if include_marks and cie_marks:
            cie_df = pd.DataFrame({"Subject": subjects})
            for label, scores in cie_marks.items():
                cie_df[label] = (scores + [None]*len(subjects))[:len(subjects)]
            cie_df = cie_df.dropna(axis=1, how='all')
            numeric_cols = cie_df.columns.drop("Subject")
            cie_df[numeric_cols] = cie_df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            cie_df["Total"] = cie_df[numeric_cols].sum(axis=1)

        if include_attendance and attendance:
            att_df = pd.DataFrame(list(attendance.items()), columns=["Subject", "Attendance (%)"])

        # Output dir
        os.makedirs("output", exist_ok=True)
        pdf_path = "output/marks_and_attendance.pdf"

        with PdfPages(pdf_path) as pdf:
            if cie_df is not None and cie_df.shape[1] > 1:
                fig = create_pdf_table(cie_df, "CIE Marks", size=(12, 6))
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
            if att_df is not None and not att_df.empty:
                fig = create_pdf_table(att_df, "Attendance (%)", size=(8, 4))
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        return {"combined": pdf_path}

    finally:
        driver.quit()
