
	# def test_shipment_note_international(self):
	# 	note_item = frappe.new_doc("DTI Shipment Note")
	#
	# 	delivery_note = get_random("Delivery Note")
	# 	items = get_delivery_items(delivery_note)
	#
	# 	note_item.update({"delivery_note": delivery_note,
	# 					  "international_shipment": True,
	# 					  "recipient_contact_person_name": "Jeniffer Lopes",
	# 					  "recipient_company_name": "Some Company",
	# 					  "recipient_contact_phone_number": "676786786876",
	# 					  "recipient_address_street_lines": "test test",
	# 					  "recipient_address_city": "Kiev",
	# 					  "recipient_address_state_or_province_code": "",
	# 					  "recipient_address_country_code": "UA",
	# 					  "recipient_address_postal_code": "02140",
	# 					  "contact_email": "1234567@gmail.com",
	# 					  "shipper_contact_person_name": "Bora Bora",
	# 					  "shipper_company_name": "Katerina",
	# 					  "shipper_contact_phone_number": "12345678",
	# 					  "shipper_address_street_lines": "Street 123456",
	# 					  "shipper_address_city": "Herndon",
	# 					  "shipper_address_state_or_province_code": "VA",
	# 					  "shipper_address_country_code": "US",
	# 					  "shipper_address_postal_code": "20171",
	# 					  "delivery_items": items,
	# 					  })
	#
	# 	note_item.save()
	#
	# 	delete_from_db(doc_type_table="tabDTI Shipment Note", key='name', value=note_item.name)



###########################################################################

from shipment_management.email_controller import send_email, get_content_picked_up, get_content_completed, get_content_cancel, get_content_fail


# ###############################################################


#
# 		#######################
#
# 	def test_email_configuration(self):
# 		#get_recipient(delivery_note_name='DN-00048')
# 		#get_shipper(delivery_note_name='DN-00048')
#
# 		shipment_note = get_doc("DTI Shipment Note",  "SHIP-00007")
#
# 		message = get_content_picked_up(shipment_note)
# 		send_email(message=message,
# 					subject="Shipment to %s [%s] - Picked UP" % (shipment_note.recipient_company_name,
# 																			  shipment_note.name),
# 					recipient_list=shipment_note.contact_email.split(","))
#
# 		message = get_content_completed(shipment_note)
# 		send_email(message=message,
# 					subject="Shipment to %s [%s] - Completed" % (shipment_note.recipient_company_name,
# 																 shipment_note.name),
# 					recipient_list=shipment_note.contact_email.split(","))
#
#
# 		message = get_content_cancel(shipment_note)
# 		send_email(message=message,
# 				   subject="Shipment to %s [%s] - Cancelled" % (shipment_note.recipient_company_name,
# 																shipment_note.name),
# 				   recipient_list=shipment_note.contact_email.split(","))
#
# 		message = get_content_fail(shipment_note)
# 		send_email(message=message,
# 				   subject="Shipment to %s [%s] - Failed" % (shipment_note.recipient_company_name,
# 																shipment_note.name),
# 				   recipient_list=shipment_note.contact_email.split(","))
# 	#
# 	# 	resp = get_fedex_shipment_status("111111111111")
# 	# 	print resp

# #
# #
