import json
from math import ceil

import pycountry
import requests

import frappe
from erpnext import get_default_company
from frappe import _
from frappe.contacts.doctype.address.address import get_address_display
from shipment_management.utils import get_country_code

DEFAULT_CONFIRMATION_TYPE = "direct_signature"
DEFAULT_FEDEX_PACKAGE = "package"
DEFAULT_FEDEX_ONE_RATE_PACKAGE = "fedex_envelope"
DEFAULT_FEDEX_SERVICE_CODE = "fedex_ground"
SHIPENGINE_BASE_URL = "api.shipengine.com"


@frappe.whitelist()
def get_rates(doc, address=None, address_obj=None, estimate=False):
	"""
	Return shipment rates based on the provided document and target address.

	Args:
		doc (str): The order details, as a stringified JSON object.
		address (str, optional): The name of the shipping address. Defaults to None.
		address_obj (str, optional): The shipping address details, as a stringified JSON object. Defaults to None.
		estimate (bool, optional): True if estimated shipping rates are required, without any additional
			charges, such as surcharges, insurance, customs, etc., otherwise False to receive all data.
			Defaults to False.

	Returns:
		list of dict: Returns the list of rates based on the shipping address
	"""

	doc = json.loads(doc)

	if isinstance(estimate, str):
		estimate = json.loads(estimate)

	if not any([address, address_obj, doc.get("shipping_address_name")]):
		frappe.throw(_("The order is missing a shipping address"))

	# get the shipper's address
	from_address = frappe.get_doc("Address", {"is_your_company_address": 1})
	from_address = from_address.as_dict()

	# get the receiver's address
	if address_obj:
		to_address = json.loads(address_obj)
	else:
		to_address = frappe.get_doc("Address", address or doc.get("shipping_address_name"))
		to_address = to_address.as_dict()

	frappe.local.response["address"] = get_address_display(to_address)

	# use addresses to return rates from ShipEngine
	return get_shipengine_rates(from_address, to_address, doc=doc, estimate=estimate)


def get_shipengine_rates(from_address, to_address, items=None, doc=None, estimate=False):
	"""
	Return shipment rates from Fedex using the ShipEngine API.

	Args:
		from_address (dict): The shipper's address.
		to_address (dict): The reciever's address.
		items (list of dict, optional): The list of items to be shipped. Defaults to None.
		doc (dict): The order details. Defaults to None.
		estimate (bool, optional): True if estimated shipping rates are required, without
			any additional charges, such as surcharges, insurance, customs, etc., otherwise
			False to receive all data. Defaults to False.

	Returns:
		list of dict: Returns the list of rates based on the shipping address
	"""

	package = {
		"weight": {
			"value": 0,
			"unit": "pound"
		},
		"insured_value": {
			"currency": "usd",
			"amount": 0
		}
	}

	item_values = frappe.get_all("Item", fields=["insured_declared_value", "name", "net_weight"])
	item_values = {elem.pop("name"): elem for elem in item_values}

	if doc and not items:
		items = doc.get("items")

	# Set the item weights, quantity and insured amounts in the package(s).
	# For repairs, only process packages once for each warranty claim.
	processed_claims = []
	weight_value = insured_amount = 0
	for item in items:
		if item.get("warranty_claim") and item.get("warranty_claim") not in processed_claims:
			repair_items = frappe.db.get_value("Warranty Claim", item.get("warranty_claim"), ["item_code", "cable", "case"])
			repair_items = list(filter(None, repair_items))

			for repair_item in repair_items:
				weight_value += item_values.get(repair_item, {}).get("net_weight", 0)
				insured_amount += item_values.get(repair_item, {}).get("insured_declared_value", 0)

			processed_claims.append(item.get("warranty_claim"))
		else:
			weight_value += item_values.get(item.get("item_code"), {}).get("net_weight", 0) * item.get("qty", 0)
			insured_amount += item_values.get(item.get("item_code"), {}).get("insured_declared_value", 0) * item.get("qty", 0)

	package["weight"]["value"] = max(1, ceil(weight_value))
	package["insured_value"]["amount"] = insured_amount or 0

	# check item conditions for applying Fedex One Rate pricing
	rate_settings = frappe.get_single("Shipment Rate Settings")

	flat_rate = False
	confirmation = DEFAULT_CONFIRMATION_TYPE
	packaging = DEFAULT_FEDEX_PACKAGE

	to_country_code = get_country_code(to_address.get("country", ""))
	if to_country_code.lower() == "us":  # One Rate only applies for intra-US deliveries
		flat_rate_items = {item.item: item.max_qty for item in rate_settings.items}
		for item in items:
			if item.get("qty", 0) < flat_rate_items.get(item.get("item_code"), 0):
				flat_rate = True
				shipping_package = frappe.db.get_value("Shipment Rate Item Settings", {"item": item.get("item_code")}, "packaging")
				packaging = frappe.db.get_value("Shipping Package", shipping_package, "box_code")
			else:
				flat_rate = False
				packaging = DEFAULT_FEDEX_PACKAGE
				break  # even if one item is not eligible for One Rate, break

	if flat_rate:
		confirmation = "none"
		packaging = packaging.lower() + "_onerate"

	package["package_code"] = packaging

	# make the request to ShipEngine
	if estimate:
		rates = get_estimated_rates(from_address, to_address, package, doc, items, confirmation)
	else:
		rates = get_shipping_rates(from_address, to_address, package, doc, items, confirmation)

	# process all the returned rates
	if not rates:
		frappe.throw("Could not get rates, please re-check your shipping address.")

	shipping_rates = []
	for rate in rates:
		# disallow FEDEX GROUND for Canada
		if to_country_code.lower() == "ca" and rate.get("service_code") == "fedex_ground":
			continue

		fee = sum([(rate.get(rate_type) or {}).get("amount", 0.0)
			for rate_type in ("shipping_amount", "insurance_amount", "confirmation_amount", "other_amount")])

		if rate_settings.upcharge_type == "Percentage":
			fee += (fee * (rate_settings.upcharge / 100))
		elif rate_settings.upcharge_type == "Actual":
			fee += rate_settings.upcharge

		fee = round(fee, 2)
		shipping_rates.append({
			"name": rate.get("service_code"),
			"label": rate.get("service_type"),
			"fee": fee,
			"days": rate.get("delivery_days"),
			"estimated_arrival": rate.get("carrier_delivery_days")
		})

	shipping_rates.sort(key=lambda rate: rate.get("fee"))
	return shipping_rates


