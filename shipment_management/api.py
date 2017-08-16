from __future__ import unicode_literals

import frappe
from frappe.utils import cint, flt
from provider_fedex import get_fedex_packages_rate
from utils import get_state_code, get_country_code
from math import ceil
import json
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

@frappe.whitelist()
def get_rates_for_doc(doc, address=None, address_obj=None):
	doc = json.loads(doc)
	from erpnext.utilities.doctype.address.address import get_address_display
	if not address_obj:
		to_address = frappe.get_doc("Address", address or doc.get("shipping_address_name"))
		frappe.local.response["address"] = get_address_display(to_address.as_dict())
	else:
		to_address = json.loads(address_obj)
		frappe.local.response["address"] = get_address_display(to_address)


	from_address = frappe.get_doc("Address", {"is_your_company_address" : 1})
	return get_rates(from_address, to_address, doc.get("items"))


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
		"insured_amount": 0
	}

	for itm in items:
		item = frappe.get_all("Item", fields=["name", "net_weight"], filters={ "item_code": itm.get("item_code") })
		if item and len(item) > 0:
			item = item[0]
			weight = flt(item.get("net_weight", 0))
			package["weight_value"] = package["weight_value"] + (weight * itm.get("qty", 1))
			package["group_package_count"] = package["group_package_count"] + itm.get("qty")

			if itm["item_code"].find("CIEM") > -1 or itm["item_code"].find("UIEM") > -1:
				package["insured_amount"] = package["insured_amount"] + (400 * itm.get("qty", 1))
			else:
				package["insured_amount"] = package["insured_amount"] + (100 * itm.get("qty", 1))

	package["weight_value"] = ceil(package["weight_value"])
	if package["weight_value"] < 1:
		package["weight_value"] = 1

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
	args = dict(
		DropoffType='REGULAR_PICKUP',
		PackagingType=packaging_type,
		EdtRequestType='NONE',
		PaymentType='SENDER',
		ShipperStateOrProvinceCode=from_address.get("state"),
		ShipperPostalCode=from_address.get("pincode"),
		ShipperCountryCode=get_country_code(from_address.get("country")),
		RecipientStateOrProvinceCode=to_address.get("state") if RecipientCountryCode in ("US", "CA") else None,
		RecipientPostalCode=to_address.get("pincode"),
		IsResidential = to_address.get("is_residential"),
		RecipientCountryCode=RecipientCountryCode,
		package_list=packages,
		ignoreErrors=True,
		signature_option="DIRECT"
	)

	upcharge_doc = frappe.get_doc("Shipment Rate Settings", "Shipment Rate Settings")

	rates = get_fedex_packages_rate(**args)
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

		sorted_rates.append({u'fee': 0, u'name': u'PICK UP', u'label': u'FLORIDA HQ PICK UP'})
		customer = frappe.get_value("Address", to_address.get("shipping_address"), "customer")
		if frappe.get_value("Customer", customer, 'has_shipping_account'):
			sorted_rates.append({u'fee': 0, u'name': u'SHIP USING MY ACCOUNT', u'label': u'SHIP USING MY ACCOUNT'})


	return sorted_rates
