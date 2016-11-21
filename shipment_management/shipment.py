# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from comment_controller import CommentController
from country_code_config import get_country_code, get_country_state_code
from frappe import _
from frappe.model.mapper import get_mapped_doc
from config.app_config import FedexTestServerConfiguration, PRIMARY_FEDEX_DOC_NAME, SupportedProviderList


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

	FedexConfig = frappe.new_doc("DTI Fedex Configuration")

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


##############################################################################
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


##############################################################################


@check_permission()
@frappe.whitelist()
def get_carriers_list():
	return [SupportedProviderList.Fedex]


##############################################################################


class Contact(object):
	def __init__(self):
		self.PersonName = "UNDEFINED"
		self.CompanyName = "UNDEFINED"
		self.PhoneNumber = "UNDEFINED"


class Address(object):
	def __init__(self):
		self.StreetLines = []
		self.City = "UNDEFINED"
		self.StateOrProvinceCode = "UNDEFINED"
		self.PostalCode = "UNDEFINED"
		self.CountryCode = "UNDEFINED"


class RequestedShipment(object):
	def __init__(self):
		self.address = Address()
		self.contact = Contact()

	def __str__(self):
		return """
		Contact PersonName            = {0}
		Contact CompanyName           = {1}
		Contact PhoneNumber           = {2}
		___________________________________________

		Address StreetLines           = {3}
		Address City                  = {4}
		Address StateOrProvinceCode   = {5}
		Address PostalCode            = {6}
		Address CountryCode           = {7} """.format(self.contact.PersonName,
													   self.contact.CompanyName,
													   self.contact.PhoneNumber,
													   self.address.StreetLines,
													   self.address.City,
													   self.address.StateOrProvinceCode,
													   self.address.PostalCode,
													   self.address.CountryCode)


def get_address_templates(address):
	result = frappe.db.get_value("Address Template", {"country": address.get("country")}, ["name", "template"])

	if not result:
		result = frappe.db.get_value("Address Template", {"is_default": 1}, ["name", "template"])

	if not result:
		frappe.throw(_(
			"No default Address Template found. Please create a new one from Setup > Printing and Branding > Address Template."))
	else:
		return result


@frappe.whitelist()
def get_shipping_address(company):
	filters = {"company": company, "is_your_company_address" : 1}
	fieldname = ["name", "address_line1", "address_line2", "city", "state", "country"]

	address_as_dict = frappe.db.get_value("Address", filters=filters, fieldname=fieldname, as_dict=True)

	if address_as_dict:
		name, address_template = get_address_templates(address_as_dict)
		return address_as_dict.get("name"), frappe.render_template(address_template, address_as_dict)


@check_permission()
@frappe.whitelist()
def get_shipper(delivery_note_name):

	print "DELIVERY NOTE: ", delivery_note_name

	delivery_note = frappe.db.sql('''SELECT * from `tabDelivery Note` WHERE name="%s"''' % delivery_note_name, as_dict=True)

	company_response = frappe.db.sql('''SELECT *  from tabCompany WHERE name="%s"''' % delivery_note[0].company, as_dict=True)

	shipper = RequestedShipment()

	if not company_response:
		frappe.throw(_("Company is mandatory for = {}").format(delivery_note.name))

	# ---------------------------------------------

	if company_response[0].company_name:
		shipper.contact.CompanyName = company_response[0].company_name
	else:
		frappe.throw(_("<company_name> is mandatory for = {}").format(delivery_note[0].company))

	if company_response[0].name:
		shipper.contact.PersonName = company_response[0].name
	else:
		frappe.throw(_("<name> is mandatory for = {}").format(delivery_note[0].company))

	if company_response[0].phone_no:
		shipper.contact.PhoneNumber = company_response[0].phone_no
	else:
		frappe.throw(_("<phone_no> is mandatory for = {}").format(delivery_note[0].company))

	# ---------------------------------------------

	address_response = frappe.db.sql(
		'''SELECT company from `tabAddress` WHERE company="%s"''' % delivery_note[0].company, as_dict=True)

	# ----------------------------------------------

	if not address_response:
		frappe.throw(_("Address is mandatory for = {}").format(delivery_note[0].company))

	print "ADDRESS", address_response[0]

	if address_response[0].address_line1:
		shipper.address.StreetLines = [address_response[0].address_line1] + [address_response[0].address_line2]
	else:
		frappe.throw(_("<address_line1> is mandatory for address = {}").format(delivery_note[0].company))

	if address_response[0].city:
		shipper.address.City = address_response[0].city
	else:
		frappe.throw(_("<city> is mandatory for address = {}").format(delivery_note[0].company))

	if address_response[0].pincode:
		shipper.address.PostalCode = address_response[0].pincode
	else:
		frappe.throw(_("<pincode> is mandatory for address = {}").format(delivery_note[0].company))

	if address_response[0].country:
		shipper.address.CountryCode = get_country_code(address_response[0].country)
	else:
		frappe.throw(_("<country> is mandatory for address = {}").format(delivery_note[0].company))

	if address_response[0].state:
		get_country_state_code(address_response[0].country, address_response[0].state)
	else:
		frappe.throw(_("<state> is mandatory for address = {}").format(delivery_note[0].company))

	print "SHIPPER:"
	print "_________________________"
	print shipper

	return shipper


@check_permission()
@frappe.whitelist()
def get_recipient(delivery_note_name):

	print "DELIVERY NOTE: ", delivery_note_name

	recipient = RequestedShipment()

	delivery_note = frappe.db.sql('''SELECT * from `tabDelivery Note` WHERE name="%s"''' % delivery_note_name, as_dict=True)
	company_response = frappe.db.sql('''SELECT *  from tabCompany WHERE name="%s"''' % delivery_note[0].company, as_dict=True)

	recipient.contact.CompanyName = company_response[0].company_name
	recipient.contact.PersonName = delivery_note[0].customer

	if not delivery_note[0].shipping_address_name:
		raise Exception('Delivery Note %s should has shipping address' % delivery_note_name)

	address_response = frappe.db.sql('''SELECT * from `tabAddress` WHERE name="%s"''' % delivery_note[0].shipping_address_name, as_dict=True)

	recipient.contact.PhoneNumber = address_response[0].phone

	recipient.address.StreetLines = [address_response[0].address_line1 + address_response[0].address_line2]
	recipient.address.City = address_response[0].city
	recipient.address.PostalCode = address_response[0].pincode

	if not address_response[0].country:
		raise Exception("Address validation error - Country is absent!")

	if not address_response[0].state:
		raise Exception("Address validation error - State is absent!")

	recipient.address.CountryCode = get_country_code(address_response[0].country)

	recipient.address.StateOrProvinceCode = get_country_state_code(address_response[0].country, address_response[0].state)

	print "RECIPIENT:"
	print "_________________________"
	print recipient

	return recipient


##############################################################################


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
def get_shipment_items(shipment_note_name):
	return frappe.db.sql('''SELECT * from `tabDTI Shipment Note Item` WHERE parent="%s"''' % shipment_note_name, as_dict=True)


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
