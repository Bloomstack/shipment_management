frappe.ui.form.on("Delivery Note", {
    refresh: function (frm) {
        if (cur_frm.doc.status == "Completed") {
            cur_frm.add_custom_button(__('Shipment'),

                function () {
                    frappe.call({
                        method: "shipment_management.utils.get_stock_items",
                        args: {
                            items: frm.doc.items,
                        },
                        callback: function (r) {
                            frm.doc.items = r.message;
                            create_dialog(frm)
                        }
                    })


                }, __("Make"));
        }

    }
});

function create_dialog(frm) {
    args = []
    box_string = ""
    var count = 1;
    for (var i = 0; i < frm.doc.items.length; i++) {
        for (var j = 0; j < frm.doc.items[i].qty; j++) {
            box_string += "Box " + count + "\n";
            count++;
        }
    }

    var item_count = 1;
    item_dict = {}
    for (var i = 0; i < frm.doc.items.length; i++) {
        for (var j = 0; j < frm.doc.items[i].qty; j++) {
            item_dict[item_count] = frm.doc.items[i].item_code
            args.push({
                label: "Row " + frm.doc.items[i].idx + ": " + frm.doc.items[i].item_name,
                fieldname: item_count,
                fieldtype: 'Select',
                default: "Box 1",
                options: box_string.slice(0, -1)
            })
            item_count++;
        }
    }

    frappe.prompt(
        args,
        function (data) {
            frappe.call({
                method: "shipment_management.utils.create_shipment_note",
                args: {
                    items: data,
                    item_dict : item_dict,
                    doc: frm.doc
                },
                freeze : 1, 
                callback: function(r){                    
                    frappe.set_route("Form", "DTI Shipment Note", r.message)
                }
            })
        },
        __("Assign Boxes"));
}