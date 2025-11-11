# Copyright (c) 2025, ARD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class DepartmentMapping(Document):
	def validate(self):
		"""Validation avant sauvegarde"""
		# Vérifier que le département BioTime n'existe pas déjà
		existing = frappe.db.exists(
			"Department Mapping",
			{
				"biotime_department": self.biotime_department,
				"name": ["!=", self.name]
			}
		)
		
		if existing:
			frappe.throw(
				_("Mapping already exists for BioTime Department: {0}").format(self.biotime_department)
			)
	
	def before_save(self):
		"""Actions avant sauvegarde"""
		# S'assurer que le nom est basé sur biotime_department
		if not self.name or self.name == "new-department-mapping":
			# ERPNext utilisera automatiquement le champ biotime_department
			# grâce à naming_rule_fieldname
			pass

@frappe.whitelist()
def get_mapping_for_department(biotime_dept):
	"""Récupère le mapping pour un département BioTime"""
	mapping = frappe.db.get_value(
		"Department Mapping",
		{"biotime_department": biotime_dept},
		["erpnext_department", "default_designation", "default_shift_type"],
		as_dict=True
	)
	return mapping or {}

@frappe.whitelist()
def create_auto_mappings():
	"""Crée des mappings automatiques basés sur les noms similaires"""
	# Récupérer tous les départements ERPNext
	erpnext_departments = frappe.get_all(
		"Department", 
		fields=["name", "department_name"]
	)
	
	# Récupérer les départements BioTime depuis Employee Discovery
	biotime_departments = frappe.db.sql("""
		SELECT DISTINCT department 
		FROM `tabEmployee Discovery` 
		WHERE department IS NOT NULL 
		AND department != ''
		AND department NOT IN (
			SELECT biotime_department 
			FROM `tabDepartment Mapping`
		)
	""", as_dict=True)
	
	created_count = 0
	
	for biotime_dept in biotime_departments:
		dept_name = biotime_dept.department
		
		# Chercher un département ERPNext similaire
		matched_dept = None
		for erpnext_dept in erpnext_departments:
			if (dept_name.lower() in erpnext_dept.department_name.lower() or
				erpnext_dept.department_name.lower() in dept_name.lower()):
				matched_dept = erpnext_dept.name
				break
		
		# Créer le mapping si trouvé
		if matched_dept:
			try:
				mapping_doc = frappe.new_doc("Department Mapping")
				mapping_doc.biotime_department = dept_name
				mapping_doc.erpnext_department = matched_dept
				mapping_doc.save()
				created_count += 1
			except Exception as e:
				frappe.log_error(f"Erreur création mapping: {e}")
	
	return {
		"created_count": created_count,
		"total_biotime_departments": len(biotime_departments)
	}