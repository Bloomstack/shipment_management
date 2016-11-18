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

from functools import wraps
from provider_fedex import FedexProvider

from app_config import FedexTestServerConfiguration, PRIMARY_FEDEX_DOC_NAME, SupportedDocTypes, SupportedProviderList
from comment_controller import CommentController


def check_permission():
	def innerfn(fn):
		# TODO - Fix during permission pass
		# if not frappe.has_permission("DTI Shipment Note", "read"):
		# 	frappe.throw(_("Permission denied"), frappe.PermissionError)
		return fn
	return innerfn


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
	FedexConfig.use_test_server = FedexTestServerConfiguration.use_test_server

	FedexConfig.submit()


class ShipmentNoteOperationalStatus(object):
	InProgress = "In progress"
	Completed = "Completed"
	Returned = "Returned"
	Cancelled = "Cancelled"
	Failed = "Failed"


# --------------------------------------------------------------
# Mapper

@check_permission()
@frappe.whitelist()
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

# --------------------------------------------------------------


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
	return frappe.db.sql('''SELECT * from `tabDelivery Note Item` WHERE parent="%s"''' % delivery_note_name, as_dict=True)


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
