# Copyright (c) 2025, ARD and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from frappe import _

class EmployeeDiscovery(Document):
    
    def validate(self):
        """Validation avant sauvegarde"""
        if self.status == "Validated" and not self.validated_by:
            self.validated_by = frappe.session.user
            self.validation_date = frappe.utils.now()
    
    @frappe.whitelist()
    def create_employee_from_discovery(self):
        """Crée un employé ERPNext depuis les données BioTime"""
        if self.status != "Validated":
            frappe.throw(_("L'employé doit être validé avant création"))
        
        try:
            # Récupérer les données BioTime
            biotime_data = json.loads(self.biotime_data) if self.biotime_data else {}
            
            # Créer le nouvel employé
            employee_doc = frappe.new_doc('Employee')
            employee_doc.employee_name = self.employee_name
            employee_doc.attendance_device_id = self.device_id
            employee_doc.status = 'Active'
            
            # Mapping des champs
            if self.mapped_department:
                employee_doc.department = self.mapped_department
            if self.mapped_designation:
                employee_doc.designation = self.mapped_designation
            if self.employment_type:
                employee_doc.employment_type = self.employment_type
            if self.default_shift_type:
                employee_doc.default_shift = self.default_shift_type
            
            # Données supplémentaires depuis BioTime
            if biotime_data:
                employee_doc.employee_number = biotime_data.get('emp_code')
                if biotime_data.get('email'):
                    employee_doc.personal_email = biotime_data.get('email')
                if biotime_data.get('mobile'):
                    employee_doc.cell_number = biotime_data.get('mobile')
            
            # Générer le nom d'employé
            employee_doc.naming_series = "EMP-.YYYY.-"
            
            employee_doc.save()
            
            # Mettre à jour le statut de découverte
            self.status = "Employee Created"
            self.notes = f"Employé créé: {employee_doc.name}"
            self.save()
            
            frappe.msgprint(
                _("Employé créé avec succès: {0}").format(employee_doc.name),
                title=_("Succès"),
                indicator="green"
            )
            
            return employee_doc.name
            
        except Exception as e:
            frappe.log_error(
                message=str(e), 
                title=f"Erreur création employé {self.device_id}"
            )
            frappe.throw(_("Erreur lors de la création de l'employé: {0}").format(str(e)))
    
    @frappe.whitelist()
    def reject_discovery(self):
        """Rejette la découverte d'employé"""
        self.status = "Rejected"
        self.validated_by = frappe.session.user
        self.validation_date = frappe.utils.now()
        if not self.notes:
            self.notes = "Rejeté par l'utilisateur"
        self.save()
        
        frappe.msgprint(
            _("Découverte d'employé rejetée"),
            title=_("Rejeté"),
            indicator="red"
        )

@frappe.whitelist()
def bulk_validate_employees(discovery_names, action="validate"):
    """Validation en masse des employés découverts"""
    results = {"success": 0, "failed": 0, "messages": []}
    
    for name in discovery_names:
        try:
            doc = frappe.get_doc("Employee Discovery", name)
            if action == "validate":
                doc.status = "Validated"
                doc.validated_by = frappe.session.user
                doc.validation_date = frappe.utils.now()
                doc.save()
                results["success"] += 1
            elif action == "reject":
                doc.reject_discovery()
                results["success"] += 1
            elif action == "create":
                if doc.status == "Validated":
                    doc.create_employee_from_discovery()
                    results["success"] += 1
                else:
                    results["messages"].append(f"{name}: Doit être validé d'abord")
                    results["failed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["messages"].append(f"{name}: {str(e)}")
    
    return results

@frappe.whitelist()
def auto_map_departments_and_designations():
    """Mapping automatique basé sur les noms similaires"""
    discoveries = frappe.get_all(
        "Employee Discovery", 
        filters={"status": "Pending Validation"},
        fields=["name", "department", "position"]
    )
    
    # Récupérer départements et désignations ERPNext
    departments = frappe.get_all("Department", fields=["name", "department_name"])
    designations = frappe.get_all("Designation", fields=["name", "designation_name"])
    
    mapped_count = 0
    
    for discovery in discoveries:
        doc = frappe.get_doc("Employee Discovery", discovery.name)
        
        # Mapping département (recherche par similarité)
        if discovery.department and not doc.mapped_department:
            for dept in departments:
                if (discovery.department.lower() in dept.department_name.lower() or
                    dept.department_name.lower() in discovery.department.lower()):
                    doc.mapped_department = dept.name
                    break
        
        # Mapping désignation
        if discovery.position and not doc.mapped_designation:
            for desig in designations:
                if (discovery.position.lower() in desig.designation_name.lower() or
                    desig.designation_name.lower() in discovery.position.lower()):
                    doc.mapped_designation = desig.name
                    break
        
        # Sauvegarder si des mappings ont été trouvés
        if doc.mapped_department or doc.mapped_designation:
            doc.save()
            mapped_count += 1
    
    return {"mapped_count": mapped_count, "total_discoveries": len(discoveries)}