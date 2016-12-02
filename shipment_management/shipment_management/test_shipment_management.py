
from __future__ import unicode_literals


import unittest
import datetime

from shipment_management.shipment import *
from shipment_management.email_controller import send_email, get_content_picked_up, get_content_completed, get_content_cancel, get_content_fail
from shipment_management.provider_fedex import get_html_code_status_with_fedex_tracking_number, get_package_rate, estimate_delivery_time
from shipment_management.config.app_config import SupportedProviderList

# TODO - Test in progress !!!


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
													'group_package_count' : 1,
													'insured_amount':100}])

		self.assertEqual(response['Currency'], "USD")
		self.assertEqual(response['Amount'], 10.27)

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
												   'group_package_count': 1,
												   'insured_amount': 100},
												  {'weight_value': 1.0,
												   'weight_units': "LB",
												   'physical_packaging': 'BOX',
												   'group_package_count': 1,
												   'insured_amount': 100}])

		self.assertEqual(response['Currency'], "USD")
		self.assertEqual(response['Amount'], 20.54)

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
		self.assertEqual(response[0], SupportedProviderList.Fedex)


##########################################################################


class TestCaseAddress(unittest.TestCase):

	#def test_temp(self):
		#status = get_fedex_shipment_status("111111111111")

		#shipment_note = get_doc("DTI Shipment Note", "SHIP-00352")

		# for i in xrange(3):
		# 	print "_______________"
		# 	print "# ", i
		# 	shipment_status_update_controller()
		# 	import time
		# 	time.sleep(5)

		# if status == 'HP':
		# 	message = get_content_picked_up(shipment_note)
		# 	send_email(message=message,
		# 			   subject="Shipment to %s [%s] - Picked UP" % (shipment_note.recipient_company_name,
		# 															shipment_note.name),
		# 			   recipient_list=shipment_note.contact_email.split(","))


		# if status == 'PU':
		# 	message = get_content_picked_up(shipment_note)
		# 	send_email(message=message,
		# 			   subject="Shipment to %s [%s] - Picked UP" % (shipment_note.recipient_company_name,
		# 															shipment_note.name),
		# 			   recipient_list=shipment_note.contact_email.split(","))

		#
		# status = 'DL'
		# print StatusMapFedexAndShipmentNote.Completed, type(StatusMapFedexAndShipmentNote.Completed)
		#
		# statuses = [i.status_code for i in StatusMapFedexAndShipmentNote.Completed]
		#
		# if status in statuses:
		#
		# 	message = get_content_completed(shipment_note)
		# 	send_email(message=message,
		# 			   subject="Shipment to %s [%s] - Completed" % (shipment_note.recipient_company_name,
		# 															shipment_note.name),
		# 			   recipient_list=shipment_note.contact_email.split(","))



		#######################

	def test_email_configuration(self):
		#get_recipient(delivery_note_name='DN-00048')
		#get_shipper(delivery_note_name='DN-00048')

		shipment_note = get_doc("DTI Shipment Note",  "SHIP-00007")

		message = get_content_picked_up(shipment_note)
		send_email(message=message,
					subject="Shipment to %s [%s] - Picked UP" % (shipment_note.recipient_company_name,
																			  shipment_note.name),
					recipient_list=shipment_note.contact_email.split(","))

		message = get_content_completed(shipment_note)
		send_email(message=message,
					subject="Shipment to %s [%s] - Completed" % (shipment_note.recipient_company_name,
																 shipment_note.name),
					recipient_list=shipment_note.contact_email.split(","))


		message = get_content_cancel(shipment_note)
		send_email(message=message,
				   subject="Shipment to %s [%s] - Cancelled" % (shipment_note.recipient_company_name,
																shipment_note.name),
				   recipient_list=shipment_note.contact_email.split(","))

		message = get_content_fail(shipment_note)
		send_email(message=message,
				   subject="Shipment to %s [%s] - Failed" % (shipment_note.recipient_company_name,
																shipment_note.name),
				   recipient_list=shipment_note.contact_email.split(","))
	#
	# 	resp = get_fedex_shipment_status("111111111111")
	# 	print resp



