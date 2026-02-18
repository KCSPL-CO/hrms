import frappe
from frappe.utils import getdate,get_last_day,add_to_date,format_time
from hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet import (
    get_columns_for_days,
    get_total_days_in_month,
)
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from frappe.query_builder.functions import Extract

@frappe.whitelist()
def get_reporting_employees():
  employee = frappe.db.get_value(
    "Employee",
    {"user_id": frappe.session.user},
    ["lft", "rgt", "employee_name", "name"],
    as_dict=True,
  )
  if employee:
    employees = [employee]
    lft = employee.lft
    rgt = employee.rgt
    if rgt - lft <= 1:
      return employees

    subordinates = (
      frappe.get_list(
        "Employee",
        filters={"lft": [">", lft], "rgt": ["<", rgt], "status": "Active"},
        fields=["name", "employee_name"],
        order_by="employee_name asc",
        limit_page_length=None,
        ignore_permissions=True,
      )
      or []
    )
    employees.extend(subordinates)
    return employees
  return frappe.get_list(
    "Employee",
    filters={"status": "Active"},
    fields=["name", "employee_name"],
    order_by="employee_name asc",
  )

@frappe.whitelist(methods=["POST"])
def get_checkin_log(month, year, employee=None):
  try:
    if not employee:
      employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})
    if not employee:
      frappe.throw("Employee not found")
    holiday_list = get_holiday_list_for_employee(employee)
    holiday_dates = get_holiday_dates_between(
      holiday_list, f"{year}-{month}-01", get_last_day(f"{year}-{month}-01")
    )

    filters = frappe._dict({"month": month, "year": year, "employee": employee})

    day_cols = get_columns_for_days(filters)
    day_map = {}
    for day in day_cols:
      day_label_split = day["label"].split()
      day_map[day_label_split[0]] = day_label_split[-1]

    attendance_list = get_attendance_records(filters)
    attendance_map = {}
    for d in attendance_list:
      attendance_map.setdefault(d.attendance_date.strftime("%d-%m-%Y"), {})
      attendance_map[d.attendance_date.strftime("%d-%m-%Y")] = {
        "status": d.status,
        "in_time": d.in_time,
        "out_time": d.out_time,
        "leave_type": d.leave_type,
        "date": d.attendance_date,
        "working_hours": d.working_hours,
        "half_day_status": d.half_day_status,
      }

    leave_applications = frappe.db.get_list(
      "Leave Application",
      filters={
        "employee": employee,
        "workflow_state": ["in", ["Draft", "Approved", "Rejected"]],
        "from_date": ["<=", get_last_day(f"{year}-{month}-01")],
        "to_date": [">=", f"{year}-{month}-01"],
      },
      fields=["from_date", "to_date", "status", "half_day"],
    )

    attendance_regularizations = frappe.db.get_list(
      "Attendance Request",
      filters={
        "employee": employee,
        "from_date": ["<=", get_last_day(f"{year}-{month}-01")],
        "to_date": [">=", f"{year}-{month}-01"],
      },
      fields=["from_date", "to_date", "workflow_state", "half_day"],
    )

    compensatory_off_requests = frappe.db.get_list(
      "Attendance Request",
      filters={
        "employee": employee,
        "from_date": ["<=", get_last_day(f"{year}-{month}-01")],
        "to_date": [">=", f"{year}-{month}-01"],
        "ignore_holiday": 1,
        "is_compensatory_leave": 1,
      },
      fields=["from_date", "to_date", "docstatus"],
    )

    work_from_home = wfh_data(month, year, employee)

    leave_application_dates = atomize_dates(leave_applications)
    attendance_regularization_dates = atomize_dates(attendance_regularizations)
    compensatory_off_request_dates = atomize_dates(compensatory_off_requests)
    work_from_home_dates = atomize_dates(work_from_home)
    
    for leave_application_date in leave_application_dates:
      date_str = leave_application_date["date"]
      attendance_map.setdefault(date_str, {})
      attendance_map[date_str]["leave_req_present"] = True
      attendance_map[date_str]["leave_status"] = leave_application_date["status"]
      attendance_map[date_str]["half_day"] = leave_application_date["half_day"]
    for attendance_regularization_date in attendance_regularization_dates:
      date_str = attendance_regularization_date["date"]
      attendance_map.setdefault(date_str, {})
      attendance_map[date_str]["reg_req_present"] = True
      attendance_map[date_str]["reg_status"] = attendance_regularization_date["status"]
    for compensatory_off_request_date in compensatory_off_request_dates:
      date_str = compensatory_off_request_date["date"]
      attendance_map.setdefault(date_str, {})
      attendance_map[date_str]["co_req_present"] = True
      attendance_map[date_str]["co_status"] = compensatory_off_request_date["status"]
    for holiday_date in holiday_dates:
      attendance_map.setdefault(holiday_date.holiday_date.strftime("%d-%m-%Y"), {})
      attendance_map[holiday_date.holiday_date.strftime("%d-%m-%Y")][
        "holiday"
      ] = holiday_date.description
    for wfh_dates in work_from_home_dates:
      date_str = wfh_dates["date"]
      attendance_map.setdefault(date_str, {})
      attendance_map[date_str]["wfh_present"] = True
      attendance_map[date_str]["wfh_status"] = wfh_dates["status"]

    data = []
    total_days = get_total_days_in_month(filters)

    for day in range(1, total_days + 1):
      attendance_map_key = f"{int(day):02}-{int(month):02}-{year}"
      row = {"date": attendance_map_key, "day": day_map.get(str(day), "")}

      if attendance_map.get(attendance_map_key, {}).get("leave_req_present", ""):
        row["leave_req_present"] = True
      if leave_status := attendance_map.get(attendance_map_key, {}).get(
        "leave_status", ""
      ):
        row["leave_status"] = leave_status
      if half_day := attendance_map.get(attendance_map_key, {}).get("half_day", ""):
        row["half_day"] = half_day
      if attendance_map.get(attendance_map_key, {}).get("reg_req_present", ""):
        row["reg_req_present"] = True
      if attendance_status := attendance_map.get(attendance_map_key, {}).get(
        "reg_status", ""
      ):
        row["reg_status"] = attendance_status
      if wfh_status := attendance_map.get(attendance_map_key, {}).get("wfh_status", ""):
        row["wfh_status"] = wfh_status
      if attendance_reg := attendance_map.get(attendance_map_key, {}).get("co_status", ""):
        row["co_status"] = attendance_reg
      if attendance_map.get(attendance_map_key, {}).get("co_req_present", ""):
        row["co_req_present"] = True
      if holiday := attendance_map.get(attendance_map_key, {}).get("holiday", ""):
        row["holiday"] = holiday
      if working_hours := attendance_map.get(attendance_map_key, {}).get(
        "working_hours", ""
      ):
        row["working_hours"] = working_hours
      if half_day_status := attendance_map.get(attendance_map_key, {}).get(
        "half_day_status", ""
      ):
        row["half_day_status"] = half_day_status

      particulars = ["in_time", "out_time"]
      for particular in particulars:
        log_time = attendance_map.get(attendance_map_key, {}).get(particular, "")
        if not log_time:
          date = attendance_map.get(attendance_map_key, {}).get("date")
          if date and getdate(date) <= getdate():
            log_filter = {
              "employee": filters.employee,
              "time": ("between", [f"{getdate(date)} 00:00:00", f"{getdate(date)} 23:59:59"]),
            }
            if particular == "In Time":
              log_filter["log_type"] = "IN"
            else:
              log_filter["log_type"] = "OUT"

            log_time = frappe.db.get_value("Employee Checkin", log_filter, "time")
        row[particular] = format_time(log_time, "HH:mm")
        status = attendance_map.get(attendance_map_key, {}).get("status", "")
      if status == "Half Day":
        if set_leave_type := attendance_map.get(attendance_map_key, {}).get("leave_type"):
          new_leave_type = frappe.db.get_value(
            "Leave Application",
            {
              "leave_type": ["!=", set_leave_type],
              "half_day": 1,
              "employee": filters.employee,
              "half_day_date": attendance_map.get(attendance_map_key, {}).get("date"),
            },
            "leave_type",
          )

          if new_leave_type:
            row["attendance"] = f"{new_leave_type}/{set_leave_type}"
          else:
            row["attendance"] = f"Half Day/{set_leave_type}"
        else:
          row["attendance"] = "Half Day/Leave Without Pay"
      elif leave_type := attendance_map.get(attendance_map_key, {}).get("leave_type"):
        row["attendance"] = leave_type
      else:
        row["attendance"] = status

      data.append(row)
    return data
  except Exception as e:
    frappe.log_error("Get Checkin Log", frappe.get_traceback())
    raise e




