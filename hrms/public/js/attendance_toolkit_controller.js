frappe.provide('octa.AttendanceToolkit');

octa.AttendanceToolkit.Controller = class {

    constructor(wrapper) {
        this.wrapper = $(wrapper).find('.layout-main-section');
        this.page = wrapper.page;

        this.isManager = false;
        this.employee = null;
        this.isSystemManager = false;
        this.managerRegularizationWindow = 0;
        this.employeeRegularizationWindow = 0;

        this.fetchAttendanceData = this.fetchAttendanceData.bind(this);
        this.openRegularizationModal = this.openRegularizationModal.bind(this);
        this.openCORequestModal = this.openCORequestModal.bind(this);
        this.newLeaveDoc = this.newLeaveDoc.bind(this);

        this.prepare_dom();
        this.initialize();
    }

    // ==============================
    // UI
    // ==============================

    prepare_dom() {
        this.wrapper.html("");

        this.wrapper.append(`
<style>

/* ================= GLOBAL ================= */
#content {
    animation: fadeIn .4s ease;
}

@keyframes fadeIn {
    from {opacity:0; transform:translateY(8px);}
    to {opacity:1; transform:translateY(0);}
}

body {
    background:#f5f7fb;
}
    /* ===== STATUS TEXT ONLY ===== */
.status-text {
    font-weight:600;
    font-size:13px;
}

.text-present { color:#16a34a; }
.text-wfh { color:#0284c7; }
.text-absent { color:#dc2626; }
.text-leave { color:#f59e0b; }
.text-holiday { color:#7c3aed; }
.text-late { color:#ef4444; font-size:11px; }
.text-early { color:#ea580c; font-size:11px; }
    /* ===== STATUS BADGES ===== */
.status-badge {
    padding:4px 10px;
    border-radius:20px;
    font-size:12px;
    font-weight:600;
    display:inline-block;
}

.badge-present { background:#dcfce7; color:#166534; }
.badge-wfh { background:#e0f2fe; color:#075985; }
.badge-absent { background:#fee2e2; color:#991b1b; }
.badge-leave { background:#fef9c3; color:#854d0e; }
.badge-holiday { background:#ede9fe; color:#5b21b6; }
.badge-halfday { background:#ffedd5; color:#9a3412; }
.badge-late { background:#fca5a5; color:#7f1d1d; }
.badge-early { background:#fed7aa; color:#9a3412; }

/* ===== LEGEND ===== */
.legend-box {
    background:#fff;
    border-radius:12px;
    padding:12px 15px;
    margin-bottom:15px;
    box-shadow:0 8px 20px rgba(0,0,0,0.05);
    font-size:13px;
}

.legend-box span {
    margin-right:15px;
}

/* ================= PROFILE CARD ================= */
.profile-card {
    background: var(--card-bg, #ffffff);
    color: var(--text-color, #111827);
    border-radius:18px;
    padding:25px;
    box-shadow:0 15px 35px rgba(0,0,0,0.08);
    margin-bottom:25px;
}

[data-theme="dark"] .profile-card {
    background:#1f2937;
    color:#f3f4f6;
}

.profile-card:hover {
    transform:translateY(-3px);
}

.profile-card h4 {
    font-weight:600;
    margin-bottom:8px;
}

.profile-card small {
    opacity:.8;
}

.profile-card img {
    border:4px solid rgba(255,255,255,.2);
}

/* ================= ATTENDANCE CIRCLE ================= */
.percent-circle {
    width:120px;
    height:120px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:700;
    font-size:20px;
    background:conic-gradient(#10b981 0%, #e5e7eb 0%);
    box-shadow:inset 0 4px 12px rgba(0,0,0,.2);
}

/* ================= FILTER CONTAINER ================= */
.dashboard-container {
    background:#fff;
    border-radius:18px;
    padding:25px;
    box-shadow:0 15px 35px rgba(0,0,0,0.06);
}

/* ================= BUTTON ================= */
#get-attendance {
    border-radius:30px;
    padding:6px 18px;
    font-weight:500;
    transition:.3s ease;
}

#get-attendance:hover {
    transform:scale(1.05);
}

/* ================= TABLE ================= */
#attendance-table {
    border-radius:12px;
    overflow:hidden;
}

#attendance-table thead th {
    background:#111827;
    color:#fff;
    font-weight:500;
    font-size:14px;
    border:none;
}

#attendance-table tbody tr {
    transition:.2s ease;
}

#attendance-table tbody tr:hover {
    background:#f3f4f6;
    transform:scale(1.002);
}

#attendance-table td {
    vertical-align:middle;
    font-size:14px;
}

/* ================= STATUS BADGES ================= */
.badge-present {
    background:#dcfce7;
    color:#166534;
    padding:4px 10px;
    border-radius:20px;
    font-size:12px;
    font-weight:600;
}

.badge-wfh {
    background:#e0f2fe;
    color:#075985;
    padding:4px 10px;
    border-radius:20px;
    font-size:12px;
    font-weight:600;
}

.badge-leave {
    background:#fee2e2;
    color:#991b1b;
    padding:4px 10px;
    border-radius:20px;
    font-size:12px;
    font-weight:600;
}

/* ================= ACTION BUTTONS ================= */
#get-attendance {
    border-radius:30px;
    font-weight:500;
    transition:.3s ease;
}

#get-attendance:hover {
    transform:scale(1.05);
}
.btn-sm {
    border-radius:20px;
    padding:4px 12px;
    font-size:12px;
    margin:2px;
    transition:.2s ease;
}

.btn-sm:hover {
    transform:translateY(-2px);
}
/* ================= CARD VIEW ================= */

.attendance-card {
    flex-direction:column;
    align-items:flex-start;
    padding:8px;
    font-size:12px;
    min-height:90px;
}

.attendance-card {
    background:#fff;
    border-radius:12px;
    padding:10px 14px; /* reduced */
    box-shadow:0 5px 15px rgba(0,0,0,0.05);
    display:flex;
    justify-content:space-between;
    align-items:center;
    transition:.2s ease;
    border-left:5px solid #e5e7eb;
}

.attendance-card:hover {
    transform:translateY(-4px);
    box-shadow:0 15px 35px rgba(0,0,0,0.12);
}

.card-left {
    flex:1;
}

.card-date {
    font-weight:600;
    font-size:15px;
}

.card-time {
   font-size:12px;
    opacity:.75;
}

.card-badges {
    margin-top:4px;
}

.card-left {
    display:flex;
    flex-direction:column;
    gap:3px;
}

.card-actions {
    display:flex;
    gap:6px;
    align-items:center;
}

.card-actions button {
    margin:3px;
}
.refresh-spin {
    animation: spin .6s linear;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
/* STATUS BORDER COLORS */
.border-present { border-left-color:#10b981; }
.border-wfh { border-left-color:#0ea5e9; }
.border-absent { border-left-color:#ef4444; }
.border-leave { border-left-color:#f59e0b; }
.border-holiday { border-left-color:#8b5cf6; }

/* DARK MODE */
[data-theme="dark"] .attendance-card {
    background:#1f2937;
    color:#f3f4f6;
}
/* ================= DROPDOWN ================= */
select.form-control {
    border-radius:10px;
    border:1px solid #e5e7eb;
    transition:.2s ease;
}
/* ===== STICKY SUMMARY ===== */
.sticky-summary {
    position:sticky;
    top:0;
    z-index:100;
    background:#ffffff;
    padding:12px 20px;
    border-radius:12px;
    display:flex;
    justify-content:space-between;
    box-shadow:0 8px 20px rgba(0,0,0,0.08);
    margin-bottom:18px;
}

.summary-item {
    text-align:center;
}

.summary-title {
    font-size:12px;
    opacity:.6;
}

.summary-value {
    font-size:18px;
    font-weight:700;
}
select.form-control:focus {
    border-color:#10b981;
    box-shadow:0 0 0 2px rgba(16,185,129,.15);
}
.filter-chips {
    margin-top:10px;
    margin-bottom:15px;
}

.chip {
    display:inline-block;
    padding:6px 14px;
    border-radius:20px;
    background:#e5e7eb;
    cursor:pointer;
    font-size:12px;
    margin-right:8px;
    transition:.2s ease;
}

.chip.active {
    background:#111827;
    color:#fff;
}
    .heatmap-grid {
    display:grid;
    grid-template-columns: repeat(7, 1fr);
    gap:6px;
    margin-bottom:20px;
}

.heat-cell {
    height:22px;
    border-radius:4px;
    background:#e5e7eb;
}

.heat-present { background:#10b981; }
.heat-wfh { background:#0ea5e9; }
.heat-leave { background:#f59e0b; }
.heat-absent { background:#ef4444; }
.heat-holiday { background:#8b5cf6; }
/* ===== Animated Progress Bar ===== */

.progress-wrapper {
    width:100%;
}

.progress-label {
    display:flex;
    justify-content:space-between;
    font-size:13px;
    font-weight:600;
    margin-bottom:6px;
}

.progress-bar-bg {
    width:100%;
    height:10px;
    background:#e5e7eb;
    border-radius:20px;
    overflow:hidden;
}
/* ===== CALENDAR GRID ===== */
.attendance-calendar {
    display:grid;
    grid-template-columns: repeat(7, 1fr);
    gap:10px;
}

.calendar-header {
    font-weight:600;
    text-align:center;
    padding:8px 0;
    background:#111827;
    color:#fff;
    border-radius:6px;
    font-size:13px;
}

.calendar-day {
    min-height: 150px; /* increase height */
    background:#fff;
    border-radius:10px;
    padding:10px;
    box-shadow:0 4px 10px rgba(0,0,0,0.05);

    display:flex;
    flex-direction:column;
    justify-content:space-between; /* important */
}

.calendar-day:hover {
    transform:translateY(-3px);
}
.day-content {
    flex-grow: 1;
    font-size: 11px;
    line-height: 1.3;
    overflow: hidden;
}
/* ===== ACTION BADGES ===== */
.action-badge {
    display:inline-block;
    padding:4px 10px;
    border-radius:20px;
    font-size:11px;
    font-weight:600;
    cursor:pointer;
    transition:.2s ease;
}

.action-co {
    background:#e0f2fe;
    color:#075985;
}

.action-regularize {
    background:#dcfce7;
    color:#166534;
}

.action-leave {
    background:#fef3c7;
    color:#92400e;
}

.action-badge:hover {
    transform:scale(1.05);
    opacity:.9;
}
.day-actions {
    margin-top:8px;
    display:flex;
    gap:6px;
    flex-wrap:wrap;
}
.day-number {
    font-size:13px;
    font-weight:600;
}

.day-content {
    font-size:11px;
}

.empty-day {
    background:transparent;
    box-shadow:none;
}
.progress-bar-fill {
    height:100%;
    width:0%;
    background:linear-gradient(90deg,#10b981,#22c55e);
    border-radius:20px;
    transition:width 1s ease;
}
    .calendar-day {
    min-height: 160px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
}

.day-content {
    flex-grow:1;
    font-size:12px;
}

.day-actions {
    margin-top:8px;
    display:flex;
    gap:6px;
    flex-wrap:wrap;
}
</style>

<div id="content">

    <!-- PROFILE -->
    <div class="profile-card row align-items-center">
        <div class="col-md-2 text-center">
            <img id="empPhoto"
                 src="/assets/frappe/images/ui/avatar.png"
                 style="width:90px;height:90px;border-radius:50%;">
        </div>

        <div class="col-md-6">
            <h4 id="empName"></h4>
            <small id="empDept"></small><br>
            <small id="empId"></small><br>
            <small id="empJoin"></small>
        </div>

        <div class="col-md-4 text-center">
           <div class="progress-wrapper">
    <div class="progress-label">
        Attendance Performance
        <span id="percentText">0%</span>
    </div>

    <div class="progress-bar-bg">
        <div id="attendanceProgress" class="progress-bar-fill"></div>
    </div>
</div>
    
        </div>
    </div>

    <!-- FILTER + TABLE -->
    <div id="sticky-summary" class="sticky-summary">
    <div class="summary-item">
        <div class="summary-title">Present</div>
        <div id="summary-present" class="summary-value">0</div>
    </div>

    <div class="summary-item">
        <div class="summary-title">Absent</div>
        <div id="summary-absent" class="summary-value">0</div>
    </div>

    <div class="summary-item">
        <div class="summary-title">Leave</div>
        <div id="summary-leave" class="summary-value">0</div>
    </div>

    <div class="summary-item">
        <div class="summary-title">Streak</div>
        <div id="summary-streak" class="summary-value">0 🔥</div>
    </div>
</div>
    <div class="dashboard-container position-relative">
<div class="legend-box d-flex flex-wrap align-items-center justify-content-between">

    <div>
        <span class="status-badge badge-present">Present</span>
        <span class="status-badge badge-wfh">WFH</span>
        <span class="status-badge badge-absent">Absent</span>
        <span class="status-badge badge-leave">Leave</span>
        <span class="status-badge badge-holiday">Holiday</span>
        <span class="status-badge badge-halfday">Half Day</span>
        <span class="status-badge badge-late">Late</span>
        <span class="status-badge badge-early">Early Exit</span>
    </div>
    <div id="filter-chips" class="filter-chips">
    <span class="chip active" data-filter="all">All</span>
    <span class="chip" data-filter="Present">Present</span>
    <span class="chip" data-filter="Absent">Absent</span>
    <span class="chip" data-filter="Leave">Leave</span>
    <span class="chip" data-filter="Work From Home">WFH</span>
</div>
    <div>
        <span id="get-attendance"
            class="status-badge"
            style="background:#111827;color:#fff;cursor:pointer;">
            ⟳ Refresh
        </span>
    </div>
<div id="heatmap" class="heatmap-grid"></div>

</div>


        <div class="row mb-4">
            <div class="col-md-4">
                <label>Employee</label>
                <select id="employee-select" class="form-control mb-2"></select>
            </div>

            <div class="col-md-4">
                <label>Month</label>
                <select id="month-select" class="form-control mb-2">
                    ${[
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ].map(m => `<option value="${m}">${m}</option>`).join("")}
                </select>
            </div>

            <div class="col-md-4">
                <label>Year</label>
                <select id="year-select" class="form-control"></select>
            </div>
        </div>

     <div id="attendance-calendar" class="attendance-calendar"></div>

    </div>
</div>
`);
    }

    // ==============================
    // INIT
    // ==============================
    fetchCurrentYear() {
        const currentYear = new Date().getFullYear();

        const yearSelect = document.getElementById("year-select");
        if (!yearSelect) return;

        yearSelect.innerHTML =
            `<option value="${currentYear}">${currentYear}</option>`;
    }
    async initialize() {

        const openRegularizationModalCapture = this.openRegularizationModal;
        const openCORequestModalCapture = this.openCORequestModal;
        const newLeaveDocCapture = this.newLeaveDoc;

        // ============================
        // PROFILE SECTION (NEW UI)
        // ============================

        let emp = await frappe.db.get_value(
            "Employee",
            { user_id: frappe.session.user },
            ["name", "employee_name", "department", "date_of_joining", "image", "is_manager"]
        );

        if (!emp.message) return;

        this.employee = emp.message.name;
        this.isManager = emp.message.is_manager;
        this.isSystemManager = frappe.user_roles.includes("System Manager");

        document.getElementById("empName").innerText = emp.message.employee_name || "";
        document.getElementById("empDept").innerText =
            "Department: " + (emp.message.department || "-");
        document.getElementById("empId").innerText =
            "Employee ID: " + emp.message.name;
        document.getElementById("empJoin").innerText =
            "Joining: " + frappe.datetime.str_to_user(emp.message.date_of_joining);

        if (emp.message.image) {
            document.getElementById("empPhoto").src = emp.message.image;
        }

        // ============================
        // ORIGINAL EMPLOYEE DROPDOWN LOGIC
        // ============================

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

                // Default logged in employee selected
                employeeSelect.value = this.employee;
            }
        });

        // ============================
        // MONTH DEFAULT
        // ============================

        const currentMonth = new Date().toLocaleString('default', { month: 'long' });
        document.getElementById('month-select').value = currentMonth;

        // ============================
        // HR SETTINGS
        // ============================

        let hrSettings = await frappe.db.get_doc("HR Settings");
        this.managerRegularizationWindow = hrSettings.manager_regularization_window;
        this.employeeRegularizationWindow = hrSettings.employee_regularization_window;

        // ============================
        // BUTTON LISTENERS (ORIGINAL)
        // ============================

        document.getElementById('get-attendance')
            .addEventListener('click', (e) => {

                e.target.classList.add("refresh-spin");

                setTimeout(() => {
                    e.target.classList.remove("refresh-spin");
                }, 600);

                this.fetchAttendanceData();
            });

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
                frappe.show_alert({
                    "message": "You can only apply for regularization within allowed window.",
                    "indicator": "red"
                });
            }

        });
        document.querySelectorAll(".chip").forEach(chip => {
            chip.addEventListener("click", (e) => {

                document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
                chip.classList.add("active");

                this.activeFilter = chip.dataset.filter;
                this.fetchAttendanceData();
            });
        });
        document.getElementById("employee-select")
            .addEventListener("change", this.fetchAttendanceData);

        document.getElementById("month-select")
            .addEventListener("change", this.fetchAttendanceData);

        document.getElementById("year-select")
            .addEventListener("change", this.fetchAttendanceData);

        // ============================
        // YEAR
        // ============================

        this.fetchCurrentYear();

        // ============================
        // FIRST LOAD
        // ============================

        this.fetchAttendanceData();
    }

    // ==============================
    // FETCH (FULL ORIGINAL LOGIC)
    // ==============================
    // ======================================================
    // FULL CLEAN WORKING fetchAttendanceData()
    // ======================================================

    async fetchAttendanceData() {

        const monthMap = {
            January: 1, February: 2, March: 3, April: 4,
            May: 5, June: 6, July: 7, August: 8,
            September: 9, October: 10, November: 11, December: 12
        };

        const selectedMonthName = document.getElementById('month-select').value;
        const month = monthMap[selectedMonthName];
        const year = parseInt(document.getElementById('year-select').value, 10);
        const employee = document.getElementById('employee-select').value;

        if (!month) return frappe.throw("Please select a month.");
        if (!employee) return frappe.throw("Please select an employee.");

        this.employee = employee;

        frappe.call({
            method: "hrms.api.report.get_checkin_log",
            args: { month, year, employee },
            freeze: true,
            freeze_message: "Fetching attendance data...",
            callback: (data) => {

                if (!data.message) return;

                // ======================================================
                // GET DOM ELEMENTS
                // ======================================================

                const heatmap = document.getElementById("heatmap");
                const container = document.getElementById("attendance-calendar");
                container.innerHTML = "";

                if (heatmap) heatmap.innerHTML = "";
                if (container) container.innerHTML = "";

                const fullData = data.message;
                // ===============================
                // 🗓 ADD WEEK HEADERS
                // ===============================
                const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

                weekDays.forEach(day => {
                    container.innerHTML += `
        <div class="calendar-header">${day}</div>
    `;
                });
                // ===============================
                // ALIGN FIRST DAY OF MONTH
                // ===============================
                const firstDate = new Date(year, month - 1, 1);
                const startDay = firstDate.getDay();

                for (let i = 0; i < startDay; i++) {
                    container.innerHTML += `
        <div class="calendar-day empty-day"></div>
    `;
                }
                // ======================================================
                // SECTION 1 → SUMMARY + STREAK + HEATMAP
                // ======================================================

                let present = 0;
                let absent = 0;
                let leave = 0;
                let streak = 0;
                let maxStreak = 0;

                fullData.forEach(item => {

                    const attendance = item.attendance || "";

                    // ===== SUMMARY COUNTS =====
                    if (attendance === "Present" || attendance === "Work From Home") {
                        present++;
                        streak++;
                        if (streak > maxStreak) maxStreak = streak;
                    } else {
                        streak = 0;
                    }

                    if (attendance === "Absent") absent++;
                    if (attendance === "Leave" || attendance === "On Leave") leave++;

                    // ===== HEATMAP COLOR =====
                    let heatClass = "heat-absent";

                    if (item.holiday) heatClass = "heat-holiday";
                    else if (attendance === "Present") heatClass = "heat-present";
                    else if (attendance === "Work From Home") heatClass = "heat-wfh";
                    else if (attendance === "Leave" || attendance === "On Leave") heatClass = "heat-leave";

                    if (heatmap) {
                        heatmap.innerHTML += `
                        <div class="heat-cell ${heatClass}" 
                             title="${item.date} - ${attendance}">
                        </div>
                    `;
                    }
                });

                // ======================================================
                // SECTION 2 → UPDATE SUMMARY UI
                // ======================================================

                document.getElementById("summary-present").innerText = present;
                document.getElementById("summary-absent").innerText = absent;
                document.getElementById("summary-leave").innerText = leave;
                document.getElementById("summary-streak").innerText = maxStreak + " 🔥";

                // ======================================================
                // SECTION 3 → ANIMATED PROGRESS BAR
                // ======================================================

                let percent = fullData.length > 0
                    ? Math.round((present / fullData.length) * 100)
                    : 0;

                document.getElementById("percentText").innerText = percent + "%";

                const progressBar = document.getElementById("attendanceProgress");
                if (progressBar) {
                    progressBar.style.width = percent + "%";
                }

                // ======================================================
                // SECTION 4 → MANAGER ANALYTICS (SAFE)
                // ======================================================

                if (this.isManager) {

                    const analytics = document.getElementById("manager-analytics");
                    const teamDays = document.getElementById("team-days");
                    const teamPresent = document.getElementById("team-present");
                    const teamAvg = document.getElementById("team-avg");

                    if (analytics) analytics.style.display = "flex";

                    if (teamDays) teamDays.innerText = fullData.length;
                    if (teamPresent) teamPresent.innerText = present;

                    let avg = fullData.length > 0
                        ? Math.round((present / fullData.length) * 100)
                        : 0;

                    if (teamAvg) teamAvg.innerText = avg + "%";
                }

                // ======================================================
                // SECTION 5 → BUILD CARDS (FILTER APPLIED HERE)
                // ======================================================
                fullData.forEach(item => {

                    const attendance = item.attendance || "";

                    //  FILTER (Still applied)
                    if (this.activeFilter && this.activeFilter !== "all") {
                        if (attendance !== this.activeFilter) return;
                    }

                    // ===== BORDER COLOR =====
                    let borderClass = "border-absent";

                    if (item.holiday) borderClass = "border-holiday";
                    else if (attendance === "Present") borderClass = "border-present";
                    else if (attendance === "Work From Home") borderClass = "border-wfh";
                    else if (attendance === "Leave" || attendance === "On Leave") borderClass = "border-leave";

                    // ===== BADGE =====
                    let badgeHTML = "";

                    if (item.holiday) {
                        badgeHTML = `<span class="status-badge badge-holiday">${item.holiday}</span>`;
                    }
                    else if (attendance === "Present") {
                        badgeHTML = `<span class="status-badge badge-present">Present</span>`;
                    }
                    else if (attendance === "Work From Home") {
                        badgeHTML = `<span class="status-badge badge-wfh">WFH</span>`;
                    }
                    else if (attendance === "Absent") {
                        badgeHTML = `<span class="status-badge badge-absent">Absent</span>`;
                    }
                    else if (attendance === "On Leave") {
                        badgeHTML = `<span class="status-badge badge-leave">Leave</span>`;
                    }

                    // ==================================================
                    // ORIGINAL CO / REGULARIZATION / LEAVE LOGIC
                    // ==================================================

                    let leaveRequestPresent = "";
                    if (item.leave_status === "Approved") {
                        leaveRequestPresent = "Leave Approved";
                    } else if (item.leave_req_present) {
                        leaveRequestPresent = "Leave Applied";
                    }

                    let regRequestPresent = "";
                    if (item.wfh_status === "Approved") {
                        regRequestPresent = "WFH";
                    } else if (item.reg_status === "Approved") {
                        regRequestPresent = "Reg.Approved";
                    } else if (item.reg_req_present) {
                        regRequestPresent = "Regularization Applied";
                    }

                    let cORequestPresent = "";
                    console.log("DATE:", item.date, "CO DOCSTATUS:", item.co_docstatus);
                    if (item.co_docstatus === 1) {
                        // Submitted → Approved
                        cORequestPresent = "CO Approved";
                    }
                    else if (item.co_docstatus === 0) {
                        // Draft → Requested
                        cORequestPresent = "CO Requested";
                    }

                    let requestPresent = leaveRequestPresent || regRequestPresent;

                    let regRelevant =
                        !item.holiday &&
                        attendance &&
                        attendance != "Present" &&
                        attendance != "Work From Home" &&

                        (item.half_day_status != "Present" || !requestPresent);

                    let showCORequestButton =
                        item.holiday &&
                        !cORequestPresent;

                    let showLeaveButton =
                        !item.holiday &&
                        attendance != "Present" &&
                        attendance != "Work From Home" &&
                        !requestPresent;

                    let splitDateArray = String(item.date).split("-");
                    let sqlDate = splitDateArray[2] + "-" +
                        splitDateArray[1] + "-" +
                        splitDateArray[0];

                    let itemDate = new Date(sqlDate);
                    let today = new Date();
                    let daysDiff = frappe.datetime.get_day_diff(today, itemDate);
                    let dateString = frappe.datetime.obj_to_str(itemDate);

                    let regAllowed;

                    if (this.isSystemManager) {
                        regAllowed = true;
                    }
                    else if (this.isManager) {
                        regAllowed = daysDiff < this.managerRegularizationWindow;
                    }
                    else {
                        regAllowed = daysDiff < this.employeeRegularizationWindow;
                    }

                    // ==================================================
                    //  BUILD CALENDAR CELL (UPDATED STRUCTURE)
                    // ==================================================
                    // ===== STATUS TEXT CLASS =====
                    let statusTextClass = "text-absent";
                    let statusLabel = attendance || "-";

                    if (item.holiday) {
                        statusTextClass = "text-holiday";
                        statusLabel = item.holiday;
                    }
                    else if (attendance === "Present") {
                        statusTextClass = "text-present";
                    }
                    else if (attendance === "Work From Home") {
                        statusTextClass = "text-wfh";
                        statusLabel = "WFH";
                    }
                    else if (attendance === "Leave" || attendance === "On Leave") {
                        statusTextClass = "text-leave";
                        statusLabel = "Leave";
                    }

                    // ============================
                    // NEW CLEAN CARD DESIGN
                    // ============================
                    // ============================
                    // FORMAT SINGLE TIME LINE
                    // ============================

                    let timeLine = "-";

                    if (item.in_time && item.out_time) {
                        timeLine = `${item.in_time} - ${item.out_time}`;
                    }

                    let hoursText = item.working_hours
                        ? `(${item.working_hours} hrs)`
                        : "";
                    container.innerHTML += `
    <div class="calendar-day">

        <!-- Top Row : Date + Status -->
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="day-number">
                ${splitDateArray[0]}
            </div>
            <div class="status-text ${statusTextClass}">
                ${statusLabel}
            </div>
        </div>

   <!-- Middle : Time Info -->
<div style="margin-top:10px; font-size:13px; font-weight:500;">
    ${timeLine}
    <span style="opacity:.7; font-weight:400;">
        ${hoursText}
    </span>

    ${item.late_entry ? `<div class="text-late">Late Entry</div>` : ''}
    ${item.early_exit ? `<div class="text-early">Early Exit</div>` : ''}
</div>

      <!-- Bottom : Actions -->
<div style="margin-top:10px; display:flex; gap:6px; flex-wrap:wrap;">

${item.holiday ? `
    <span 
        class="action-badge action-co ${cORequestPresent ? 'disabled-action' : 'CORequest'}"
        data-date="${cORequestPresent ? '' : dateString}"
        title="${cORequestPresent === 'CO Approved'
                                ? 'CO Approved'
                                : cORequestPresent === 'CO Requested'
                                    ? 'CO Requested (Draft)'
                                    : 'Request Compensatory Off'
                            }"
        style="${cORequestPresent ? 'opacity:.6; cursor:not-allowed;' : ''}">
        ${cORequestPresent
                                ? cORequestPresent
                                : 'CO'
                            }
    </span>
` : ''}

${regRelevant ? `
    <span 
        class="action-badge action-regularize 
        ${regRequestPresent ? 'disabled-action' : (regAllowed ? 'regularization' : 'regularizationReject')}"
        data-date="${regRequestPresent ? '' : dateString}"
        title="${regRequestPresent
                                ? 'Already Applied'
                                : (!regAllowed ? 'Outside Allowed Window' : 'Apply Regularization')
                            }"
        style="${regRequestPresent ? 'opacity:.5; cursor:not-allowed;' : ''}">
        Regularize
    </span>
` : ''}

    ${showLeaveButton ? `
        <span class="action-badge action-leave apply-leave-button"
            data-date="${dateString}">
            Leave
        </span>` : ''}

</div>

    </div>
`;

                });

            }
        });
    }
    // ==============================
    // KEEP ALL ORIGINAL FUNCTIONS
    // ==============================
    openRegularizationModal(date) {

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
                    label: 'Reason',
                    fieldname: 'reason',
                    fieldtype: 'Select',
                    options: ['Work From Home', 'On Duty'],
                    reqd: 1
                },
                {
                    label: 'Explanation',
                    fieldname: 'explanation',
                    fieldtype: 'Small Text',
                    reqd: 1
                }
            ],
            primary_action_label: 'Submit Regularization',
            primary_action: (values) => {

                frappe.call({
                    method: "frappe.client.insert",
                    args: {
                        doc: {
                            doctype: "Attendance Request",
                            employee: employee,
                            from_date: values.date,
                            to_date: values.date,
                            reason: values.reason,
                            explanation: values.explanation
                        }
                    },
                    freeze: true,
                    freeze_message: "Submitting Regularization...",
                    callback: (r) => {
                        if (!r.exc) {

                            frappe.call({
                                method: "frappe.client.submit",
                                args: {
                                    doc: r.message
                                },
                                callback: () => {
                                    frappe.show_alert({
                                        message: "Regularization submitted successfully",
                                        indicator: "green"
                                    });

                                    // d.hide();
                                    this.fetchAttendanceData();
                                }
                            });

                        }
                    }
                });

            }
        });

        d.show();
        d.set_value("date", date);
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
                    label: 'Reason',
                    fieldname: 'reason',
                    fieldtype: 'Select',
                    options: ['Work From Home', 'On Duty'],
                    reqd: 1
                },
                {
                    label: 'Explanation',
                    fieldname: 'explanation',
                    fieldtype: 'Small Text',
                    reqd: 1
                }
            ],
            primary_action_label: 'Submit CO Request',
            primary_action(values) {

                frappe.call({
                    method: "frappe.client.insert",
                    args: {
                        doc: {
                            doctype: "Attendance Request",
                            employee: employee,
                            from_date: values.date,
                            to_date: values.date,
                            reason: values.reason,
                            explanation: values.explanation,
                            include_holidays: 1,
                            is_compensatory_leave: 1
                        }
                    },
                    freeze: true,
                    freeze_message: "Creating CO Request...",
                    callback: (r) => {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: "CO request created (Draft).",
                                indicator: "green"
                            });

                            d.hide();
                            this.fetchAttendanceData();
                        }
                    }
                });
            }
        });

        d.show();
        d.set_value("date", date);
    }

    newLeaveDoc(date) {
        frappe.new_doc("Leave Application", {
            employee: this.employee,
        }).then(() => {
            cur_frm.set_value("from_date", date);
            cur_frm.set_value("to_date", date);
        });
    }

};