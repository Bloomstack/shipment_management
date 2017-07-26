# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigiThinkit Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.file_manager import *
from frappe.utils import cstr


class DTIShipmentNote(Document):

	def set_tracking_ids(self):
		tracking_ids = ",".join([box.tracking_number.replace("-", "") for box in self.box_list])
		for so in set([item.against_sales_order for item in self.delivery_items]):
			existing_tracking_ids = frappe.db.get_value("Sales Order", so, "tracking_ids")
			if existing_tracking_ids:
				if not tracking_ids in existing_tracking_ids:
					updated_tracking_ids = existing_tracking_ids + "," + tracking_ids
			else:
				updated_tracking_ids = tracking_ids

			frappe.db.set_value("Sales Order", so, "tracking_ids", updated_tracking_ids)

	def on_submit(self):

		from shipment_management.config.app_config import SupportedProviderList
		from shipment_management.shipment import ShipmentNoteOperationalStatus

		if self.shipment_provider != SupportedProviderList.Fedex:
			frappe.throw(_("Please specify shipment provider!"))

		if self.shipment_provider == SupportedProviderList.Fedex:
			from shipment_management.provider_fedex import create_fedex_shipment
			create_fedex_shipment(self)

			frappe.db.set(self, 'shipment_note_status', ShipmentNoteOperationalStatus.Created)
			frappe.db.set(self, 'fedex_status', ShipmentNoteOperationalStatus.InProgress)

		self.set_tracking_ids()
		

	def on_cancel(self):

		from shipment_management.config.app_config import SupportedProviderList
		from shipment_management.shipment import ShipmentNoteOperationalStatus

		if self.shipment_provider == SupportedProviderList.Fedex:

			try:
				from shipment_management.provider_fedex import delete_fedex_shipment
				delete_fedex_shipment(self)
				frappe.msgprint(_("Shipment {} has been canceled!".format(self.name)))

				frappe.db.set(self, 'shipment_note_status', ShipmentNoteOperationalStatus.Cancelled)
				frappe.db.set(self, 'fedex_status', ShipmentNoteOperationalStatus.Cancelled)

				from shipment_management.email_controller import get_content_cancel, send_email

				message = get_content_cancel(self)

				send_email(message=message,
						   subject="Shipment to %s [%s] - Cancelled" % (self.recipient_company_name, self.name),
						   recipient_list=self.contact_email.split(","))

			except Exception, error:
				frappe.throw(_(error))
