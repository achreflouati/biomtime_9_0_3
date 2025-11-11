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
	}
});
