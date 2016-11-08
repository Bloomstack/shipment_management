# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils.password import get_decrypted_password
from frappe import _
import app_config

import logging
import sys
import json
import binascii
import datetime
import sys
import os
from frappe.utils import get_site_name, get_site_path, get_site_base_path, get_path, cstr
from frappe.model.mapper import get_mapped_doc


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
					 package_list = None):
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
	
	return data['RateReplyDetails'][0]['RatedShipmentDetails'][0]["ShipmentRateDetail"]['TotalNetChargeWithDutiesAndTaxes']


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


class FedexProvider:
	"""It is responsible for fedex configuration"""

	def __init__(self):
		self.fedex_server_doc_type = None
		self.config_message = ""
		self.config_obj = self.get_fedex_config()

	def get_fedex_config(self, general_doc_type_name=app_config.config["fedex_config"]):

		_fedex_config = frappe.db.sql('''SELECT * from `tabDTI Fedex Configuration` WHERE name = "%s"''' % general_doc_type_name, as_dict=True)

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
						password=get_decrypted_password('DTI Fedex Configuration', general_doc_type_name, fieldname='password', raise_exception=True),
						account_number=self.fedex_server_doc_type['account_number'],
						meter_number=self.fedex_server_doc_type['meter_number'],
						freight_account_number=self.fedex_server_doc_type['freight_account_number'],
						use_test_server=_test_server)

