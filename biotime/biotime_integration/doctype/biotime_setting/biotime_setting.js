// Copyright (c) 2023, ARD and contributors
// For license information, please see license.txt

frappe.ui.form.on('BioTime Setting', {
	fetch_transactions: function (frm) {
		frappe.call({
			method: "biotime.biotime_integration.doctype.biotime_setting.biotime_setting.enqueue_long_job_fetch_transactions",
			args: {
				"doc": frm.doc
			},
			callback: function (r) {
				if (!r.exc) {
					console.log("Fetch transactions completed");
					frappe.msgprint("✅ Transactions synchronisées avec succès");
				}
			},
		});
	},

	fetch: function (frm) {
		frappe.call({
			method: "biotime.biotime_integration.doctype.biotime_setting.biotime_setting.enqueue_long_job_fetch",
			args: {
				"doc": frm.doc
			},
			callback: function (r) {
				if (!r.exc) {
					console.log("Custom fetch completed");
				}
			},
		});
	},

	discover_employees: function (frm) {
		frappe.show_alert({
			message: __('Scanning BioTime for new employees...'),
			indicator: 'blue'
		});
		
		frappe.call({
			method: "biotime.biotime_integration.doctype.biotime_setting.biotime_setting.discover_employees",
			args: {
				"doc": frm.doc
			},
			callback: function (r) {
				if (!r.exc) {
					// Le message est affiché dans la méthode Python
					// Rediriger vers la liste Employee Discovery
					setTimeout(() => {
						frappe.set_route('List', 'Employee Discovery', {
							'status': 'Pending Validation'
						});
					}, 2000);
				}
			},
		});
	},

	sync_to_biotime: function (frm) {
		frappe.confirm(
			'Voulez-vous synchroniser les nouveaux employés ERPNext vers BioTime ?',
			function() {
				frappe.show_alert({
					message: __('Synchronizing employees to BioTime...'),
					indicator: 'blue'
				});
				
				frappe.call({
					method: "biotime.biotime_integration.doctype.biotime_setting.biotime_setting.sync_to_biotime",
					args: {
						"doc": frm.doc
					},
					callback: function (r) {
						if (!r.exc) {
							console.log("Sync to BioTime completed");
						}
					},
				});
			}
		);
	},

	test_connection: function (frm) {
		frappe.show_alert({
			message: __('Testing BioTime connection...'),
			indicator: 'blue'
		});
		
		frappe.call({
			method: "biotime.biotime_integration.doctype.biotime_setting.biotime_setting.test_biotime_connection",
			args: {
				"doc": frm.doc
			},
			callback: function (r) {
				if (!r.exc) {
					console.log("Connection test completed");
				}
			},
		});
	},

	debug_data: function (frm) {
		frappe.show_alert({
			message: __('Debugging BioTime raw data...'),
			indicator: 'blue'
		});
		
		frappe.call({
			method: "biotime.biotime_integration.doctype.biotime_setting.biotime_setting.debug_raw_data",
			args: {
				"doc": frm.doc
			},
			callback: function (r) {
				if (!r.exc) {
					console.log("Raw data debug completed");
				}
			},
		});
	},

	test_auth: function (frm) {
		frappe.show_alert({
			message: __('Testing authentication only...'),
			indicator: 'blue'
		});
		
		frappe.call({
			method: "biotime.biotime_integration.doctype.biotime_setting.biotime_setting.test_auth_only",
			args: {
				"doc": frm.doc
			},
			callback: function (r) {
				if (!r.exc) {
					console.log("Auth test completed");
				}
			},
		});
	}
});
