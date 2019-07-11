from __future__ import unicode_literals

import frappe
from provider_fedex import get_fedex_packages_rate
from awesome_cart.compat.customer import get_current_customer
from utils import get_country_code
from math import ceil
import json

from dti_devtools.debug import pretty_json

VALID_PACKAGING_TYPES = (
	"FEDEX_10KG_BOX",
	"FEDEX_25KG_BOX",
	"FEDEX_BOX",
	"FEDEX_ENVELOPE",
	"FEDEX_PAK",
	"FEDEX_TUBE",
	"YOUR_PACKAGING"
)

@frappe.whitelist()
def get_rates_for_doc(doc, address=None, address_obj=None):
	doc = json.loads(doc)
	from frappe.contacts.doctype.address.address import get_address_display
	if not address_obj:
		to_address = frappe.get_doc("Address", address or doc.get("shipping_address_name"))
		frappe.local.response["address"] = get_address_display(to_address.as_dict())
	else:
		to_address = json.loads(address_obj)
		frappe.local.response["address"] = get_address_display(to_address)


	from_address = frappe.get_doc("Address", {"is_your_company_address" : 1})
	return get_rates(from_address, to_address, doc=doc)


def get_rates(from_address, to_address, items=None, doc=None, packaging_type="YOUR_PACKAGING"):
	"""Simple wrapper over fedex rating service.

	It takes the standard address field values for the from_ and to_ addresses
	to keep a consistent address api.
	"""

	# quick hack to package all items into one box for quick shipping quotations
	# packages = find_packages(items)
	packages = []
	package = {
		"weight_value": 0,
		"weight_units": "LB",
		"physical_packaging": "BOX",
		"group_package_count": 0,
		"insured_amount": 0
	}

	item_values = frappe.get_all("Item", fields=["insured_declared_value", "name", "net_weight"])
	item_values = {elem.pop("name"): elem for elem in item_values}

	if doc and not items:
		items = doc.get("items")

	# Set the item weights, quantity and insured amounts in the package(s).
	# For repairs, only process packages once for each warranty claim.
	processed_claims = []
	weight_value = group_package_count = insured_amount = 0
	for item in items:
		if item.get("warranty_claim") and item.get("warranty_claim") not in processed_claims:
			repair_items = frappe.db.get_value("Warranty Claim", item.get("warranty_claim"), ["item_code", "cable", "case"])
			repair_items = list(filter(None, repair_items))
			group_package_count = len(repair_items)

			for repair_item in repair_items:
				weight_value += item_values.get(repair_item, {}).get("net_weight", 0)
				insured_amount += item_values.get(repair_item, {}).get("insured_declared_value", 0)

			processed_claims.append(item.get("warranty_claim"))
		else:
			group_package_count += item.get("qty", 0)
			weight_value += item_values.get(item.get("item_code"), {}).get("net_weight", 0) * item.get("qty", 0)
			insured_amount += item_values.get(item.get("item_code"), {}).get("insured_declared_value", 0) * item.get("qty", 0)

	package["weight_value"] = max(1, ceil(weight_value))
	package["group_package_count"] = group_package_count
	package["insured_amount"] = insured_amount
	packages.append(package)

	# to try and keep some form of standardization we'll minimally  require
	# a weight_value. Any other values will be passed as is to the rates service.
	surcharge = 0
	for package in packages:
		if package.get("weight_value", None) is None or \
		   package.get("weight_units", None) is None:
			raise frappe.exceptions.ValidationError("Missing weight_value data")

		#if not package.get("group_package_count"):
		# keep count on 1 as we don't care about package groups
		package["group_package_count"] = 1

		if not package.get("insured_amount"):
			package["insured_amount"] = 0

		if not package.get("physical_packaging"):
			package["physical_packaging"] = "BOX"

		surcharge = surcharge + package.get("surcharge", 0)

	RecipientCountryCode = get_country_code(to_address.get("country"))
	rate_exceptions = []
	args = dict(
		DropoffType='REGULAR_PICKUP',
		PackagingType=packaging_type,
		EdtRequestType='NONE',
		PaymentType='SENDER',
		# Shipper
		ShipperPostalCode=from_address.get("pincode").strip(),
		ShipperCountryCode=get_country_code(from_address.get("country")),
		# Recipient
		RecipientPostalCode=to_address.get("pincode").strip(),
		IsResidential=to_address.get("is_residential"),
		RecipientCountryCode=RecipientCountryCode,
		# Delivery options
		package_list=packages,
		ignoreErrors=True,
		signature_option="DIRECT",
		exceptions=rate_exceptions,
		delivery_date=doc.get("delivery_date") if doc else "",
		saturday_delivery=doc.get("saturday_delivery") if doc else ""
	)

	upcharge_doc = frappe.get_doc("Shipment Rate Settings", "Shipment Rate Settings")

	if to_address:
		rates = get_fedex_packages_rate(**args)
	else:
		rates = []

	sorted_rates = []
	if rates:
		for rate in sorted(rates, key=lambda rate: rate["fee"]):
			rate["fee"] = rate["fee"] + surcharge

			if upcharge_doc.upcharge_type == "Percentage":
				rate["fee"] = rate["fee"] + (rate["fee"] * (upcharge_doc.upcharge/100))
			elif upcharge_doc.upcharge_type == "Actual":
				rate["fee"] = rate["fee"] + upcharge_doc.upcharge

			rate['fee'] = round(rate['fee'], 2)

			sorted_rates.append(rate)

		final_sorted_rates = sorted_rates

		# Disallow FEDEX GROUND for Canada
		if RecipientCountryCode.lower() == "ca":
			for rate in sorted_rates:
				if rate['label'] == "FEDEX GROUND":
					final_sorted_rates.remove(rate)

		return final_sorted_rates
	else:
		msg = "Could not get rates, please check your Shipping Address"
		if len(rate_exceptions) > 0:

			for ex in rate_exceptions:
				if ex["type"] == "request":
					msg = str(ex["exception"])
					break

		frappe.throw(msg, title="Error")
