frappe.ui.form.on("Delivery Note", {
    refresh: function (frm) {
        if (!in_list(["PICK_UP", "PICK UP"], frm.doc.fedex_shipping_method)) {
            frm.add_custom_button(__('Shipment'),
                function () {
                    frappe.call({
                        method: "shipment_management.utils.get_stock_items",
                        args: {
                            items: frm.doc.items
                        },
                        callback: function (r) {
                            if (r.message) {
                                frm.doc.items = r.message;
                                create_dialog(frm);
                            } else {
                                frappe.throw(__(`None of the items are deliverable. Please mark an Item
                                    to "Manage Stock" and start delivering them.`))
                            }
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
                    item_dict: item_dict,
                    doc: frm.doc
                },
                freeze: 1,
                callback: function (r) {
                    sales_orders = []
                    for (var i = 0; i < frm.doc.items.length; i++) {
                        sales_orders.push(frm.doc.items[i].against_sales_order)
                    }
                    sales_orders = Array.from(new Set(sales_orders));
                    for (var i = 0; i < sales_orders.length; i++) {
                        window.open('/desk#Form/Sales%20Order/' + sales_orders[i], '_blank');
                    }
                    frappe.set_route("Form", "DTI Shipment Note", r.message)
                }
            })
        },
        __("Assign Boxes"));
}
