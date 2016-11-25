# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigiThinkit Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from shipment_management.config.app_config import SupportedProviderList
from frappe import _

from frappe.model.document import Document

from frappe.utils.file_manager import *

from shipment_management.provider_fedex import create_fedex_shipment
from shipment_management.shipment import ShipmentNoteOperationalStatus
from shipment_management.shipment import delete_fedex_shipment

fedex_track_service = frappe.get_module("fedex.services.track_service")
fedex_config = frappe.get_module("fedex.config")
ship_service = frappe.get_module("fedex.services.ship_service")
FedexTrackRequest = fedex_track_service.FedexTrackRequest
FedexConfig = fedex_config.FedexConfig
FedexProcessShipmentRequest = ship_service.FedexProcessShipmentRequest


class DTIShipmentNote(Document):

	def on_submit(self):

		if self.shipment_provider != SupportedProviderList.Fedex:
			frappe.throw(_("Please specify shipment provider!"))

		if self.shipment_provider == SupportedProviderList.Fedex:
			create_fedex_shipment(self)
			frappe.db.set(self, 'shipment_note_status', ShipmentNoteOperationalStatus.InProgress)
			frappe.db.set(self, 'fedex_status', ShipmentNoteOperationalStatus.InProgress)

	def on_cancel(self):
		if self.shipment_provider == SupportedProviderList.Fedex:
			#delete_fedex_shipment(self)

			frappe.msgprint(_("Shipment {} has been canceled!".format(self.name)))

			frappe.db.set(self, 'shipment_note_status', ShipmentNoteOperationalStatus.Cancelled)
			frappe.db.set(self, 'fedex_status', ShipmentNoteOperationalStatus.Cancelled)