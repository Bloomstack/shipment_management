# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import get_doc
from frappe.model.mapper import get_mapped_doc

from comment_controller import CommentController

from config.app_config import FedexTestServerConfiguration, PRIMARY_FEDEX_DOC_NAME, SupportedProviderList, \
	StatusMapFedexAndShipmentNote

from utils import get_state_code, get_country_code

from email_controller import send_email, get_content_picked_up, get_content_fail, get_content_completed

def check_permission(fn):
	def innerfn(*args, **kwargs):
		for role in ["Shipment Management Admin", "Shipment Management User", "Admin", "Administrator"]:
			if str(role) in frappe.get_roles():
				break
			frappe.throw(_("Permission denied for = {}".format(frappe.session.user)), frappe.PermissionError)
		return fn(*args, **kwargs)

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
	Created = "ReadyToPickUp"
	InProgress = "In progress"
	Completed = "Completed"
	Cancelled = "Cancelled"
	Failed = "Failed"


##############################################################################
@frappe.whitelist()
def get_sales_order(delivery_note_name):
	against_sales_order = frappe.db.sql('''SELECT against_sales_order from `tabDelivery Note Item` WHERE parent="%s"''' % delivery_note_name, as_dict=True)
	if against_sales_order:
		return against_sales_order[0]


##############################################################################


@frappe.whitelist()
def get_carriers_list():
	return [SupportedProviderList.Fedex]


##############################################################################


class Contact(object):
	def __init__(self):
		self.PersonName = None
		self.CompanyName = None
		self.PhoneNumber = None
		self.Email_List = []


class Address(object):
	def __init__(self):
		self.StreetLines = []
		self.City = None
		self.StateOrProvinceCode = None
		self.PostalCode = None
		self.Country = None
		self.CountryCode = None


class RequestedShipment(object):
	def __init__(self):
		self.address = Address()
		self.contact = Contact()

	def __str__(self):
		return """
		Contact PersonName            = {0}
		Contact CompanyName           = {1}
		Contact PhoneNumber           = {2}
		Email list                    = {3}
		___________________________________________

		Address StreetLines           = {4}
		Address City                  = {5}
		Address StateOrProvinceCode   = {6}
		Address PostalCode            = {7}
		Address Country               = {8}
		Address CountryCode           = {9} """.format(self.contact.PersonName,
													   self.contact.CompanyName,
													   self.contact.PhoneNumber,
													   self.contact.Email_List,
													   self.address.StreetLines,
													   self.address.City,
													   self.address.StateOrProvinceCode,
													   self.address.PostalCode,
													   self.address.Country,
													   self.address.CountryCode)


def get_shipper(delivery_note_name):
	shipper = RequestedShipment()

	delivery_note = frappe.db.sql('''SELECT * from `tabDelivery Note` WHERE name="%s"''' % delivery_note_name,
								  as_dict=True)

	if delivery_note[0].company:
		shipper.contact.PersonName = delivery_note[0].company
		shipper.contact.CompanyName = delivery_note[0].company

		company = frappe.db.sql('''SELECT *  from tabCompany WHERE name="%s"''' % delivery_note[0].company,
								as_dict=True)

		if company:
			if company[0].phone_no:
				shipper.contact.PhoneNumber = company[0].phone_no

			if company[0].country:
				shipper.address.Country = company[0].country
				shipper.address.CountryCode = get_country_code(shipper.address.Country)

			company_address = frappe.db.sql(
				'''SELECT * from tabAddress WHERE company="%s" AND is_your_company_address=1''' % delivery_note[
					0].company, as_dict=True)

			if company_address:
				if company_address[0].address_line1:
					shipper.address.StreetLines.append(company_address[0].address_line1)

				if company_address[0].address_line2:
					shipper.address.StreetLines.append(company_address[0].address_line2)

				if company_address[0].city:
					shipper.address.City = company_address[0].city

				if company_address[0].pincode:
					shipper.address.PostalCode = company_address[0].pincode

				if company_address[0].state:
					shipper.address.StateOrProvinceCode = get_state_code({"country" : shipper.address.Country,
																				 "state" : company_address[0].state})

	return shipper


