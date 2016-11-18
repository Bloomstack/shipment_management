# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import logging
import sys
import json
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from hooks import app_email
from frappe.utils.password import encrypt
from functools import wraps
from provider_fedex import FedexProvider

from app_config import FedexTestServerConfiguration, PRIMARY_FEDEX_DOC_NAME, SupportedDocTypes, SupportedProviderList


def after_install():
	"""
	Creation Test Server Configuration for debug and testing during Application Development
	"""

	FedexConfig = frappe.new_doc(SupportedDocTypes.FedexConfig)

	FedexConfig.fedex_config_name = PRIMARY_FEDEX_DOC_NAME
	FedexConfig.fedex_key = FedexTestServerConfiguration.key
	FedexConfig.password = FedexTestServerConfiguration.password
	FedexConfig.account_number = FedexTestServerConfiguration.account_number
	FedexConfig.meter_number = FedexTestServerConfiguration.meter_number
	FedexConfig.freight_account_number = FedexTestServerConfiguration.freight_account_number
	FedexConfig.use_test_server = str(FedexTestServerConfiguration.use_test_server)

	FedexConfig.submit()



##############################################################################

# class DocTypeStatus(object):
# 	Open = 0
# 	Submitted = 1
# 	Cancelled = 2
#
#
# class DeliveryNoteOperationalStatus(object):
# 	ToBill = "To Bill"
# 	Completed = "Completed"
# 	Cancelled = "Cancelled"
# 	Closed = "Closed"


class ShipmentNoteOperationalStatus(object):
	InProgress = "In progress"
	Completed = "Completed"
	Returned = "Returned"
	Cancelled = "Cancelled"
	Failed = "Failed"


class FedexStatusCode(object):
	def __init__(self, status_code, definition):
		self.status_code = status_code
		self.definition = definition


class ShipmentNoteWithFedexStatusMap(object):
	"""
	ALL STATUSES:
	AA - At Airport
	PL - Plane Landed
	AD - At Delivery
	PM - In Progress
	AF - At FedEx Facility
	PU - Picked Up
	AP - At Pickup
	PX - Picked up (see Details)
	AR - Arrived at
	RR - CDO Requested
	AX - At USPS facility
	RM - CDO Modified
	CA - Shipment Canceled
	RC - CDO Cancelled
	CH - Location Changed
	RS - Return to Shipper
	DD - Delivery Delay
	DE - Delivery Exception
	DL - Delivered
	DP - Departed FedEx Location
	SE - Shipment Exception
	DS - Vehicle dispatched
	SF - At Sort Facility
	DY - Delay
	SP - Split status - multiple statuses
	EA - Enroute to Airport delay
	TR - Transfer
	"""
	Completed = [FedexStatusCode("DL", "Delivered")]

	Canceled = [FedexStatusCode("CA", "Shipment Canceled"),
				FedexStatusCode("DE", "Delivery Exception"),
				FedexStatusCode("SE", "Shipment Exception")]

	Return = [FedexStatusCode("RS", "Return to Shipper")]

