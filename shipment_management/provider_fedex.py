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


from config.app_config import PRIMARY_FEDEX_DOC_NAME, ExportComplianceStatement
from shipment import check_permission


# #############################################################################
# #############################################################################
# #############################################################################
# #############################################################################
# #############################################################################

# ########################### FEDEX IMPORT ####################################

# IMPORT FEDEX LIBRARY IS WITH <<frappe.get_module>> BECAUSE OF BUG
# Seems like the sandbox import path is broken on certain modules.
# More details: https://discuss.erpnext.com/t/install-requirements-with-bench-problem-importerror/16558/5

# If import error during installation try reinstall fedex manually:
# bench shell
# pip install fedex

# Make sure fedex and all the library file files are there  ~/frappe-bench/env/lib/python2.7/

fedex_track_service = frappe.get_module("fedex.services.track_service")

# TODO - Fix import after https://github.com/python-fedex-devs/python-fedex/pull/86

from temp_fedex.ship_service import FedexDeleteShipmentRequest, FedexProcessInternationalShipmentRequest, FedexProcessShipmentRequest
from temp_fedex.rate_service import FedexRateServiceRequest, FedexInternationalRateServiceRequest

# #############################################################################

# rate_service = frappe.get_module("fedex.services.rate_service")
# ship_service = frappe.get_module("fedex.services.ship_service")
# FedexDeleteShipmentRequest = ship_service.FedexDeleteShipmentRequest
# FedexProcessShipmentRequest = ship_service.FedexProcessShipmentRequest
# FedexRateServiceRequest = rate_service.FedexRateServiceRequest
fedex_config = frappe.get_module("fedex.config")
conversion = frappe.get_module("fedex.tools.conversion")
availability_commitment_service = frappe.get_module("fedex.services.availability_commitment_service")
base_service = frappe.get_module("fedex.base_service")
FedexError = base_service.FedexError
subject_to_json = conversion.sobject_to_json
FedexTrackRequest = fedex_track_service.FedexTrackRequest
FedexConfig = fedex_config.FedexConfig
FedexAvailabilityCommitmentRequest = availability_commitment_service.FedexAvailabilityCommitmentRequest

# #############################################################################
# #############################################################################
# #############################################################################
# #############################################################################
# #############################################################################


CUSTOMER_TRANSACTION_ID = "*** TrackService Request v10 using Python ***"


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


# #############################################################################
# #############################################################################
# #############################################################################

@check_permission()
@frappe.whitelist()
def estimate_delivery_time(OriginPostalCode=None,
						   OriginCountryCode=None,
						   DestinationPostalCode=None,
						   DestinationCountryCode=None):

	avc_request = FedexAvailabilityCommitmentRequest(CONFIG_OBJ)

	avc_request.Origin.PostalCode = OriginPostalCode
	avc_request.Origin.CountryCode = OriginCountryCode

	avc_request.Destination.PostalCode = DestinationPostalCode
	avc_request.Destination.CountryCode = DestinationCountryCode

	return avc_request.ShipDate


# ###############################################################################
# ###############################################################################
# ###############################################################################

# ################## SHIPMENT PRIMARY WORKFLOW ##################################


def _create_package(shipment,
						  sequence_number=None,
						  package_weight_value=0,
						  package_weight_units=None,
						  physical_packaging=None,
						  insure_currency="USD",
						  insured_amount=None):

	package_weight = shipment.create_wsdl_object_of_type('Weight')
	package_weight.Value = package_weight_value
	package_weight.Units = package_weight_units

	package = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')

	package.PhysicalPackaging = physical_packaging
	package.Weight = package_weight

	if insured_amount:
		package_insure = shipment.create_wsdl_object_of_type('Money')

		package_insure.Currency = insure_currency
		package_insure.Amount = insured_amount

		package.InsuredValue = package_insure

	package.SpecialServicesRequested.SpecialServiceTypes = 'SIGNATURE_OPTION'
	package.SpecialServicesRequested.SignatureOptionDetail.OptionType = 'SERVICE_DEFAULT'
	package.SequenceNumber = sequence_number
	return package

