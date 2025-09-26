import base64
import frappe
from frappe.utils import cint
from frappe import _


# ------------------ Authentication ------------------
def authenticate_user():
    auth_header = frappe.get_request_header("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        frappe.local.response["http_status_code"] = 401
        return None

    try:
        encoded_token = auth_header.split("Basic ")[1]
        decoded = base64.b64decode(encoded_token).decode("utf-8")
        api_key, api_secret = decoded.split(":")
    except Exception:
        frappe.local.response["http_status_code"] = 401
        return None

    user = frappe.db.get("User", {"api_key": api_key})
    if (
        not user
        or frappe.utils.password.get_decrypted_password("User", user.name, "api_secret") != api_secret
    ):
        frappe.local.response["http_status_code"] = 401
        return None

    return user


# ------------------ Generic List API ------------------
def get_list_api(doctype):
    """Generic list API with pagination and auth"""
    if frappe.request.method != "GET":
        frappe.local.response["http_status_code"] = 405
        return {"error": "Only GET method allowed"}

    if not authenticate_user():
        frappe.local.response["http_status_code"] = 401
        return {"error": "Unauthorized"}

    try:
        # Pagination
        limit_start = int(frappe.form_dict.get("limit_start", 0))
        raw_limit = frappe.form_dict.get("limit_page_length", 10)

        total = frappe.db.count(doctype)
        if str(raw_limit).lower() in ("0", "all"):
            limit_page_length = total
        else:
            try:
                limit_page_length = int(raw_limit)
            except ValueError:
                limit_page_length = 10

        MAX_LIMIT = 1000
        if limit_page_length > MAX_LIMIT:
            limit_page_length = MAX_LIMIT

        data = frappe.get_all(
            doctype,
            fields=["*"],
            order_by="creation desc",
            limit_start=limit_start,
            limit_page_length=limit_page_length,
        )

        return {
            "total": total,
            "limit_start": limit_start,
            "applied_limit": limit_page_length,
            "returned_count": len(data),
            "data": data,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"List API for {doctype}")
        frappe.local.response["http_status_code"] = 500
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def listUsers():
    return get_list_api("User")

@frappe.whitelist(allow_guest=True)
def listEmploymentTypes():
    return get_list_api("Employment Type")

@frappe.whitelist(allow_guest=True)
def listDesignations():
    return get_list_api("Designation")

@frappe.whitelist(allow_guest=True)
def listBranches():
    return get_list_api("Branch")

@frappe.whitelist(allow_guest=True)
def listEmployeeGrades():
    return get_list_api("Employee Grade")

@frappe.whitelist(allow_guest=True)
def listSalutations():
    return get_list_api("Salutation")

@frappe.whitelist(allow_guest=True)
def listSignatures():
    return get_list_api("Signature")

@frappe.whitelist(allow_guest=True)
def listJobApplicants():
    return get_list_api("Job Applicant")

@frappe.whitelist(allow_guest=True)
def listRelationships():
    return get_list_api("Relationship")

@frappe.whitelist(allow_guest=True)
def listHolidayLists():
    return get_list_api("Holiday List")

@frappe.whitelist(allow_guest=True)
def listShiftTypes():
    return get_list_api("Shift Type")

@frappe.whitelist(allow_guest=True)
def listEmployeeHealthInsurances():
    return get_list_api("Employee Health Insurance")


@frappe.whitelist(allow_guest=True)
def listAllRole():
    return get_list_api("Role")