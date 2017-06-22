import frappe
import requests
import json
from collections import defaultdict
from frappe import _

def get_state_code(address):
	if len(address.get("state")) == 2:
		return address.get("state")

	URL = "https://maps.googleapis.com/maps/api/geocode/json"
	params = { "address" : " ".join((address.get("pincode", ""),
		address.get("city",
			address.get("state", "")),
				address.get("country", "")))
					}

	r = requests.get(URL, params)
	if r.status_code != 200:
		frappe.throw(_("Error connecting to Google Maps API"))
	
	address_data = r.json().get("results")
	if address_data:
		address_data = address_data[0].get("address_components")
	for address_component in address_data:
		if address_component.get("long_name").lower() == address.get("state").lower():
			# To make sure that state code is either 2 or 3 letters only. 
			# Google API sometimes sends bad data
			if address_component.get("short_name"):
				if len(address_component.get("short_name")) <= 3:
					return address_component.get("short_name")

def get_country_code(country):
	return frappe.get_value("Country", country, "code")



@frappe.whitelist()
def create_shipment_note(items, item_dict, doc):
	from shipment import get_recipient_details, get_shipper_details, get_delivery_items

	items = json.loads(items)
	item_dict = json.loads(item_dict)
	doc = json.loads(doc)

	box_items = defaultdict(list)
	
	for item_idx, item_code in item_dict.items():
		box_items[items[item_idx]].append(item_code + ":1")

	shipment_doc = frappe.new_doc("DTI Shipment Note")
	shipment_doc.delivery_note = doc.get("name")
	for box, items in box_items.items():
		shipment_doc.append("box_list" , {"physical_packaging" : "BOX",
			"items_in_box": "\n".join(items)})

	for field, fielddata in get_recipient_details(doc.get("name")).items():
		setattr(shipment_doc, field, fielddata)

	for field, fielddata in get_shipper_details(doc.get("name")).items():
		setattr(shipment_doc, field, fielddata)	

	if shipment_doc.recipient_address_country_code.lower() != "us":
		shipment_doc.international_shipment = 1
		shipment_doc.service_type_international = doc.get("fedex_shipping_method").replace(" ", "_")
	else:
		shipment_doc.service_type_domestic = doc.get("fedex_shipping_method").replace(" ", "_")

	shipment_doc.packaging_type = "YOUR_PACKAGING"

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
	shipment_doc.submit()

	frappe.db.set_value("Delivery Note", doc.get("name"), "status", "Shipped")
	frappe.db.commit()
	
	return shipment_doc.name



@frappe.whitelist()
def get_stock_items(items):
	items = json.loads(items)
	stock_items = []
	for item in items:
		if frappe.db.get_value("Item", {"item_code" : item.get("item_code")}, "is_stock_item"):
			stock_items.append(item)
	return stock_items
