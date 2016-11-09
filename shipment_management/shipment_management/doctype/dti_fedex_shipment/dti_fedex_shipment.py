# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigiThinkit Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals


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

from shipment_management.fedex_provider import FedexProvider, get_package_rate, estimate_delivery_time


fedex_track_service = frappe.get_module("fedex.services.track_service")
fedex_config = frappe.get_module("fedex.config")
ship_service = frappe.get_module("fedex.services.ship_service")
FedexTrackRequest = fedex_track_service.FedexTrackRequest
FedexConfig = fedex_config.FedexConfig
FedexProcessShipmentRequest = ship_service.FedexProcessShipmentRequest


class DTIFedexShipment(Document):
	"""
	For FedEx, the first tracking # should provide you with the
	links to the other packages in a Multi-parcel shipment.
	There isn't a Master to cover them all.

	We can rate multiple packages using one SOAP request; however, to ship an
	Multiple Pieces Shipment (MPS), you have to perform a shipping request for each one of the packages.

	The first package (the package in the first request),
	will be your Master containing the master tracking number.
	Once you have this master tracking number, you have to attach it to the shipping request
	of the remaining packages.
	"""

	def on_submit(self):
		self.create_shipment()
		frappe.db.set(self, 'shipment_status', 'InProgress')

	def create_package(self, shipment, sequence_number=1, package_weight_value=1.0, package_weight_units="LB",
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

	def create_shipment(self):

		if len(self.get_all_children()) > 9:
			frappe.throw(_("Max amount of packages is 10"))

		# ===================================================================

		GENERATE_IMAGE_TYPE = 'PNG'

		logging.basicConfig(stream=sys.stdout, level=logging.INFO)

		customer_transaction_id = "*** ShipService Request v17 using Python ***"  # Optional transaction_id

		provider = FedexProvider()
		CONFIG_OBJ = provider.get_fedex_config()

		shipment = FedexProcessShipmentRequest(CONFIG_OBJ, customer_transaction_id=customer_transaction_id)

		shipment.RequestedShipment.DropoffType = self.drop_off_type
		shipment.RequestedShipment.ServiceType = self.service_type
		shipment.RequestedShipment.PackagingType = self.packaging_type

		# Shipper contact info.
		shipment.RequestedShipment.Shipper.Contact.PersonName = 'Sender Name' # Company
		shipment.RequestedShipment.Shipper.Contact.CompanyName = 'Some Company' # Company
		shipment.RequestedShipment.Shipper.Contact.PhoneNumber = '9012638716' # Company

		# Shipper address.
		shipment.RequestedShipment.Shipper.Address.StreetLines = ['Address Line 1']
		shipment.RequestedShipment.Shipper.Address.City = 'Herndon'
		shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = 'VA'
		shipment.RequestedShipment.Shipper.Address.PostalCode = '20171'
		shipment.RequestedShipment.Shipper.Address.CountryCode = 'US'
		shipment.RequestedShipment.Shipper.Address.Residential = True # check

		# Recipient contact info.
		shipment.RequestedShipment.Recipient.Contact.PersonName = 'Recipient Name'
		shipment.RequestedShipment.Recipient.Contact.CompanyName = 'Recipient Company'
		shipment.RequestedShipment.Recipient.Contact.PhoneNumber = '9012637906'

		# Recipient addressStateOrProvinceCode
		shipment.RequestedShipment.Recipient.Address.StreetLines = ['Address Line 1']
		shipment.RequestedShipment.Recipient.Address.City = 'Herndon'
		shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = 'VA'
		shipment.RequestedShipment.Recipient.Address.PostalCode = '20171'
		shipment.RequestedShipment.Recipient.Address.CountryCode = 'US'
		# This is needed to ensure an accurate rate quote with the response. Use AddressValidation to get ResidentialStatus
		shipment.RequestedShipment.Recipient.Address.Residential = True
		shipment.RequestedShipment.EdtRequestType = 'NONE'

		# Senders account information
		shipment.RequestedShipment.ShippingChargesPayment.Payor.ResponsibleParty.AccountNumber = CONFIG_OBJ.account_number
		shipment.RequestedShipment.ShippingChargesPayment.PaymentType = self.payment_type
		shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'
		shipment.RequestedShipment.LabelSpecification.ImageType = GENERATE_IMAGE_TYPE
		shipment.RequestedShipment.LabelSpecification.LabelStockType = self.label_stock_type
		shipment.RequestedShipment.ShipTimestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
		shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = 'TOP_EDGE_OF_TEXT_FIRST'

		if hasattr(shipment.RequestedShipment.LabelSpecification, 'LabelOrder'):
			del shipment.RequestedShipment.LabelSpecification.LabelOrder  # Delete, not using.

		# ===================================================

		# FIRST / MASTER Package

		package1 = self.create_package(shipment=shipment,
									   sequence_number=1,
									   package_weight_value=5.0,
									   package_weight_units="LB",
								       physical_packaging="ENVELOPE")

		shipment.RequestedShipment.RequestedPackageLineItems = [package1]

		shipment.RequestedShipment.PackageCount = len(self.get_all_children())
		shipment.send_request()

		master_label = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0]

		master_tracking_number = master_label.TrackingIds[0].TrackingNumber
		master_tracking_id_type = master_label.TrackingIds[0].TrackingIdType
		master_tracking_form_id = master_label.TrackingIds[0].FormId

		ascii_label_data = master_label.Label.Parts[0].Image
		label_binary_data = binascii.a2b_base64(ascii_label_data)

		file_name = "label_%s.%s" % (master_tracking_number, GENERATE_IMAGE_TYPE.lower())

		saved_file = save_file(file_name, label_binary_data, self.doctype, self.name, is_private=1)

		frappe.db.set(self, 'tracking_number', master_tracking_number)
		frappe.db.set(self, 'label_1', saved_file.file_url)

		# ===================================================

		# Track additional package in shipment :

		packages = self.get_all_children()

		labels = []

		for i, child_package in enumerate(packages[1:]):

			i += 1

			frappe.db.set(child_package, 'tracking_number', master_tracking_number)

			package = self.create_package(shipment=shipment,
										   sequence_number=i+1,
										   package_weight_value=5.0,
										   package_weight_units="LB",
										   physical_packaging="ENVELOPE")

			shipment.RequestedShipment.RequestedPackageLineItems = [package]
			shipment.RequestedShipment.MasterTrackingId.TrackingNumber = master_tracking_number
			shipment.RequestedShipment.MasterTrackingId.TrackingIdType = master_tracking_id_type
			shipment.RequestedShipment.MasterTrackingId.FormId = master_tracking_form_id

			shipment.send_request()

			for label in shipment.response.CompletedShipmentDetail.CompletedPackageDetails:
				child_tracking_number = label.TrackingIds[0].TrackingNumber
				ascii_label_data = label.Label.Parts[0].Image
				label_binary_data = binascii.a2b_base64(ascii_label_data)

				file_name = "label_%s_%s.%s" % (master_tracking_number, child_tracking_number, GENERATE_IMAGE_TYPE.lower())

				saved_file = save_file(file_name, label_binary_data, self.doctype, self.name, is_private=1)

				labels.append(saved_file.file_url)

		for i, path in enumerate(labels):
			i +=1
			frappe.db.set(self, 'label_' + str(i+1), path)

		# =====================================================

		delivery_time = estimate_delivery_time(OriginPostalCode='M5V 3A4',
									      OriginCountryCode='CA',
									      DestinationPostalCode='27577',
									      DestinationCountryCode='US')

		rate = get_package_rate(DropoffType='REGULAR_PICKUP',
								    ServiceType='FEDEX_GROUND',
								    PackagingType = 'YOUR_PACKAGING',
									 ShipperStateOrProvinceCode='SC',
									 ShipperPostalCode = '29631',
									 ShipperCountryCode='US',
									 RecipientStateOrProvinceCode='NC',
									 RecipientPostalCode='27577',
									 RecipientCountryCode='US',
									 EdtRequestType='NONE',
									 PaymentType='SENDER',
									 package_list=[{'weight_value':1.0,
													'weight_units':"LB",
													'physical_packaging':'BOX',
													'group_package_count' : 1}])

		frappe.db.set(self, 'delivery_time', delivery_time)
		frappe.db.set(self, 'rate', "%s (%s)" % (rate["Amount"], rate["Currency"]))

		# -----------------------------------------------

		frappe.msgprint("DONE!", "Tracking number:{}".format(master_tracking_number))