# #############################################################################


def add_export_detail(shipment):
	"""
	For The FTR Exemption or AES Citation we are provided to be valid for EEI.
	if shipment is for Canada or Mexico or shipment custom value is more that 2500 $

	"""
	export_detail = shipment.create_wsdl_object_of_type('ExportDetail')
	export_detail.ExportComplianceStatement = ExportComplianceStatement
	shipment.RequestedShipment.CustomsClearanceDetail.ExportDetail = export_detail


def _create_commodity_for_package(box, package_weight, sequence_number, shipment, source_doc):
	"""
	Only for international shipment
	"""
	commodity = shipment.create_wsdl_object_of_type('Commodity')
	commodity_default_currency = "USD"

	dict_of_items_in_box = parse_items_in_box(box)

	# ------------------------------------

	commodity.UnitPrice.Amount = 0
	commodity.CustomsValue.Amount = 0
	quantity_of_all_items_in_box = 0

	for item in dict_of_items_in_box:
		item_quantity = dict_of_items_in_box[item]

		commodity.UnitPrice.Amount += int(get_item_by_item_code(source_doc, item).rate) * item_quantity

		custom_value = int(get_item_by_item_code(source_doc, item).custom_value)
		if custom_value == 0:
			frappe.throw(_("[ITEM # {}] CUSTOM VALUE = 0. Please specify custom value for items in box".format(item)))

		commodity.CustomsValue.Amount += custom_value * item_quantity

		quantity_of_all_items_in_box += item_quantity

		# ---------------------------------------------------------------

		if commodity.CustomsValue.Amount >= 2500 or source_doc.recipient_address_country_code in ['CA', 'MX']:
			add_export_detail(shipment)

	# --------------------------------------
	frappe.db.set(box, 'total_box_custom_value', commodity.CustomsValue.Amount)
	# -----------------------------------------

	commodity.Name = "Shipment with " + ",".join(
		get_item_by_item_code(source_doc, item).item_name for item in dict_of_items_in_box)

	commodity.NumberOfPieces = quantity_of_all_items_in_box

	commodity.Description = ";<br>".join("<b>%s</b> <br><i>%s</i>" % (get_item_by_item_code(source_doc, item).item_name,
																	  get_item_by_item_code(source_doc,
																							item).description)
										 for item in dict_of_items_in_box)

	commodity.CountryOfManufacture = source_doc.shipper_address_country_code
	commodity.Weight = package_weight
	commodity.Quantity = quantity_of_all_items_in_box

	commodity.QuantityUnits = 'EA'

	commodity.UnitPrice.Currency = commodity_default_currency
	commodity.CustomsValue.Currency = commodity_default_currency

	shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount = commodity.CustomsValue.Amount
	shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency = commodity.CustomsValue.Currency

	shipment.add_commodity(commodity)

	commodity_message = """
		<b style="background-color: rgba(152, 216, 91, 0.43);">THE PACKAGE # {box_number} </b><br>
		<b>NAME</b>                     {name}<br>
		<b>NUMBER OF PIECES </b>        =  {number_of_pieces}<br>
		<b>DESCRIPTION</b> <br>
		{description}<br>
		<b>COUNTRY OF MANUFACTURE </b>  =  {country_manufacture}<br>
		<b>WIGHT  </b>                  =  {wight} <br>
		<b>QUANTITY     </b>            =  {quantity} <br>
		<b>QUANTITY UNITS   </b>        =  {quantity_unites} <br>
		<b>UNIT PRICE CURRENCY    </b>  =  {unit_price_currency} <br>
		<b>UNIT PRICE AMOUNT    </b>    =  {unit_price_amount} <br>
		<b>CUSTOM VALUE CURRENCY   </b> =  {custom_value_currency} <br>
		<b>CUSTOM VALUE AMOUNT    </b>  =  {custom_value_amount} <br>
		<br>
		""".format(box_number=sequence_number,
				   name=commodity.Name,
				   number_of_pieces=commodity.NumberOfPieces,
				   description=commodity.Description,
				   country_manufacture=commodity.CountryOfManufacture,
				   wight="%s %s" % (commodity.Weight.Value, commodity.Weight.Units),
				   quantity=commodity.Quantity,
				   quantity_unites=commodity.QuantityUnits,
				   unit_price_currency=commodity.UnitPrice.Currency,
				   unit_price_amount=commodity.UnitPrice.Amount,
				   custom_value_currency=commodity.CustomsValue.Currency,
				   custom_value_amount=commodity.CustomsValue.Amount)

	if sequence_number != 1:
		commodity_message = source_doc.commodity_information + commodity_message

	frappe.db.set(source_doc, 'commodity_information', unicode(commodity_message))


