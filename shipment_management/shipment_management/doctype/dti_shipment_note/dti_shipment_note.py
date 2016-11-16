# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigiThinkit Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _


class DTIShipmentNote(Document):
	def validate(self):
		if self.shipment_provider == "N/A":
			frappe.throw(_("STEP 2: Please specify shipment provider!"))

		if self.shipment_provider == "FEDEX":

			# fedex = frappe.get_doc('DTI Fedex Shipment', self.fedex_name)
			pass

	def on_submit(self):

		if self.shipment_provider == "FEDEX" and not self.fedex_name:
			frappe.throw(_("STEP 2: Please create FEDEX shipment!"))

		frappe.clear_cache(doctype="DTI Shipment Note")
