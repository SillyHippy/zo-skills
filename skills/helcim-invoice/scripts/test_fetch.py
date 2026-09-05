import helcim_monitor
import json

invoices = helcim_monitor.fetch_invoices()
print("All invoices fetched from API:")
for inv in invoices:
    print(inv['invoiceNumber'], inv['status'])
