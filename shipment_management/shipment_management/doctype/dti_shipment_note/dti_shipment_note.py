# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigiThinkit Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

from shipment_management.app_config import SupportedProviderList


class DTIShipmentNote(Document):

	def validate(self):
		if self.shipment_provider == SupportedProviderList.Undefined:
			frappe.throw(_("Please specify shipment provider!"))

		if self.shipment_provider == SupportedProviderList.Fedex:

			# fedex = frappe.get_doc('DTI Fedex Shipment', self.fedex_name)
			pass

	def on_submit(self):

		if self.shipment_provider == SupportedProviderList.Fedex and not self.fedex_name:
			frappe.throw(_("Please create {} shipment!".format(SupportedProviderList.Fedex)))

		frappe.clear_cache(doctype="DTI Shipment Note")