def create_fedex_shipment(source_doc):

	GENERATE_IMAGE_TYPE = 'PNG'

	if source_doc.international_shipment:
		shipment = FedexProcessInternationalShipmentRequest(CONFIG_OBJ, customer_transaction_id=CUSTOMER_TRANSACTION_ID)
		service_type = source_doc.service_type_international

	else:
		shipment = FedexProcessShipmentRequest(CONFIG_OBJ, customer_transaction_id=CUSTOMER_TRANSACTION_ID)
		service_type = source_doc.service_type_domestic

	shipment.RequestedShipment.DropoffType = source_doc.drop_off_type
	shipment.RequestedShipment.ServiceType = service_type

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

	# #############################################################################

	DictDiffer.validate_shipment_integrity(source_doc)

	# #############################################################################

	labels = []

	all_boxes = source_doc.get_all_children("DTI Shipment Package")

	total_for_all_shipment_weight = shipment.create_wsdl_object_of_type('Weight')
	total_for_all_shipment_weight.Value = sum([box.weight_value for box in all_boxes])
	total_for_all_shipment_weight.Units = all_boxes[0].weight_units
	shipment.RequestedShipment.TotalWeight = total_for_all_shipment_weight

	for i, box in enumerate(all_boxes):

		box_sequence_number = i + 1

		total_box_insurance = get_box_total_insurance(source_doc, box)
		frappe.db.set(box, 'total_box_insurance', total_box_insurance)

		fedex_package = _create_package(shipment=shipment,
										sequence_number=box_sequence_number,
										package_weight_value=box.weight_value,
										package_weight_units=box.weight_units,
										physical_packaging=box.physical_packaging,
										insured_amount=total_box_insurance)

		if source_doc.international_shipment:
			_create_commodity_for_package(box=box,
										  package_weight=fedex_package.Weight,
										  sequence_number=box_sequence_number,
										  shipment=shipment,
										  source_doc=source_doc)

		shipment.RequestedShipment.RequestedPackageLineItems = [fedex_package]
		shipment.RequestedShipment.PackageCount = len(all_boxes)

		if box_sequence_number >1 :
			shipment.RequestedShipment.MasterTrackingId.TrackingNumber = master_tracking_number
			shipment.RequestedShipment.MasterTrackingId.TrackingIdType = master_tracking_id_type
			shipment.RequestedShipment.MasterTrackingId.FormId = master_tracking_form_id

		_send_request_to_fedex(sequence_number=box_sequence_number,
							   box=box,
							   shipment=shipment)

		label = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0]

		if box_sequence_number == 1:
			master_tracking_number = label.TrackingIds[0].TrackingNumber
			master_tracking_id_type = label.TrackingIds[0].TrackingIdType
			master_tracking_form_id = label.TrackingIds[0].FormId

			frappe.db.set(source_doc, 'tracking_number', master_tracking_number)
			frappe.db.set(source_doc, 'master_tracking_id_type', master_tracking_id_type)

			frappe.db.set(box, 'tracking_number', master_tracking_number)
			frappe.db.set(box, 'total_box_insurance', total_box_insurance)

		box_tracking_number = label.TrackingIds[0].TrackingNumber
		ascii_label_data = label.Label.Parts[0].Image
		label_binary_data = binascii.a2b_base64(ascii_label_data)

		frappe.db.set(box, 'tracking_number', box_tracking_number)

		file_name = "label_%s_%s.%s" % (master_tracking_number, box_tracking_number, GENERATE_IMAGE_TYPE.lower())

		saved_file = save_file(file_name, label_binary_data, source_doc.doctype, source_doc.name, is_private=1)

		labels.append(saved_file.file_url)

	# ############################################################################
	# ############################################################################

	for i, path in enumerate(labels):
		frappe.db.set(source_doc, 'label_' + str(i + 1), path)

	# ############################################################################
	# ############################################################################

	set_delivery_time(source_doc)
	set_shipment_rate(source_doc.name)

	frappe.db.set(source_doc, 'total_insurance', sum([box.total_box_insurance for box in all_boxes]))
	frappe.db.set(source_doc, 'total_custom_value', sum([box.total_box_custom_value for box in all_boxes]))

	# #############################################################################
	# #############################################################################

	frappe.msgprint("DONE!", "Tracking number:{}".format(master_tracking_number))


