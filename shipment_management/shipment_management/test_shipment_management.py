
from __future__ import unicode_literals


import unittest

from shipment_management.shipment import *
from shipment_management.email_controller import send_email, get_content_picked_up
from frappe.model.document import get_doc


class TestCaseAddress(unittest.TestCase):

	def test_email_configuration(self):
		#get_recipient(delivery_note_name='DN-00048')
		#get_shipper(delivery_note_name='DN-00048')

		shipment_note = get_doc("DTI Shipment Note",  "SHIP-00350")

		message = get_content_picked_up(shipment_note)
		send_email(message=message,
					subject="Shipment to %s [%s] - Picked UP" % (shipment_note.recipient_company_name,
																			  shipment_note.name),
					recipient_list=shipment_note.contact_email.split(","))


if __name__ == '__main__':
	unittest.main()