# =======================================================================

# # Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# # See license.txt
# from __future__ import unicode_literals
#
# import unittest
# import random
# import string
# import frappe
# import datetime
#
#
# from shipment_management.shipment import *
#
#
# def generate_random_string(amount_of_symbols=50000):
# 	return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(amount_of_symbols))
#
#
# def delete_from_db(doc_type_table, key, value):
# 	frappe.db.sql('DELETE from `%s` WHERE %s="%s"' % (doc_type_table, key, value))
#
#
# def get_count_from_db(table_name):
# 	return frappe.db.sql('SELECT COUNT(*) FROM `%s`' % table_name)[0][0]
#
#
# def _print_debug_message():
# 	print "=" * 70
# 	print "Amount of Delivery Note             = ", get_count_from_db('tabDelivery Note')
# 	print "Amount of DTI Fedex Configuration   = ", get_count_from_db('tabDTI Fedex Configuration')
# 	print "=" * 70
#
#
# def setUpModule():
# 	print "\nBefore test execution:"
# 	_print_debug_message()
#
#
# def tearDownModule():
# 	print "\nAfter test execution (and clean up):"
#
# 	frappe.clear_cache()
# 	_print_debug_message()
#
#
#
# class TestDTIFedexConfiguration(unittest.TestCase):
# 	def test_creation(self):
# 		fedex_config = frappe.new_doc("DTI Fedex Configuration")
#
# 		fedex_config.fedex_config_name = "TestFedexName"
# 		fedex_config.fedex_key = "TestKey"
# 		fedex_config.password = "TestPassword"
# 		fedex_config.account_number = "TestAccountNumber"
# 		fedex_config.meter_number = "TestMeterNumber"
# 		fedex_config.freight_account_number = "FreightAccountNumber"
# 		fedex_config.use_test_server = False
#
# 		fedex_config.save()
#
# 		delete_from_db(doc_type_table="tabDTI Fedex Configuration", key='name', value=fedex_config.fedex_config_name)
#
#
#
#
#
# import unittest
# from shipment_management.shipment import *
#
#
# class TestDeliveryNote(unittest.TestCase):
#     def test_status_completed(self):
#         delivery_note_status_sync(target_doc="", status = DeliveryNoteOperationalStatus.Completed)
#
#         note = get_related_shipment_note()
#         package = get_related_shipment_package()
#         fedex_shipment = get_related_fedex_shipment()
#
#         self.assertEqual(note.status, DocTypeStatus.Submitted)
#         self.assertEqual(note.shipment_status, ShipmentNoteOperationalStatus.Completed)
#
#         self.assertEqual(package.status, DocTypeStatus.Submitted)
#         self.assertEqual(package.shipment_status, ShipmentNoteOperationalStatus.Completed)
#
#         self.assertEqual(fedex_shipment.status, DocTypeStatus.Submitted)
#         self.assertEqual(fedex_shipment.shipment_status, ShipmentNoteOperationalStatus.Completed)
#
#     def test_status_canceled(self):
#         pass
#
#     def test_status_closed(self):
#         pass
#
#
# class TestShipmentNote(unittest.TestCase):
#     def test_status_completed(self):
#         pass
#
#     def test_status_canceled(self):
#         pass
#
#     def test_status_failed(self):
#         pass
#
#     def test_status_returned(self):
#         pass
#
#
# class TestFedexShipment(unittest.TestCase):
#     def test_status_completed(self):
#         pass
#
#     def test_status_canceled(self):
#         fedex_shipment_status_sync
#
#
# if __name__ == '__main__':
#       unittest.main()


#############################

# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt
# from __future__ import unicode_literals
#
# import unittest
# import random
# import string
# import frappe
#
# from frappe.utils import today
# from shipment_management.shipment import *
#
#
# def setup_currency_exchange():
# 	frappe.get_doc({
# 		'doctype': 'Currency Exchange',
# 		'from_currency': 'UAH',
# 		'to_currency': 'INR',
# 		'exchange_rate': 1.13
# 	}).insert()
#
# # def create_customer():
# # 	pass
# #
# #
# # def create_warehouse():
# # 	wh = frappe.new_doc("Warehouse")
# #
# # 	wh.append({
# # 		"company": "Coca Cola",
# # 		"doctype": "Warehouse",
# # 		"warehouse_name": "_Test Warehouse",
# # 		"is_group": 0,
# # 		"parent_warehouse": "_Test Warehouse Group - _TC"
# # 	})
# #
# # 	wh.submit()
#
#
# def create_delivery_note(**args):
# 	dn = frappe.new_doc("Delivery Note")
# 	args = frappe._dict(args)
# 	dn.posting_date = args.posting_date or today()
# 	if args.posting_time:
# 		dn.posting_time = args.posting_time
#
# 	# create_company()
# 	#
# 	dn.company = args.company or "_Test Company"
# 	dn.customer = args.customer or "_Test Customer"
#
# 	company_currency = frappe.db.get_value("Company", dn.company, "default_currency", cache=True)
#
# 	dn.currency = company_currency
#
# 	dn.is_return = args.is_return
# 	dn.return_against = args.return_against
#
# 	dn.append("items", {
# 		"item_code": args.item or args.item_code or "_Test Item",
# 		"warehouse": args.warehouse or "_Test Warehouse - _TC",
# 		"qty": 1,
# 		"rate": 100,
# 		"conversion_factor": 1.0,
# 		"expense_account": "Cost of Goods Sold - _TC",
# 		"cost_center": "_Test Cost Center - _TC",
# 		"serial_no": args.serial_no,
# 		"target_warehouse": args.target_warehouse
# 	})
#
# 	if not args.do_not_save:
# 		dn.insert()
# 		if not args.do_not_submit:
# 			dn.submit()
# 	return dn
#
#
# def generate_random_string(amount_of_symbols=50000):
# 	return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(amount_of_symbols))
#
#
# def delete_from_db(doc_type_table, key, value):
# 	frappe.db.sql('DELETE from `%s` WHERE %s="%s"' % (doc_type_table, key, value))
#
#
# def get_count_from_db(table_name):
# 	return frappe.db.sql('SELECT COUNT(*) FROM `%s`' % table_name)[0][0]
#
#
# def _print_debug_message():
# 	print "=" * 70
# 	print "Amount of Delivery Note             = ", get_count_from_db('tabDelivery Note')
# 	print "Amount of DTI Shipment Note         = ", get_count_from_db('tabDTI Shipment Note')
# 	print "Amount of DTI Shipment Note Item    = ", get_count_from_db('tabDTI Shipment Note Item')
# 	print "Amount of DTI Shipment Package      = ", get_count_from_db('tabDTI Shipment Package')
# 	print "Amount of DTI Fedex Configuration   = ", get_count_from_db('tabDTI Fedex Configuration')
# 	print "Amount of DTI Fedex Shipment        = ", get_count_from_db('tabDTI Fedex Shipment')
# 	print "Amount of DTI Fedex Shipment Item   = ", get_count_from_db('tabDTI Fedex Shipment Item')
# 	print "=" * 70
#
#
# def setUpModule():
# 	print "\nBefore test execution:"
# 	_print_debug_message()
#
# 	if not frappe.db.exists("Currency Exchange", 'UAH-INR'):
# 		setup_currency_exchange()
#
#
# def tearDownModule():
# 	print "\nAfter test execution (and clean up):"
#
# 	frappe.clear_cache()
# 	_print_debug_message()
#
#
# class TestCaseAddress(unittest.TestCase):
# 	def __test_recipient(self):
# 		# TODO create delivery note for testing
#
# 		get_recipient(delivery_note_name='DN-00007')
#
# 	def test_shipper(self):
# 		# TODO create delivery note for testing
#
# 		#dn = create_delivery_note()
# 		#get_shipper(delivery_note_name=dn.name)
# 		pass


if __name__ == '__main__':
	unittest.main()
