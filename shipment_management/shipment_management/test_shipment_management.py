
from __future__ import unicode_literals

import unittest
import random
import string
import frappe

from frappe.utils import today
from shipment_management.shipment import *
from shipment_management.email_controller import send_email_status_update, TEMPLATE_PickedUP
from doctype.dti_fedex_shipment.dti_fedex_shipment import set_fedex_status


class TestCaseAddress(unittest.TestCase):
	# def __test_recipient(self):
	# 	# TODO create delivery note for testing
	#
	# 	get_recipient(delivery_note_name='DN-00007')
	#
	# def test_shipper(self):
	# 	# TODO create delivery note for testing
	#
	# 	#dn = create_delivery_note()
	# 	get_shipper(delivery_note_name='DN-00007')

	def test_email(self):
		#send_email_status_update("SHIP-00000", TEMPLATE_PickedUP)
		set_fedex_status(fedex_name="6d93a2aaaf", new_status="Picked Up")


if __name__ == '__main__':
	unittest.main()