def get_estimated_rates(from_address, to_address, package, doc, items, confirmation):
	from_postal_code = (from_address.get("pincode") or "").strip()
	from_country_code = get_country_code(from_address.get("country", ""))
	from_state = validate_state(from_address)

	to_postal_code = (to_address.get("pincode") or "").strip()
	to_country_code = get_country_code(to_address.get("country", ""))
	to_state = validate_state(to_address)

	data = {
		"carrier_id": frappe.conf.get("shipengine_fedex_carrier_id"),
		"from_country_code": from_country_code.upper(),
		"from_postal_code": from_postal_code,
		"from_city_locality": from_address.get("city"),
		"from_state_province": from_state,
		"to_country_code": to_country_code.upper(),
		"to_postal_code": to_postal_code,
		"to_city_locality": to_address.get("city"),
		"to_state_province": to_state,
		"weight": package.get("weight", {}),
		"confirmation": confirmation,
		"address_residential_indicator": "unknown",
		"ship_date": doc.get("delivery_date") if doc else None
	}

	url = "https://{base_url}/v1/rates/estimate".format(base_url=SHIPENGINE_BASE_URL)

	headers = {
		'Host': SHIPENGINE_BASE_URL,
		'API-Key': frappe.conf.get("shipengine_api_key"),
		'Content-Type': 'application/json'
	}

	response = requests.request("POST", url, headers=headers, data=json.dumps(data))
	rates = response.json()

	return rates


def get_shipping_rates(from_address, to_address, package, doc, items, confirmation):
	from_postal_code = (from_address.get("pincode") or "").strip()
	from_country_code = get_country_code(from_address.get("country", ""))
	from_state = validate_state(from_address)

	to_postal_code = (to_address.get("pincode") or "").strip()
	to_country_code = get_country_code(to_address.get("country", ""))
	to_state = validate_state(to_address)

	# build a list of items for international shipments
	customs_items = []
	items = items or doc.get("items")
	for item in items:
		customs_items.append({
			"description": item.get("description"),
			"quantity": item.get("qty"),
			"value": item.get("rate"),
			"country_of_origin": from_country_code.upper(),
			"sku": item.get("item_code")
		})

	data = {
		"shipment": {
			"validate_address": "validate_only",
			"carrier_id": frappe.conf.get("shipengine_fedex_carrier_id"),
			"ship_date": doc.get("delivery_date") if doc else None,
			"ship_to": {
				"name": doc.get("customer_name"),
				"phone": to_address.get("phone"),
				"address_line1": to_address.get("address_line1"),
				"city_locality": to_address.get("city"),
				"state_province": to_state,
				"postal_code": to_postal_code,
				"country_code": to_country_code.upper(),
				"address_residential_indicator": "unknown"
			},
			"ship_from": {
				"name": get_default_company(),
				"phone": from_address.get("phone"),
				"company_name": get_default_company(),
				"address_line1": from_address.get("address_line1"),
				"city_locality": from_address.get("city"),
				"state_province": from_state,
				"postal_code": from_postal_code,
				"country_code": from_country_code.upper(),
				"address_residential_indicator": "unknown"
			},
			"packages": [package],
			"confirmation": confirmation,
			"customs": {
				"contents": "merchandise",
				"non_delivery": "return_to_sender",
				"customs_items": customs_items
			},
			"insurance_provider": "third_party",
			"advanced_options": {
				"saturday_delivery": doc.get("saturday_delivery", False) if doc else False
			}
		}
	}

	url = "https://{base_url}/v1/rates".format(base_url=SHIPENGINE_BASE_URL)

	headers = {
		'Host': SHIPENGINE_BASE_URL,
		'API-Key': frappe.conf.get("shipengine_api_key"),
		'Content-Type': 'application/json'
	}

	response = requests.request("POST", url, headers=headers, data=json.dumps(data))
	response = response.json()

	# throw any errors to the user
	errors = response.get("errors")

	if errors:
		frappe.throw(_(errors[0].get("message", "")))

	rates = response.get("rate_response").get("rates")
	return rates


def validate_state(address):
	country_code = frappe.db.get_value("Country", address.get("country"), "code")
	state = address.get("state", "").upper().strip()

	if not state or country_code.lower() != "us":
		return address.get("state")

	error_message = _("""{} is not a valid state! Check for typos or enter the ISO code for your state.""".format(address.get("state")))

	# The max length for ISO state codes is 3, excluding the country code
	if len(state) <= 3:
		address_state = (country_code + "-" + state).upper()  # PyCountry returns state code as {country_code}-{state-code} (e.g. US-FL)

		states = pycountry.subdivisions.get(country_code=country_code.upper())
		states = [pystate.code for pystate in states]

		if address_state in states:
			return state

		frappe.throw(error_message)
	else:
		try:
			lookup_state = pycountry.subdivisions.lookup(state)
		except LookupError:
			frappe.throw(error_message)
		else:
			return lookup_state.code.split('-')[1]
