# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import json
import logging
import binascii
import datetime
import sys

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

subject_to_json = conversion.sobject_to_json
FedexTrackRequest = fedex_track_service.FedexTrackRequest
FedexConfig = fedex_config.FedexConfig
FedexRateServiceRequest = rate_service.FedexRateServiceRequest
FedexAvailabilityCommitmentRequest = availability_commitment_service.FedexAvailabilityCommitmentRequest
FedexProcessShipmentRequest = ship_service.FedexProcessShipmentRequest


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

	fedex_configuration = FedexProvider()

	rate = FedexRateServiceRequest(fedex_configuration.config_obj)

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

		rate.add_package(package1)

	rate.send_request()

	response_json = subject_to_json(rate.response)
	data = json.loads(response_json)

	return data['RateReplyDetails'][0]['RatedShipmentDetails'][0]["ShipmentRateDetail"][
		'TotalNetChargeWithDutiesAndTaxes']


@frappe.whitelist()
def estimate_delivery_time(OriginPostalCode, OriginCountryCode, DestinationPostalCode, DestinationCountryCode):
	"""
		Projected package delivery date based on ship date, service, and destination
		:param OriginPostalCode:
		:param OriginCountryCode:
		:param DestinationPostalCode:
		:param DestinationCountryCode:
		:return: ShipDate
		"""
	fedex_configuration = FedexProvider()

	avc_request = FedexAvailabilityCommitmentRequest(fedex_configuration.config_obj)

	avc_request.Origin.PostalCode = OriginPostalCode
	avc_request.Origin.CountryCode = OriginCountryCode

	avc_request.Destination.PostalCode = DestinationPostalCode
	avc_request.Destination.CountryCode = DestinationCountryCode

	return avc_request.ShipDate


################################################################################
################################################################################
################################################################################


