# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest
import random
import string
import frappe
import datetime


from shipment_management.shipment import *


def generate_random_string(amount_of_symbols=50000):
	return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(amount_of_symbols))


def delete_from_db(doc_type_table, key, value):
	frappe.db.sql('DELETE from `%s` WHERE %s="%s"' % (doc_type_table, key, value))


def get_count_from_db(table_name):
	return frappe.db.sql('SELECT COUNT(*) FROM `%s`' % table_name)[0][0]


def _print_debug_message():
	print "=" * 70
	print "Amount of Delivery Note             = ", get_count_from_db('tabDelivery Note')
	print "Amount of DTI Fedex Configuration   = ", get_count_from_db('tabDTI Fedex Configuration')
	print "=" * 70


def setUpModule():
	print "\nBefore test execution:"
	_print_debug_message()


def tearDownModule():
	print "\nAfter test execution (and clean up):"
	
	frappe.clear_cache()
	_print_debug_message()


class TestCaseFedexAPI(unittest.TestCase):

	def tests_tracking_number_validation(self):
		response = get_html_code_status_with_fedex_tracking_number(track_value="1111111111")
		self.assertNotIn("Authentication Failed", response)

	def tests_get_package_rate_for_one_package(self):

		response = get_package_rate(DropoffType='REGULAR_PICKUP',
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

		self.assertEqual(response['Currency'], "USD")
		self.assertEqual(response['Amount'], 10.25)

	def tests_get_package_rate_for_two_packages(self):
		response = get_package_rate(DropoffType='REGULAR_PICKUP',
									ServiceType='FEDEX_GROUND',
									PackagingType='YOUR_PACKAGING',
									ShipperStateOrProvinceCode='SC',
									ShipperPostalCode='29631',
									ShipperCountryCode='US',
									RecipientStateOrProvinceCode='NC',
									RecipientPostalCode='27577',
									RecipientCountryCode='US',
									EdtRequestType='NONE',
									PaymentType='SENDER',
									package_list=[{'weight_value': 1.0,
												   'weight_units': "LB",
												   'physical_packaging': 'BOX',
												   'group_package_count': 1},
												  {'weight_value': 1.0,
												   'weight_units': "LB",
												   'physical_packaging': 'BOX',
												   'group_package_count': 1}])

		self.assertEqual(response['Currency'], "USD")
		self.assertEqual(response['Amount'], 20.5)

	def tests_estimate_delivery_time(self):
		response = estimate_delivery_time(OriginPostalCode='M5V 3A4',
									      OriginCountryCode='CA',
									      DestinationPostalCode='27577',
									      DestinationCountryCode='US')

		try:
			datetime.datetime.strptime(response, "%Y-%m-%d")
		except ValueError as err:
			self.fail("Invalid response!" % err)

	def tests_define_carriers_list(self):
		response = get_carriers_list()
		self.assertEqual(len(response), 1)
		self.assertEqual(response[0], "Fedex")


class TestDTIFedexConfiguration(unittest.TestCase):
	def test_creation(self):
		fedex_config = frappe.new_doc("DTI Fedex Configuration")

		fedex_config.fedex_config_name = "TestFedexName"
		fedex_config.fedex_key = "TestKey"
		fedex_config.password = "TestPassword"
		fedex_config.account_number = "TestAccountNumber"
		fedex_config.meter_number = "TestMeterNumber"
		fedex_config.freight_account_number = "FreightAccountNumber"
		fedex_config.use_test_server = False

		fedex_config.save()

		delete_from_db(doc_type_table="tabDTI Fedex Configuration", key='name', value=fedex_config.fedex_config_name)

		