# ##############################################################################
# ##############################################################################


def _send_request_to_fedex(sequence_number, box, shipment):
	try:
		box.save()

		shipment.send_request()

	except Exception as error:
		if "Customs Value is required" in str(error):
			frappe.throw(_("International Shipment option is required".upper()))

		elif "Total Insured value exceeds customs value" in str(error) or " Insured Value can not exceed customs value" in str(error):

			frappe.throw(_("""[BOX # {0}]
			Error from Fedex: {1}.
			Insurance: {2}
			Custom Value: {3}
			ITEMS IN BOX: {4}""".format(sequence_number,
										str(error),
										box.total_box_insurance,
										box.total_box_custom_value,
										box.items_in_box)))
		else:
			frappe.throw(_("[BOX # {}] Error from Fedex: {}".format(sequence_number, str(error))))


# #############################################################################
# #############################################################################


def parse_items_in_box(box):
	items = {}
	lines = box.items_in_box.split("\n")
	for line in lines:
		try:
			item = line.split(":")
		except ValueError:
			frappe.msgprint(_("WARNING! Bad lines:%s" % line))

		if items.has_key(item[0]):
			items[item[0]] += int(item[1])
		else:
			items.update({item[0]: int(item[1])})
	return items


# #############################################################################
# #############################################################################

def get_item_by_item_code(source_doc, item_code):
	all_delivery_items = source_doc.get_all_children("DTI Shipment Note Item")

	for item in all_delivery_items:
		if item.item_code == item_code:
			return item

# #############################################################################
# #############################################################################


def get_box_total_insurance(source_doc, box):
	"""
	Insurance of all items in box calculation:
	"""
	dict_of_items_in_box = parse_items_in_box(box)
	total_box_insurance = 0
	for item in dict_of_items_in_box:
		item_quantity = dict_of_items_in_box[item]
		total_box_insurance += int(get_item_by_item_code(source_doc, item).insurance) * item_quantity

	return total_box_insurance

# #############################################################################
# #############################################################################


