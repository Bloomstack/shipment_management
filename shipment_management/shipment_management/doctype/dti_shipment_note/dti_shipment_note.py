# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigiThinkit Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from shipment_management.config.app_config import SupportedProviderList


class DTIShipmentNote(Document):

	def validate(self):

		if self.shipment_provider == SupportedProviderList.Fedex:

			# fedex = frappe.get_doc('DTI Fedex Shipment', self.fedex_name)
			pass

	def on_submit(self):

		if self.shipment_provider == SupportedProviderList.Fedex and not self.fedex_name:
			frappe.throw(_("Please create {} shipment!".format(SupportedProviderList.Fedex)))

		frappe.clear_cache(doctype="DTI Shipment Note")
