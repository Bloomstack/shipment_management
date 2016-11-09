from __future__ import unicode_literals
import frappe
import traceback

def get_context(context):
	print("######### WORKING?")
	try:
		doc_name = frappe.request.args.get('name', '')
		print("######## name: %s" % doc_name)
		doc = frappe.get_doc('DTI Fedex Shipment', doc_name);

		context.no_cache = 1
		context.no_sitemap = 1
		context['label_url'] = doc.label_1
		print("######### RENDER TEMPLATE?")
	except Exception:
		print("######### EXCEPTION")
		print(traceback.format_exc())