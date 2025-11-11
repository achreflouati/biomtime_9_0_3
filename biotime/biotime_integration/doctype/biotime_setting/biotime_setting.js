// Copyright (c) 2023, ARD and contributors
// For license information, please see license.txt

frappe.ui.form.on('BioTime Setting', {
	fetch_transactions: function (frm) {
		frappe.call({
			method: "enqueue_long_job_fetch_transactions",
			doc: frm.doc,
			callback: function (r) {
				if (!r.exc) {
					console.log("Done !!!!!!!!!!!!!!!!!!!!!");
				}
			},
		});
	},

	fetch: function (frm) {
		frappe.call({
			method: "enqueue_long_job_fetch",
			doc: frm.doc,
			callback: function (r) {
				if (!r.exc) {
					console.log("Done !!!!!!!!!!!!!!!!!!!!!");
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
			method: "discover_employees",
			doc: frm.doc,
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
					method: "sync_to_biotime",
					doc: frm.doc,
					callback: function (r) {
						if (!r.exc) {
							// Le message est affiché dans la méthode Python
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
			method: "test_biotime_connection",
			doc: frm.doc,
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
			method: "debug_raw_data",
			doc: frm.doc,
			callback: function (r) {
				if (!r.exc) {
					console.log("Raw data debug completed");
				}
			},
		});
	}
});
