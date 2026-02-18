// Copyright (c) 2025, Wahni IT Solutions and contributors
// For license information, please see license.txt

frappe.provide('octa.AttendanceToolkit');

octa.AttendanceToolkit.Controller = class {
    constructor(wrapper) {
        this.wrapper = $(wrapper).find('.layout-main-section');
        this.page = wrapper.page;
        this.prepare_dom();

        this.isManager = false;
        this.employee = null;
        this.isSystemManager = false;
        this.managerRegularizationWindow = 0;
        this.employeeRegularizationWindow = 0;

        this.fetchAttendanceData = this.fetchAttendanceData.bind(this);
        this.openRegularizationModal = this.openRegularizationModal.bind(this);
        this.openCORequestModal = this.openCORequestModal.bind(this);
        this.newLeaveDoc = this.newLeaveDoc.bind(this);
        this.initialize().then(() => {
            this.fetchAttendanceData();
            this.fetchCurrentYear();
        });
    }

    prepare_dom() {
        this.wrapper.html("");
        this.wrapper.append(
            `
            <div id="content">
                <div class="container my-4 p-4 position-relative">
                    <button id="get-attendance" class="btn btn-primary position-absolute" style="top: 0px; right: 20px;">
                        Get Attendance
                    </button>
                    <div class="mb-4">
                        <!-- <div class="form-group">
                            <div class="name-box" id="name-text">Test Api</div>
                        </div> -->

                        <div class="form-group">
                            <div>
                                <label for="employee-select">Employee:</label>
                                <select id="employee-select" class="form-control mb-2" style="width: 100%;">
                                </select>
                                <label for="month-select">Month:</label>
                                <select id="month-select" class="form-control mb-2" style="width: 100%;">
                                    <option value="January">January</option>
                                    <option value="February">February</option>
                                    <option value="March">March</option>
                                    <option value="April">April</option>
                                    <option value="May">May</option>
                                    <option value="June">June</option>
                                    <option value="July">July</option>
                                    <option value="August">August</option>
                                    <option value="September">September</option>
                                    <option value="October">October</option>
                                    <option value="November">November</option>
                                    <option value="December">December</option>
                                </select>

                            </div>
                            <div>
                                <label for="year-select">Year:</label>
                                <select id="year-select" class="form-control" style="width: 100%;">
                                    // <option value="2026">2026</option>
                                    // <option value="2025">2025</option>
                                    // <option value="2024">2024</option>
                                    // <option value="2023">2023</option>
                                    // <option value="2022">2022</option>
                                </select>
                            </div>
                        </div>

                    </div>

                    <table class="table table-bordered table-hover log-table" id="attendance-table">
                        <thead class="thead-light">
                            <tr>
                                <th>Date</th>
                                <th>Day</th>
                                <th>In</th>
                                <th>Out</th>
                                <th>Total Hrs</th>
                                <th>Activity</th>
                                <th>Info/Action</th>
                            </tr>
                        </thead>
                        <tbody>

                        </tbody>
                    </table>
                </div>
            </div>

            <div class="modal fade" id="regularizationModal" tabindex="-1" role="dialog" aria-labelledby="modalTitle"
                aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modalTitle">Regularization Request</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <form id="regularizationForm">
                                <label for="date">Date:</label>
                                <input type="text" id="regularizationDate" readonly>

                                <div class="form-group">
                                    <label for="explanation">Explanation:</label>
                                    <textarea id="explanation" class="form-control" rows="4"
                                        placeholder="Enter explanation"></textarea>
                                </div>
                                <label for="reason">Reason:</label>
                                <select id="reason" name="reason">
                                    <option value="Work From Home">Work From Home</option>
                                    <option value="On Duty">On Duty</option>
                                </select>
                                <br>
                                <button type="button" class="btn btn-primary" id="submitRegularization">Submit</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            `
        )
    }

    async initialize() {
        const openRegularizationModalCapture = this.openRegularizationModal;
        const openCORequestModalCapture = this.openCORequestModal;
        const newLeaveDocCapture = this.newLeaveDoc;

        document.getElementById('get-attendance').addEventListener('click', this.fetchAttendanceData);

        const employeeSelect = document.getElementById('employee-select');
        employeeSelect.innerHTML = '';

        frappe.call({
           
            method: "hrms.api.report.get_reporting_employees",
            callback: (r) => {
                if (r.message) {
                    r.message.forEach(employee => {
                        let option = document.createElement('option');
                        option.value = employee.name;
                        option.text = employee.employee_name;
                        employeeSelect.appendChild(option);
                    });
                }
            }
        });

        let response = await frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["name", "is_manager"])
        if (response.message.name) {
            document.getElementById("employee-select").value = response.message.name;
        }
        else {
            document.getElementById("employee-select").value = null;
        }

        const currentMonth = new Date().toLocaleString('default', { month: 'long' });
        document.getElementById('month-select').value = currentMonth;

        if (response.message.is_manager) {
            this.isManager = true;
        }

        this.isSystemManager = frappe.user_roles.includes("System Manager");
        let hrSettings = await frappe.db.get_doc("HR Settings");
        this.managerRegularizationWindow = hrSettings.manager_regularization_window;
        this.employeeRegularizationWindow = hrSettings.employee_regularization_window;

        document.getElementById('content').classList.add('loading-content');
        document.addEventListener('click', function (event) {
            if (event.target && event.target.classList.contains('apply-leave-button')) {
                newLeaveDocCapture(event.target.dataset.date);
            }
            else if (event.target && event.target.classList.contains('regularization')) {
                openRegularizationModalCapture(event.target.dataset.date);
            }
            else if (event.target && event.target.classList.contains('CORequest')) {
                openCORequestModalCapture(event.target.dataset.date);
            }
            else if (event.target && event.target.classList.contains('regularizationReject')) {
                frappe.show_alert({"message": "You can only apply for regularization within 3 days.", "indicator": "red"});
            }
        });
    }

    fetchCurrentYear() {
        document.getElementById("year-select").innerHTML =
            `<option value="${new Date().getFullYear()}">${new Date().getFullYear()}</option>`;
    }


    async fetchAttendanceData() {
        const monthMapping = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12
        };

        const selectedMonthName = document.getElementById('month-select').value;
        const month = monthMapping[selectedMonthName];

        if (!month) {
            frappe.throw("Please select a month.");
        }

        const year = parseInt(document.getElementById('year-select').value, 10);
        const employee = document.getElementById('employee-select').value;
        if (!employee) {
            frappe.throw("Please select an employee.");
        }

        this.employee = employee;
        let sessionEmployee = await frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name");
        sessionEmployee = sessionEmployee.message.name;

        frappe.call({
            method: "hrms.api.report.get_checkin_log",
            args: {
                'month': month,
                'year': year,
                'employee': employee
            },
            freeze: true,
            freeze_message: "Fetching attendance data...",
            callback: (data) => {
                if (data.message) {
                    const tableBody = document
                        .getElementById('attendance-table')
                        .getElementsByTagName('tbody')[0];

                    tableBody.innerHTML = '';
                    let today = new Date();
                    var regAllowed;
                    data.message.forEach(item => {
                        // let leaveRequestPresent = item.leave_req_present || false;
                        let leaveRequestPresent = "";
                        if (item.leave_status === "Approved") {
                            leaveRequestPresent = "Leave Approved";
                        } else if (item.leave_req_present) {
                            leaveRequestPresent = "Leave Applied";
                        }
                        // let regRequestPresent = item.reg_req_present || false;
                        let regRequestPresent = "";
                        if (item.wfh_status === "Approved") {
                            regRequestPresent = "WFH";
                        } else if (item.reg_status === "Approved"){
                            regRequestPresent = "Reg.Approved"
                        }
                        else if (item.reg_req_present) {
                            regRequestPresent = "Regularization Applied";
                        }
                        // let cORequestPresent = item.co_req_present || false;
                        let cORequestPresent = "";
                        if (item.co_status === "Approved"){
                            cORequestPresent = "CO Approved"
                        } else if(item.co_req_present){
                            cORequestPresent = "CO Requested"
                        }
                        let requestPresent = leaveRequestPresent || regRequestPresent;
                        let row = document.createElement('tr');
                        let attendance = item.attendance || '';
                        let regRelevant = !item.holiday && attendance && attendance != "Present" && attendance != "Work From Home" && item.reg_req_present != true && (item.half_day_status != "Present" || !requestPresent);
                        let showCORequestButton = item.holiday && !cORequestPresent;
                        let showLeaveButton = !item.holiday && attendance != "Present" && attendance != "Work From Home" && !requestPresent;
                        let splitDateArray = String(item.date).split("-")
                        let sqlDate = splitDateArray[2] + "-" + splitDateArray[1] + "-" + splitDateArray[0]
                        let itemDate = new Date(sqlDate);
                        let daysDiff = frappe.datetime.get_day_diff(today, itemDate);
                        let dateString = frappe.datetime.obj_to_str(itemDate);
                        if (this.isSystemManager) {
                            regAllowed = true;
                        }
                        else if (this.isManager && employee != sessionEmployee) {
                            if (daysDiff < this.managerRegularizationWindow) {
                                regAllowed = true;
                            }
                            else {
                                regAllowed = false;
                            }
                        }
                        else {
                            if (daysDiff < this.employeeRegularizationWindow) {
                                regAllowed = true;
                            }
                            else {
                                regAllowed = false;
                            }
                        }

                        row.innerHTML = `
                            <td>${item.date || ''}</td>
                            <td>${item.day || ''}</td>
                            <td>${item["in_time"] || ''}</td>
                            <td>${item["out_time"] || ''}</td>
                            <td>${item["working_hours"] || ''}</td>
                            <td>${item.attendance || ''}</td>
                            <td>
                                ${item.holiday ? `
                                    ${item.holiday}` : ''}
                                ${showCORequestButton ? `
                                    <br><button class="btn btn-info btn-sm action-button CORequest"
                                        data-toggle="modal"
                                        data-date="${dateString}"
                                        onclick="()=>{}">
                                        Request CO
                                    </button>` : ''}
                                ${cORequestPresent ? cORequestPresent: ''}
                                ${(regRelevant && regAllowed) ? `
                                    <button class="btn btn-success btn-sm action-button regularization"
                                        data-toggle="modal"
                                        data-date="${dateString}"
                                        onclick="()=>{}">
                                        Regularization
                                    </button>` : ''}
                                ${(regRelevant && !regAllowed) ? `
                                    <button class="btn btn-secondary btn-sm action-button regularizationReject"
                                        data-toggle="modal"
                                        onclick="()=>{}">
                                        Regularization
                                    </button>` : ''}
                                ${showLeaveButton ? `
                                    <button class="btn btn-warning btn-sm action-button absent apply-leave-button"
                                        data-date="${dateString}">
                                        Apply leave
                                    </button>` : ''}
                                ${leaveRequestPresent ? leaveRequestPresent : ''}
                                ${regRequestPresent ? regRequestPresent : ''}
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                }
                document.getElementById('content').classList.remove('loading-content');
    	    }
        });
    }



    openRegularizationModal(date) {
        const fetchAttendanceDataCapture = this.fetchAttendanceData;
        let employee = this.employee;
        let d = new frappe.ui.Dialog({
            title: 'Regularization Request',
            fields: [
                {
                    label: 'Date',
                    fieldname: 'date',
                    fieldtype: 'Date',
                    read_only: 1,
                },
                {
                    fieldtype: 'Column Break',
                    fieldname: 'column_break'
                },
                {
                    label: 'Reason',
                    fieldname: 'reason',
                    fieldtype: 'Select',
                    options: ['Work From Home', 'On Duty']
                },
                {
                    fieldtype: "Check",
                    fieldname: "half_day",
                    label: "Half Day"
                },
                {
                    fieldtype: "Date",
                    fieldname: "half_day_date",
                    label: "Half Day Date",
                    depends_on: "half_day",
                    mandatory_depends_on: "half_day"
                },
                {
                    fieldtype: 'Section Break',
                    fieldname: 'section_break'
                },
                {
                    label: 'Explanation',
                    fieldname: 'explanation',
                    fieldtype: 'Small Text'
                }
            ],
            size: 'medium',
            primary_action_label: 'Submit Regularization',
            primary_action(values) {
                let args = {
                    employee: employee,
                    date: values.date,
                    reason: values.reason,
                    explanation: values.explanation,
                }
                if (values.half_day === 1){
                    args.half_day = values.half_day,
                    args.half_day_date = values.half_day_date
                }

                frappe.call({
                    method: "hrms.api.hr.create_regularization",
                    args: args,
                    freeze: true,
                    freeze_message: "Submitting Regularization...",
                    callback: (response) => {
                        if (!response.exc) {
                            frappe.show_alert({"message": "Regularization request submitted successfully.", "indicator": "green"});
                        }
                        d.hide();
                        // fetchAttendanceDataCapture();
                    },
                });
            }
        });
        d.show();
        d.set_value('date', date);
    }

    openCORequestModal(date) {
        let employee = this.employee;
        let d = new frappe.ui.Dialog({
            title: 'Compensatory Off Request',
            fields: [
                {
                    label: 'Date',
                    fieldname: 'date',
                    fieldtype: 'Date',
                    read_only: 1,
                },
                {
                    fieldtype: 'Column Break',
                    fieldname: 'column_break'
                },
                {
                    label: 'Reason',
                    fieldname: 'reason',
                    fieldtype: 'Select',
                    options: ['Work From Home', 'On Duty']
                },
                {
                    fieldtype: 'Section Break',
                    fieldname: 'section_break'
                },
                {
                    label: 'Explanation',
                    fieldname: 'explanation',
                    fieldtype: 'Small Text'
                }
            ],
            size: 'medium',
            primary_action_label: 'Submit CO Request',
            primary_action(values) {
                frappe.call({
                    method: "hrms.api.hr.create_attendance_request",
                    args: {
                        employee: employee,
                        date: values.date,
                        reason: values.reason,
                        explanation: values.explanation,
                        ignore_holiday: 1,
                        is_compensatory_leave: 1,
                    },
                    freeze: true,
                    freeze_message: "Submitting CO Request...",
                    callback: (response) => {
                        if (!response.exc) {
                            frappe.show_alert({"message": "CO request submitted successfully.", "indicator": "green"});
                        }
                        d.hide();
                    },
                });
            }
        });
        d.show();
        d.set_value('date', date);
    }

    newLeaveDoc(date) {
        frappe.new_doc("Leave Application", {
            "employee": this.employee,
        }).then(() => {
            cur_frm.set_value("from_date", date);
            cur_frm.set_value("to_date", date);
        });
    }
}