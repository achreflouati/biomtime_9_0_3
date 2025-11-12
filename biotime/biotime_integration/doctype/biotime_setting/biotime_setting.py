# Copyright (c) 2023, ARD and contributors
# For license information, please see license.txt
# Updated: 2025-11-11 - Force module reload

import frappe
import requests
import json
from frappe.model.document import Document
from frappe import enqueue
from biotime.api import fetch_transactions, fetch, discover_biotime_employees, sync_erpnext_employees_to_biotime, get_tokan, get_url, debug_biotime_raw_data, test_authentication_only, diagnose_biotime_auth_issue, fetch_biotime_transactions


class BioTimeSetting(Document):
    
    @frappe.whitelist()
    def enqueue_long_job_fetch_transactions(self):
        """Synchronise les transactions BioTime vers ERPNext"""
        fetch_transactions()
        return {"status": "success", "message": "Transactions synchronisées"}
    
    @frappe.whitelist()
    def sync_transactions_now(self):
        """Synchronise les transactions BioTime récentes"""
        result = fetch_biotime_transactions()
        if result.get("status") == "success":
            frappe.msgprint(
                f"""
                <b>✅ Transactions Synchronisées</b><br><br>
                <b>📊 Résultats:</b><br>
                • Transactions récupérées: {result.get('transactions_count', 0)}<br>
                • Check-ins créés: {result.get('checkins_created', 0)}<br>
                • Check-ins ignorés: {result.get('checkins_skipped', 0)}<br><br>
                {result.get('message', '')}
                """,
                title="Synchronisation Transactions",
                indicator="green"
            )
        else:
            frappe.msgprint(
                f"""
                <b>❌ Erreur Synchronisation</b><br><br>
                {result.get('error', result.get('message', 'Erreur inconnue'))}
                """,
                title="Erreur Transactions",
                indicator="red"
            )

    @frappe.whitelist()
    def fetch_biotime_transactions(self):
        """Méthode alternative pour synchroniser les transactions"""
        fetch_transactions()
        return {"status": "success", "message": "Transactions synchronisées"}
    
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
            from biotime.api import get_auth_headers
            headers = get_auth_headers()
            main_url = get_url()
            
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

    @frappe.whitelist()
    def diagnose_auth_issue(self):
        """Diagnostic avancé du problème d'authentification"""
        result = diagnose_biotime_auth_issue()
        if result.get("status") == "success":
            working_format = result.get('working_format', 'Aucun')
            working_endpoint = result.get('working_endpoint', 'Aucun')
            
            frappe.msgprint(
                f"""
                <b>🔬 Diagnostic Authentification</b><br><br>
                <b>✅ Format d'auth fonctionnel:</b> {working_format}<br>
                <b>✅ Endpoint fonctionnel:</b> {working_endpoint}<br><br>
                <b>💡 Recommandations:</b><br>
                • Vérifiez les logs de la console pour plus de détails<br>
                • Testez la création d'employés avec ces paramètres<br><br>
                Message: {result.get('message', '')}
                """,
                title="Diagnostic Authentification",
                indicator="green"
            )
        else:
            frappe.msgprint(
                f"""
                <b>❌ Échec Diagnostic</b><br><br>
                Erreur: {result.get('message', '')}<br><br>
                <b>💡 Actions suggérées:</b><br>
                • Vérifiez la configuration URL et credentials<br>
                • Confirmez que le serveur BioTime est accessible<br>
                • Consultez les logs du serveur pour plus de détails
                """,
                title="Diagnostic Authentification",
                indicator="red"
            )

    @frappe.whitelist()
    def test_auth_only(self):
        """Test spécifique de l'authentification"""
        result = test_authentication_only()
        if result.get("status") == "success":
            frappe.msgprint(
                f"""
                <b>✅ Authentification Réussie</b><br><br>
                Message: {result.get('message', '')}<br><br>
                <b>Données reçues:</b><br>
                <pre>{json.dumps(result.get('response_data', {}), indent=2)}</pre>
                """,
                title="Test Authentification",
                indicator="green"
            )
        else:
            frappe.msgprint(
                f"""
                <b>❌ Échec Authentification</b><br><br>
                Erreur: {result.get('message', '')}<br><br>
                Vérifiez vos identifiants BioTime.
                """,
                title="Test Authentification",
                indicator="red"
            )

