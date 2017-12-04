import json
from collections import defaultdict

import pycountry

import frappe
from frappe import _


def get_state_code(address):
	if not address.get("state"):
		return

	valid_state = True

	try:
		state = pycountry.subdivisions.lookup(address.get("state"))
	except LookupError:
		valid_state = False
	else:
		# pycountry returns state code as {country}-{state} (e.g., US-FL)
		return state.code.split('-')[1]

	if not valid_state and len(address.get("state")) == 2:
		try:
			country = pycountry.countries.lookup(address.get("country"))
		except LookupError:
			pass
		else:
			state_iso = "{}-{}".format(str(country.alpha_2), address.get("state"))

			try:
				state = pycountry.subdivisions.lookup(state_iso)
			except LookupError:
				pass
			else:
				return state.code.split('-')[1]

	if not valid_state:
		error_message = """{} is not a valid state!
						Check for typos or enter the
						2-letter ISO code for your state."""

		frappe.throw(_(error_message.format(address.get("state"))))

def get_country_code(country):
	return frappe.get_value("Country", country, "code")


@frappe.whitelist()
def create_shipment_note(items, item_dict, doc):
	from shipment import get_recipient_details, get_shipper_details, get_delivery_items

	items = json.loads(items)
	item_dict = json.loads(item_dict)
	doc = json.loads(doc)
	box_list = []

	box_items = defaultdict(list)

	for item_idx, item_code in item_dict.items():
		box_items[items[item_idx]].append(item_code + ":1")

	shipment_doc = frappe.new_doc("DTI Shipment Note")
	shipment_doc.delivery_note = doc.get("name")
	for box, items in box_items.items():
		box_list.append({"physical_packaging": "BOX", "items_in_box": "\n".join(items)})

	shipment_doc.extend("box_list", list(reversed(box_list)))

	for field, fielddata in get_recipient_details(doc.get("name")).items():
		setattr(shipment_doc, field, fielddata)

	for field, fielddata in get_shipper_details(doc.get("name")).items():
		setattr(shipment_doc, field, fielddata)

	if shipment_doc.recipient_address_country_code.lower() != "us":
		shipment_doc.international_shipment = 1
		if doc.get("fedex_shipping_method"):
			shipment_doc.service_type_international = doc.get("fedex_shipping_method").replace(" ", "_")
	else:
		if doc.get("fedex_shipping_method"):
			shipment_doc.service_type_domestic = doc.get("fedex_shipping_method").replace(" ", "_")

	for item in get_delivery_items(doc.get("name")):
		if frappe.db.get_value("Item", item.get("item_code"), "is_stock_item"):
			item['weight_value'] = frappe.get_value("Item", item.get("item_code"), "net_weight")
			if shipment_doc.international_shipment:
				if item['rate'] < 400:
					item['insurance'] = item['rate']
				else:
					item['insurance'] = 400
				item['custom_value'] = item.get("rate")
			shipment_doc.append("delivery_items", item)

	shipment_doc.save()
	frappe.db.commit()

	return shipment_doc.name


@frappe.whitelist()
def get_stock_items(items):
	items = json.loads(items)
	stock_items = []
	for item in items:
		if frappe.db.get_value("Item", {"item_code": item.get("item_code")}, "is_stock_item"):
			stock_items.append(item)
	return stock_items


@frappe.whitelist()
def get_packages_in_order(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("select `name`, `box_code` from `tabShipping Package` where name like '%{0}%' ORDER BY `order` ASC".format(txt))
