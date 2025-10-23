import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class PolicyAcknowledgement(Document):
    pass


@frappe.whitelist()  # allows API access from JS
def save_acknowledgement(policy, employee):
    """
    Create a new Policy Acknowledgement record when user clicks the Acknowledge button.
    Automatically sets acknowledged_on = server datetime.
    """
    ack = frappe.get_doc({
        "doctype": "Policy Acknowledgement",
        "policy": policy,
        "employee": employee,
        "acknowledged_on": now_datetime()
    })
    ack.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"message": "Acknowledgement saved successfully"}