class FedexProvider(object):
	def __init__(self):
		self.fedex_server_doc_type = None
		self.config_message = ""
		self.config_obj = self.get_fedex_config()

	def get_fedex_config(self, general_doc_type_name=PRIMARY_FEDEX_DOC_NAME):

		_fedex_config = frappe.db.sql(
			'''SELECT * from `tabDTI Fedex Configuration` WHERE name = "%s"''' % general_doc_type_name, as_dict=True)

		if not _fedex_config:
			raise Exception("Please create Fedex Configuration: %s" % general_doc_type_name)

		self.fedex_server_doc_type = _fedex_config[0]

		if self.fedex_server_doc_type['use_test_server']:
			_test_server = True
		else:
			_test_server = False

		self.config_message = """<b>FEDEX CONFIG:</b>
<br><b>key </b>                   : '{key}'
<br><b>password </b>              : '{password}'
<br><b>account_number </b>        : '{account_number}'
<br><b>meter_number </b>          : '{meter_number}'
<br><b>freight_account_number</b> : '{freight_account_number}'
<br><b>use_test_server </b>       : '{use_test_server}'""".format(
			key=self.fedex_server_doc_type['fedex_key'],
			password=self.fedex_server_doc_type['password'],
			account_number=self.fedex_server_doc_type['account_number'],
			meter_number=self.fedex_server_doc_type['meter_number'],
			freight_account_number=self.fedex_server_doc_type['freight_account_number'],
			use_test_server=_test_server)

		return FedexConfig(key=self.fedex_server_doc_type['fedex_key'],
						   password=get_decrypted_password('DTI Fedex Configuration',
														   general_doc_type_name,
														   fieldname='password',
														   raise_exception=True),
						   account_number=self.fedex_server_doc_type['account_number'],
						   meter_number=self.fedex_server_doc_type['meter_number'],
						   freight_account_number=self.fedex_server_doc_type['freight_account_number'],
						   use_test_server=_test_server)

	@staticmethod
	def create_package(shipment, sequence_number=1, package_weight_value=1.0, package_weight_units="LB",
					   physical_packaging="ENVELOPE"):
		package_weight = shipment.create_wsdl_object_of_type('Weight')
		package_weight.Value = package_weight_value
		package_weight.Units = package_weight_units

		package = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
		package.PhysicalPackaging = physical_packaging
		package.Weight = package_weight

		package.SpecialServicesRequested.SpecialServiceTypes = 'SIGNATURE_OPTION'
		package.SpecialServicesRequested.SignatureOptionDetail.OptionType = 'SERVICE_DEFAULT'
		package.SequenceNumber = sequence_number
		return package

	@staticmethod
	def create_shipment(source_doc):

		BOXES = source_doc.get_all_children("DTI Shipment Package")

		if len(BOXES) > 9:
			frappe.throw(_("Max amount of packages is 10"))

		if not BOXES:
			frappe.throw(_("Please create shipment box packages!"))

		GENERATE_IMAGE_TYPE = 'PNG'

		logging.basicConfig(stream=sys.stdout, level=logging.INFO)

		customer_transaction_id = "*** ShipService Request v17 using Python ***"

		provider = FedexProvider()
		CONFIG_OBJ = provider.get_fedex_config()

		shipment = FedexProcessShipmentRequest(CONFIG_OBJ, customer_transaction_id=customer_transaction_id)

		shipment.RequestedShipment.DropoffType = source_doc.drop_off_type
		shipment.RequestedShipment.ServiceType = source_doc.service_type
		shipment.RequestedShipment.PackagingType = source_doc.packaging_type

		# Shipper contact info.
		shipment.RequestedShipment.Shipper.Contact.PersonName = source_doc.shipper_contact_person_name
		shipment.RequestedShipment.Shipper.Contact.CompanyName = source_doc.shipper_contact_company_name
		shipment.RequestedShipment.Shipper.Contact.PhoneNumber = source_doc.shipper_contact_phone_number

		# Shipper address.
		shipment.RequestedShipment.Shipper.Address.StreetLines = [source_doc.shipper_address_streetlines]
		shipment.RequestedShipment.Shipper.Address.City = source_doc.shipper_address_city
		shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = source_doc.shipper_address_state_or_provincecode
		shipment.RequestedShipment.Shipper.Address.PostalCode = source_doc.shipper_address_postalcode
		shipment.RequestedShipment.Shipper.Address.CountryCode = source_doc.shipper_address_country_code
		shipment.RequestedShipment.Shipper.Address.Residential = True

		# Recipient contact info.
		shipment.RequestedShipment.Recipient.Contact.PersonName = source_doc.recipient_contact_person_name
		shipment.RequestedShipment.Recipient.Contact.CompanyName = source_doc.recipient_company_name
		shipment.RequestedShipment.Recipient.Contact.PhoneNumber = source_doc.recipient_contact_phone_number

		# Recipient addressStateOrProvinceCode
		shipment.RequestedShipment.Recipient.Address.StreetLines = [source_doc.recipient_address_street_lines]
		shipment.RequestedShipment.Recipient.Address.City = source_doc.recipient_address_city
		shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = source_doc.recipient_address_state_or_provincecode
		shipment.RequestedShipment.Recipient.Address.PostalCode = source_doc.recipient_address_postalcode
		shipment.RequestedShipment.Recipient.Address.CountryCode = source_doc.recipient_address_countrycode
		# This is needed to ensure an accurate rate quote with the response. Use AddressValidation to get ResidentialStatus
		shipment.RequestedShipment.Recipient.Address.Residential = True
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

		package1 = FedexProvider.create_package(shipment=shipment,
												sequence_number=1,
												package_weight_value=5.0,
												package_weight_units="LB",
												physical_packaging="ENVELOPE")

		shipment.RequestedShipment.RequestedPackageLineItems = [package1]

		shipment.RequestedShipment.PackageCount = len(BOXES)

		try:
			shipment.send_request()
		except Exception as error:
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

		for i, child_package in enumerate(BOXES[1:]):

			i += 1

			package = source_doc.create_package(shipment=shipment,
												sequence_number=i + 1,
												package_weight_value=5.0,
												package_weight_units="LB",
												physical_packaging="ENVELOPE")

			shipment.RequestedShipment.RequestedPackageLineItems = [package]
			shipment.RequestedShipment.MasterTrackingId.TrackingNumber = master_tracking_number
			shipment.RequestedShipment.MasterTrackingId.TrackingIdType = master_tracking_id_type
			shipment.RequestedShipment.MasterTrackingId.FormId = master_tracking_form_id

			try:
				shipment.send_request()
			except Exception as error:
				frappe.throw(_(error))

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
			delivery_time = estimate_delivery_time(OriginPostalCode=source_doc.shipper_address_postalcode,
												   OriginCountryCode=source_doc.shipper_address_country_code,
												   DestinationPostalCode=source_doc.recipient_address_postalcode,
												   DestinationCountryCode=source_doc.recipient_address_countrycode)
			frappe.db.set(source_doc, 'delivery_time', delivery_time)
		except Exception as error:
			frappe.throw(_(error))

		# ################################################

		try:
			rate = get_package_rate(DropoffType=source_doc.drop_off_type,
									ServiceType=source_doc.service_type,
									PackagingType=source_doc.packaging_type,
									ShipperStateOrProvinceCode=source_doc.shipper_address_state_or_provincecode,
									ShipperPostalCode=source_doc.shipper_address_postalcode,
									ShipperCountryCode=source_doc.shipper_address_country_code,
									RecipientStateOrProvinceCode=source_doc.recipient_address_state_or_provincecode,
									RecipientPostalCode=source_doc.recipient_address_postalcode,
									RecipientCountryCode=source_doc.recipient_address_countrycode,
									EdtRequestType='NONE',
									PaymentType=source_doc.payment_type,
									package_list=[{'weight_value': 1.0,
												   'weight_units': "LB",
												   'physical_packaging': 'BOX',
												   'group_package_count': 1}])
			frappe.db.set(source_doc, 'rate', "%s (%s)" % (rate["Amount"], rate["Currency"]))
		except Exception as error:
			frappe.throw(_(error))

		# ################################################

		frappe.msgprint("DONE!", "Tracking number:{}".format(master_tracking_number))

	@staticmethod
	def delete_shipment(source_doc):
		from fedex.services.ship_service import FedexDeleteShipmentRequest
		from fedex.base_service import FedexError

		# Un-comment to see the response from Fedex printed in stdout.
		logging.basicConfig(stream=sys.stdout, level=logging.INFO)

		provider = FedexProvider()
		CONFIG_OBJ = provider.get_fedex_config()

		del_request = FedexDeleteShipmentRequest(CONFIG_OBJ)

		# Either delete all packages in a shipment, or delete an individual package.
		# Docs say this isn't required, but the WSDL won't validate without it.
		# DELETE_ALL_PACKAGES, DELETE_ONE_PACKAGE
		del_request.DeletionControlType = "DELETE_ALL_PACKAGES"

		# The tracking number of the shipment to delete.
		del_request.TrackingId.TrackingNumber = source_doc.tracking_number

		# What kind of shipment the tracking number used.
		# Docs say this isn't required, but the WSDL won't validate without it.
		# EXPRESS, GROUND, or USPS
		del_request.TrackingId.TrackingIdType = 'EXPRESS'

		# Fires off the request, sets the 'response' attribute on the object.
		try:
			del_request.send_request()
		except FedexError as error:
			if 'Unable to retrieve record' in str(error):
				frappe.throw(_("WARNING: Unable to delete the shipment with the provided tracking number."))
			else:
				frappe.throw(_("%s" % error))

		# See the response printed out.
		# print(del_request.response)

		# This will convert the response to a python dict object. To
		# make it easier to work with.
		# from fedex.tools.response_tools import basic_sobject_to_dict
		# print(basic_sobject_to_dict(del_request.response))

		# This will dump the response data dict to json.
		# from fedex.tools.response_tools import sobject_to_json
		# print(sobject_to_json(del_request.response))

		# Here is the overall end result of the query.
		print("HighestSeverity: {}".format(del_request.response.HighestSeverity))


@frappe.whitelist(allow_guest=True)
def get_html_code_status_with_fedex_tracking_number(track_value):
	if not track_value:
		return "Track value can't be empty"

	logging.basicConfig(stream=sys.stdout, level=logging.INFO)

	customer_transaction_id = "*** TrackService Request v10 using Python ***"  # Optional transaction_id

	fedex_configuration = FedexProvider()

	track = FedexTrackRequest(fedex_configuration.get_fedex_config(), customer_transaction_id=customer_transaction_id)

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
		return """<b>ERROR :</b><br> Fedex invalid configuration error! <br>{0}<br><br>{1} """.format(error.value, fedex_configuration.config_message)