def get_recipient(delivery_note_name):
	recipient = RequestedShipment()

	recipient.contact.PersonName = \
	frappe.db.sql('''SELECT customer_name from `tabDelivery Note` WHERE name="%s"''' % delivery_note_name,
				  as_dict=True)[0].customer_name

	recipient.contact.CompanyName = \
	frappe.db.sql('''SELECT * from tabCustomer WHERE name="%s"''' % recipient.contact.PersonName, as_dict=True)[0].name

	shipping_address = frappe.db.sql(
		'''SELECT * from tabAddress WHERE customer_name="%s" AND is_shipping_address=1''' % recipient.contact.PersonName,
		as_dict=True)
	primary_contact = frappe.db.sql(
		'''SELECT * from tabContact WHERE customer="%s" and is_primary_contact=1''' % recipient.contact.PersonName,
		as_dict=True)

	if shipping_address:
		if shipping_address[0].phone:
			recipient.contact.PhoneNumber = shipping_address[0].phone

		if shipping_address[0].email_id:
			recipient.contact.Email_List.append(shipping_address[0].email_id)

		if shipping_address[0].address_line1:
			recipient.address.StreetLines.append(shipping_address[0].address_line1)

		if shipping_address[0].address_line2:
			recipient.address.StreetLines.append(shipping_address[0].address_line2)

		if shipping_address[0].city:
			recipient.address.City = shipping_address[0].city

		if shipping_address[0].pincode:
			recipient.address.PostalCode = shipping_address[0].pincode

		if shipping_address[0].country:
			recipient.address.Country = shipping_address[0].country
			recipient.address.CountryCode = get_country_code(recipient.address.Country)
		
		if shipping_address[0].state:
			recipient.address.StateOrProvinceCode = get_state_code({"country" : recipient.address.Country,
																		   "state" : shipping_address[0].state})

	if primary_contact:
		if not recipient.contact.PhoneNumber:
			recipient.contact.PersonName = "{} {}".format(primary_contact[0].first_name, primary_contact[0].last_name)
			recipient.contact.PhoneNumber = primary_contact[0].phone

	if shipping_address:
		if primary_contact[0].email_id and (primary_contact[0].email_id != shipping_address[0].email_id):
			recipient.contact.Email_List.append(primary_contact[0].email_id)

	return recipient


@frappe.whitelist()
def get_recipient_details(delivery_note_name):
	recipient = get_recipient(delivery_note_name)
	return {"recipient_contact_person_name": recipient.contact.PersonName or "",
			"recipient_company_name": recipient.contact.CompanyName or "",
			"recipient_contact_phone_number": recipient.contact.PhoneNumber or "",
			"recipient_address_street_lines": " ".join(recipient.address.StreetLines),
			"recipient_address_city": recipient.address.City or "",
			"recipient_address_state_or_province_code": recipient.address.StateOrProvinceCode or "",
			"recipient_address_country_code": recipient.address.CountryCode or "",
			"recipient_address_postal_code": recipient.address.PostalCode or "",
			"contact_email": ", ".join(recipient.contact.Email_List)}


@frappe.whitelist()
def get_shipper_details(delivery_note_name):
	shipper = get_shipper(delivery_note_name)
	return {"shipper_contact_person_name": shipper.contact.PersonName or "",
			"shipper_company_name": shipper.contact.CompanyName or "",
			"shipper_contact_phone_number": shipper.contact.PhoneNumber or "",
			"shipper_address_street_lines": " ".join(shipper.address.StreetLines) or "",
			"shipper_address_city": shipper.address.City or "",
			"shipper_address_state_or_province_code": shipper.address.StateOrProvinceCode or "",
			"shipper_address_country_code": shipper.address.CountryCode or "",
			"shipper_address_postal_code": shipper.address.PostalCode or ""}


##############################################################################


@frappe.whitelist()
def get_delivery_items(delivery_note_name):
	return frappe.db.sql('''SELECT * from `tabDelivery Note Item` WHERE parent="%s"''' % delivery_note_name,
						 as_dict=True)


##############################################################################
##############################################################################
##############################################################################

