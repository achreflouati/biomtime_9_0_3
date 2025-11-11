# Copyright (c) 2023, ARD and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document
from frappe import enqueue
from biotime.api import fetch_transactions, fetch, discover_biotime_employees, sync_erpnext_employees_to_biotime, get_tokan, get_url, debug_biotime_raw_data


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
    
    @frappe.whitelist()
    def sync_to_biotime(self):
        """Synchronise les employés ERPNext vers BioTime"""
        result = sync_erpnext_employees_to_biotime()
        if result.get("status") == "success":
            frappe.msgprint(
                f"""
                <b>Synchronisation vers BioTime Terminée</b><br><br>
                • Employés créés: {result.get('created_count', 0)}<br>
                • Échecs: {result.get('failed_count', 0)}<br><br>
                {result.get('message', '')}
                """,
                title="Synchronisation BioTime",
                indicator="green" if result.get('failed_count', 0) == 0 else "orange"
            )
        else:
            frappe.msgprint(
                f"Erreur lors de la synchronisation: {result.get('message', '')}",
                title="Erreur",
                indicator="red"
            )
    
    @frappe.whitelist()
    def test_biotime_connection(self):
        """Teste la connexion avec BioTime"""
        try:
            print("🔍 Test de connexion BioTime...")
            tokan = get_tokan()
            main_url = get_url()
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'JWT ' + tokan
            }
            
            # Test simple: récupérer les infos du serveur
            response = requests.get(f"{main_url}/personnel/api/employees/?page_size=1", headers=headers, timeout=10)
            
            if response.ok:
                data = response.json()
                total_employees = data.get('count', 0)
                
                frappe.msgprint(
                    f"""
                    <b>✅ Connexion BioTime Réussie</b><br><br>
                    • URL: {main_url}<br>
                    • Token: Valide<br>
                    • Total employés: {total_employees}<br>
                    • Status: {response.status_code}
                    """,
                    title="Test Connexion",
                    indicator="green"
                )
                print(f"✅ Connexion réussie: {total_employees} employés trouvés")
            else:
                frappe.msgprint(
                    f"""
                    <b>❌ Échec Connexion BioTime</b><br><br>
                    • Status Code: {response.status_code}<br>
                    • Erreur: {response.text}
                    """,
                    title="Test Connexion",
                    indicator="red"
                )
                print(f"❌ Connexion échouée: {response.status_code}")
                
        except Exception as e:
            frappe.msgprint(
                f"❌ Erreur de connexion: {str(e)}",
                title="Test Connexion",
                indicator="red"
            )
            print(f"❌ Exception connexion: {str(e)}")
    
    @frappe.whitelist()
    def debug_raw_data(self):
        """Débogage des données brutes BioTime"""
        result = debug_biotime_raw_data()
        frappe.msgprint(
            f"""
            <b>🔍 Débogage Terminé</b><br><br>
            Status: {result.get('status')}<br>
            Message: {result.get('message', '')}<br>
            Employés trouvés: {result.get('employees_count', 0)}<br><br>
            <b>Vérifiez la console du serveur pour les détails complets</b>
            """,
            title="Débogage BioTime",
            indicator="blue"
        )

