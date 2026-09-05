#!/usr/bin/env python3
"""
Create a clean typed version of Erica Shafer's PFAS Plaintiff Fact Sheet.
"""

import sys
from fpdf import FPDF

def create_pfas_form(output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(False, margin=15)
    
    # Page 1 - Title and Case Info
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "IN RE: Aqueous Film-Forming Foams (AFFF)", 0, 1, "C")
    pdf.cell(0, 8, "Products Liability Litigation", 0, 1, "C")
    pdf.ln(3)
    pdf.cell(0, 8, "MDL No. 2873", 0, 1, "C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "PLAINTIFF FACT SHEET", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    
    pdf.multi_cell(0, 5, "In completing this Plaintiff Fact Sheet, you are under oath, subject to the penalties of perjury, and must provide information that is true and correct to the best of your knowledge.")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "I. CASE INFORMATION", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(3)
    pdf.cell(30, 7, "1. Caption:", 0, 0)
    pdf.cell(0, 7, "________________________________________  Date: ______________", 0, 1)
    pdf.cell(35, 7, "2. Docket No.:", 0, 0)
    pdf.cell(0, 7, "________________________________________", 0, 1)
    pdf.ln(3)
    pdf.multi_cell(0, 5, "3. Plaintiff's attorney's name, law firm, address, phone, and email:\n\n_________________________________________________________\n_________________________________________________________\n_________________________________________________________")
    
    # Page 2 - Plaintiff Information
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "II. PLAINTIFF INFORMATION", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(3)
    
    # Plaintiff details
    details = [
        ("4. Name of plaintiff:", "Erica Shafer n/u Schredni"),
        ("5. Date and place of birth:", "11/25/1977  Brookline MA"),
        ("6. Gender:", "Female"),
        ("7. Spouse's Name (if currently married):", "Christopher Shafer"),
    ]
    
    for label, value in details:
        pdf.set_font("Helvetica", "", 10)
        w = pdf.get_string_width(label)
        pdf.cell(w + 2, 7, label, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, value, 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "9. Current and Prior Residences since 1970:", 0, 1)
    pdf.ln(2)
    
    # Residences table
    col_widths = [55, 35, 45, 55]
    headers = ["Current or Prior Address", "Dates Lived", "Own or Rent/Lease", "Source of Water"]
    
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, 1, 0, "C", fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 7)
    residences = [
        ("46 Calumet Dr\nBrockton MA", "1978-1990", "X Own", "Municipal"),
        ("20 Costner Rd\nEaston MA", "1990-1995", "X Own", "Municipal"),
        ("Unknown\nWashington DC", "1995-1997", "X Rent/Lease", "Unknown"),
        ("Cortes St\nBoston MA", "1997-2001", "X Rent/Lease", "Unknown"),
        ("508 Elliot St\nBeverly MA", "2001-2005", "X Rent/Lease", "Municipal"),
        ("91st + Sheridan Apts\nTulsa OK", "2005-2006", "Rent", "Unknown"),
        ("91st + Sheridan Heatheridge\nTulsa OK", "2006-2008", "Rent", "Unknown"),
        ("51st + Harvard Waterford Apts\nTulsa OK", "2008-2010", "Rent", "Unknown"),
        ("6231 S Yorktown\nTulsa OK 74136", "2010-2021", "Own", "Municipal"),
        ("4017 S Sycamore Ave\nBroken Arrow OK 74011", "2021-present", "Own", "Municipal"),
    ]
    
    for addr, dates, own, water in residences:
        pdf.cell(col_widths[0], 10, addr, 1, 0, "L")
        pdf.cell(col_widths[1], 10, dates, 1, 0, "C")
        pdf.cell(col_widths[2], 10, own, 1, 0, "C")
        pdf.cell(col_widths[3], 10, water, 1, 0, "C")
        pdf.ln()
    
    # Page 3 - Alleged Exposure
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "III. ALLEGED EXPOSURE", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(3)
    
    pdf.multi_cell(0, 5, "11. State all sites or locations where you claim to have been exposed to PFAS, the source(s) of PFAS, and approximate dates of exposure:")
    pdf.ln(3)
    
    col_widths = [60, 60, 70]
    headers = ["Site/Location of Exposure", "Source(s) of PFAS", "Approximate Dates"]
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, 1, 0, "C", fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 8)
    exposures = [
        ("Brockton MA", "Unknown", "1978-1990"),
        ("Easton MA", "Unknown", "1990-1995"),
    ]
    for site, source, dates in exposures:
        pdf.cell(col_widths[0], 9, site, 1, 0, "L")
        pdf.cell(col_widths[1], 9, source, 1, 0, "L")
        pdf.cell(col_widths[2], 9, dates, 1, 0, "L")
        pdf.ln()
    
    # Page 4 - Water Consumption
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, "14. Identify whether you have consumed on a regular basis any of the following sources of drinking water since 1970:")
    pdf.ln(3)
    
    col_widths = [45, 45, 55, 50]
    headers = ["", "Ever Used?", "When used", "Where obtained"]
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, 1, 0, "C", fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 8)
    water = [
        ("Municipal Water", "Yes", "1978-present", "Faucet"),
        ("Private Well", "No", "", ""),
        ("Bottled Water", "Yes", "Unknown", "Store"),
        ("Water at Employment", "Yes", "1990-present", "Work"),
    ]
    for src, used, dates, where in water:
        pdf.cell(col_widths[0], 9, src, 1, 0, "L")
        pdf.cell(col_widths[1], 9, used, 1, 0, "C")
        pdf.cell(col_widths[2], 9, dates, 1, 0, "L")
        pdf.cell(col_widths[3], 9, where, 1, 0, "L")
        pdf.ln()
    
    # Page 5 - Injuries
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "IV. DISEASE OR INJURY ATTRIBUTED TO PFAS EXPOSURE", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(3)
    pdf.cell(0, 7, "20. Please indicate alleged injuries claimed in your lawsuit:", 0, 1)
    pdf.ln(2)
    
    injuries = [
        ("Kidney Cancer:", "No"),
        ("Testicular Cancer:", "No"),
        ("Thyroid Disease:", "Yes"),
        ("Ulcerative Colitis:", "Yes"),
        ("Pregnancy-Induced Hypertension:", "No"),
        ("High Cholesterol:", "No"),
        ("Liver Cancer:", "No"),
        ("Thyroid Cancer:", "Yes"),
    ]
    
    for injury, answer in injuries:
        pdf.cell(50, 7, injury, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        if answer == "Yes":
            pdf.cell(15, 7, "[X] Yes", 0, 0)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(15, 7, "[  ] No", 0, 1)
        else:
            pdf.cell(15, 7, "[  ] Yes", 0, 0)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(15, 7, "[X] No", 0, 1)
    
    # Page 6 - Healthcare Providers
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, "21. Identify healthcare providers you have treated with for the injuries/damages identified above:")
    pdf.ln(3)
    
    col_widths = [30, 25, 40, 30, 35, 35]
    headers = ["Physician Name", "Specialty", "Practice/Facility", "Address", "Dates", "Condition"]
    
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, 1, 0, "C", fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 7)
    providers = [
        ("Dr. Paris", "GI/Peds", "Unknown", "Brockton MA", "1990-95", "Ulcerative Colitis"),
        ("Childrens Hospital", "GI/Peds", "Unknown", "Boston MA", "1995", "Ulcerative Colitis"),
        ("Dr. Wexler", "GP", "St Johns", "Tulsa OK", "Around 2010", "Thyroid Cancer"),
    ]
    for name, spec, prac, addr, dates, cond in providers:
        pdf.cell(col_widths[0], 9, name, 1, 0, "L")
        pdf.cell(col_widths[1], 9, spec, 1, 0, "L")
        pdf.cell(col_widths[2], 9, prac, 1, 0, "L")
        pdf.cell(col_widths[3], 9, addr, 1, 0, "L")
        pdf.cell(col_widths[4], 9, dates, 1, 0, "L")
        pdf.cell(col_widths[5], 9, cond, 1, 0, "L")
        pdf.ln()
    
    # Page 7 - Verification
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "VERIFICATION", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    pdf.multi_cell(0, 5, "I declare under penalty of perjury subject to all applicable laws, that I have carefully reviewed the final copy of this Plaintiff Fact Sheet and verified that all of the information provided is true and correct to the best of my knowledge, information and belief.")
    pdf.ln(15)
    
    pdf.cell(0, 7, "_______________________________", 0, 1, "C")
    pdf.cell(0, 5, "Signature of Plaintiff", 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Erica Shafer", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Print Name", 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "5/17/2026", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Date", 0, 1, "C")
    
    pdf.output(output_path)
    print(f"Created: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output.pdf>")
        sys.exit(1)
    create_pfas_form(sys.argv[1])