@check_permission()
@frappe.whitelist()
def get_package_rate(international=False,
					 DropoffType=None,
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
	:param international:
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
	:return: data rate

	EXAMPLE

	DropoffType: 'REGULAR_PICKUP',
	ServiceType:'FEDEX_GROUND',
	PackagingType: 'YOUR_PACKAGING',
	ShipperStateOrProvinceCode:'SC',
	ShipperPostalCode: '29631',
	ShipperCountryCode:'US',
	RecipientStateOrProvinceCode:'NC',
	RecipientPostalCode:'27577',
	RecipientCountryCode:'US',
	EdtRequestType:'NONE',
	PaymentType:'SENDER',
	package_list:
	[{"weight_value":"1",
	"weight_units":"LB",
	"physical_packaging":"BOX",
	"group_package_count":"1",
	"insured_amount":"100"},
	{"weight_value":"10004000",
	"weight_units":"LB",
	"physical_packaging":"BOX",
	"group_package_count":"1",
	"insured_amount":"100"}]

	_______________________________

	KNOWN ISSUES (FEDEX TEST SERVER)

	Test server caches rate for the same Shipper/Recipient data

	"""

	if international:
		rate = FedexInternationalRateServiceRequest(CONFIG_OBJ)
	else:
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

	try:
		rate.send_request()
	except Exception as e:
		if 'RequestedPackageLineItem object cannot be null or empty' in str(e):
			raise Exception("WARNING: Please create packages with shipment")

	response_json = subject_to_json(rate.response)
	data = json.loads(response_json)

	if "Service is not allowed" in str(data['Notifications'][0]['Message']):
		frappe.throw(_("WARNING: Service is not allowed. Please verify address data!"))

	return data['RateReplyDetails'][0]['RatedShipmentDetails'][0]["ShipmentRateDetail"]['TotalNetChargeWithDutiesAndTaxes']


@check_permission()
@frappe.whitelist()
def get_shipment_rate(doc_name):
	source_doc = frappe.get_doc("DTI Shipment Note", doc_name)
	BOXES = source_doc.get_all_children("DTI Shipment Package")

	rate_box_list = []
	for i, box in enumerate(BOXES):
		rate_box_list.append({'weight_value': box.weight_value,
							  'weight_units': box.weight_units,
							  'physical_packaging': box.physical_packaging,
							  'group_package_count': i+1,
							  'insured_amount': box.total_box_insurance})

	if source_doc.international_shipment:
		service_type = source_doc.service_type_international
	else:
		service_type = source_doc.service_type_domestic

	return get_package_rate(international=source_doc.international_shipment,
							DropoffType=source_doc.drop_off_type,
							ServiceType=service_type,
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


@check_permission()
@frappe.whitelist()
def set_shipment_rate(doc_name):
	source_doc = frappe.get_doc("DTI Shipment Note", doc_name)

	try:
		rate = get_shipment_rate(doc_name)
		frappe.db.set(source_doc, 'shipment_rate', "%s (%s)" % (rate["Amount"], rate["Currency"]))

		frappe.msgprint("Rate: %s (%s)" % (rate["Amount"], rate["Currency"]), "Updated!")
	except Exception:
		frappe.db.set(source_doc, 'shipment_rate', "N/A")


@check_permission()
@frappe.whitelist()
def show_shipment_estimates(doc_name):
	"""
	Fedex's shipping calculator estimates the time and cost of delivery based on the destination and service.
	"""
	source_doc = frappe.get_doc("DTI Shipment Note", doc_name)

	DictDiffer.validate_shipment_integrity(source_doc=source_doc)

	rate = get_shipment_rate(doc_name)

	time = estimate_delivery_time(OriginPostalCode=source_doc.recipient_address_postal_code,
						          OriginCountryCode=source_doc.recipient_address_postal_code,
						          DestinationPostalCode=source_doc.shipper_address_country_code,
						          DestinationCountryCode=source_doc.shipper_address_postal_code)

	frappe.msgprint("""Shipment calculator estimates the time and cost of delivery based on the destination and service.
					<br>
					<br>
					<b>Rate: </b> %s (%s) <br>
					<b>Delivery Time: </b>%s"""% (rate["Amount"], rate["Currency"], time), "INFO")


# #############################################################################
# #############################################################################

def set_delivery_time(source_doc):
	try:
		delivery_time = estimate_delivery_time(OriginPostalCode=source_doc.shipper_address_postal_code,
											   OriginCountryCode=source_doc.shipper_address_country_code,
											   DestinationPostalCode=source_doc.recipient_address_postal_code,
											   DestinationCountryCode=source_doc.recipient_address_country_code)
		frappe.db.set(source_doc, 'delivery_time', delivery_time)
		frappe.msgprint("Delivery Time: %s" % delivery_time, "Updated!")
	except Exception as error:
		frappe.throw(_("Delivery time error - %s" % error))


# #############################################################################
# #############################################################################

def delete_fedex_shipment(source_doc):
	del_request = FedexDeleteShipmentRequest(CONFIG_OBJ)
	del_request.DeletionControlType = "DELETE_ALL_PACKAGES"
	del_request.TrackingId.TrackingNumber = source_doc.tracking_number
	del_request.TrackingId.TrackingIdType = source_doc.master_tracking_id_type

	try:
		del_request.send_request()
	except Exception as e:
		if 'Unable to retrieve record' in str(e):
			raise Exception("WARNING: Unable to delete the shipment with the provided tracking number.")
		else:
			raise Exception("ERROR: %s. Tracking number: %s. Type: %s" % (e, source_doc.tracking_number, source_doc.master_tracking_id_type))


# #############################################################################
# #############################################################################


def get_fedex_shipment_status(track_value):
	track = FedexTrackRequest(CONFIG_OBJ, customer_transaction_id=CUSTOMER_TRANSACTION_ID)

	track.SelectionDetails.PackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
	track.SelectionDetails.PackageIdentifier.Value = track_value

	del track.SelectionDetails.OperatingCompany

	try:
		track.send_request()
		return track.response[4][0].TrackDetails[0].Events[0].EventType
	except AttributeError:
			return None
	except FedexError as error:
		frappe.throw(_("Fedex error! {} {}".format(error, get_fedex_server_info())))


# #############################################################################
# #############################################################################


@frappe.whitelist(allow_guest=True)
def get_html_code_status_with_fedex_tracking_number(track_value):
	"""
	FOR WEB PAGE WITH SHIPMENT TRACKING - shipment_tracking.html
	:param track_value:
	:return:
	"""
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

# #############################################################################
# #############################################################################


class DictDiffer(object):
	"""
	Calculate the difference between two dictionaries as:
	(1) items added
	(2) items removed
	(3) keys same in both but changed values
	(4) keys same in both and unchanged values
	"""
	def __init__(self, current_dict, past_dict):
		self.current_dict, self.past_dict = current_dict, past_dict
		self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
		self.intersect = self.set_current.intersection(self.set_past)

	def added(self):
		return self.set_current - self.intersect

	def removed(self):
		return self.set_past - self.intersect

	def changed(self):
		return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

	def unchanged(self):
		return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

	@staticmethod
	def validate_shipment_integrity(source_doc):
		"""
		Basic validation that shipment is correct.
		That all items from delivery note are in boxes and etc.
		"""

		boxes = source_doc.get_all_children("DTI Shipment Package")

		if len(boxes) > 9:
			frappe.throw(_("Max amount of packages is 10"))

		if not boxes:
			frappe.throw(_("Please create shipment box packages!"))

		# ---------------------------------

		if len(set([box.weight_units for box in boxes])) > 1:
			frappe.throw(_("Please select the same weight units for all boxes. They can't be different."))

		# ---------------------------------

		parsed_items_per_box = {i: parse_items_in_box(package) for i, package in enumerate(boxes)}
		all_items_in_all_boxes = {}
		for box in parsed_items_per_box:
			for item_code in parsed_items_per_box[box]:
				if all_items_in_all_boxes.has_key(item_code):
					all_items_in_all_boxes[item_code] += parsed_items_per_box[box][item_code]
				else:
					all_items_in_all_boxes.update({item_code: int(parsed_items_per_box[box][item_code])})

		delivery_items_dict = {}
		for item in source_doc.get_all_children("DTI Shipment Note Item"):
			if delivery_items_dict.has_key(item.item_code):
				delivery_items_dict[item.item_code] += int(item.qty)
			else:
				delivery_items_dict.update({item.item_code: int(item.qty)})

		differ = DictDiffer(delivery_items_dict, all_items_in_all_boxes)

		if differ.changed():
			delivery_string = "<br>".join("%s = %i" % (item, delivery_items_dict[item]) for item in delivery_items_dict)
			all_items_string = "<br>".join(
				"%s = %i" % (item, all_items_in_all_boxes[item]) for item in all_items_in_all_boxes)

			error_message = """<b style="color:orange;">WARNING!</b><br>
			Integrity error for: <b>{}</b> <br>
			<hr>
			<b>DELIVERY ITEMS:</b> <br>{} <br><br>
			<b>ITEMS IN BOX:</b> <br>{}""".format(",".join(differ.changed()), delivery_string, all_items_string)

			frappe.throw(_(error_message))