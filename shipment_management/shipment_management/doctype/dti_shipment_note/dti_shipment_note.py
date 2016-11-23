# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigiThinkit Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from shipment_management.config.app_config import SupportedProviderList

import logging
import binascii
import datetime
import sys
import os

from frappe.utils.password import get_decrypted_password
from frappe import _

import frappe
from frappe.utils import get_site_name, get_site_path, get_site_base_path, get_path, cstr
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

from frappe.utils.file_manager import *

from shipment_management.provider_fedex import FedexProvider
from shipment_management.shipment import ShipmentNoteOperationalStatus, check_permission
from shipment_management.email_controller import send_email_status_update, TEMPLATE_PickedUP
from shipment_management.comment_controller import CommentController


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
			FedexProvider.create_shipment(self)
			frappe.db.set(self, 'shipment_note_status', ShipmentNoteOperationalStatus.InProgress)
			frappe.db.set(self, 'fedex_status', ShipmentNoteOperationalStatus.InProgress)
			#send_email_status_update(self.name, TEMPLATE_PickedUP)
