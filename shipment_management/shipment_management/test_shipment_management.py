
from __future__ import unicode_literals


import unittest

import random
import string
import frappe
import logging

from frappe.utils import today
from frappe.utils.make_random import get_random


from shipment_management.provider_fedex import parse_items_in_box, get_item_by_item_code


def generate_random_string(amount_of_symbols=50000):
	return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(amount_of_symbols))


def delete_from_db(doc_type_table, key, value):
	frappe.db.sql('DELETE from `%s` WHERE %s="%s"' % (doc_type_table, key, value))


def get_count_from_db(table_name):
	return frappe.db.sql('SELECT COUNT(*) FROM `%s`' % table_name)[0][0]


def _print_debug_message():
	print "=" * 70
	print "Amount of Delivery Note             = ", get_count_from_db('tabDelivery Note')
	print "Amount of DTI Shipment Note         = ", get_count_from_db('tabDTI Shipment Note')
	print "Amount of DTI Shipment Note Item    = ", get_count_from_db('tabDTI Shipment Note Item')
	print "Amount of DTI Shipment Package      = ", get_count_from_db('tabDTI Shipment Package')
	print "Amount of DTI Fedex Configuration   = ", get_count_from_db('tabDTI Fedex Configuration')

	print "=" * 70


def get_boxes(shipment_note_name):
	return frappe.db.sql('''SELECT * from `tabDTI Shipment Package` WHERE parent="%s"''' % shipment_note_name, as_dict=True)


def get_attached_labels_count(tracking_number):
	response = frappe.db.sql("""select file_url, file_name from tabFile WHERE file_name LIKE '%{}%'""".format(tracking_number),
							 as_dict=True)
	return len(response)


def get_delivery_note(amount_of_items):
	# TODO Create delivery note with item in tests!!!

	delivery_note = get_random("Delivery Note")

	all_delivery_items = frappe.db.sql('''SELECT * from `tabDelivery Note Item`''', as_dict=True)

	items_list = []
	for i in xrange(1000):
		if all_delivery_items[i].item_code not in [item.item_code for item in items_list]:
			items_list.append(all_delivery_items[i])
			if len(items_list) == amount_of_items:
				break

	assert items_list, "Delivery Note Items are absent for testing"

	return delivery_note, items_list


###########################################################################
###########################################################################
###########################################################################

def setUpModule():
	print "\nBefore test execution:"
	_print_debug_message()

	# -------------------------------
	logger = logging.getLogger('fedex')
	ch = logging.StreamHandler()
	ch.setLevel(logging.ERROR)
	logger.setLevel(logging.ERROR)
	logger.addHandler(ch)


def tearDownModule():
	print "\nAfter test execution (and clean up):"

	frappe.clear_cache()
	_print_debug_message()

###########################################################################
###########################################################################
###########################################################################

class TestDocTypes(unittest.TestCase):
	def test_fedex_configuration(self):
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

###########################################################################


