# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import json
import binascii
import datetime

import frappe
from frappe.utils.password import get_decrypted_password
from frappe import _
from frappe.utils.file_manager import *


from config.app_config import PRIMARY_FEDEX_DOC_NAME

fedex_track_service = frappe.get_module("fedex.services.track_service")
rate_service = frappe.get_module("fedex.services.rate_service")
fedex_config = frappe.get_module("fedex.config")
conversion = frappe.get_module("fedex.tools.conversion")
availability_commitment_service = frappe.get_module("fedex.services.availability_commitment_service")
ship_service = frappe.get_module("fedex.services.ship_service")

# TODO fix import
from fedex.services.ship_service import FedexDeleteShipmentRequest
from fedex.base_service import FedexError

subject_to_json = conversion.sobject_to_json
FedexTrackRequest = fedex_track_service.FedexTrackRequest
FedexConfig = fedex_config.FedexConfig
FedexRateServiceRequest = rate_service.FedexRateServiceRequest
FedexAvailabilityCommitmentRequest = availability_commitment_service.FedexAvailabilityCommitmentRequest
FedexProcessShipmentRequest = ship_service.FedexProcessShipmentRequest

CUSTOMER_TRANSACTION_ID = "*** TrackService Request v10 using Python ***"

# http://help.deposco.com/w/index.php/FedEx_Error_Handling

################################################################################
################################################################################
################################################################################


def _get_configuration():
	fedex_server_doc_type = frappe.db.sql(
		'''SELECT * from `tabDTI Fedex Configuration` WHERE name = "%s"''' % PRIMARY_FEDEX_DOC_NAME, as_dict=True)

	if not fedex_server_doc_type:
		frappe.throw(_("Please create Fedex Configuration: %s" % PRIMARY_FEDEX_DOC_NAME))

	return fedex_server_doc_type[0]


def get_fedex_server_info():
	fedex_server_doc_type = _get_configuration()

	config_message = """<b>FEDEX CONFIG:</b>
	<br><b>key </b>                   : '{key}'
	<br><b>password </b>              : '{password}'
	<br><b>account_number </b>        : '{account_number}'
	<br><b>meter_number </b>          : '{meter_number}'
	<br><b>freight_account_number</b> : '{freight_account_number}'
	<br><b>use_test_server </b>       : '{use_test_server}'""".format(
		key=fedex_server_doc_type['fedex_key'],
		password=fedex_server_doc_type['password'],
		account_number=fedex_server_doc_type['account_number'],
		meter_number=fedex_server_doc_type['meter_number'],
		freight_account_number=fedex_server_doc_type['freight_account_number'],
		use_test_server=fedex_server_doc_type['use_test_server'])

	return config_message


def get_fedex_config():
	fedex_server_doc_type = _get_configuration()

	if fedex_server_doc_type['use_test_server']:
		_test_server = True
	else:
		_test_server = False

	return FedexConfig(key=fedex_server_doc_type['fedex_key'],
					   password=get_decrypted_password('DTI Fedex Configuration',
													   PRIMARY_FEDEX_DOC_NAME,
													   fieldname='password',
													   raise_exception=True),
					   account_number=fedex_server_doc_type['account_number'],
					   meter_number=fedex_server_doc_type['meter_number'],
					   freight_account_number=fedex_server_doc_type['freight_account_number'],
					   use_test_server=_test_server)


CONFIG_OBJ = get_fedex_config()


################################################################################
################################################################################
################################################################################

# API:

@frappe.whitelist()
def get_package_rate(DropoffType=None,
					 ServiceType=None,
					 PackagingType=None,
					 ShipperStateOrProvinceCode=None,
					 ShipperPostalCode=None,
					 ShipperCountryCode=None,
					 RecipientStateOrProvinceCode=None,
					 RecipientPostalCode=None,
					 RecipientCountryCode=None,
					 EdtRequestType=None,
					 PaymentType=None,
					 package_list=None):
	"""
	Define package rate
	:param DropoffType:
	:param ServiceType:
	:param PackagingType:
	:param ShipperStateOrProvinceCode:
	:param ShipperPostalCode:
	:param ShipperCountryCode:
	:param RecipientStateOrProvinceCode:
	:param RecipientPostalCode:
	:param RecipientCountryCode:
	:param EdtRequestType:
	:param PaymentType:
	:param package_list:
	:return: TotalNetChargeWithDutiesAndTaxes
	"""

	rate = FedexRateServiceRequest(CONFIG_OBJ)

	rate.RequestedShipment.DropoffType = DropoffType
	rate.RequestedShipment.ServiceType = ServiceType
	rate.RequestedShipment.PackagingType = PackagingType

	rate.RequestedShipment.Shipper.Address.StateOrProvinceCode = ShipperStateOrProvinceCode
	rate.RequestedShipment.Shipper.Address.PostalCode = ShipperPostalCode
	rate.RequestedShipment.Shipper.Address.CountryCode = ShipperCountryCode

	rate.RequestedShipment.Recipient.Address.StateOrProvinceCode = RecipientStateOrProvinceCode
	rate.RequestedShipment.Recipient.Address.PostalCode = RecipientPostalCode
	rate.RequestedShipment.Recipient.Address.CountryCode = RecipientCountryCode
	rate.RequestedShipment.EdtRequestType = EdtRequestType
	rate.RequestedShipment.ShippingChargesPayment.PaymentType = PaymentType

	for package in package_list:
		package1_weight = rate.create_wsdl_object_of_type('Weight')

		package1_weight.Value = package["weight_value"]
		package1_weight.Units = package["weight_units"]
		package1 = rate.create_wsdl_object_of_type('RequestedPackageLineItem')
		package1.Weight = package1_weight

		package1.PhysicalPackaging = package["physical_packaging"]
		package1.GroupPackageCount = package["group_package_count"]

		package_insure = rate.create_wsdl_object_of_type('Money')
		package_insure.Currency = "USD"
		package_insure.Amount = package["insured_amount"]

		rate.add_package(package1)

	rate.send_request()

	response_json = subject_to_json(rate.response)
	data = json.loads(response_json)

	return data['RateReplyDetails'][0]['RatedShipmentDetails'][0]["ShipmentRateDetail"][
		'TotalNetChargeWithDutiesAndTaxes']


@frappe.whitelist()
def estimate_delivery_time(OriginPostalCode=None,
						   OriginCountryCode=None,
						   DestinationPostalCode=None,
						   DestinationCountryCode=None):
	"""
	Projected package delivery date based on ship date, service, and destination
	:param OriginPostalCode:
	:param OriginCountryCode:
	:param DestinationPostalCode:
	:param DestinationCountryCode:
	:return: ShipDate
	"""

	avc_request = FedexAvailabilityCommitmentRequest(CONFIG_OBJ)

	avc_request.Origin.PostalCode = OriginPostalCode
	avc_request.Origin.CountryCode = OriginCountryCode

	avc_request.Destination.PostalCode = DestinationPostalCode
	avc_request.Destination.CountryCode = DestinationCountryCode

	return avc_request.ShipDate


################################################################################
################################################################################
################################################################################

# SHIPMENT


def _create_fedex_package(shipment,
						  sequence_number=None,
						  package_weight_value=0,
						  package_weight_units=None,
						  physical_packaging=None,
						  insure_currency=None,
						  insured_amount=None):
	package_weight = shipment.create_wsdl_object_of_type('Weight')
	package_weight.Value = package_weight_value
	package_weight.Units = package_weight_units

	package = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')

	package.PhysicalPackaging = physical_packaging
	package.Weight = package_weight

	if insure_currency and insured_amount:
		package_insure = shipment.create_wsdl_object_of_type('Money')
		package_insure.Currency = insure_currency
		package_insure.Amount = insured_amount
		package.InsuredValue = package_insure

	package.SpecialServicesRequested.SpecialServiceTypes = 'SIGNATURE_OPTION'
	package.SpecialServicesRequested.SignatureOptionDetail.OptionType = 'SERVICE_DEFAULT'
	package.SequenceNumber = sequence_number
	return package


