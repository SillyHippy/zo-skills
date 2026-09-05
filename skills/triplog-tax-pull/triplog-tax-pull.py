#!/usr/bin/env python3
"""
TripLog Native API Tax Pull — FULL VERSION
Pulls all 2026 data and produces a tax-ready summary.
"""

import json, requests
from collections import defaultdict

API_KEY = "7b6d5f4152aa4483bce69861556aa45a"
EMAIL = "iannazzi.joseph@gmail.com"
BASE = "https://app.triplog.net/web/api"
HEADERS = {"Authorization": f"apikey {API_KEY}"}
YEAR = 2026

def get(endpoint, params=None):
    r = requests.get(f"{BASE}/{endpoint}", headers=HEADERS, params=params or {}, timeout=60)
    r.raise_for_status()
    return r.json()

# --- INCOME ---
print("Pulling income...")
income_data = get("expenses", {
    "category": "Income",
    "userEmail": EMAIL,
    "startDate": f"{YEAR}-01-01",
    "endDate": f"{YEAR}-12-31"
})
income_total = sum(e["amount"] for e in income_data.get("expenses", []))

# --- EXPENSES (non-income) ---
print("Pulling expenses...")
expense_data = get("expenses", {
    "userEmail": EMAIL,
    "startDate": f"{YEAR}-01-01",
    "endDate": f"{YEAR}-12-31"
})
expenses = [e for e in expense_data.get("expenses", []) if e.get("category") != "Income"]

by_category = defaultdict(float)
expense_lines = []
for e in expenses:
    cat = e.get("category", "Unknown")
    amt = e["amount"]
    by_category[cat] += amt
    expense_lines.append({
        "date": e["date"][:10],
        "category": cat,
        "merchant": e.get("merchant", "n/a"),
        "amount": amt,
        "notes": e.get("notes", "")
    })

# --- TRIPS / MILEAGE ---
print("Pulling trips...")
trip_data = get("trips", {
    "userEmail": EMAIL,
    "startDate": f"{YEAR}-01-01",
    "endDate": f"{YEAR}-12-31"
})
trips = trip_data.get("trips", [])

business_miles = 0
personal_miles = 0
total_miles = 0

for t in trips:
    dist = t.get("mileage", 0) or 0
    total_miles += dist
    activity = t.get("activity", "").lower()
    if "business" in activity:
        business_miles += dist
    elif "personal" in activity:
        personal_miles += dist
    else:
        business_miles += dist  # default to business

IRS_RATE = 0.725  # 2026 rate
mileage_deduction = business_miles * IRS_RATE

# --- STATE MILEAGE (calculate from trips) ---
state_miles = defaultdict(float)
for t in trips:
    dist = t.get("mileage", 0) or 0
    # Try to infer state from location addresses
    from_addr = ""
    to_addr = ""
    from_loc = t.get("fromLocation") or {}
    to_loc = t.get("toLocation") or {}
    from_addr = from_loc.get("address", "") if from_loc else ""
    to_addr = to_loc.get("address", "") if to_loc else ""
    # Extract state from address (last 2 chars before zip pattern)
    state = "Unknown"
    for addr in [from_addr, to_addr]:
        if ", OK" in addr or addr.endswith("OK 7"):
            state = "OK"
            break
    if state == "Unknown" and ("Oklahoma" in from_addr or "Oklahoma" in to_addr):
        state = "OK"
    state_miles[state] += dist

# --- OUTPUT ---
print("\n" + "="*50)
print(f"2026 TAX SUMMARY")
print("="*50)

print(f"\n📥 INCOME: ${income_total:,.2f}")
for e in income_data.get("expenses", []):
    print(f"   {e['merchant']}: ${e['amount']:,.2f}")

print(f"\n📤 LOGGED EXPENSES: ${sum(by_category.values()):,.2f}")
for cat, amt in sorted(by_category.items(), key=lambda x: -x[1]):
    print(f"   {cat}: ${amt:,.2f}")

print(f"\n🚗 MILEAGE:")
print(f"   Business miles: {business_miles:,.1f}")
print(f"   Personal miles: {personal_miles:,.1f}")
print(f"   Total miles: {total_miles:,.1f}")
print(f"   Deduction @ ${IRS_RATE}/mi: ${mileage_deduction:,.2f}")

print(f"\n🗺️  STATE MILEAGE:")
for state, dist in sorted(state_miles.items(), key=lambda x: -x[1]):
    print(f"   {state}: {dist:,.1f} mi")

net = income_total - sum(by_category.values()) - mileage_deduction
print(f"\n💰 NET TAXABLE INCOME: ${net:,.2f}")
print(f"   (Income - Expenses - Mileage)")

# Save JSON backup
output = {
    "year": YEAR,
    "income": income_data.get("expenses", []),
    "expenses": expense_lines,
    "trips_count": len(trips),
    "trips": [{"id": t["id"], "date": t.get("startTime", "")[:10], "mileage": t.get("mileage", 0), "activity": t.get("activity", ""), "from": (t.get("fromLocation") or {}).get("name", ""), "to": (t.get("toLocation") or {}).get("name", "")} for t in trips],
    "state_miles": dict(state_miles),
    "summary": {
        "income_total": income_total,
        "expense_total": sum(by_category.values()),
        "business_miles": business_miles,
        "personal_miles": personal_miles,
        "total_miles": total_miles,
        "mileage_deduction": mileage_deduction,
        "net_taxable": net
    }
}

with open(f"triplog_{YEAR}_tax_data.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Saved to triplog_{YEAR}_tax_data.json")
print(f"   {len(trips)} trips, {len(expenses)} expenses, {len(income_data.get('expenses', []))} income entries")
