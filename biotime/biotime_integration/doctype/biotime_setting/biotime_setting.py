# Copyright (c) 2023, ARD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import enqueue
from biotime.api import fetch_transactions , fetch


class BioTimeSetting(Document):
    @frappe.whitelist()
    def enqueue_long_job_fetch_transactions(self):
        # enqueue('biotime.api.fetch_transactions', queue="long", timeout=3600)
       fetch_transactions()
    @frappe.whitelist()
    def enqueue_long_job_fetch(self):
        # enqueue('biotime.api.fetch_transactions', queue="long", timeout=3600)
        fetch()

