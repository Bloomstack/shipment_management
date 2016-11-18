import frappe
from frappe import _


class CommentController(object):
	Email = 'Email'
	Chat = 'Chat'
	Phone = 'Phone'
	SMS = 'SMS'
	Created = 'Created'
	Submitted = 'Submitted'
	Cancelled = 'Cancelled'
	Assigned = 'Assigned'
	Assignment = 'Assignment'
	Completed = 'Completed'
	Comment = 'Comment'
	Workflow = 'Workflow'
	Label = 'Label'
	Attachment = 'Attachment'
	Removed = 'Removed'

	@staticmethod
	def add_comment(doc_type, source_name, comment_type, comment_message):
		shipment = frappe.get_doc(doc_type, source_name)
		shipment.add_comment(comment_type, _(comment_message))