// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt
// cur_frm.cscript.shipment_note_link = function(doc, cdt, cd){}


frappe.ui.form.on('DTI Fedex Shipment', {

	refresh: function(frm) {
		        if (cur_frm.doc.label_1)
                    {
                    cur_frm.add_custom_button(__('Print label'),
                    function ()
                        {
                           var url = '/labels?name=' + cur_frm.doc.name
                           window.location.assign(url)
                        }).addClass("btn btn-primary");
                }
	}

});

get_shipment_items = function(doc) {
		return frappe.call({
			method:'shipment_management.shipment.get_shipment_items',
			args: { shipment_note_name: cur_frm.doc.shipment_note_link}
		});
};


frappe.ui.form.on('DTI Fedex Shipment', "shipment_note_link", function(frm) {
        if (frm.doc.shipment_note_link)
            {

            get_shipment_items()
                .done(function(item_list){
                frappe.model.clear_table(cur_frm.doc, 'shipment_items');
                for (i = 0; i < item_list.message.length; i++) {

                    var new_row = frappe.model.add_child(cur_frm.doc, "DTI Fedex Shipment Item", "shipment_items")

                    var dt = "DTI Fedex Shipment Item";
                    frappe.model.set_value(dt, new_row.name, 'item_code', item_list.message[i].item_code);
                    frappe.model.set_value(dt, new_row.name, 'item_name', item_list.message[i].item_name);
                    frappe.model.set_value(dt, new_row.name, 'item_group', item_list.message[i].item_group);
                    frappe.model.set_value(dt, new_row.name, 'installed_qty', item_list.message[i].installed_qty);

					frappe.model.set_value(dt, new_row.name, 'qty', item_list.message[i].qty);
                    frappe.model.set_value(dt, new_row.name, 'description', item_list.message[i].description);

                    cur_frm.refresh_fields("shipment_items")
                }

            });
            }
     }
)
