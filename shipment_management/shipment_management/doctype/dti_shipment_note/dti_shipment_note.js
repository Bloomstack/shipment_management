// Copyright (c) 2016, DigiThinkit Inc. and contributors
// For license information, please see license.txt

function create_fedex_shipment() {
	frappe.model.open_mapped_doc({
		method: "shipment_management.shipment.make_fedex_shipment_from_shipment_note",
		frm: cur_frm
	})
}

frappe.ui.form.on("DTI Shipment Note", "before_cancel", function(frm) {
     if(frm.doc.clearance_date){
        frappe.confirm('Are you sure?' ,
                function(){
                  show_alert('block one')
                },
                function(){
                  show_alert('block two')
                }
            );
     }
});

frappe.ui.form.on('DTI Shipment Note', {
	onload_post_render: function(frm) {

					$("[data-fieldname='fedex_button']:button").css({'color':'white', 'background-color': '#5e64ff', 'border-color': '#444bff'})

					if ((cur_frm.doc.fedex_name) && (cur_frm.doc.shipment_note_status != 'Cancelled') && (cur_frm.doc.shipment_note_status != 'Returned')){

			                cur_frm.add_custom_button(__('Cancel shipment process'),
													function(doc) {
																frappe.confirm('This action cannot be reverted! Do you really want to cancel shipment?' ,
																				function(){
																									show_alert('Cancel shipment procces.')
																									frappe.call({
																									            method:'shipment_management.shipment.cancel_shipment',
																									            args: {source_name: cur_frm.doc.name}
																														})
																								  cur_frm.clear_custom_buttons();
																									location.reload();
																									},
																				function(){
																									show_alert('No canceling...')
																									}
																		   );
																		    }
																			).addClass("btn btn-primary");

											            }
				},

	refresh: function(frm) {
			cur_frm.refresh_fields();

	},

	fedex_button: function(frm) {
			create_fedex_shipment();
		}

});


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

            get_company_email()
                .done(function(email_resp){
                    frm.doc.delivery_email = email_resp.message[0].email;
                    cur_frm.refresh_fields()
                    });

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
            }
     }
)