def get_holiday_dates_between(
  holiday_list: str,
  start_date: str,
  end_date: str,
  skip_weekly_offs: bool = False,
) -> list:
  Holiday = frappe.qb.DocType("Holiday")
  query = (
    frappe.qb.from_(Holiday)
    .select(Holiday.holiday_date, Holiday.description)
    .where(
      (Holiday.parent == holiday_list)
      & (Holiday.holiday_date.between(start_date, end_date))
    )
    .orderby(Holiday.holiday_date)
  )

  if skip_weekly_offs:
    query = query.where(Holiday.weekly_off == 0)

  return query.run(as_dict=True)


# def get_attendance_records(filters: Filters) -> List[Dict]:
#   Attendance = frappe.qb.DocType("Attendance")
#   query = (
#     frappe.qb.from_(Attendance)
#     .select(
#       Extract("day", Attendance.attendance_date).as_("day_of_month"),
#       Attendance.status,
#       Attendance.in_time,
#       Attendance.out_time,
#       Attendance.leave_type,
#       Attendance.attendance_date,
#       Attendance.working_hours,
#       Attendance.half_day_status,
#     )
#     .where(
#       (Attendance.docstatus == 1)
#       # & (Attendance.company == filters.company)
#       & (Extract("month", Attendance.attendance_date) == filters.month)
#       & (Extract("year", Attendance.attendance_date) == filters.year)
#       & (Attendance.employee == filters.employee)
#     )
#   )
#   query = query.orderby(Attendance.attendance_date)

