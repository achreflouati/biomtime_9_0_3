import frappe
import json
import requests
from frappe import _
from frappe import publish_progress
from frappe.utils import get_first_day, get_last_day, today, add_to_date
from frappe.utils import add_to_date

from datetime import datetime

# Biometric Integration

@frappe.whitelist()
def discover_biotime_employees():
    """Découvre les employés présents dans BioTime mais absents dans ERPNext"""
    main_url = get_url()
    headers = get_auth_headers()
    
    try:
        # Console de débogage
        print("🔍 DEBUG: Début de découverte des employés BioTime")
        print(f"🌐 URL BioTime: {main_url}")
        print(f"🔑 Headers auth: {headers}")
        
        # Récupérer tous les employés depuis BioTime
        biotime_employees = fetch_all_biotime_employees(headers, main_url)
        print(f"👥 Employés BioTime trouvés: {len(biotime_employees)}")
        
        # Afficher les premiers employés pour débogage
        if biotime_employees:
            print("📋 Premiers employés BioTime:")
            for i, emp in enumerate(biotime_employees[:3]):
                print(f"   {i+1}. Code: {emp.get('emp_code')} | Nom: {emp.get('emp_name')} | Dept: {emp.get('department', {}).get('dept_name', 'N/A')}")
        
        # Récupérer tous les employés ERPNext avec device_id
        erpnext_employees = frappe.db.get_all(
            "Employee", 
            fields=["name", "employee_name", "attendance_device_id"],
            filters={"attendance_device_id": ["!=", ""]}
        )
        print(f"👥 Employés ERPNext avec device_id: {len(erpnext_employees)}")
        
        # Afficher les device_ids ERPNext pour débogage
        if erpnext_employees:
            device_ids = [emp.attendance_device_id for emp in erpnext_employees if emp.attendance_device_id]
            print(f"🔢 Device IDs ERPNext: {device_ids[:10]}...")  # Afficher les 10 premiers
        
        # Identifier les employés manquants
        missing_employees = find_missing_employees(biotime_employees, erpnext_employees)
        print(f"❓ Employés manquants trouvés: {len(missing_employees)}")
        
        if missing_employees:
            print("📝 Employés manquants détaillés:")
            for i, emp in enumerate(missing_employees[:5]):  # Afficher les 5 premiers
                print(f"   {i+1}. Device ID: {emp['device_id']} | Nom: {emp['name']} | Dept: {emp['department']}")
        
        # Sauvegarder pour validation utilisateur
        save_discovered_employees(missing_employees)
        
        # Console de fin
        print("✅ Découverte terminée avec succès")
        
        return {
            "status": "success",
            "biotime_count": len(biotime_employees),
            "erpnext_count": len(erpnext_employees),
            "missing_count": len(missing_employees),
            "message": f"Trouvé {len(missing_employees)} employés à valider"
        }
        
    except Exception as e:
        print(f"❌ ERREUR lors de la découverte: {str(e)}")
        frappe.log_error(message=str(e), title="Erreur Découverte Employés")
        return {"status": "error", "message": str(e)}