# def get_related_shipment_note():
# 	shipment_note = None
# 	return shipment_note
#
#
# def get_related_fedex_shipment():
# 	fedex_shipment = None
# 	return fedex_shipment
#
#
# def get_related_shipment_package():
# 	shipment_package = None
# 	return shipment_package
#
#
# def _close_delivery_note(shipment_note=None, fedex_shipment=None, shipment_package=None):
# 	if shipment_note:
# 		shipment_note.status = DocTypeStatus.Cancelled
# 		shipment_note.shipment_status = ShipmentNoteOperationalStatus.Cancelled
#
# 		shipment_note.save()
#
# 	if fedex_shipment:
# 		fedex_shipment.status = DocTypeStatus.Cancelled
# 		fedex_shipment.shipment_status = FedexOperationalStatus.Canceled
#
# 		fedex_shipment.save()
#
# 	if shipment_package:
# 		shipment_package.status = DocTypeStatus.Cancelled
#
# 		shipment_package.save()
#
#
# def _close_shipment_note(fedex_shipment=None, shipment_package=None):
#
# 	if fedex_shipment:
# 		fedex_shipment.status = DocTypeStatus.Cancelled
# 		fedex_shipment.shipment_status = FedexOperationalStatus.Canceled
#
# 		fedex_shipment.save()
#
# 	if shipment_package:
# 		shipment_package.status = DocTypeStatus.Cancelled
#
# 		shipment_package.save()
#
#
# def delivery_note_status_sync(target_doc=None, status=None):
# 	shipment_note = get_related_shipment_note()
# 	fedex_shipment = get_related_fedex_shipment()
# 	shipment_package = get_related_shipment_package()
#
# 	if status == DeliveryNoteOperationalStatus.Completed:
# 		_close_delivery_note(shipment_note=shipment_note,
# 							 fedex_shipment=fedex_shipment,
# 							 shipment_package = shipment_package)
#
# 	elif status == DeliveryNoteOperationalStatus.Cancelled:
# 		_close_delivery_note(shipment_note=shipment_note,
# 							 fedex_shipment=fedex_shipment,
# 							 shipment_package = shipment_package)
#
# 	elif status == DeliveryNoteOperationalStatus.Closed:
# 		_close_delivery_note(shipment_note=shipment_note,
# 							 fedex_shipment=fedex_shipment,
# 							 shipment_package = shipment_package)
#
# 	else:
# 		raise Exception("Can't mach Delivery Note status = %s (%s)", (target_doc, status))
#
#
# def shipment_note_status_sync(target_doc, status):
# 	"""
# 	Our own Shipment Note statuses
# 	- In progress – the shipment and its parcels handed to a Delivery Service to pick up and do delivery
# 	- Completed – successfully delivered to a customer
# 	- Returned – the shipment returned to Sender by Customer
# 	- Cancelled – the delivery of the shipment cancelled by Customer
# 	- Failed – there is an error or physical failure delivering
# 	"""
#
# 	fedex_shipment = get_related_fedex_shipment()
# 	shipment_package = get_related_shipment_package()
#
# 	if status == ShipmentNoteOperationalStatus.Failed:
# 		_close_shipment_note(fedex_shipment=fedex_shipment,
# 							 shipment_package = shipment_package)
#
# 	elif status == ShipmentNoteOperationalStatus.Cancelled:
# 		_close_shipment_note(fedex_shipment=fedex_shipment,
# 							 shipment_package = shipment_package)
#
# 	elif status == ShipmentNoteOperationalStatus.Returned:
# 		_close_shipment_note(fedex_shipment=fedex_shipment,
# 							 shipment_package = shipment_package)
#
# 	elif status == DeliveryNoteOperationalStatus.Completed:
# 		if fedex_shipment:
# 			fedex_shipment.status = DocTypeStatus.Submitted
# 			fedex_shipment.shipment_status = FedexOperationalStatus.Canceled
#
# 			fedex_shipment.save()
#
# 		if shipment_package:
# 			shipment_package.status = DocTypeStatus.Cancelled
#
# 			shipment_package.save()
#
#
# def fedex_shipment_status_sync(target_doc, status):
# 	shipment_note = get_related_shipment_note()
# 	shipment_package = get_related_shipment_package()
#
# 	if status in FedexOperationalStatus.Completed:
# 		if shipment_note:
# 			shipment_note.status = DocTypeStatus.Submitted
# 			shipment_note.shipment_status = ShipmentNoteOperationalStatus.Completed
#
# 		if shipment_package:
# 			shipment_note.status = DocTypeStatus.Submitted
#
# 	if status in FedexOperationalStatus.Canceled:
# 		if shipment_note:
# 			shipment_note.status = DocTypeStatus.Cancelled
# 			shipment_note.shipment_status = ShipmentNoteOperationalStatus.Cancelled
#
# 		if shipment_package:
# 			shipment_note.status = DocTypeStatus.Submitted


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
		# if not frappe.has_permission("DTI Shipment Note", "read"):
		# 	frappe.throw(_("Permission denied"), frappe.PermissionError)
		return fn
	return innerfn


@check_permission()
@frappe.whitelist()
def get_carriers_list():
	return [SupportedProviderList.Fedex]


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
def cancel_shipment(source_name):
	shipment = frappe.get_doc('DTI Shipment Note', source_name)

	frappe.db.set(shipment, "shipment_note_status", ShipmentNoteOperationalStatus.Cancelled)
	CommentController.add_comment('DTI Shipment Note',
								  source_name,
								  CommentController.Comment,
								  "Shipment has been cancelled.")

	if shipment.shipment_provider == 'FEDEX':

		fedex = frappe.get_doc('DTI Fedex Shipment', shipment.fedex_name)
		fedex.delete_shipment()


class CommentController(object):
	Email = 'Email'
	Chat = 'Chat'
	Phone = 'Phone'
	SMS = 'SMS'
	Created = 'Created'
	Submitted = 'Submitted'
	Cancelled = 'Cancelled'
	Assigned = 'Assigned'
	Assignment = 'Assignment'
	Completed = 'Completed'
	Comment = 'Comment'
	Workflow = 'Workflow'
	Label = 'Label'
	Attachment = 'Attachment'
	Removed = 'Removed'

	@staticmethod
	def add_comment(doc_type, source_name, comment_type, comment_message):
		shipment = frappe.get_doc(doc_type, source_name)
		shipment.add_comment(comment_type, _(comment_message))


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