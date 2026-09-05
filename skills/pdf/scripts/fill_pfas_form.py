#!/usr/bin/env python3
"""
Fill PFAS Plaintiff Fact Sheet with typed responses instead of handwriting.
Reads the original blank form PDF and overlays typed text at appropriate positions.
"""

import sys
import json
from fpdf import FPDF
from PIL import Image
import os

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <original_form.pdf> <output.pdf>")
        sys.exit(1)
    
    original_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    
    # Create PDF with typed responses
    pdf = FPDF()
    pdf.set_auto_page_break(False)
    
    # Add title page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 20, "IN RE: Aqueous Film-Forming Foams (AFFF)", 0, 1, "C")
    pdf.cell(0, 10, "Products Liability Litigation", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 15, "PLAINTIFF FACT SHEET", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, "MDL No. 2873", 0, 1, "C")
    pdf.cell(0, 10, "UNITED STATES DISTRICT COURT", 0, 1, "C")
    pdf.cell(0, 10, "FOR THE DISTRICT OF SOUTH CAROLINA", 0, 1, "C")
    pdf.cell(0, 10, "CHARLESTON DIVISION", 0, 1, "C")
    
    # Page 1 - Case Information
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    y = 20
    pdf.cell(0, 10, "In completing this Plaintiff Fact Sheet, you are under oath, subject to the penalties of perjury,", 0, 1)
    pdf.cell(0, 10, "and must provide information that is true and correct to the best of your knowledge.", 0, 1)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "I. CASE INFORMATION", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    
    pdf.cell(30, 8, "1. Caption:", 0, 0)
    pdf.cell(0, 8, "__________________________________  Date: ______________", 0, 1)
    pdf.cell(35, 8, "2. Docket No.:", 0, 0)
    pdf.cell(0, 8, "__________________________________", 0, 1)
    pdf.ln(5)
    pdf.multi_cell(0, 6, "3. Plaintiff's attorney's name, law firm, address, phone, and email:\n\n_________________________________________________________\n_________________________________________________________\n_________________________________________________________\n_________________________________________________________\n_________________________________________________________")
    
    # Page 2 - Plaintiff Information
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "II. PLAINTIFF INFORMATION", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    
    pdf.cell(30, 8, "4. Name of plaintiff:", 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "Erica Shafer n/u Schredni", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(35, 8, "5. Date and place of birth:", 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "11/25/1977  Brookline MA", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(20, 8, "6. Gender:", 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "Female", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(65, 8, "7. Spouse's Name (if currently married):", 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "Christopher Shafer", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(10)
    
    # Residences table
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "9. Current and Prior Residences since 1970:", 0, 1)
    pdf.ln(2)
    
    # Table header
    col_widths = [60, 40, 40, 50]
    headers = ["Current or Prior Address", "Dates Lived At This Address", "Did You Own or Rent/Lease this Property?", "Source of Water (Municipal or Private Well)"]
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(220, 220, 220)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, "C", fill=True)
    pdf.ln()
    
    # Table data
    pdf.set_font("Helvetica", "", 8)
    residences = [
        ("46 Calumet Dr\nBrockton MA", "1978-1990", "X Own", "Municipal"),
        ("20 Costner Rd\nEaston MA", "1990-1995", "X Own", "Municipal"),
        ("Unknown\nWashington DC", "1995-1997", "X Rent/Lease", "Unknown"),
        ("Cortes St\nBoston MA", "1997-2001", "X Rent/Lease", "Unknown"),
        ("508 Elliot St\nBeverly MA", "2001-2005", "X Rent/Lease", "Municipal"),
        ("91st + Sheridan Apartments\nTulsa OK", "2005-2006", "Rent", "Unknown"),
        ("91st + Sheridan Heatheridge House\nTulsa OK", "2006-2008", "Rent", "Unknown"),
        ("51st + Harvard Waterford Apts\nTulsa OK", "2008-2010", "Rent", "Unknown"),
        ("6231 S Yorktown\nTulsa OK 74136", "2010-2021", "Own", "Municipal"),
        ("4017 S Sycamore Ave\nBroken Arrow OK 74011", "2021-present", "Own", "Municipal"),
    ]
    
    for address, dates, ownership, water in residences:
        pdf.cell(col_widths[0], 12, address, 1, 0, "L")
        pdf.cell(col_widths[1], 12, dates, 1, 0, "C")
        pdf.cell(col_widths[2], 12, ownership, 1, 0, "C")
        pdf.cell(col_widths[3], 12, water, 1, 0, "C")
        pdf.ln()
    
    # Page 3 - Alleged Exposure
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "III. ALLEGED EXPOSURE", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    
    pdf.multi_cell(0, 6, "11. State (a) all sites or locations where you claim to have been exposed to PFAS; (b) the source or sources of the PFAS to which you claim you were exposed; and (c) the approximate dates of the alleged exposure:")
    pdf.ln(5)
    
    # Exposure table
    col_widths = [65, 65, 65]
    headers = ["Site/Location of Exposure to PFAS", "Source(s) of PFAS", "Approximate Dates (Start Date, End Date or Continuing)"]
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(220, 220, 220)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, "C", fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 8)
    exposures = [
        ("Brockton MA", "Unknown", "1978-1990"),
        ("Easton MA", "Unknown", "1990-1995"),
    ]
    
    for site, source, dates in exposures:
        pdf.cell(col_widths[0], 10, site, 1, 0, "L")
        pdf.cell(col_widths[1], 10, source, 1, 0, "L")
        pdf.cell(col_widths[2], 10, dates, 1, 0, "L")
        pdf.ln()
    
    # Page 4 - Water Consumption
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, "14. Identify whether you have consumed on a regular basis (for at least one year prior to filing your lawsuit during any time period since 1970) any of the following sources of drinking water and list the dates you used each source:")
    pdf.ln(5)
    
    # Water consumption table
    col_widths = [50, 40, 50, 55]
    headers = ["", "Ever Used (Y/N/unsure)?", "When used (Approx dates)", "Where obtained"]
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(220, 220, 220)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, "C", fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 8)
    water_sources = [
        ("Municipal Water", "Yes", "1978-present", "Faucet"),
        ("Private Well", "No", "", ""),
        ("Bottled Water", "Yes", "Unknown", "Store"),
        ("Water at Place of Employment", "Yes", "1990-present", "Work"),
    ]
    
    for source, used, dates, where in water_sources:
        pdf.cell(col_widths[0], 10, source, 1, 0, "L")
        pdf.cell(col_widths[1], 10, used, 1, 0, "C")
        pdf.cell(col_widths[2], 10, dates, 1, 0, "L")
        pdf.cell(col_widths[3], 10, where, 1, 0, "L")
        pdf.ln()
    
    # Page 5 - Injuries Claimed
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "IV. DISEASE OR INJURY ATTRIBUTED TO PFAS EXPOSURE", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(5)
    
    pdf.cell(0, 8, "20. Please indicate alleged injuries claimed in your lawsuit:", 0, 1)
    pdf.ln(3)
    
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
        pdf.cell(10, 7, f"[X] {answer}", 0, 1)
        pdf.set_font("Helvetica", "", 10)
    
    # Page 6 - Healthcare Providers
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, "21. Identify the following for each healthcare provider, clinic, and/or hospital with whom you have treated or consulted for the injuries/damages identified in the question above:")
    pdf.ln(5)
    
    # Healthcare providers table
    col_widths = [35, 25, 40, 35, 35, 35]
    headers = ["Physician Name", "Specialty", "Practice Name / Facility Name", "Address", "Approximate Dates of Treatment", "Condition Treated or Diagnosed"]
    
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(220, 220, 220)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, "C", fill=True)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 7)
    providers = [
        ("Dr. Paris", "GI/Peds", "Unknown", "Brockton MA", "1990-5", "Ulcerative Colitis"),
        ("Childrens Hospital", "GI/Peds", "Unknown", "Boston MA", "1995", "Ulcerative Colitis"),
        ("Dr. Wexler", "GP", "St Johns", "Tulsa OK", "Around 2010", "Thyroid Cancer"),
    ]
    
    for name, specialty, practice, address, dates, condition in providers:
        pdf.cell(col_widths[0], 10, name, 1, 0, "L")
        pdf.cell(col_widths[1], 10, specialty, 1, 0, "L")
        pdf.cell(col_widths[2], 10, practice, 1, 0, "L")
        pdf.cell(col_widths[3], 10, address, 1, 0, "L")
        pdf.cell(col_widths[4], 10, dates, 1, 0, "L")
        pdf.cell(col_widths[5], 10, condition, 1, 0, "L")
        pdf.ln()
    
    # Page 7 - Verification
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "VERIFICATION", 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, "I declare under penalty of perjury subject to all applicable laws, that I have carefully reviewed the final copy of this Plaintiff Fact Sheet and verified that all of the information provided is true and correct to the best of my knowledge, information and belief.")
    pdf.ln(15)
    
    pdf.cell(0, 8, "__________________________", 0, 1, "C")
    pdf.cell(0, 6, "Signature of Plaintiff", 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Erica Shafer", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Print Name", 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "5/17/2026", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Date", 0, 1, "C")
    
    # Save the PDF
    pdf.output(output_pdf)
    print(f"Created filled form: {output_pdf}")

if __name__ == "__main__":
    main()
