// Copyright (c) 2025, ARD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Department Mapping', {
	refresh: function(frm) {
		// Ajouter bouton de validation
		if (!frm.doc.__islocal && frm.doc.erpnext_department) {
			frm.add_custom_button(__('Test Mapping'), function() {
				test_department_mapping(frm);
			});
		}
	}
});

function test_department_mapping(frm) {
	frappe.call({
		method: 'biotime.biotime_integration.doctype.department_mapping.department_mapping.get_mapping_for_department',
		args: {
			'biotime_dept': frm.doc.biotime_department
		},
		callback: function(r) {
			if (r.message) {
				frappe.msgprint({
					title: __('Mapping Test Result'),
					message: `
						<b>BioTime Department:</b> ${frm.doc.biotime_department}<br>
						<b>ERPNext Department:</b> ${r.message.erpnext_department || 'Not Set'}<br>
						<b>Default Designation:</b> ${r.message.default_designation || 'Not Set'}<br>
						<b>Default Shift:</b> ${r.message.default_shift_type || 'Not Set'}
					`,
					indicator: 'green'
				});
			}
		}
	});
}

// Configuration pour la liste
frappe.listview_settings['Department Mapping'] = {
	onload: function(listview) {
		listview.page.add_action_item(__('Create Auto Mappings'), function() {
			frappe.call({
				method: 'biotime.biotime_integration.doctype.department_mapping.department_mapping.create_auto_mappings',
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(`Created ${r.message.created_count} auto-mappings out of ${r.message.total_biotime_departments} BioTime departments`);
						listview.refresh();
					}
				}
			});
		});
	},
	
	get_indicator: function(doc) {
		if (doc.default_shift_type && doc.default_designation) {
			return [__("Complete"), "green", "default_shift_type,!=,"];
		} else if (doc.erpnext_department) {
			return [__("Partial"), "orange", "erpnext_department,!=,"];
		} else {
			return [__("Incomplete"), "red", "erpnext_department,=,"];
		}
	}
};