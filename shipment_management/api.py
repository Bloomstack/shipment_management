from __future__ import unicode_literals

import frappe
from frappe.utils import cint
from provider_fedex import get_fedex_packages_rate
from utils import get_state_code, get_country_code
from shipment_management.doctype.shipping_package_rule.shipping_package_rule import find_packages

VALID_PACKAGING_TYPES = (
	"FEDEX_10KG_BOX",
	"FEDEX_25KG_BOX",
	"FEDEX_BOX",
	"FEDEX_ENVELOPE",
	"FEDEX_PAK",
	"FEDEX_TUBE",
	"YOUR_PACKAGING"
)

def get_rates(from_address, to_address, items, packaging_type="YOUR_PACKAGING"):
	"""Simple wrapper over fedex rating service.
	It takes the standard address field values for the from_ and to_ addresses
	to keep a consistent address api. Packaging is a list of items with only
	two foe;d requirements "item_code" and "qty". """

	# quick hack to package all items into one box for quick shipping quotations
	#packages = find_packages(items)
	packages = []
	package = {
		"weight_value": 0,
		"weight_units": "LB",
		"physical_packaging": "BOX",
		"group_package_count": 0,
		"insured_amount": 300
	}

	for itm in items:
		item = frappe.get_all("Item", fields=["name", "net_weight"], filters={ "item_code": itm.get("sku") })

		if item and len(item) > 0:
			item = item[0]
			package["weight_value"] = package["weight_value"] + cint(item.get("net_weight") * 2 * itm.get("qty"))
			package["group_package_count"] = package["group_package_count"] + itm.get("qty")

	packages.append(package)

	# to try and keep some form of standardization we'll minimally  require
	# a weight_value. Any other values will be passed as is to the rates service.
	surcharge = 0
	for package in packages:
		if package.get("weight_value", None) is None or \
		   package.get("weight_units", None) is None:
			raise frappe.exceptions.ValidationError("Missing weight_value data")

		if not package.get("group_package_count"):
			package["group_package_count"] = 1

		if not package.get("insured_amount"):
			package["insured_amount"] = 0

		if not package.get("physical_packaging"):
			package["physical_packaging"] = "BOX"

		surcharge = surcharge + package.get("surcharge", 0)

	args = dict(
		DropoffType='REGULAR_PICKUP',
		PackagingType=packaging_type,
		EdtRequestType='NONE',
		PaymentType='SENDER',
		ShipperStateOrProvinceCode=from_address.get("state"),
		ShipperPostalCode=from_address.get("pincode"),
		ShipperCountryCode=get_country_code(from_address.get("country")),
		RecipientStateOrProvinceCode=to_address.get("state"),
		RecipientPostalCode=to_address.get("pincode"),
		RecipientCountryCode=get_country_code(to_address.get("country")),
		package_list=packages,
		ignoreErrors=True
	)

	rates = get_fedex_packages_rate(**args)
	sorted_rates = []
	for rate in sorted(rates, key=lambda rate: rate["fee"]):
		rate["fee"] = rate["fee"] + surcharge
		sorted_rates.append(rate)

	return sorted_rates
