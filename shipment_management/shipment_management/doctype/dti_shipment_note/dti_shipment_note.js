// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt


frappe.ui.form.on('DTI Shipment Note', {
	refresh: function(frm) {

			$("[data-fieldname='cancel_shipment']", frm.body).css({'color': 'red'})
			$("[data-fieldname='return_shipment']", frm.body).css({'color': 'red'})
            $("[data-fieldname='shipment_status']", frm.body).css({"font-size": "18px", "color":"orange"})
			cur_frm.refresh_fields();

	}});

//var r = confirm("Press a button");
//if (r == true) {
//    x = "You pressed OK!";
//} else {
//    x = "You pressed Cancel!";
//}

cur_frm.cscript.cancel_shipment = function(doc) {
    frappe.call({
			method:'shipment_management.shipment.cancel_shipment',
			args: {
			    target_doc: cur_frm.doc
			      }
			})
		};

cur_frm.cscript.return_shipment = function(doc) {
    frappe.call({
			method:'shipment_management.shipment.return_shipment',
			args: {
			    target_doc: cur_frm.doc
			      }
			})
		};



// #########################################

get_company_email = function(doc) {
		return frappe.call({
			method:'shipment_management.shipment.get_company_email',
			args: { delivery_note_company: cur_frm.doc.delivery_note_company}
		});
};

get_delivery_items = function(doc) {
		return frappe.call({
			method:'shipment_management.shipment.get_delivery_items',
			args: { delivery_note_name: cur_frm.doc.delivery_note}
		});
};


frappe.ui.form.on('DTI Shipment Note', "delivery_note", function(frm) {
        if (frm.doc.delivery_note)
            {

            get_company_email()
                .done(function(email_resp){
                    frm.doc.delivery_email = email_resp.message[0].email;
                    cur_frm.refresh_fields()
                    });

            get_delivery_items()
                .done(function(item_list){
                frappe.model.clear_table(cur_frm.doc, 'delivery_items');
                for (i = 0; i < item_list.message.length; i++) {

                    console.log("item_list.message = ", item_list.message)

                    var new_row = frappe.model.add_child(cur_frm.doc, "DTI Shipment Note Item", "delivery_items")

                    console.log("item=", item_list.message[i])

                    var dt = "DTI Shipment Note Item";
                    frappe.model.set_value(dt, new_row.name, 'item_code', item_list.message[i].item_code);
                    frappe.model.set_value(dt, new_row.name, 'item_name', item_list.message[i].item_name);
                    frappe.model.set_value(dt, new_row.name, 'item_group', item_list.message[i].item_group);
                    frappe.model.set_value(dt, new_row.name, 'installed_qty', item_list.message[i].installed_qty);
                    //new_row.name = item_list.message[i].name;
                    //new_row.item_code = item_list.message[i].item_code;
                    //new_row.item_name = item_list.message[i].item_name;
                    //new_row.item_group = item_list.message[i].item_group;
                    //new_row.installed_qty = item_list.message[i].installed_qty;


                    cur_frm.refresh_fields("delivery_items")
                }

            });
            }
     }
)