class TestShipmentInternational(unittest.TestCase):

	def setUp(self):
		self.note_list = []

	# def tearDown(self):
	#
	# 	for note in self.note_list:
	#	    delete_fedex_shipment(note)
	# 		delete_from_db(doc_type_table="tabDTI Shipment Note", key='name', value=note.name)
	# 		delete_from_db(doc_type_table="tabDTI Shipment Note Item", key='parent', value=note.name)
	# 		delete_from_db(doc_type_table="tabDTI Shipment Package", key='parent', value=note.name)

	def get_saved_international_shipment_note(self, type, test_data_for_items=[]):

		print "\n=================== %s =============================" % type

		self.note = frappe.new_doc("DTI Shipment Note")

		delivery_note, items = get_delivery_note(amount_of_items=len(test_data_for_items))

		for i, item in enumerate(items):

			item.custom_value = test_data_for_items[i]['custom_value']
			item.insurance = test_data_for_items[i]['insurance']
			item.qty = test_data_for_items[i]['quantity']

		self.note.update({"delivery_note": delivery_note,
					 "international_shipment": True,
					 "service_type_international": type,
					 "recipient_contact_person_name": "Jeniffer Lopes",
					 "recipient_company_name": "Some Company",
					 "recipient_contact_phone_number": "676786786876",
					 "recipient_address_street_lines": "test test",
					 "recipient_address_city": "Kiev",
					 "recipient_address_state_or_province_code": "",
					 "recipient_address_country_code": "UA",
					 "recipient_address_postal_code": "02140",
					 "contact_email": "1234567@gmail.com",
					 "shipper_contact_person_name": "Bora Bora",
					 "shipper_company_name": "Katerina",
					 "shipper_contact_phone_number": "12345678",
					 "shipper_address_street_lines": "Street 123456",
					 "shipper_address_city": "Herndon",
					 "shipper_address_state_or_province_code": "VA",
					 "shipper_address_country_code": "US",
					 "shipper_address_postal_code": "20171",
					 "delivery_items": items,
					 })

		self.note.save()

		print "NOTE :", self.note.name

		self.note_list.append(self.note)

	def validation_for_insurance_and_custom_value(self, source_doc):

		expected_all_shipment_insurance = 0
		expected_all_shipment_custom_value = 0

		for box in source_doc.box_list:

			expected_box_insurance = 0
			expected_box_custom_value = 0

			items = parse_items_in_box(box)

			for item in items:

				quantity_in_box = items[item]

				item = get_item_by_item_code(source_doc=source_doc, item_code=item)

				expected_item_insurance = item.insurance * quantity_in_box
				expected_item_custom_value = item.custom_value * quantity_in_box

				expected_box_insurance += expected_item_insurance
				expected_box_custom_value += expected_item_custom_value

			self.assertEqual(box.total_box_custom_value, expected_box_custom_value)
			self.assertEqual(box.total_box_insurance, expected_box_insurance)

			expected_all_shipment_insurance += expected_box_insurance
			expected_all_shipment_custom_value += expected_box_custom_value

		self.assertEqual(source_doc.total_insurance, expected_all_shipment_insurance)
		self.assertEqual(source_doc.total_custom_value, expected_all_shipment_custom_value)

	def submit_and_validate(self):
		self.assertEqual(self.note.tracking_number, "0000-0000-0000-0000")
		self.assertEqual(self.note.shipment_note_status, "NEW")
		self.assertIsNone(self.note.commodity_information)
		self.assertIsNone(self.note.label_1)

		self.note.submit()

		self.assertNotEqual(self.note.tracking_number, "0000-0000-0000-0000")
		self.assertEqual(self.note.shipment_note_status, "ReadyToPickUp")
		self.assertIn("THE PACKAGE # 1 ", unicode(self.note.commodity_information))

		self.assertEqual(get_attached_labels_count(tracking_number=self.note.tracking_number),
						 len(self.note.get_all_children("DTI Shipment Package")))

		self.validation_for_insurance_and_custom_value(source_doc=self.note)

	def validate_error_during_shipment_creation(self, expected_error_message):
		print "EXPECTED ERROR:", expected_error_message
		try:
			self.submit_and_validate()
			self.fail("Shipment was created successful with wrong data")
		except frappe.ValidationError as error:
			if expected_error_message not in str(error):
				self.fail("Wrong expected error: %s" % error)

	def add_to_box(self, weight_value=3,
						 weight_units="LB",
						 physical_packaging="BOX",
				         items_to_ship_in_one_box=[]):

		self.note.append("box_list", {"weight_value": weight_value,
									  "weight_units": weight_units,
									  "physical_packaging": physical_packaging,
									  "items_in_box": "\n".join(r"{}:{}".format(item.item_code,
																				int(item.qty))
																for item in items_to_ship_in_one_box)})

	# ############################################################################################
	#
	# def test_shipment_note_1(self):
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[{'custom_value':70,
	# 																		 'insurance':50,
	# 																		 'quantity':5}])
	#
	# 		self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items)
	#
	# 		self.submit_and_validate()
	#
	# def test_shipment_note_2(self):
	#
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[{'custom_value': 70,
	# 																		 'insurance': 0,
	# 																		 'quantity': 5}])
	#
	# 		self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items)
	#
	# 		self.submit_and_validate()
	#
	# def test_shipment_note_3(self):
	#
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[{'custom_value': 0,
	# 																		 'insurance': 0,
	# 																		 'quantity': 5}])
	#
	# 		self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items)
	#
	# 		self.validate_error_during_shipment_creation(expected_error_message="CUSTOM VALUE = 0")
	#
	# def test_shipment_note_4(self):
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[{'custom_value': 5,
	# 																		 'insurance': 10,
	# 																		 'quantity': 5}])
	#
	# 		self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items)
	#
	# 		self.validate_error_during_shipment_creation(expected_error_message=
	# 													 "Total Insured value exceeds customs value (Error code: 2519)")
	#
	# def test_shipment_note_5(self):
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[{'custom_value': 8, 'insurance': 6, 'quantity': 2},
	# 																		{'custom_value': 7, 'insurance': 2, 'quantity': 5},
	# 																		{'custom_value': 6, 'insurance': 5, 'quantity': 4},
	# 																		{'custom_value': 6, 'insurance': 5,'quantity': 4}])
	#
	# 		self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items)
	#
	# 		self.submit_and_validate()
	#
	# def test_shipment_note_6(self):
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[
	# 													   {'custom_value': 3, 'insurance': 1, 'quantity': 5},
	# 													   {'custom_value': 3, 'insurance': 1, 'quantity': 5},
	# 													   {'custom_value': 3, 'insurance': 1, 'quantity': 5},
	# 													   {'custom_value': 3, 'insurance': 1, 'quantity': 5}])
	#
	#
	# 		for i in xrange(4):
	# 			self.add_to_box(items_to_ship_in_one_box=[self.note.delivery_items[i]])
	#
	# 		self.submit_and_validate()
	#
	# def test_shipment_note_7(self):
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[
	# 													   {'custom_value': 3, 'insurance': 1, 'quantity': 5},
	# 													   {'custom_value': 5, 'insurance': 3, 'quantity': 5},
	# 													   {'custom_value': 3, 'insurance': 1, 'quantity': 5},
	# 													   {'custom_value': 5, 'insurance': 3, 'quantity': 5},
	# 													   {'custom_value': 5, 'insurance': 3, 'quantity': 5},
	# 													   {'custom_value': 6, 'insurance': 4, 'quantity': 4},
	# 													   {'custom_value': 10, 'insurance': 9, 'quantity': 4}])
	#
	# 		for i in xrange(7):
	# 			self.add_to_box(items_to_ship_in_one_box=[self.note.delivery_items[i]])
	#
	# 		self.submit_and_validate()
	#
	# def test_shipment_note_8(self):
	# 	for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
	# 		self.get_saved_international_shipment_note(type=ship_type,
	# 												   test_data_for_items=[{'custom_value': 2501,
	# 																		 'insurance': 2501, 'quantity': 1}])
	#
	# 		self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items)
	#
	# 		self.submit_and_validate()

	def test_shipment_note_9(self):
		for ship_type in ['INTERNATIONAL_PRIORITY', 'INTERNATIONAL_ECONOMY']:
			self.get_saved_international_shipment_note(type=ship_type,
													   test_data_for_items=[
														   {'custom_value': 8, 'insurance': 6, 'quantity': 2},
														   {'custom_value': 7, 'insurance': 2, 'quantity': 5},
														   {'custom_value': 6, 'insurance': 5, 'quantity': 4},
														   {'custom_value': 6, 'insurance': 5, 'quantity': 2}])

			self.add_to_box(items_to_ship_in_one_box=[self.note.delivery_items[0]])
			self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items[1:3])
			self.add_to_box(items_to_ship_in_one_box=[self.note.delivery_items[3]])

			self.submit_and_validate()

if __name__ == '__main__':
	unittest.main()
