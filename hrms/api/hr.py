import frappe
from frappe.utils import getdate

@frappe.whitelist(methods=["POST"])
def create_regularization(**kwargs):
  try:
    if not kwargs.get("employee"):
      kwargs["employee"] = frappe.db.get_value("Employee", {"user_id": frappe.session.user})
    
    employee_details = frappe.db.get_value(
      "Employee",
      kwargs["employee"],
      ["employee_name", "department", "company"],
      as_dict=True
    )

    kwargs["from_date"] = kwargs["to_date"] = getdate(kwargs.pop("date"))
    regularization = frappe.new_doc("Attendance Regularization")
    regularization.update(kwargs)
    regularization.update(employee_details)
    regularization.save()
    return {"success": True, "doc": regularization.name}
  except Exception as e:
    frappe.log_error("Regularization Creation", frappe.get_traceback())
    raise e