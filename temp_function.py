def create_employee_in_biotime(employee_data, headers, main_url):
    """Crée un employé dans BioTime selon la documentation officielle"""
    try:
        # Récupérer l'ID de la première zone disponible (obligatoire)
        area_id = get_default_biotime_area_id(headers, main_url)
        
        # ✅ Structure minimale selon la documentation API officielle
        biotime_data = {
            "emp_code": employee_data.name,  # Obligatoire : Code employé unique
            "department": get_biotime_department_id(employee_data.department),  # Obligatoire : ID département  
            "area": [area_id] if area_id else [1]  # Obligatoire : Array d'IDs de zones
        }
        
        # Ajouter les champs optionnels seulement s'ils existent
        if employee_data.employee_name:
            name_parts = employee_data.employee_name.split()
            if len(name_parts) > 0:
                biotime_data["first_name"] = name_parts[0]
            if len(name_parts) > 1:
                biotime_data["last_name"] = " ".join(name_parts[1:])
        
        # Ajouter le poste si disponible
        position_id = get_biotime_position_id(employee_data.designation)
        if position_id:
            biotime_data["position"] = position_id
        
        print(f"📤 Données envoyées à BioTime: {json.dumps(biotime_data, indent=2)}")
        
        # ✅ Envoyer vers BioTime selon la documentation officielle
        url = f"{main_url}/personnel/api/employees/"
        
        print(f"🌐 URL: {url}")
        print(f"🔑 Headers: {headers}")
        
        # Utiliser json= pour l'encodage automatique (plus fiable)
        response = requests.post(url, json=biotime_data, headers=headers, timeout=30)
        
        print(f"📡 Réponse BioTime Status: {response.status_code}")
        print(f"📡 Réponse BioTime Headers: {dict(response.headers)}")
        print(f"📡 Réponse BioTime Body: {response.text[:500]}...")  # Limiter l'affichage
        
        if response.ok:
            # Vérifier si la réponse est du JSON valide
            try:
                response_data = response.json()
                print(f"✅ Réponse JSON parsée: {response_data}")
                
                biotime_emp_code = response_data.get("emp_code")
                biotime_emp_id = response_data.get("id")
                
                # Mettre à jour ERPNext avec le device_id (utiliser emp_code ou id)
                device_id = biotime_emp_code or str(biotime_emp_id)
                if device_id:
                    frappe.db.set_value("Employee", employee_data.name, "attendance_device_id", device_id)
                    frappe.db.commit()
                    print(f"✅ Device ID mis à jour: {device_id}")
                    return True
                else:
                    print("⚠️ Pas d'emp_code ni d'id dans la réponse")
                    return False
                
            except json.JSONDecodeError as json_err:
                print(f"❌ Erreur parsing JSON: {str(json_err)}")
                print(f"❌ Réponse brute: '{response.text}'")
                return False
                
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