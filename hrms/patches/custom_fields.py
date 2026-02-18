import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "System Settings": [
                {
                    "fieldname": "custom_keys_tab",
                    "fieldtype": "Tab Break",
                    "label": "Custom Keys",
                    "insert_after": "log_api_requests",
                },
                {
                    "fieldname": "azure_key",
                    "fieldtype": "Data",
                    "label": "Azure Key",
                    "insert_after": "custom_keys_tab",
                },
                {
                    "fieldname": "distance_api",
                    "fieldtype": "Link",
                    "options": "URL Response Fields",
                    "label": "Distance API",
                    "insert_after": "azure_key",
                },
                {
                    "fieldname": "location_api",
                    "fieldtype": "Link",
                    "options": "URL Response Fields",
                    "label": "Location API",
                    "insert_after": "distance_api",
                },
            ],
            "User": [
                {
                    "fieldname": "vehicle_type",
                    "fieldtype": "Select",
                    "label": "Vehicle Type",
                    "options": "\nBike\nCar\nBoth",
                    "insert_after": "username",
                },
                {
                    "fieldname": "device_id",
                    "fieldtype": "Data",
                    "label": "Device ID",
                    "insert_after": "vehicle_type",
                    "read_only": 1
                },
                {
                    "fieldname": "reset_deviceid",
                    "fieldtype": "Button",
                    "label": "Reset Device Id",
                    "insert_after": "device_id",
                    "depends_on": "eval:doc.device_id",
                }
                
            ],
           "Employee": [
                {
                    "fieldname": "field_employee",
                    "fieldtype": "Select",
                    "label": "Field Employee",
                    "options": "\nYes\nNo",
                    "reqd": 1,
                    "insert_after": "status",
                },
                {
                    "fieldname": "is_manager",
                    "fieldtype": "Check",
                    "label": "Is Manager",
                    "insert_after": "field_employee",
                }
                
            ],
            "Attendance Request":[
                {
                    "fieldname": "ignore_holiday",
                    "fieldtype": "Check",
                    "label": "Ignore Holiday",
                    "insert_after": "include_holidays",
                },
                {
                    "fieldname": "is_compensatory_leave",
                    "fieldtype": "Check",
                    "label": "Is Compensatory Leave",
                    "insert_after": "ignore_holiday",
                }
            ]
        }
    )
