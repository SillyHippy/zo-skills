#!/usr/bin/env python3
"""TripLog native API pull — profit & loss for tax year"""
import json, requests, sys
from collections import defaultdict

API_KEY = "7b6d5f4152aa4483bce69861556aa45a"
EMAIL = "iannazzi.joseph@gmail.com"
BASE = "https://app.triplog.net/web/api"
HEADERS = {"Authorization": f"apikey {API_KEY}"}
IRS_RATE = 0.725  # 2026 business mileage rate (72.5¢/mile)

def get(endpoint, params=None):
    r = requests.get(f"{BASE}/{endpoint}", headers=HEADERS, params=params or {}, timeout=60)
    r.raise_for_status()
    return r.json()

print("=== PULLING TRIPLOG DATA ===\n")

# Income
print("Income:")
income_expenses = get("expenses", {
    "startDate": "2025-11-01", "endDate": "2026-12-31",
    "userEmail": EMAIL, "category": "Income"
}).get("expenses", [])
print(f"  {len(income_expenses)} income records")

# Expenses (exclude income category)
expense_cats = [
    "Gas", "Oil", "Tires", "Repairs", "Insurance", "Registration", "Garage", "Lease",
    "Taxes", "Interest", "Other", "Advertising", "BusinessHome", "Commissions",
    "Contractors", "CostOfGoods", "Depletion", "Depreciation", "EmpBenefit", "Gifts",
    "InsuranceBiz", "InterestMort", "InterestOther", "LegalProf", "Meals", "Office",
    "Pension", "RentEquipment", "RentOther", "RepairsBiz", "Supplies", "TaxesLicenses",
    "Transporation", "TravelBaggage", "TravelLodging", "TravelMisc", "Utilities",
    "Wages", "OtherBiz", "CC-Purchases", "Hardware", "Software", "Dues", "Internet", "Shipping"
]
print("Expenses:")
all_expenses = []
for cat in expense_cats:
    data = get("expenses", {
        "startDate": "2025-11-01", "endDate": "2026-12-31",
        "userEmail": EMAIL, "category": cat
    })
    exps = data.get("expenses", [])
    if exps:
        print(f"  {cat}: {len(exps)} records")
    all_expenses.extend(exps)

# Trips for mileage
print("\nTrips:")
trips_data = get("trips", {
    "startDate": "2025-11-01", "endDate": "2026-12-31", "userEmail": EMAIL
})
trips = trips_data.get("trips", [])
business = [t for t in trips if t.get("activity") == "Business"]
personal = [t for t in trips if t.get("activity") == "Personal"]
biz_miles = sum(t.get("mileage", 0) for t in business)
pers_miles = sum(t.get("mileage", 0) for t in personal)
print(f"  {len(trips)} trips ({len(business)} biz, {len(personal)} pers)")
print(f"  Biz: {biz_miles:,.1f} mi | Pers: {pers_miles:,.1f} mi")

# Calculate income
income_total = sum(e.get("amount", 0) for e in income_expenses)
income_by_merchant = defaultdict(float)
for e in income_expenses:
    income_by_merchant[e.get("merchant", "Unknown")] += e.get("amount", 0)

# Calculate expenses by category (excluding income)
expense_by_category = defaultdict(float)
for e in all_expenses:
    cat = e.get("category", "Other")
    if cat == "Income":
        continue
    expense_by_category[cat] += e.get("amount", 0)
total_expenses = sum(expense_by_category.values())

# Mileage deduction (weighted by year)
miles_2025 = biz_miles * (2/14)
miles_2026 = biz_miles * (12/14)
mileage_deduction = (miles_2025 * IRS_RATE) + (miles_2026 * IRS_RATE)

# Vehicle expenses (actual method comparison)
vehicle_cats = ["Gas", "Oil", "Tires", "Repairs", "Insurance", "Registration", 
                "Garage", "Lease", "Depreciation", "Interest", "Taxes"]
vehicle_expenses = sum(expense_by_category.get(k, 0) for k in vehicle_cats)

# Total deductions
non_vehicle_expenses = sum(v for k, v in expense_by_category.items() if k not in vehicle_cats)
vehicle_deduction = max(mileage_deduction, vehicle_expenses)
total_deductions = vehicle_deduction + non_vehicle_expenses

net_profit = income_total - total_deductions

# Tax calculations
se_tax = net_profit * 0.9235 * 0.153 if net_profit > 0 else 0
taxable_income = net_profit - (se_tax * 0.5) if net_profit > 0 else 0
income_tax_rate = 0.10 if taxable_income < 11600 else (0.12 if taxable_income < 47150 else 0.22)
income_tax = taxable_income * income_tax_rate if taxable_income > 0 else 0
total_tax = se_tax + income_tax

# Output
print("\n" + "="*60)
print("PROFIT & LOSS — Just Legal Solutions (VXM LLC DBA)")
print("Period: Nov 2025 – Dec 2026")
print("="*60)

print(f"\nGROSS INCOME: ${income_total:,.2f}")
for m, a in sorted(income_by_merchant.items(), key=lambda x: -x[1]):
    print(f"  {m}: ${a:,.2f}")

print(f"\nBUSINESS EXPENSES: ${total_expenses:,.2f}")
for c, a in sorted(expense_by_category.items(), key=lambda x: -x[1]):
    print(f"  {c}: ${a:,.2f}")

print(f"\nMILEAGE: {biz_miles:,.1f} business miles")
print(f"  2025 ({miles_2025:,.0f} mi @ $0.70): ${miles_2025 * IRS_RATE:,.2f}")
print(f"  2026 ({miles_2026:,.0f} mi @ $0.67): ${miles_2026 * IRS_RATE:,.2f}")
print(f"  Mileage deduction: ${mileage_deduction:,.2f}")
print(f"  Vehicle expenses (actual): ${vehicle_expenses:,.2f}")
print(f"  Using {'MILEAGE' if mileage_deduction > vehicle_expenses else 'ACTUAL'} method")

print(f"\nTOTAL DEDUCTIONS: ${total_deductions:,.2f}")
print(f"NET PROFIT (LOSS): ${net_profit:,.2f}")

print(f"\nESTIMATED TAX LIABILITY:")
if net_profit > 0:
    print(f"  Self-Employment Tax (15.3%): ${se_tax:,.2f}")
    print(f"  Federal Income Tax (~{income_tax_rate*100:.0f}%): ${income_tax:,.2f}")
    print(f"  TOTAL: ${total_tax:,.2f}")
else:
    print(f"  NO TAX DUE — Net loss of ${abs(net_profit):,.2f}")
    print(f"  This loss carries forward to offset future income")

# Save
with open("/home/workspace/triplog_tax_data_2026.json", "w") as f:
    json.dump({
        "income_total": income_total,
        "income_by_merchant": dict(income_by_merchant),
        "total_expenses": total_expenses,
        "expense_by_category": dict(expense_by_category),
        "biz_miles": biz_miles, "pers_miles": pers_miles,
        "mileage_deduction": mileage_deduction,
        "vehicle_expenses": vehicle_expenses,
        "total_deductions": total_deductions,
        "net_profit": net_profit,
        "estimated_tax": total_tax
    }, f, indent=2)
print(f"\nData saved: /home/workspace/triplog_tax_data_2026.json")
