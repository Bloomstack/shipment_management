// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt


frappe.ui.form.on('DTI Shipment Note', {

	refresh: function(frm) {
			cur_frm.refresh_fields();
		    if ((cur_frm.doc.label_1) && (cur_frm.doc.docstatus==1))
                    {
                    cur_frm.add_custom_button(__('Print label'),
                    function ()
                        {
                           var url = '/labels?name=' + cur_frm.doc.name
                           window.location.assign(url)
                        }).addClass("btn btn-primary");
                              }
	                    },
});


get_recipient_info = function(doc) {
		return frappe.call({
			method:'shipment_management.shipment.get_recipient_details',
			args: { delivery_note_name: cur_frm.doc.delivery_note}
		});
};


get_shipper_info = function(doc) {
		return frappe.call({
			method:'shipment_management.shipment.get_shipper_details',
			args: { delivery_note_name: cur_frm.doc.delivery_note}
		});
};

get_delivery_items = function(doc) {
		return frappe.call({
			method:'shipment_management.shipment.get_delivery_items',
			args: { delivery_note_name: cur_frm.doc.delivery_note}
		});
};

cur_frm.fields_dict['delivery_note'].get_query = function(doc) {
	return {
		filters: {
			"docstatus": '1'
		}
	}
}

frappe.ui.form.on('DTI Shipment Note', "delivery_note", function(frm) {
        if (frm.doc.delivery_note)
            {

            get_delivery_items()
                .done(function(item_list){
                frappe.model.clear_table(cur_frm.doc, 'delivery_items');
                for (i = 0; i < item_list.message.length; i++) {

                    var new_row = frappe.model.add_child(cur_frm.doc, "DTI Shipment Note Item", "delivery_items")

                    var dt = "DTI Shipment Note Item";
                    frappe.model.set_value(dt, new_row.name, 'item_code', item_list.message[i].item_code);
                    frappe.model.set_value(dt, new_row.name, 'item_name', item_list.message[i].item_name);
                    frappe.model.set_value(dt, new_row.name, 'item_group', item_list.message[i].item_group);
                    frappe.model.set_value(dt, new_row.name, 'installed_qty', item_list.message[i].installed_qty);
					frappe.model.set_value(dt, new_row.name, 'qty', item_list.message[i].qty);
                    frappe.model.set_value(dt, new_row.name, 'description', item_list.message[i].description);

                    cur_frm.refresh_fields("delivery_items")
                                                        }

                                   });
            get_recipient_info()
                 .done(function(recipient){
                 var resp = recipient.message
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_contact_person_name', resp['recipient_contact_person_name']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_company_name', resp['recipient_company_name']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_contact_phone_number', resp['recipient_contact_phone_number']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_address_street_lines', resp['recipient_address_street_lines']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_address_city', resp['recipient_address_city']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_address_state_or_province_code', resp['recipient_address_state_or_province_code']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_address_country_code', resp['recipient_address_country_code']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'recipient_address_postal_code', resp['recipient_address_postal_code']);
                 });

            }
     }
)