def write_to_log(message):
	"""
	/frappe-bench/logs/frappe.log
	"""
	frappe.logger().info('[SHIPMENT APP] :: ' + message)


@frappe.whitelist()
def shipment_status_update_controller():
	"""
	Shipment Management Status Controller Job
	"""

	all_ships = frappe.db.sql(
			'''SELECT * from `tabDTI Shipment Note` WHERE shipment_note_status="%s"''' % ShipmentNoteOperationalStatus.InProgress,
			as_dict=True)

	completed = [i.status_code for i in StatusMapFedexAndShipmentNote.Completed]
	failed = [i.status_code for i in StatusMapFedexAndShipmentNote.Failed]

	write_to_log('Ship in progress:' + " ".join([ship.tracking_number for ship in all_ships]))

	from provider_fedex import get_fedex_shipment_status
	for ship in all_ships:
		latest_status = get_fedex_shipment_status(ship.tracking_number)

		if latest_status != ship.fedex_status:

			CommentController.add_comment(doc_type="DTI Shipment Note",
										  source_name= ship.name,
										  comment_type=CommentController.Comment,
										  comment_message="Status updated to [%s]" % latest_status)

			shipment_note = get_doc("DTI Shipment Note", ship.name)

			current_status = shipment_note.tracking_number
			frappe.db.set(shipment_note, 'fedex_status', latest_status)

			write_to_log("[{0}] - Tracking number [{1}] updated from {2} to {3}".format(shipment_note.name,
																						shipment_note.tracking_number,
																						current_status,
																						latest_status))

			if latest_status == 'PU':

				frappe.db.set(shipment_note, 'shipment_note_status', ShipmentNoteOperationalStatus.InProgress)

				send_email(message=get_content_picked_up(shipment_note),
						   subject="Shipment to %s [%s] - Picked UP" % (shipment_note.recipient_company_name,
																		shipment_note.name),
						   recipient_list=shipment_note.contact_email.split(","))

			elif latest_status in completed:

				frappe.db.set(shipment_note, 'shipment_note_status', ShipmentNoteOperationalStatus.Completed)

				send_email(message=get_content_completed(shipment_note),
						   subject="Shipment to %s [%s] - Completed" % (shipment_note.recipient_company_name,
																		shipment_note.name),
						   recipient_list=shipment_note.contact_email.split(","))

			elif latest_status in failed:
				frappe.db.set(shipment_note, 'shipment_note_status', ShipmentNoteOperationalStatus.Failed)

				send_email(message=get_content_fail(shipment_note),
						   subject="Shipment to %s [%s] - Failed" % (shipment_note.recipient_company_name,
																	 shipment_note.name),
						   recipient_list=shipment_note.contact_email.split(","))


##############################################################################
##############################################################################
##############################################################################

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

	recipient = get_recipient(source_name)
	shipper = get_shipper(source_name)

	items = get_delivery_items(source_name)

	doclist.update({"recipient_contact_person_name": recipient.contact.PersonName or "",
			"recipient_company_name": recipient.contact.CompanyName or "",
			"recipient_contact_phone_number": recipient.contact.PhoneNumber or "",
			"recipient_address_street_lines": " ".join(recipient.address.StreetLines),
			"recipient_address_city": recipient.address.City or "",
			"recipient_address_state_or_province_code": recipient.address.StateOrProvinceCode or "",
			"recipient_address_country_code": recipient.address.CountryCode or "",
			"recipient_address_postal_code": recipient.address.PostalCode or "",
			"contact_email": ", ".join(recipient.contact.Email_List),
	 		"shipper_contact_person_name": shipper.contact.PersonName or "",
			"shipper_company_name": shipper.contact.CompanyName or "",
			"shipper_contact_phone_number": shipper.contact.PhoneNumber or "",
			"shipper_address_street_lines": " ".join(shipper.address.StreetLines) or "",
			"shipper_address_city": shipper.address.City or "",
			"shipper_address_state_or_province_code": shipper.address.StateOrProvinceCode or "",
			"shipper_address_country_code": shipper.address.CountryCode or "",
			"shipper_address_postal_code": shipper.address.PostalCode or "",
			"delivery_items": items,
	})

	return doclist