def create_fedex_shipment(source_doc):
	BOXES = source_doc.get_all_children("DTI Shipment Package")

	if len(BOXES) > 9:
		frappe.throw(_("Max amount of packages is 10"))

	if not BOXES:
		frappe.throw(_("Please create shipment box packages!"))

	GENERATE_IMAGE_TYPE = 'PNG'

	shipment = FedexProcessShipmentRequest(CONFIG_OBJ, customer_transaction_id=CUSTOMER_TRANSACTION_ID)

	shipment.RequestedShipment.DropoffType = source_doc.drop_off_type
	shipment.RequestedShipment.ServiceType = source_doc.service_type

	shipment.RequestedShipment.PackagingType = source_doc.packaging_type

	# Shipper contact info.
	shipment.RequestedShipment.Shipper.Contact.PersonName = source_doc.shipper_contact_person_name
	shipment.RequestedShipment.Shipper.Contact.CompanyName = source_doc.shipper_company_name
	shipment.RequestedShipment.Shipper.Contact.PhoneNumber = source_doc.shipper_contact_phone_number

	# Shipper address.
	shipment.RequestedShipment.Shipper.Address.StreetLines = [source_doc.shipper_address_street_lines]
	shipment.RequestedShipment.Shipper.Address.City = source_doc.shipper_address_city
	shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = source_doc.shipper_address_state_or_province_code
	shipment.RequestedShipment.Shipper.Address.PostalCode = source_doc.shipper_address_postal_code
	shipment.RequestedShipment.Shipper.Address.CountryCode = source_doc.shipper_address_country_code

	if source_doc.shipper_address_residential:
		shipment.RequestedShipment.Shipper.Address.Residential = True
	else:
		shipment.RequestedShipment.Shipper.Address.Residential = False

	# Recipient contact info.
	shipment.RequestedShipment.Recipient.Contact.PersonName = source_doc.recipient_contact_person_name
	shipment.RequestedShipment.Recipient.Contact.CompanyName = source_doc.recipient_company_name
	shipment.RequestedShipment.Recipient.Contact.PhoneNumber = source_doc.recipient_contact_phone_number

	# Recipient addressStateOrProvinceCode
	shipment.RequestedShipment.Recipient.Address.StreetLines = [source_doc.recipient_address_street_lines]
	shipment.RequestedShipment.Recipient.Address.City = source_doc.recipient_address_city
	shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = source_doc.recipient_address_state_or_province_code
	shipment.RequestedShipment.Recipient.Address.PostalCode = source_doc.recipient_address_postal_code
	shipment.RequestedShipment.Recipient.Address.CountryCode = source_doc.recipient_address_country_code

	if source_doc.recipient_address_residential:
		shipment.RequestedShipment.Recipient.Address.Residential = True
	else:
		shipment.RequestedShipment.Recipient.Address.Residential = False

	shipment.RequestedShipment.EdtRequestType = 'NONE'

	# Senders account information
	shipment.RequestedShipment.ShippingChargesPayment.Payor.ResponsibleParty.AccountNumber = CONFIG_OBJ.account_number
	shipment.RequestedShipment.ShippingChargesPayment.PaymentType = source_doc.payment_type
	shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'
	shipment.RequestedShipment.LabelSpecification.ImageType = GENERATE_IMAGE_TYPE
	shipment.RequestedShipment.LabelSpecification.LabelStockType = source_doc.label_stock_type
	shipment.RequestedShipment.ShipTimestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
	shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = 'TOP_EDGE_OF_TEXT_FIRST'

	if hasattr(shipment.RequestedShipment.LabelSpecification, 'LabelOrder'):
		del shipment.RequestedShipment.LabelSpecification.LabelOrder  # Delete, not using.

	# ===================================================

	# First/Master Package

	package1 = _create_fedex_package(shipment=shipment,
									 sequence_number=1,
									 package_weight_value=BOXES[0].weight_value,
									 package_weight_units=BOXES[0].weight_units,
									 physical_packaging=BOXES[0].physical_packaging,
									 insure_currency=BOXES[0].currency,
									 insured_amount=BOXES[0].insured_amount)

	shipment.RequestedShipment.RequestedPackageLineItems = [package1]

	shipment.RequestedShipment.PackageCount = len(BOXES)

	try:
		shipment.send_request()
	except Exception as error:

		# __message = """{0}<hr>
		# Shipper.Address.StreetLines = {1} <br>
		# Shipper.Address.City        = {2} <br>
		# Shipper.Address.StateOrProvinceCode = {3} <br>
		# Shipper.Address.PostalCode  = {4} <br>
		# Shipper.Address.CountryCode = {5} <br>
		# <hr>
		# Recipient.Address.StreetLines = {6} <br>
		# Recipient.Address.City        = {7} <br>
		# Recipient.Address.StateOrProvinceCode = {8} <br>
		# Recipient.Address.PostalCode = {9} <br>
		# Recipient.Address.CountryCode = {10}""".format(error,
		# shipment.RequestedShipment.Shipper.Address.StreetLines,
		# shipment.RequestedShipment.Shipper.Address.City,
		# shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode,
		# shipment.RequestedShipment.Shipper.Address.PostalCode,
		# shipment.RequestedShipment.Shipper.Address.CountryCode,
		# shipment.RequestedShipment.Recipient.Address.StreetLines,
		# shipment.RequestedShipment.Recipient.Address.City,
		# shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode,
		# shipment.RequestedShipment.Recipient.Address.PostalCode,
		# shipment.RequestedShipment.Recipient.Address.CountryCode)

		frappe.throw(_(error))

	master_label = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0]

	master_tracking_number = master_label.TrackingIds[0].TrackingNumber
	master_tracking_id_type = master_label.TrackingIds[0].TrackingIdType
	master_tracking_form_id = master_label.TrackingIds[0].FormId

	ascii_label_data = master_label.Label.Parts[0].Image
	label_binary_data = binascii.a2b_base64(ascii_label_data)

	file_name = "label_%s.%s" % (master_tracking_number, GENERATE_IMAGE_TYPE.lower())

	saved_file = save_file(file_name, label_binary_data, source_doc.doctype, source_doc.name, is_private=1)

	frappe.db.set(source_doc, 'tracking_number', master_tracking_number)
	frappe.db.set(source_doc, 'label_1', saved_file.file_url)

	# ################################################

	# Track additional package in shipment :

	labels = []

	frappe.db.set(BOXES[0], 'tracking_number', master_tracking_number)

	############################################################

	rate_box_list = []

	master_box_dict = {'weight_value': BOXES[0].weight_value,
					   'weight_units': BOXES[0].weight_units,
					   'physical_packaging': BOXES[0].physical_packaging,
					   'group_package_count': 1,
					   'insured_amount': BOXES[0].insured_amount}

	rate_box_list.append(master_box_dict)

	############################################################

	for i, child_package in enumerate(BOXES[1:]):

		i += 1

		package = _create_fedex_package(shipment=shipment,
										sequence_number=i + 1,
										package_weight_value=child_package.weight_value,
										package_weight_units=child_package.weight_units,
										insure_currency=child_package.currency,
										physical_packaging=child_package.physical_packaging,
										insured_amount=child_package.insured_amount)

		shipment.RequestedShipment.RequestedPackageLineItems = [package]
		shipment.RequestedShipment.MasterTrackingId.TrackingNumber = master_tracking_number
		shipment.RequestedShipment.MasterTrackingId.TrackingIdType = master_tracking_id_type
		shipment.RequestedShipment.MasterTrackingId.FormId = master_tracking_form_id

		#########################

		child_box_dict = {'weight_value': child_package.weight_value,
						  'weight_units': child_package.weight_units,
						  'physical_packaging': child_package.physical_packaging,
						  'group_package_count': i + 1,
						  'insured_amount': child_package.insured_amount}

		rate_box_list.append(child_box_dict)

		#########################

		try:
			shipment.send_request()
		except Exception as error:
			frappe.throw(_("Error in box # %s - %s" % (i, error)))

		for label in shipment.response.CompletedShipmentDetail.CompletedPackageDetails:
			child_tracking_number = label.TrackingIds[0].TrackingNumber
			ascii_label_data = label.Label.Parts[0].Image
			label_binary_data = binascii.a2b_base64(ascii_label_data)

			frappe.db.set(child_package, 'tracking_number', child_tracking_number)

			file_name = "label_%s_%s.%s" % (
				master_tracking_number, child_tracking_number, GENERATE_IMAGE_TYPE.lower())

			saved_file = save_file(file_name, label_binary_data, source_doc.doctype, source_doc.name, is_private=1)

			labels.append(saved_file.file_url)

	for i, path in enumerate(labels):
		i += 1
		frappe.db.set(source_doc, 'label_' + str(i + 1), path)

	# ################################################

	try:
		delivery_time = estimate_delivery_time(OriginPostalCode=source_doc.shipper_address_postal_code,
											   OriginCountryCode=source_doc.shipper_address_country_code,
											   DestinationPostalCode=source_doc.recipient_address_postal_code,
											   DestinationCountryCode=source_doc.recipient_address_country_code)
		frappe.db.set(source_doc, 'delivery_time', delivery_time)
	except Exception as error:
		frappe.throw(_("Delivery time error - %s" % error))

	# ################################################

	try:
		rate = get_package_rate(DropoffType=source_doc.drop_off_type,
								ServiceType=source_doc.service_type,
								PackagingType=source_doc.packaging_type,
								ShipperStateOrProvinceCode=source_doc.shipper_address_state_or_province_code,
								ShipperPostalCode=source_doc.shipper_address_postal_code,
								ShipperCountryCode=source_doc.shipper_address_country_code,
								RecipientStateOrProvinceCode=source_doc.recipient_address_state_or_province_code,
								RecipientPostalCode=source_doc.recipient_address_postal_code,
								RecipientCountryCode=source_doc.recipient_address_country_code,
								EdtRequestType='NONE',
								PaymentType=source_doc.payment_type,
								package_list=rate_box_list)

		frappe.db.set(source_doc, 'rate', "%s (%s)" % (rate["Amount"], rate["Currency"]))
	except Exception as error:
		frappe.throw(_("Rate error - %s" % error))

	# ################################################

	frappe.msgprint("DONE!", "Tracking number:{}".format(master_tracking_number))


