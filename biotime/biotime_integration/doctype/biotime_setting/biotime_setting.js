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
	}
});
