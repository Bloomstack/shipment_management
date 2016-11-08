// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt

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


//frappe.ui.form.on("DTI Shipment Note", "delivery_items", function(frm) {
//    frappe.model.with_doc("Delivery Note", frm.doc.items, function() {
//        var delivery_items = frappe.model.get_doc("Delivery Note", frm.doc.items);
//
//        $.each(delivery_items.items, function(index,row) {
//        d = frm.add_child("items");
//        d.item_code = row.item_code;
//        d.installed_qty=delivery_items.installed_qty;
//        })
//
//        cur_frm.refresh_field("delivery_items");
//        })
//})

//
frappe.ui.form.on("DTI Shipment Note", "validate", function(frm) {
    var d = frm.doc;
    frappe.call({
        method:"erpnext.stock.Stock_custom_methods.check_eq_items",
        args: {
            doc: frm.doc
        },
        callback:function(r){
            //if(r.message == "item not in table"){
                var new_row = frm.add_child("engine_compatibility_");
                new_row.name = d.item_code;
                new_row.item_name = d.item_name;
                new_row.item_group = d.item_group;
                new_row.brand = d.brand;
                //}
        }
    });
    refresh_field("engine_compatibility_")
});


frappe.ui.form.on('DTI Shipment Note', "delivery_note", function(frm) {
        if (frm.doc.delivery_note)
            {

            get_company_email()
                .done(function(email_resp){
                    frm.doc.delivery_email = email_resp.message[0].email;
                    cur_frm.refresh_fields()
                    });

//            get_delivery_items()
//                .done(function(item_list){
//
//                for (i = 0; i < item_list.message.length; i++) {
//
//                    var new_row = frappe.model.add_child(cur_frm.doc, "DTI Shipment Note Item", "delivery_items")
//
//                    new_row.name = item_list.message[i].name;
//
//                    cur_frm.refresh_fields("delivery_items")
//                }
//
//
//
//
//                //frappe.db.set_value(this, "delivery_items", "item_code", "11111111")
////                    var items = ""
////                    console.log(item_list)
////                    for (i = 0; i < item_list.message.length; i++) {
////                         items  += "- <b>NAME:</b>" + item_list.message[i].name +
////                                    ", <b>ITEM CODE:</b>" +
////                                    item_list.message[i].item_code+
////                                    ", <b>ITEM NAME:</b>" +
////                                    item_list.message[i].item_name+
////                                    ",<b>ITEM GROUP:</b>" +
////                                    item_list.message[i].item_group+
////                                    ",<b>QTY:</b>" +
////                                    item_list.message[i].installed_qty+ "," +
////                                    "<br>";
////                        }
//
////                    frm.doc.delivery_items = "!!!!!!"
//
//
//
//                    //cur_frm.refresh_fields()
//
//                    });
            }
     }
)

frappe.ui.form.on('DTI Shipment Note', {
	refresh: function(frm) {

			$("[data-fieldname='cancel_shipment']", frm.body).css({'color': 'red'})
			$("[data-fieldname='return_shipment']", frm.body).css({'color': 'red'})

			cur_frm.refresh_fields();

	}});


// ################################################

cur_frm.cscript.cancel_shipment = function(doc) {
    frappe.call({
			method:'shipment_management.shipment.cancel_shipment',
			args: {
			    target_doc: cur_frm.doc
			      }
			})
		};