def delete_fedex_shipment(source_doc):

	del_request = FedexDeleteShipmentRequest(CONFIG_OBJ)

	del_request.DeletionControlType = "DELETE_ALL_PACKAGES"

	del_request.TrackingId.TrackingNumber = source_doc.tracking_number

	# What kind of shipment the tracking number used.
	# Docs say this isn't required, but the WSDL won't validate without it.
	# EXPRESS, GROUND, or USPS
	# TODO!!!!!!!!!!!
	# del_request.TrackingId.TrackingIdType = FedexProvider.master_tracking_id_type

	# Fires off the request, sets the 'response' attribute on the object.
	try:
		del_request.send_request()
	except FedexError as error:
		if 'Unable to retrieve record' in str(error):
			frappe.throw(_("WARNING: Unable to delete the shipment with the provided tracking number."))
		else:
			frappe.throw(_("%s" % error))

	frappe.throw(_("%s" % del_request.response))

	print("HighestSeverity: {}".format(del_request.response.HighestSeverity))


################################################################################
################################################################################
################################################################################

# FOR WEB PAGE WITH SHIPMENT TRACKING - shipment_tracking.html

@frappe.whitelist(allow_guest=True)
def get_html_code_status_with_fedex_tracking_number(track_value):
	if not track_value:
		return "Track value can't be empty"

	track = FedexTrackRequest(CONFIG_OBJ, customer_transaction_id=CUSTOMER_TRANSACTION_ID)

	track.SelectionDetails.PackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
	track.SelectionDetails.PackageIdentifier.Value = track_value

	del track.SelectionDetails.OperatingCompany

	try:
		track.send_request()
		html = ""

		for match in track.response.CompletedTrackDetails[0].TrackDetails:
			html += "<b>Tracking #:</b> {}".format(match.TrackingNumber)

			if hasattr(match, 'TrackingNumberUniqueIdentifier'):
				html += "<br><b>UniqueID:</b> {}".format(match.TrackingNumberUniqueIdentifier)

			if hasattr(match, 'Notification'):
				html += "<br>{}".format(match.Notification.Message)

			if hasattr(match, 'StatusDetail.Description'):
				html += "<br>Status Description: {}".format(match.StatusDetail.Description)

			if hasattr(match, 'StatusDetail.AncillaryDetails'):
				html += "<br>Status AncillaryDetails Reason: {}".format(match.StatusDetail.AncillaryDetails[-1].Reason)
				html += "<br>Status AncillaryDetails Description: {}".format(
					match.StatusDetail.AncillaryDetails[-1].ReasonDescription)

			if hasattr(match, 'ServiceCommitMessage'):
				html += "<br><b>{}</b>".format(match.ServiceCommitMessage)

			html += "<br><br>"

		return html

	except Exception as error:
		return """<b>ERROR :</b><br> Fedex invalid configuration error! <br>{0}<br><br>{1} """.format(error.value,
																									  get_fedex_server_info())


