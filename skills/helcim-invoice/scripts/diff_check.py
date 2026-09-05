import helcim_monitor
import sqlite3

db = sqlite3.connect('helcim_monitor.db')
c = db.cursor()

invoices = helcim_monitor.fetch_invoices()
for inv in invoices:
    num = inv['invoiceNumber']
    status = inv['status']
    
    c.execute("SELECT status FROM invoices WHERE invoice_number=?", (num,))
    row = c.fetchone()
    if row:
        db_status = row[0]
        if db_status != status:
            print(f"{num} changed from {db_status} in DB to {status} in API")
            
