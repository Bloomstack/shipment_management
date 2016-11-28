// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt


//get_insurance = function(doc) {
//		return frappe.call({
//			method:'shipment_management.shipment.get_total_insurance',
//			args: { source: cur_frm.doc}
//		});
//};
//get_rate = function(doc) {
//		return frappe.call({
//			method:'shipment_management.provider_fedex.get_package_rate',
//			args: { source: cur_frm.doc}
//		});
//};
//get_delivery_time = function(doc) {
//		return frappe.call({
//			method:'shipment_management.provider_fedex.estimate_delivery_time',
//			args: { OriginPostalCode:doc.recipient_address_postal_code,
//					OriginCountryCode:'CA',
//					DestinationPostalCode:'27577',
 //					DestinationCountryCode:'US'}
//		});
//};

all_required = function(frm, fields) {
    for(var i in fields) {
        if ( !frm.doc[fields[i]] ) {
            return false;
        }
    }
    return true;
}

multifield_events = function(fields, callback) {
    var obj = {};
    for(var i in fields) {
        console.log("watching for ", fields[i], i);
        (function(field) {
            obj[field] = function(frm) { callback(field, frm, all_required(frm, fields)); };
        }(fields[i]));
    }
    return obj;
}

frappe.ui.form.on('DTI Shipment Note', $.extend(multifield_events([
        'recipient_contact_person_name',
        'recipient_company_name'
    ], function(field, frm, all_fields_set) {
        console.log("field change", field, frm);
        console.log((all_fields_set)?"ALL REQUIRED FIELDS ARE SET":"MISSING REQUIRED FIELDS");
    }), {

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

        onload_post_render: function(frm) {
            //TODO Run Time Reload
            //var total = get_insurance()
    //      var rate = get_rate()
    //      var delivery_time = get_delivery_time()
            console.log(cur_frm.doc.package);

            //frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'total_insurance', total);
    //	    frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'rate', "100");
    //	    frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'delivery_time', "100");

        },

        package: function(frm) {
            console.log(cur_frm.doc.package);

        },

        package_add: function(frm) {
            console.log("package_add?", frm);
        },
        package_remove: function(frm) {
            console.log("package_remove?", frm);
        }
}));

frappe.ui.form.on("DTI Shipment Package", "insured_amount", function(frm) {
    console.log("FROM CHILD  TABLE? ", frm);
});

frappe.ui.form.on("DTI Shipment Note", "recipient_adress", "shipper_addres", function(frm) {
    console.log("FROM CHILD  TABLE? ", frm);
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

                    frappe.model.set_value(dt, new_row.name, 'barcode', item_list.message[i].barcode);
                    frappe.model.set_value(dt, new_row.name, 'item_code', item_list.message[i].item_code);
                    frappe.model.set_value(dt, new_row.name, 'item_name', item_list.message[i].item_name);
                    frappe.model.set_value(dt, new_row.name, 'customer_item_code', item_list.message[i].customer_item_code);
                    frappe.model.set_value(dt, new_row.name, 'description', item_list.message[i].description);
                    frappe.model.set_value(dt, new_row.name, 'image', item_list.message[i].image);
                    frappe.model.set_value(dt, new_row.name, 'image_view', item_list.message[i].image_view);
                    frappe.model.set_value(dt, new_row.name, 'qty', item_list.message[i].qty);
                    frappe.model.set_value(dt, new_row.name, 'price_list_rate', item_list.message[i].price_list_rate);
                    frappe.model.set_value(dt, new_row.name, 'stock_uom', item_list.message[i].stock_uom);
                    frappe.model.set_value(dt, new_row.name, 'base_price_list_rate', item_list.message[i].base_price_list_rate);
                    frappe.model.set_value(dt, new_row.name, 'discount_percentage', item_list.message[i].discount_percentage);
                    frappe.model.set_value(dt, new_row.name, 'margin_rate_or_amount', item_list.message[i].margin_rate_or_amount);
                    frappe.model.set_value(dt, new_row.name, 'total_margin', item_list.message[i].total_margin);
                    frappe.model.set_value(dt, new_row.name, 'rate', item_list.message[i].rate);
                    frappe.model.set_value(dt, new_row.name, 'amount', item_list.message[i].amount);
                    frappe.model.set_value(dt, new_row.name, 'base_rate', item_list.message[i].base_rate);
                    frappe.model.set_value(dt, new_row.name, 'base_amount', item_list.message[i].base_amount);
                    frappe.model.set_value(dt, new_row.name, 'pricing_rule', item_list.message[i].pricing_rule);
                    frappe.model.set_value(dt, new_row.name, 'net_rate', item_list.message[i].net_rate);
                    frappe.model.set_value(dt, new_row.name, 'net_amount', item_list.message[i].net_amount);
                    frappe.model.set_value(dt, new_row.name, 'base_net_rate', item_list.message[i].base_net_rate);
                    frappe.model.set_value(dt, new_row.name, 'base_net_amount', item_list.message[i].base_net_amount);
                    frappe.model.set_value(dt, new_row.name, 'warehouse', item_list.message[i].warehouse);
                    frappe.model.set_value(dt, new_row.name, 'target_warehouse', item_list.message[i].target_warehouse);
                    frappe.model.set_value(dt, new_row.name, 'serial_no', item_list.message[i].serial_no);
                    frappe.model.set_value(dt, new_row.name, 'batch_no', item_list.message[i].batch_no);
                    frappe.model.set_value(dt, new_row.name, 'actual_qty', item_list.message[i].actual_qty);
                    frappe.model.set_value(dt, new_row.name, 'actual_batch_qty', item_list.message[i].actual_batch_qty);
                    frappe.model.set_value(dt, new_row.name, 'item_group', item_list.message[i].item_group);
                    frappe.model.set_value(dt, new_row.name, 'brand', item_list.message[i].brand);
                    frappe.model.set_value(dt, new_row.name, 'expense_account', item_list.message[i].expense_account);
                    frappe.model.set_value(dt, new_row.name, 'cost_center', item_list.message[i].cost_center);
                    frappe.model.set_value(dt, new_row.name, 'against_sales_order', item_list.message[i].against_sales_order);
                    frappe.model.set_value(dt, new_row.name, 'against_sales_invoice', item_list.message[i].against_sales_invoice);
                    frappe.model.set_value(dt, new_row.name, 'so_detail', item_list.message[i].so_detail);
                    frappe.model.set_value(dt, new_row.name, 'si_detail', item_list.message[i].si_detail);
                    frappe.model.set_value(dt, new_row.name, 'installed_qty', item_list.message[i].installed_qty);
                    frappe.model.set_value(dt, new_row.name, 'billed_amt', item_list.message[i].billed_amt);

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

                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'contact_email', resp['contact_email']);


                 });

            get_shipper_info()
                 .done(function(shipper){
                 var resp = shipper.message
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_contact_person_name', resp['shipper_contact_person_name']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_company_name', resp['shipper_company_name']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_contact_phone_number', resp['shipper_contact_phone_number']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_address_street_lines', resp['shipper_address_street_lines']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_address_city', resp['shipper_address_city']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_address_state_or_province_code', resp['shipper_address_state_or_province_code']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_address_country_code', resp['shipper_address_country_code']);
                 frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'shipper_address_postal_code', resp['shipper_address_postal_code']);
                 });

//            get_insurance()
//                .done(function(total_insurance){
//                frappe.model.set_value('DTI Shipment Note', cur_frm.doc.name, 'total_insurance', total_insurance)});
        }
        }

)
