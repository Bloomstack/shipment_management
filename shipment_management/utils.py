import json
import unicodedata
from collections import defaultdict

import pycountry

import frappe
from frappe import _


class InvalidStateError(Exception):
	pass


def get_state_code(address):
	if not (address.get("state") and address.get("country")):
		return

	if frappe.db.exists("Country", {"code": address.get("country")}):
		country_code = address.get("country")
	else:
		country_code = get_country_code(address.get("country"))

	country_code = country_code.upper()

	# Ignore countries without any states or subdivisions
	countries_without_states = []
	for country in pycountry.countries:
		state_count = pycountry.subdivisions.get(country_code=country.alpha_2)

		if len(state_count) == 0:
			countries_without_states.append(country.alpha_2)

	if country_code in countries_without_states:
		return

	# Handle special characters in state names
	# https://docs.python.org/2/library/unicodedata.html#unicodedata.normalize
	def normalize_characters(state_name):
		nfkd_form = unicodedata.normalize("NFKD", state_name)
		return nfkd_form.encode("ASCII", "ignore")

	error_message = _("{} is not a valid state! Check for typos or enter the ISO code for your state.")
	error_message = error_message.format(normalize_characters(address.get("state")))

	state = address.get("state").upper().strip()

	# Convert full ISO code formats (US-FL)
	# to simple state codes (FL)
	if "{}-".format(country_code) in state:
		state = state.split("-")[1]

	# Form a list of state names and codes for the selected country
	states = pycountry.subdivisions.get(country_code=country_code)
	state_details = {pystate.name.upper(): pystate.code.split('-')[1] for pystate in states}

	for state_name, state_code in state_details.items():
		normalized_state = normalize_characters(state_name)

		if normalized_state not in state_details:
			state_details[normalized_state] = state_code

	# Check if the input string (full name or state code) is in the formed list
	if state in state_details:
		return state_details.get(state)
	elif state in state_details.values():
		return state

	frappe.throw(error_message, InvalidStateError)


def get_country_code(country):
	return frappe.db.get_value("Country", country, "code")


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
