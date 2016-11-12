# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from hooks import app_email

import logging
import sys
import json
from functools import wraps

from fedex_provider import FedexProvider

fedex_track_service = frappe.get_module("fedex.services.track_service")
rate_service = frappe.get_module("fedex.services.rate_service")
fedex_config = frappe.get_module("fedex.config")
conversion = frappe.get_module("fedex.tools.conversion")
availability_commitment_service = frappe.get_module("fedex.services.availability_commitment_service")

subject_to_json = conversion.sobject_to_json
FedexTrackRequest = fedex_track_service.FedexTrackRequest
FedexConfig = fedex_config.FedexConfig
FedexRateServiceRequest = rate_service.FedexRateServiceRequest
FedexAvailabilityCommitmentRequest = availability_commitment_service.FedexAvailabilityCommitmentRequest


def make_new_shipment_note_from_delivery_note(source_name, target_doc=None):
	doclist = get_mapped_doc("Delivery Note", source_name, {
		"Delivery Note": {
			"doctype": "DTI Shipment Note",
			"field_map": {
				"name": "delivery_note",
			}
		}
	}, target_doc)

	return doclist


def check_permission():
	def innerfn(fn):
		if not frappe.has_permission("DTI Shipment Note", "read"):
			frappe.throw(_("Permission denied"), frappe.PermissionError)
		return fn
	return innerfn


@check_permission()
@frappe.whitelist()
def get_carriers_list():
	return ["Fedex"]


@check_permission()
@frappe.whitelist()
def get_company_email(delivery_note_company):
	return frappe.db.sql('''SELECT email, name from tabCompany WHERE name="%s"''' % delivery_note_company, as_dict=True)


@check_permission()
@frappe.whitelist()
def get_delivery_items(delivery_note_name):
	resp = frappe.db.sql('''SELECT * from `tabDelivery Note Item` WHERE parent="%s"''' % delivery_note_name, as_dict=True)
	return resp


@check_permission()
@frappe.whitelist()
def send_email_status_update(target_doc, old_status="NEW"):
	frappe.msgprint(_("""Important: Cancel issues action cannot be reverted. Send email....."""))

	message = """Good day!
	Shipment status was changed from {} to {}!
	Thank you!""".format(target_doc.name, target_doc)

	frappe.sendmail(recipients="romanchuk.katerina@gmail.com",
		sender=app_email,
		subject="Status update for shipment [{}]on {}".format(target_doc.name, frappe.local.site),
		message=message,
		delayed=False)


@check_permission()
@frappe.whitelist()
def cancel_shipment(target_doc):
	send_email_status_update(target_doc, old_status="NEW")


@check_permission()
@frappe.whitelist()
def make_fedex_shipment_from_shipment_note(source_name, target_doc=None):
	doclist = get_mapped_doc("DTI Shipment Note", source_name, {
		"DTI Shipment Note": {
			"doctype": "DTI Fedex Shipment",
			"field_map": {
				"name": "shipment_note_link"
			}
		}
	}, target_doc)

	return doclist