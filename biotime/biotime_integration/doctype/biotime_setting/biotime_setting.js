// Copyright (c) 2023, ARD and contributors
// For license information, please see license.txt

frappe.ui.form.on('BioTime Setting', {
	fetch_transactions: function (frm) {
		frappe.call({
			method: "enqueue_long_job_fetch_transactions",
			doc: frm.doc,
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
			method: "enqueue_long_job_fetch",
			doc: frm.doc,
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
	},

	test_auth: function (frm) {
		frappe.show_alert({
			message: __('Testing authentication only...'),
			indicator: 'blue'
		});
		
		frappe.call({
			method: "test_auth_only",
			doc: frm.doc,
			callback: function (r) {
				if (!r.exc) {
					console.log("Auth test completed");
				}
			},
		});
	},

	diagnose_auth: function (frm) {
		frappe.show_alert({
			message: __('Running comprehensive auth diagnosis...'),
			indicator: 'blue'
		});
		
		frappe.call({
			method: "diagnose_auth_issue", 
			doc: frm.doc,
			callback: function(r) {
				if (!r.exc) {
					console.log("Auth diagnosis completed");
				}
			},
		});
	},

	sync_transactions: function (frm) {
		// Créer un dialogue pour sélectionner la période
		let dialog = new frappe.ui.Dialog({
			title: __('Select Date Range for Transaction Sync'),
			fields: [
				{
					label: __('Quick Select'),
					fieldname: 'quick_select',
					fieldtype: 'Select',
					options: [
						'',
						'Last 1 Hour',
						'Last 6 Hours', 
						'Last 24 Hours',
						'Today',
						'Yesterday',
						'This Week',
						'Last Week',
						'This Month',
						'Custom Range'
					].join('\n'),
					description: __('Select a predefined period or choose Custom Range'),
					change: function() {
						let selected = this.get_value();
						let start_date, end_date;
						let now = new Date();
						
						switch(selected) {
							case 'Last 1 Hour':
								start_date = new Date(now.getTime() - 60*60*1000);
								end_date = now;
								break;
							case 'Last 6 Hours':
								start_date = new Date(now.getTime() - 6*60*60*1000);
								end_date = now;
								break;
							case 'Last 24 Hours':
								start_date = new Date(now.getTime() - 24*60*60*1000);
								end_date = now;
								break;
							case 'Today':
								start_date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
								end_date = now;
								break;
							case 'Yesterday':
								let yesterday = new Date(now.getTime() - 24*60*60*1000);
								start_date = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 0, 0, 0);
								end_date = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59);
								break;
							case 'This Week':
								let startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()));
								start_date = new Date(startOfWeek.getFullYear(), startOfWeek.getMonth(), startOfWeek.getDate(), 0, 0, 0);
								end_date = new Date();
								break;
							case 'Last Week':
								let lastWeekEnd = new Date(now.setDate(now.getDate() - now.getDay() - 1));
								let lastWeekStart = new Date(lastWeekEnd.getTime() - 6*24*60*60*1000);
								start_date = new Date(lastWeekStart.getFullYear(), lastWeekStart.getMonth(), lastWeekStart.getDate(), 0, 0, 0);
								end_date = new Date(lastWeekEnd.getFullYear(), lastWeekEnd.getMonth(), lastWeekEnd.getDate(), 23, 59, 59);
								break;
							case 'This Month':
								start_date = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0);
								end_date = new Date();
								break;
						}
						
						if (selected && selected !== 'Custom Range') {
							dialog.set_value('start_date', frappe.datetime.obj_to_str(start_date));
							dialog.set_value('end_date', frappe.datetime.obj_to_str(end_date));
						}
					}
				},
				{
					fieldname: 'section_break_dates',
					fieldtype: 'Section Break',
					label: __('Date Range')
				},
				{
					label: __('Start Date'),
					fieldname: 'start_date',
					fieldtype: 'Datetime',
					default: frappe.datetime.add_days(frappe.datetime.now_datetime(), -1),
					reqd: 1,
					description: __('Start date and time for transaction sync')
				},
				{
					fieldname: 'column_break_1',
					fieldtype: 'Column Break'
				},
				{
					label: __('End Date'),
					fieldname: 'end_date',
					fieldtype: 'Datetime',
					default: frappe.datetime.now_datetime(),
					reqd: 1,
					description: __('End date and time for transaction sync')
				},
				{
					fieldname: 'section_break_2',
					fieldtype: 'Section Break',
					label: __('Filters (Optional)')
				},
				{
					label: __('Employee Code'),
					fieldname: 'emp_code',
					fieldtype: 'Data',
					description: __('Sync transactions for specific employee only (leave empty for all employees)')
				}
			],
			primary_action_label: __('Sync Transactions'),
			primary_action(values) {
				// Validation des dates
				if (values.start_date >= values.end_date) {
					frappe.msgprint({
						title: __('Invalid Date Range'),
						indicator: 'red',
						message: __('Start date must be before end date')
					});
					return;
				}
				
				// Vérifier que la période n'est pas trop longue (max 30 jours)
				let start_date = new Date(values.start_date);
				let end_date = new Date(values.end_date);
				let diff_days = (end_date - start_date) / (1000 * 60 * 60 * 24);
				
				if (diff_days > 30) {
					frappe.confirm(
						__('You selected a period longer than 30 days. This might take a while and could create many records. Do you want to continue?'),
						() => {
							sync_transactions_with_dates(frm, values);
							dialog.hide();
						}
					);
				} else {
					sync_transactions_with_dates(frm, values);
					dialog.hide();
				}
			}
		});
		
		dialog.show();
	}
});

function sync_transactions_with_dates(frm, values) {
	frappe.show_alert({
		message: __('Synchronizing BioTime transactions for selected period...'),
		indicator: 'blue'
	});
	
	frappe.call({
		method: "sync_transactions_with_daterange",
		doc: frm.doc,
		args: {
			start_date: values.start_date,
			end_date: values.end_date,
			emp_code: values.emp_code || null
		},
		callback: function(r) {
			if (!r.exc) {
				console.log("Transactions sync with date range completed");
			}
		},
	});
}

function auto_map_single_employee(frm) {
    frappe.call({
        method: 'biotime.biotime_integration.doctype.employee_discovery.employee_discovery.auto_map_departments_and_designations',
        callback: function(r) {
            if (r.message) {
                frm.reload_doc();
                frappe.msgprint(__('Auto-mapping completed'));
            }
        }
    });
}

// Actions de masse depuis la liste
frappe.listview_settings['Employee Discovery'] = {
    onload: function(listview) {
        listview.page.add_action_item(__('Discover New Employees'), function() {
            frappe.call({
                method: 'biotime.api.discover_biotime_employees',
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.msgprint(r.message.message);
                        listview.refresh();
                    }
                }
            });
        });
        
        listview.page.add_action_item(__('Auto Map All'), function() {
            frappe.call({
                method: 'biotime.biotime_integration.doctype.employee_discovery.employee_discovery.auto_map_departments_and_designations',
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(`Mapped ${r.message.mapped_count} of ${r.message.total_discoveries} discoveries`);
                        listview.refresh();
                    }
                }
            });
        });
    },
    
    get_indicator: function(doc) {
        if (doc.status === "Employee Created") {
            return [__("Created"), "green", "status,=,Employee Created"];
        } else if (doc.status === "Validated") {
            return [__("Validated"), "blue", "status,=,Validated"];
        } else if (doc.status === "Rejected") {
            return [__("Rejected"), "red", "status,=,Rejected"];
        } else {
            return [__("Pending"), "orange", "status,=,Pending Validation"];
        }
    }
};