#   return query.run(as_dict=1)

def get_attendance_records(filters):
    Attendance = frappe.qb.DocType("Attendance")
    query = (
        frappe.qb.from_(Attendance)
        .select(
            Extract("day", Attendance.attendance_date).as_("day_of_month"),
            Attendance.status,
            Attendance.in_time,
            Attendance.out_time,
            Attendance.leave_type,
            Attendance.attendance_date,
            Attendance.working_hours,
            Attendance.half_day_status,
        )
        .where(
            (Attendance.docstatus == 1)
            & (Extract("month", Attendance.attendance_date) == filters.month)
            & (Extract("year", Attendance.attendance_date) == filters.year)
            & (Attendance.employee == filters.employee)
        )
    )
    return query.orderby(Attendance.attendance_date).run(as_dict=1)


def wfh_data(month, year, employee):
  if not employee:
    return
  wfh = frappe.qb.DocType("Employee WFH")
  wfh_date = frappe.qb.DocType("Employee WFH Date")
  wfh_details = frappe.qb.DocType("Employee WFH Detail")

  if employee:
    employee = [employee]

  query = (
    frappe.qb.from_(wfh)
    .inner_join(wfh_date)
    .on(wfh_date.parent == wfh.name)
    .inner_join(wfh_details)
    .on(wfh_details.parent == wfh.name)
    .select(wfh_date.date, wfh_details.employee)
    .where(
      (wfh_details.employee.isin(employee))
      & (wfh_date.date >= f"{year}-{month}-01")
      & (wfh_date.date <= get_last_day(f"{year}-{month}-01"))
      & (wfh.docstatus == 1)
    )
  ).run(as_dict=True)

  return query if query else []


def atomize_dates(item_list):
  result_list = []

  for item in item_list:
    from_date = item.get("from_date")
    to_date = item.get("to_date")
    single_date = item.get("date")

    if from_date and to_date:
      current_date = from_date
      while current_date <= to_date:
        result_list.append(
          {
            "date": current_date.strftime("%d-%m-%Y"),
            # "status": item.get("status") or item.get("workflow_state")
            "status": "Approved"
            if item.get("docstatus") == 1
            else (item.get("workflow_state") or item.get("status")),
            "half_day": item.get("half_day"),
          }
        )
        current_date = add_to_date(current_date, days=1)

    elif single_date:
      result_list.append({"date": single_date.strftime("%d-%m-%Y"), "status": "Approved"})

  return result_list