# Copyright (c) 2023, ARD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import enqueue
from biotime.api import fetch_transactions, fetch, discover_biotime_employees


class BioTimeSetting(Document):
    @frappe.whitelist()
    def enqueue_long_job_fetch_transactions(self):
        # enqueue('biotime.api.fetch_transactions', queue="long", timeout=3600)
        fetch_transactions()
    
    @frappe.whitelist()
    def enqueue_long_job_fetch(self):
        # enqueue('biotime.api.fetch_transactions', queue="long", timeout=3600)
        fetch()
    
    @frappe.whitelist()
    def discover_employees(self):
        """Découvre les nouveaux employés depuis BioTime"""
        result = discover_biotime_employees()
        if result.get("status") == "success":
            frappe.msgprint(
                f"""
                <b>Découverte d'Employés Terminée</b><br><br>
                • Employés BioTime: {result.get('biotime_count', 0)}<br>
                • Employés ERPNext: {result.get('erpnext_count', 0)}<br>
                • <b>Nouveaux trouvés: {result.get('missing_count', 0)}</b><br><br>
                Consultez la liste <b>Employee Discovery</b> pour valider et créer les nouveaux employés.
                """,
                title="Découverte Employés",
                indicator="green"
            )
        else:
            frappe.msgprint(
                f"Erreur lors de la découverte: {result.get('message', '')}",
                title="Erreur",
                indicator="red"
            )

