import frappe

from shipment_management.email_controller import send_email, get_content_picked_up, get_content_completed, get_content_cancel, get_content_fail
from test_fedex import TestShipmentBase, get_delivery_note, delete_from_db


class TestCaseEmail(TestShipmentBase):

	def setUp(self):
		self.note = frappe.new_doc("DTI Shipment Note")
		self.note_list = []

		delivery_note, items = get_delivery_note(amount_of_items=1)

		for i, item in enumerate(items):
			item.insurance = 0
			item.qty = 1
			item.weight_value = 2
			item.weight_units = 'LB'

		self.note.update({"delivery_note": delivery_note,
						  "international_shipment": False,
						  "service_type_domestic": "FEDEX_2_DAY",
						  "recipient_contact_person_name": "George",
						  "recipient_company_name": "Fantastic Book shop",
						  "recipient_contact_phone_number": "0234876",
						  "recipient_address_street_lines": "b/t 24th St & 23rd St Potrero Hill",
						  "recipient_address_city": "Minnesota",
						  "recipient_address_state_or_province_code": "MN",
						  "recipient_address_country_code": "US",
						  "recipient_address_postal_code": "55037",
						  "contact_email": "katerina@digithinkit.com",
						  "shipper_contact_person_name": "Terry Gihtrer-Assew",
						  "shipper_company_name": "JH Audio Company",
						  "shipper_contact_phone_number": "12345678",
						  "shipper_address_street_lines": "St & 230rd St Terropty Hill",
						  "shipper_address_city": "Florida",
						  "shipper_address_state_or_province_code": "FL",
						  "shipper_address_country_code": "US",
						  "shipper_address_postal_code": "32216",
						  "delivery_items": items,
						  })

		self.add_to_box(items_to_ship_in_one_box=self.note.delivery_items)

		self.submit_and_validate()

		self.note.save()

		self.note_list.append(self.note)

	def test_email_configuration(self):

		message = get_content_picked_up(self.note)
		send_email(message=message,
				   subject="Shipment to %s [%s] - Picked UP" % (self.note.recipient_company_name,
																self.note.name),
				   recipient_list=self.note.contact_email.split(","))

		message = get_content_completed(self.note)
		send_email(message=message,
				   subject="Shipment to %s [%s] - Completed" % (self.note.recipient_company_name,
																self.note.name),
				   recipient_list=self.note.contact_email.split(","))

		message = get_content_cancel(self.note)
		send_email(message=message,
				   subject="Shipment to %s [%s] - Cancelled" % (self.note.recipient_company_name,
																self.note.name),
				   recipient_list=self.note.contact_email.split(","))

		message = get_content_fail(self.note)
		send_email(message=message,
				   subject="Shipment to %s [%s] - Failed" % (self.note.recipient_company_name,
															 self.note.name),
				   recipient_list=self.note.contact_email.split(","))