def fetch_all_biotime_employees(headers, main_url):
    """Récupère tous les employés depuis BioTime avec pagination et débogage"""
    employees_list = []
    is_next_page = True
    url = f"{main_url}/personnel/api/employees/"
    page_count = 0
    
    print(f"🔗 URL initiale: {url}")
    
    while is_next_page:
        page_count += 1
        print(f"📄 Traitement page {page_count}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"📡 Status Code: {response.status_code}")
            
            if response.ok:
                res = response.json()
                employees = res.get("data", [])
                total_count = res.get("count", 0)
                
                print(f"👥 Page {page_count}: {len(employees)} employés récupérés")
                print(f"📊 Total dans BioTime: {total_count}")
                
                # Afficher structure d'un employé pour débogage
                if employees and page_count == 1:
                    sample_emp = employees[0]
                    print(f"📋 Structure employé exemple:")
                    print(f"   - emp_code: {sample_emp.get('emp_code')}")
                    print(f"   - emp_name: {sample_emp.get('emp_name')}")
                    print(f"   - department: {sample_emp.get('department')}")
                    print(f"   - position: {sample_emp.get('position')}")
                    print(f"   - Toutes les clés: {list(sample_emp.keys())}")
                
                employees_list.extend(employees)
                url = res.get("next")
                if not url:
                    is_next_page = False
                    print("✅ Dernière page atteinte")
                else:
                    print(f"➡️ Page suivante: {url}")
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                frappe.log_error(
                    message=f"Erreur API BioTime: {response.status_code} - {response.text}", 
                    title="Erreur Récupération Employés"
                )
                break
        except Exception as e:
            print(f"❌ Exception page {page_count}: {str(e)}")
            frappe.log_error(message=str(e), title="Erreur API BioTime")
            break
    
    print(f"✅ Total employés récupérés: {len(employees_list)} sur {page_count} pages")
    return employees_list

def find_missing_employees(biotime_employees, erpnext_employees):
    """Trouve les employés présents dans BioTime mais absents dans ERPNext"""
    erpnext_device_ids = {emp.attendance_device_id for emp in erpnext_employees if emp.attendance_device_id}
    
    missing_employees = []
    for biotime_emp in biotime_employees:
        device_id = str(biotime_emp.get("emp_code", ""))
        if device_id and device_id not in erpnext_device_ids:
            missing_employees.append({
                "device_id": device_id,
                "name": biotime_emp.get("emp_name", ""),
                "department": biotime_emp.get("department", {}).get("dept_name", ""),
                "position": biotime_emp.get("position", {}).get("position_name", ""),
                "biotime_data": biotime_emp
            })
    
    return missing_employees

def save_discovered_employees(missing_employees):
    """Sauvegarde les employés découverts pour validation"""
    # Supprimer les anciennes découvertes
    frappe.db.delete("Employee Discovery", {})
    
    for emp in missing_employees:
        discovery_doc = frappe.new_doc("Employee Discovery")
        discovery_doc.device_id = emp["device_id"]
        discovery_doc.employee_name = emp["name"]
        discovery_doc.department = emp["department"]
        discovery_doc.position = emp["position"]
        discovery_doc.biotime_data = json.dumps(emp["biotime_data"])
        discovery_doc.status = "Pending Validation"
        discovery_doc.save()
    
    frappe.db.commit()

@frappe.whitelist()
def sync_erpnext_employees_to_biotime():
    """Synchronise les employés ERPNext vers BioTime"""
    main_url = get_url()
    headers = get_auth_headers()
    
    try:
        print("🔄 DEBUG: Début synchronisation ERPNext vers BioTime")
        
        # Récupérer employés ERPNext sans device_id (nouveaux employés)
        new_employees = frappe.db.get_all(
            "Employee",
            fields=["name", "employee_name", "department", "designation", "employment_type"],
            filters=[
                ["status", "=", "Active"],
                ["attendance_device_id", "in", [None, ""]]
            ]
        )
        
        print(f"👥 Employés ERPNext sans device_id: {len(new_employees)}")
        
        if not new_employees:
            return {
                "status": "success",
                "message": "Aucun nouvel employé à synchroniser",
                "created_count": 0
            }
        
        created_count = 0
        failed_count = 0
        
        for emp in new_employees[:5]:  # Limiter à 5 pour test
            print(f"🆕 Création employé: {emp.employee_name}")
            
            success = create_employee_in_biotime(emp, headers, main_url)
            if success:
                created_count += 1
                print(f"✅ Employé créé avec succès: {emp.employee_name}")
            else:
                failed_count += 1
                print(f"❌ Échec création: {emp.employee_name}")
        
        print(f"📊 Résumé: {created_count} créés, {failed_count} échecs")
        
        return {
            "status": "success",
            "created_count": created_count,
            "failed_count": failed_count,
            "message": f"Synchronisation terminée: {created_count} employés créés, {failed_count} échecs"
        }
        
    except Exception as e:
        print(f"❌ ERREUR synchronisation: {str(e)}")
        frappe.log_error(message=str(e), title="Erreur Sync ERPNext vers BioTime")
        return {"status": "error", "message": str(e)}

def create_employee_in_biotime(employee_data, headers, main_url):
    """Crée un employé dans BioTime selon la documentation officielle"""
    try:
        # ✅ CORRECTION: Structure selon la documentation API
        biotime_data = {
            "emp_code": employee_data.name,  # Code employé unique
            "first_name": employee_data.employee_name.split()[0] if employee_data.employee_name else "Unknown",
            "last_name": " ".join(employee_data.employee_name.split()[1:]) if len(employee_data.employee_name.split()) > 1 else "",
            # Département doit être un ID, pas un objet
            "department": get_biotime_department_id(employee_data.department),
        }
        
        # Ajouter le poste si disponible
        position_id = get_biotime_position_id(employee_data.designation)
        if position_id:
            biotime_data["position"] = position_id
        
        print(f"📤 Données envoyées à BioTime: {json.dumps(biotime_data, indent=2)}")
        
        # Envoyer vers BioTime
        url = f"{main_url}/personnel/api/employees/"
        response = requests.post(url, data=json.dumps(biotime_data), headers=headers, timeout=30)
        
        print(f"📡 Réponse BioTime Status: {response.status_code}")
        print(f"📡 Réponse BioTime Body: {response.text}")
        
        if response.ok:
            response_data = response.json()
            biotime_emp_code = response_data.get("emp_code")
            
            # Mettre à jour ERPNext avec le device_id
            if biotime_emp_code:
                frappe.db.set_value("Employee", employee_data.name, "attendance_device_id", biotime_emp_code)
                frappe.db.commit()
                print(f"✅ Device ID mis à jour: {biotime_emp_code}")
            
            return True
        else:
            print(f"❌ Erreur création BioTime: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception création BioTime: {str(e)}")
        frappe.log_error(
            message=f"Erreur création employé {employee_data.employee_name}: {str(e)}",
            title="Erreur Création BioTime"
        )
        return False

def get_biotime_department_id(erpnext_dept):
    """Récupère l'ID du département BioTime"""
    if not erpnext_dept:
        return None
    
    # Chercher dans les mappings
    mapping = frappe.db.get_value(
        "Department Mapping",
        {"erpnext_department": erpnext_dept},
        "biotime_department"
    )
    
    if mapping:
        # TODO: Ici, il faudrait faire un appel API pour récupérer l'ID du département
        # Pour l'instant, retournons 1 (département par défaut)
        return 1
    
    # Retourner département par défaut
    return 1

def get_biotime_position_id(erpnext_designation):
    """Récupère l'ID du poste BioTime"""
    if not erpnext_designation:
        return None
    
    # TODO: Implémenter la recherche de poste via API
    # Pour l'instant, retournons None
    return None



@frappe.whitelist()
def debug_biotime_raw_data():
    """Fonction de débogage pour voir les données brutes BioTime"""
    main_url = get_url()
    headers = get_auth_headers()
    
    try:
        print("🔍 === DÉBOGAGE DONNÉES BIOTIME ===")
        print(f"🌐 URL: {main_url}")
        print(f"🔑 Headers: {headers}")
        
        # Test plusieurs endpoints
        endpoints = [
            "/personnel/api/employees/",
            "/personnel/api/departments/", 
            "/personnel/api/positions/",
            "/iclock/api/transactions/"
        ]
        
        for endpoint in endpoints:
            print(f"\n📡 Test endpoint: {endpoint}")
            url = f"{main_url}{endpoint}?page_size=2"
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"   Status: {response.status_code}")
                
                if response.ok:
                    data = response.json()
                    print(f"   Structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    if isinstance(data, dict) and 'data' in data:
                        print(f"   Count: {data.get('count', 'N/A')}")
                        if data['data']:
                            print(f"   Premier élément clés: {list(data['data'][0].keys())}")
                            print(f"   Premier élément: {json.dumps(data['data'][0], indent=4, ensure_ascii=False)}")
                else:
                    print(f"   Erreur: {response.text}")
                    
            except Exception as e:
                print(f"   Exception: {str(e)}")
        
        # Test récupération employés complet
        print(f"\n👥 === TEST RÉCUPÉRATION EMPLOYÉS COMPLET ===")
        employees = fetch_all_biotime_employees(headers, main_url)
        
        if employees:
            print(f"✅ Total employés récupérés: {len(employees)}")
            print(f"📋 Structure premier employé:")
            emp_example = employees[0]
            for key, value in emp_example.items():
                print(f"   {key}: {value}")
        
        return {
            "status": "success", 
            "message": "Débogage terminé, vérifiez la console du serveur",
            "employees_count": len(employees) if employees else 0
        }
        
    except Exception as e:
        print(f"❌ ERREUR DÉBOGAGE: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def test_authentication_only():
    """Test spécifique de l'authentification BioTime"""
    try:
        print("🔐 === TEST AUTHENTIFICATION BIOTIME ===")
        
        doc = frappe.get_single("BioTime Setting")
        # ✅ CORRECTION: Endpoint correct selon la documentation
        url = doc.url + "/api-token-auth/"
        
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "username": doc.user_name,
            "password": doc.get_password('password')
        }
        
        print(f"🌐 URL auth: {url}")
        print(f"👤 Username: '{doc.user_name}'")
        print(f"🔑 Password length: {len(doc.get_password('password') or '')}")
        print(f"📤 Données envoyées: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Headers réponse: {dict(response.headers)}")
        print(f"📡 Réponse brute: '{response.text}'")
        
        if response.ok:
            try:
                response_data = response.json()
                print(f"📋 JSON parsé: {json.dumps(response_data, indent=2)}")
                
                return {
                    "status": "success",
                    "message": "Authentification réussie",
                    "response_data": response_data,
                    "raw_response": response.text
                }
            except Exception as e:
                print(f"❌ Erreur parsing JSON: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Réponse non-JSON: {response.text}"
                }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        print(f"❌ Exception test auth: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_tokan():
    """Récupère un token depuis BioTime selon la documentation officielle"""
    doc = frappe.get_single("BioTime Setting")
    # ✅ CORRECTION: Endpoint correct selon la documentation
    url = doc.url + "/api-token-auth/"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "username": doc.user_name,
        "password": doc.get_password('password')
    }
    
    print(f"🔐 Récupération token depuis: {url}")
    print(f"👤 Username: {doc.user_name}")
    print(f"🔑 Password fourni: {'✅ Oui' if doc.get_password('password') else '❌ Non'}")
    print(f"📤 Données envoyées: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Response: {response.text}")
        
        if response.ok:
            response_data = response.json()
            print(f"📋 Structure réponse: {response_data}")
            
            # ✅ CORRECTION: Selon la doc, le token est dans {"token": "..."}
            token = response_data.get("token")
            
            if token:
                print(f"✅ Token récupéré avec succès: {token[:20]}...")
                return token
            else:
                print(f"❌ Pas de token dans la réponse: {response_data}")
                frappe.throw(
                    title='Erreur Token',
                    msg=f'Token non trouvé. Structure: {response_data}',
                )
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            frappe.throw(
                title='Erreur Authentification',
                msg=f'Erreur {response.status_code}: Vérifiez vos identifiants BioTime',
            )
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau: {str(e)}")
        frappe.log_error(
            message=f"Erreur réseau lors de l'authentification: {str(e)}", 
            title="Erreur Connexion BioTime"
        )
        frappe.throw(
            title='Erreur Connexion',
            msg='Impossible de se connecter au serveur BioTime. Vérifiez l\'URL.',
        )
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        frappe.log_error(
            message=f"Erreur lors de la récupération du token: {str(e)}", 
            title="Erreur Token BioTime"
        )
        frappe.throw(
            title='Erreur',
            msg='Échec de récupération du token. Vérifiez vos paramètres.',
        )
    


def get_url():
    doc = frappe.get_single("BioTime Setting")
    url = doc.url
    return url

def get_auth_headers():
    """Retourne les headers d'authentification selon la documentation officielle"""
    token = get_tokan()
    return {
        'Content-Type': 'application/json',
        # ✅ CORRECTION: Format correct selon la documentation officielle
        'Authorization': 'Token ' + token
    }

@frappe.whitelist()
def fetch_transactions():
    main_url = get_url()
    headers = get_auth_headers()

    transactions_list = []

    start_date = get_first_day(today()).strftime("%Y-%m-%d %H:%M:%S")
    end_date = get_last_day(today()).strftime("%Y-%m-%d %H:%M:%S")
    end_date = add_to_date(end_date, days=1)
    is_next_page = True
    url = f"{main_url}/iclock/api/transactions/?start_time={start_date}&end_time={end_date}"

    progress_count = 0
    count = 0
    while is_next_page:
        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if not res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")
    
    is_next_page = True
    while is_next_page:

        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")

        progress_count += 10
        publish_progress(progress_count*100/int(count + 1),
                         title="Fetching Transactions...")

    if len(transactions_list):

        handel_transactions(transactions_list)

def handel_transactions(transactions):
    exists_trans = 0
    progress_count = 0
    created = 0
    errors = 0
    for transaction in transactions:
        
        # Check if Transaction is Exists
        is_exists = frappe.db.exists(
            {"doctype": "Employee Checkin", "transaction_id": transaction.get("id")})
        if is_exists:
            exists_trans += 1
        else:
            # Check if employee exists
            is_emp_exists = frappe.db.exists(
                {"doctype": "Employee", "attendance_device_id": transaction.get("emp_code")})
            if is_emp_exists:
                # Create Transaction
                new_trans = create_employee_checkin(transaction)
                if new_trans:
                    created += 1
                else:
                    errors += 1
            else:
                trans_no = transaction.get("id")
                emp_code = transaction.get("emp_code")         
                errors += 1
                frappe.msgprint(
                    msg=_(f"Can't Create Transaction No. { str(trans_no) } because Employee with code { emp_code } Not in System, Please make sure to Fetching Employees"),
                    title=_("Transaction Creation Faild"),
                )
        progress_count += 1

        publish_progress(int(progress_count * 100/len(transactions)),
                         title="Creating Employee Checkin...")

    msg = "Try to Create {} Employee Checkin: <br> {} already Exists In System  <br> {} Successfully Created ,<br> {} Failed <hr> for more details about Failed Employee Checkin Docs review errors log".format(
        len(transactions), exists_trans, created, errors)
    if created >0:
        shift_list =  frappe.get_list("Shift Type" , filters = {"enable_auto_attendance" : 1})
        for shift in shift_list:
            shift_doc = frappe.get_doc("Shift Type" , shift)
            shift_doc.last_sync_of_checkin = datetime.now()
            shift_doc.save()
            frappe.db.commit()
    frappe.publish_realtime('msgprint', msg)
    
def create_employee_checkin(transaction):
    res = False
    if transaction:
        try:
            log_type = ""
            if transaction.get("punch_state") == "1":
                log_type = "OUT"
            elif transaction.get("punch_state") == "0":
                log_type = "IN"
            else:
                log_type = ""

            employee = frappe.db.get_list(
                "Employee", filters={"attendance_device_id": transaction.get("emp_code")})
            doc = frappe.new_doc('Employee Checkin')
            doc.employee = employee[0].name
            doc.time = transaction.get("punch_time")
            doc.log_type = log_type
            doc.transaction_id = transaction.get("id")
            doc.save()
            res = True
            frappe.db.commit()
        except Exception as e:
            trans_no = transaction.get("id")
            frappe.log_error(
                message=e, title=f"Failed to Create Employee With id <b> {trans_no} <b>")
            res = False
    return res

# هذا الكود كتب على وجه الاستعجال لحل مشكلة بشكل شريع ,,,,  سيحتاج الكود الى تعديل و تحسين ف المستقبل ليكون اقل في عدد الاسطر و اكثر فاعليى
# كتب بتاريخ 11 / 02 /2024
# من قبل م هديل
# لحل مشكلة في عبور ,,, الشمكلة حدثت قبل تسيلم تعديل الكود الاخير الذي سيكون بدوره مانع لوقوع المشكلة 

@frappe.whitelist()
def fetch():
    main_url = get_url()
    headers = get_auth_headers()

    transactions_list = []
    date = frappe.get_single("BioTime Setting").date
    print("DDDDDDDDDDDDDDDDDDDD" , date)
    start_date = get_first_day(date).strftime("%Y-%m-%d %H:%M:%S")
    end_date = get_last_day(date).strftime("%Y-%m-%d %H:%M:%S")
    end_date = add_to_date(end_date, days=1)
    print("DDDDDDDDDDDDDDDDDDDD" , start_date, end_date)

    is_next_page = True
    url = f"{main_url}/iclock/api/transactions/?start_time={start_date}&end_time={end_date}"

    progress_count = 0
    count = 0
    is_next_page = True
    while is_next_page:

        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if not res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")
    is_next_page = True
    while is_next_page:

        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")

        progress_count += 10
        publish_progress(progress_count*100/int(count + 1),
                         title="Fetching Transactions...")
        progress_count += 10
        publish_progress(progress_count*100/int(count + 1),
                         title="Fetching Transactions...")
    print(len(transactions_list))
    if len(transactions_list):
        handel_transactions(transactions_list)
