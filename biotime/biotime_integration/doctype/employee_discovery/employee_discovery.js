// Copyright (c) 2025, ARD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Discovery', {
    refresh: function(frm) {
        // Ajouter boutons personnalisés
        if (frm.doc.status === "Pending Validation") {
            frm.add_custom_button(__('Validate'), function() {
                frm.set_value('status', 'Validated');
                frm.save();
            }, __('Actions'));
            
            frm.add_custom_button(__('Auto Map'), function() {
                auto_map_single_employee(frm);
            }, __('Actions'));
        }
        
        if (frm.doc.status === "Validated") {
            frm.add_custom_button(__('Create Employee'), function() {
                frappe.call({
                    method: "create_employee_from_discovery",
                    doc: frm.doc,
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Employee created successfully!'));
                            frm.reload_doc();
                        }
                    },
                    error: function(r) {
                        // Fallback: utiliser le wrapper
                        console.log("Trying fallback method...");
                        frappe.call({
                            method: "biotime.api.create_employee_from_discovery_wrapper",
                            args: {
                                "discovery_name": frm.doc.name
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.msgprint(__('Employee created successfully!'));
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });
            }, __('Actions')).addClass('btn-primary');
        }
        
        // Bouton de rejet toujours disponible
        if (frm.doc.status !== "Employee Created" && frm.doc.status !== "Rejected") {
            frm.add_custom_button(__('Reject'), function() {
                frappe.call({
                    method: "reject_discovery",
                    doc: frm.doc,
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Discovery rejected'));
                            frm.reload_doc();
                        }
                    },
                    error: function(r) {
                        // Fallback: utiliser le wrapper
                        frappe.call({
                            method: "biotime.api.reject_employee_discovery_wrapper",
                            args: {
                                "discovery_name": frm.doc.name
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.msgprint(__('Discovery rejected'));
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });
            }, __('Actions'));
        }
    },
    
    create_employee: function(frm) {
        frappe.call({
            method: "create_employee_from_discovery",
            doc: frm.doc,
            callback: function(r) {
                if (!r.exc) {
                    frappe.msgprint(__('Employee created successfully!'));
                    frm.reload_doc();
                }
            }
        });
    },
    
    reject_discovery: function(frm) {
        frappe.call({
            method: "reject_discovery",
            doc: frm.doc,
            callback: function(r) {
                if (!r.exc) {
                    frappe.msgprint(__('Discovery rejected'));
                    frm.reload_doc();
                }
            }
        });
    },
    
    status: function(frm) {
        if (frm.doc.status === "Validated" && !frm.doc.validated_by) {
            frm.set_value('validated_by', frappe.session.user);
            frm.set_value('validation_date', frappe.datetime.now_datetime());
        }
    }
});

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