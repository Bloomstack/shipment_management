# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.model.document import get_doc


def get_sender_email():
	email = frappe.db.sql('''SELECT * from `tabEmail Account` WHERE default_outgoing=1''', as_dict=True)
	if email:
		return email[0].email_id
	else:
		frappe.throw(_("Default outgoing email is absent!"))


def send_email(message, subject, recipient_list):
	frappe.sendmail(recipients=set(recipient_list),
					sender=get_sender_email(),
					subject=subject,
					message=message)


################################################################
################################################################
################################################################


def get_content_picked_up(shipment_note):

	address_string = """<b>Street Lines:</b> {0} <br>
		<b>City:</b> {1} <br>
		<b>StateOrProvinceCode :</b> {2} <br>
		<b>PostalCode :</b> {3} <br>
		<b>CountryCode :</b> {4}""".format(
		shipment_note.recipient_address_street_lines,
		shipment_note.recipient_address_city,
		shipment_note.recipient_address_state_or_province_code,
		shipment_note.recipient_address_postal_code,
		shipment_note.recipient_address_country_code)

	shipment_source = get_doc("DTI Shipment Note", shipment_note.name)

	items = shipment_source.get_all_children("DTI Shipment Note Item")

	items_html = """
	<style>
	table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
    padding: 5px;
    text-align: left;
    background-color: #f1f1c1;
    }
	</style>
	<table>"""

	items_html += "<tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th></tr>".format("Name",
																					 "Item code",
																					 "Qty",
																					 "Description")

	for item in items:
		items_html += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>".format(item.item_name,
																						 item.item_code,
																						 item.qty,
																						 item.description.encode(
																							 'ascii', 'ignore').decode(
																							 'ascii'))

	items_html += "</table>"

	if shipment_note.international_shipment:
		service_type = shipment_note.service_type_international

	else:
		service_type = shipment_note.service_type_domestic

	return frappe.render_template("templates/email/picked_up.html",
								  {"customer_name": shipment_note.recipient_company_name,
								   "shipment_note_address": address_string,
								   "items": items_html,
								   "sales_order_id": shipment_note.sales_order,
								   "delivery_note": shipment_note.delivery_note,
								   "carrier_name": shipment_note.shipment_provider,
								   "delivery_type": service_type,
								   "rate": shipment_note.shipment_rate,
								   "tracking_number": shipment_note.tracking_number,
								   "delivery_time": shipment_note.delivery_time})


def get_content_completed(shipment_note):

	template_completed = frappe.render_template("templates/email/completed.html",
												{"customer_name": shipment_note.recipient_company_name,
												 "sales_order_id": shipment_note.sales_order,
												 "delivery_note": shipment_note.delivery_note,
												 "tracking_number": shipment_note.tracking_number})
	return template_completed


def get_content_cancel(shipment_note):

	return frappe.render_template("templates/email/cancel.html",
								  {"customer_name": shipment_note.recipient_company_name,
								   "sales_order_id": shipment_note.sales_order,
								   "delivery_note": shipment_note.delivery_note,
								   "tracking_number": shipment_note.tracking_number})


def get_content_fail(shipment_note, error_from_fedex="Delivery has been failed"):

	return frappe.render_template("templates/email/fail.html",
								  {"customer_name": shipment_note.recipient_company_name,
								   "sales_order_id": shipment_note.sales_order,
								   "delivery_note": shipment_note.delivery_note,
								   "tracking_number": shipment_note.tracking_number,
								   "shipment_note": shipment_note.name,
								   "error": error_from_fedex})