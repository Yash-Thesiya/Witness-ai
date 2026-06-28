"""
Calendar page — Witness modern UI.
Theme: matches theme.py (orange sidebar, blue-gray primary, beige background)
"""
import json
import httpx
from nicegui import ui
from app.state import app_state, is_logged_in, logout

BACKEND_URL = "http://backend:8000"

STATUS_COLORS = {
    "active":    "#277dff",
    "detected":  "#d97706",
    "fulfilled": "#059669",
    "missed":    "#dc2626",
    "modified":  "#7c3aed",
    "blocked":   "#ea580c",
    "cancelled": "#6b7280",
    "confirmed": "#0891b2",
}

# Event styles matched to theme.py STATUS dict
STATUS_EVENT_STYLES = {
    "active":    {"bg": "rgba(75,96,127,0.12)",   "color": "#277dff", "dot": "#277dff"},
    "detected":  {"bg": "rgba(217,119,6,0.12)",   "color": "#d97706", "dot": "#d97706"},
    "fulfilled": {"bg": "rgba(5,150,105,0.12)",   "color": "#059669", "dot": "#059669"},
    "missed":    {"bg": "rgba(220,38,38,0.12)",   "color": "#dc2626", "dot": "#dc2626"},
    "modified":  {"bg": "rgba(124,58,237,0.12)",  "color": "#7c3aed", "dot": "#7c3aed"},
    "blocked":   {"bg": "rgba(234,88,12,0.12)",   "color": "#ea580c", "dot": "#ea580c"},
    "cancelled": {"bg": "rgba(107,114,128,0.12)", "color": "#6b7280", "dot": "#6b7280"},
    "confirmed": {"bg": "rgba(8,145,178,0.12)",   "color": "#0891b2", "dot": "#0891b2"},
}


def get_commitments_for_calendar(token: str) -> list:
    try:
        r = httpx.get(
            f"{BACKEND_URL}/commitments/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code != 200:
            return []

        commitments = r.json()
        events = []

        for c in commitments:
            if not c.get("due_date"):
                continue

            due_date = c["due_date"][:10]
            status   = c.get("status", "detected")
            es       = STATUS_EVENT_STYLES.get(status, STATUS_EVENT_STYLES["detected"])

            events.append({
                "id":              str(c["id"]),
                "title":           c["action"][:40],
                "date":            due_date,
                "backgroundColor": es["bg"],
                "borderColor":     es["dot"],
                "textColor":       es["color"],
                "extendedProps": {
                    "owner":      c["owner"],
                    "action":     c["action"],
                    "status":     status,
                    "confidence": c.get("confidence_score", 0),
                    "dot":        es["dot"],
                }
            })

        return events

    except Exception as e:
        print(f"[Calendar] Error: {e}")
        return []


def calendar_page():
    if not is_logged_in():
        ui.navigate.to("/")
        return

    events      = get_commitments_for_calendar(app_state["token"])
    events_json = json.dumps(events)

    status_colors_json = json.dumps(STATUS_COLORS)
    event_styles_json  = json.dumps(STATUS_EVENT_STYLES)

    ui.add_head_html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.css" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#e8d8c9 !important; font-family:'Inter',sans-serif; }
.nicegui-content { padding:0 !important; }

/* ── Sidebar ─────────────────────────────────── */
.sidebar {
    position:fixed; left:0; top:0; width:240px; height:100vh;
    background:#f3701e; display:flex; flex-direction:column;
    z-index:100; border-right:1px solid rgba(0,0,0,0.1);
    box-shadow:4px 0 20px rgba(0,0,0,0.1);
}
.sidebar-logo {
    display:flex; align-items:center; gap:10px;
    padding:24px 20px 28px 20px;
    border-bottom:1px solid rgba(0,0,0,0.1);
}
.sidebar-logo-icon {
    width:38px; height:38px;
    background:rgba(255,255,255,0.2);
    border-radius:10px; backdrop-filter:blur(10px);
    display:flex; align-items:center; justify-content:center; font-size:20px;
}
.sidebar-logo-text {
    font-size:1.2rem; font-weight:800; color:white; letter-spacing:-0.02em;
}
.sidebar-nav {
    padding:20px 12px; flex:1;
    display:flex; flex-direction:column; gap:4px; overflow-y:auto;
}
.nav-item {
    display:flex; align-items:center; gap:12px; padding:10px 14px;
    border-radius:10px; cursor:pointer; color:rgba(255,255,255,0.8);
    font-size:0.88rem; font-weight:500; transition:all 0.2s; text-decoration:none;
}
.nav-item:hover { background:rgba(0,0,0,0.12); color:white; }
.nav-item.active { background:rgba(0,0,0,0.2); color:white; font-weight:700; }
.nav-icon { font-size:1rem; width:20px; text-align:center; }
.sidebar-bottom {
    padding:16px 12px;
    border-top:1px solid rgba(0,0,0,0.1);
}

/* ── Main ────────────────────────────────────── */
.main-content {
    margin-left:240px; padding:0; min-height:100vh; background:#e8d8c9;
    display:flex; flex-direction:column;
}

/* ── Top bar ─────────────────────────────────── */
.cal-topbar {
    display:flex; align-items:center; justify-content:space-between;
    padding:18px 32px 14px;
    background:#ffffff;
    border-bottom:1.5px solid rgba(0,0,0,0.08);
}
.cal-nav-group { display:flex; align-items:center; gap:6px; }
.cal-nav-btn {
    width:34px; height:34px;
    background:#f5ede4; border:1px solid rgba(0,0,0,0.08);
    border-radius:8px; cursor:pointer; color:#6b7280;
    display:flex; align-items:center; justify-content:center;
    font-size:1rem; transition:all 0.15s;
}
.cal-nav-btn:hover { background:#e8d8c9; color:#1f2937; }
.cal-today-btn {
    display:flex; align-items:center; gap:6px;
    padding:7px 16px;
    background:#f5ede4; border:1px solid rgba(0,0,0,0.08);
    border-radius:8px; cursor:pointer;
    font-size:0.83rem; font-weight:600; color:#374151;
    transition:all 0.15s; font-family:'Inter',sans-serif;
}
.cal-today-btn:hover { background:#e8d8c9; }
.cal-month-title {
    font-size:1.4rem; font-weight:800; color:#1f2937; letter-spacing:-0.02em;
}
.cal-topbar-right { display:flex; align-items:center; gap:10px; }
.cal-search {
    display:flex; align-items:center; gap:8px;
    background:#f5ede4; border:1px solid rgba(0,0,0,0.08);
    border-radius:8px; padding:8px 14px;
}
.cal-search input {
    background:none; border:none; outline:none;
    font-size:0.83rem; color:#1f2937; width:180px;
    font-family:'Inter',sans-serif;
}
.cal-search input::placeholder { color:#9ca3af; }
.view-toggle {
    display:flex; background:#f5ede4;
    border:1px solid rgba(0,0,0,0.08); border-radius:8px; overflow:hidden;
}
.view-btn {
    padding:7px 14px; font-size:0.78rem; font-weight:600;
    cursor:pointer; color:#6b7280; border:none; background:none;
    font-family:'Inter',sans-serif; transition:all 0.15s;
}
.view-btn.active, .view-btn:hover { background:white; color:#4b607f; }

/* ── Calendar area ───────────────────────────── */
.cal-area { flex:1; padding:24px 32px; }

/* ── FullCalendar overrides ──────────────────── */
#witness-calendar {
    background:white; border-radius:14px; padding:20px;
    border:1px solid rgba(0,0,0,0.08);
    box-shadow:0 1px 4px rgba(0,0,0,0.06);
}
.fc-toolbar { margin-bottom:16px !important; display:none !important; }
.fc-button-primary { display:none !important; }
.fc-col-header-cell { background:white !important; padding:10px 0 !important; }
.fc-col-header-cell-cushion {
    color:#4b607f !important; font-weight:600 !important;
    font-size:0.83rem !important; text-decoration:none !important;
    font-family:'Inter',sans-serif !important;
}
.fc-daygrid-day-number {
    color:#374151 !important; font-size:0.83rem !important;
    font-weight:500 !important; text-decoration:none !important;
    padding:6px 8px !important;
}
.fc-day-today .fc-daygrid-day-number {
    background:#f3701e !important; color:white !important;
    border-radius:50% !important; width:28px !important; height:28px !important;
    display:flex !important; align-items:center !important;
    justify-content:center !important; margin:4px !important;
}
.fc-day-today { background:rgba(243,112,30,0.04) !important; }
.fc-daygrid-day-frame { min-height:90px !important; }
.fc-event {
    border-radius:6px !important; padding:3px 8px !important;
    font-size:0.75rem !important; font-weight:500 !important;
    cursor:pointer !important; border-left-width:3px !important;
    border-top:none !important; border-right:none !important;
    border-bottom:none !important; margin-bottom:2px !important;
    font-family:'Inter',sans-serif !important;
}
.fc-event:hover { opacity:0.88 !important; }
.fc-daygrid-more-link {
    color:#4b607f !important; font-size:0.72rem !important; font-weight:600 !important;
}
.fc-scrollgrid { border:none !important; }
.fc-scrollgrid td, .fc-scrollgrid th { border-color:rgba(0,0,0,0.06) !important; }
.fc-theme-standard .fc-scrollgrid { border:none !important; }

/* ── Event detail modal ──────────────────────── */
#cal-modal-overlay {
    display:none; position:fixed; inset:0;
    background:rgba(17,24,39,0.45); z-index:9998;
    backdrop-filter:blur(2px);
}
#cal-modal {
    display:none; position:fixed;
    top:50%; left:50%; transform:translate(-50%,-50%);
    background:white; border-radius:16px; padding:28px;
    box-shadow:0 20px 60px rgba(0,0,0,0.18);
    z-index:9999; width:420px; max-width:92vw;
    border:1px solid rgba(0,0,0,0.08);
}
.modal-close {
    position:absolute; top:14px; right:16px;
    background:none; border:none; font-size:1.4rem;
    cursor:pointer; color:#9ca3af; line-height:1;
}
.modal-close:hover { color:#374151; }
.modal-status-badge {
    display:inline-flex; align-items:center;
    padding:4px 12px; border-radius:20px;
    font-size:0.72rem; font-weight:700; margin-bottom:14px;
}
.modal-title {
    font-size:1rem; font-weight:700; color:#1f2937;
    margin-bottom:16px; line-height:1.4;
}
.modal-row {
    display:flex; align-items:flex-start; gap:10px;
    padding:9px 0; border-bottom:1px solid #f5ede4;
}
.modal-row:last-of-type { border-bottom:none; }
.modal-label { color:#9ca3af; font-size:0.78rem; font-weight:600; min-width:90px; padding-top:1px; }
.modal-value { color:#374151; font-size:0.83rem; font-weight:500; flex:1; }
.modal-actions { display:flex; gap:10px; margin-top:18px; }
.modal-btn-primary {
    flex:1; padding:10px; background:#4b607f; color:white;
    border:none; border-radius:9px; font-size:0.83rem;
    font-weight:600; cursor:pointer; font-family:'Inter',sans-serif;
    transition:background 0.2s;
}
.modal-btn-primary:hover { background:#3a4f6e; }
.modal-btn-secondary {
    padding:10px 18px; background:#f5ede4; color:#6b7280;
    border:1px solid rgba(0,0,0,0.08); border-radius:9px;
    font-size:0.83rem; font-weight:500; cursor:pointer;
    font-family:'Inter',sans-serif; transition:all 0.2s;
}
.modal-btn-secondary:hover { background:#e8d8c9; color:#1f2937; }
</style>
""")

    # ── Sidebar ──────────────────────────────────────────────────────
    ui.add_body_html("""
<div class="sidebar">
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">👁</div>
        <span class="sidebar-logo-text">Witness</span>
    </div>
    <nav class="sidebar-nav">
        <a class="nav-item" href="/dashboard"><span class="nav-icon">📊</span> Dashboard</a>
        <a class="nav-item" href="/commitments"><span class="nav-icon">📋</span> Commitments</a>
        <a class="nav-item active" href="/calendar"><span class="nav-icon">📅</span> Calendar</a>
        <a class="nav-item" href="/upload"><span class="nav-icon">⬆️</span> Upload</a>
        <a class="nav-item" href="/report"><span class="nav-icon">📈</span> Report</a>
    </nav>
    <div class="sidebar-bottom">
        <a class="nav-item" href="/" style="color:rgba(255,255,255,0.7);">
            <span class="nav-icon">🚪</span> Logout
        </a>
    </div>
</div>
""")

    # ── Main content ─────────────────────────────────────────────────
    ui.add_body_html(f"""
<!-- Event detail modal -->
<div id="cal-modal-overlay" onclick="calCloseModal()"></div>
<div id="cal-modal">
    <button class="modal-close" onclick="calCloseModal()">×</button>
    <div id="modal-badge" class="modal-status-badge"></div>
    <div id="modal-title" class="modal-title"></div>
    <div class="modal-row">
        <span class="modal-label">👤 Owner</span>
        <span class="modal-value" id="modal-owner"></span>
    </div>
    <div class="modal-row">
        <span class="modal-label">📅 Due Date</span>
        <span class="modal-value" id="modal-due"></span>
    </div>
    <div class="modal-row">
        <span class="modal-label">🎯 Confidence</span>
        <span class="modal-value" id="modal-conf"></span>
    </div>
    <div class="modal-actions">
        <button class="modal-btn-primary" id="modal-view-btn">View Detail →</button>
        <button class="modal-btn-secondary" onclick="calCloseModal()">Close</button>
    </div>
</div>

<div class="main-content">

    <!-- Topbar -->
    <div class="cal-topbar">
        <div style="display:flex;align-items:center;gap:16px;">
            <div id="cal-month-display" class="cal-month-title">Loading...</div>
            <div class="cal-nav-group">
                <button class="cal-nav-btn" onclick="calPrev()">&#8249;</button>
                <button class="cal-nav-btn" onclick="calNext()">&#8250;</button>
                <button class="cal-today-btn" onclick="calToday()">📅 Today</button>
            </div>
        </div>

        <div class="cal-topbar-right">
            <div class="cal-search">
                <span style="color:#9ca3af;">🔍</span>
                <input type="text" placeholder="Find Events &amp; Contacts" id="cal-search-input"
                    oninput="calSearch(this.value)">
            </div>
            <div class="view-toggle">
                <button class="view-btn active" id="vbtn-month" onclick="calView('dayGridMonth', this)">Month</button>
                <button class="view-btn"         id="vbtn-week"  onclick="calView('timeGridWeek',  this)">Week</button>
                <button class="view-btn"         id="vbtn-list"  onclick="calView('listWeek',      this)">List</button>
            </div>
        </div>
    </div>

    <!-- Calendar -->
    <div class="cal-area">
        <div id="witness-calendar"></div>
    </div>

</div>

<!-- FullCalendar JS -->
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js"></script>
<script>
(function() {{
    var EVENTS        = {events_json};
    var STATUS_COLORS = {status_colors_json};
    var EVENT_STYLES  = {event_styles_json};
    var calInstance   = null;
    var allEvents     = EVENTS.slice();

    function updateTitle() {{
        if (!calInstance) return;
        var d = calInstance.getDate();
        var months = ['January','February','March','April','May','June',
                      'July','August','September','October','November','December'];
        document.getElementById('cal-month-display').textContent =
            months[d.getMonth()] + ' ' + d.getFullYear();
    }}

    function initCalendar() {{
        var el = document.getElementById('witness-calendar');
        if (!el) {{ setTimeout(initCalendar, 200); return; }}

        calInstance = new FullCalendar.Calendar(el, {{
            initialView:   'dayGridMonth',
            headerToolbar: false,
            height:        'auto',
            events:        allEvents,
            dayMaxEvents:  3,
            firstDay:      0,
            eventClick: function(info) {{
                calShowModal(info.event);
            }},
            datesSet: function() {{
                updateTitle();
            }},
            noEventsText: 'No commitments this period.',
            moreLinkText: function(n) {{ return '+' + n + ' more'; }},
            eventContent: function(arg) {{
                var props   = arg.event.extendedProps;
                var dot     = props.dot || '#4b607f';
                var title   = arg.event.title;
                var timeStr = arg.timeText || '';
                return {{
                    html: '<div style="display:flex;align-items:center;gap:5px;padding:2px 4px;">' +
                          (timeStr ? '<span style="font-size:0.68rem;opacity:0.75;white-space:nowrap;">' + timeStr + '</span>' : '') +
                          '<span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px;">' + title + '</span>' +
                          '<span style="width:6px;height:6px;border-radius:50%;background:' + dot + ';flex-shrink:0;margin-left:2px;"></span>' +
                          '</div>'
                }};
            }},
        }});

        calInstance.render();
        updateTitle();
    }}

    window.calPrev  = function() {{ if(calInstance){{ calInstance.prev();  updateTitle(); }} }};
    window.calNext  = function() {{ if(calInstance){{ calInstance.next();  updateTitle(); }} }};
    window.calToday = function() {{ if(calInstance){{ calInstance.today(); updateTitle(); }} }};

    window.calView = function(view, btn) {{
        if (calInstance) calInstance.changeView(view);
        document.querySelectorAll('.view-btn').forEach(function(b) {{ b.classList.remove('active'); }});
        if (btn) btn.classList.add('active');
    }};

    window.calSearch = function(q) {{
        if (!calInstance) return;
        var filtered = q
            ? allEvents.filter(function(e) {{
                return (e.title || '').toLowerCase().includes(q.toLowerCase()) ||
                       (e.extendedProps && (
                           (e.extendedProps.owner  || '').toLowerCase().includes(q.toLowerCase()) ||
                           (e.extendedProps.action || '').toLowerCase().includes(q.toLowerCase())
                       ));
              }})
            : allEvents;
        calInstance.removeAllEvents();
        calInstance.addEventSource(filtered);
    }};

    function calShowModal(event) {{
        var props  = event.extendedProps;
        var status = props.status || 'detected';
        var es     = EVENT_STYLES[status] || EVENT_STYLES['detected'];

        document.getElementById('modal-badge').textContent        = status.toUpperCase();
        document.getElementById('modal-badge').style.background   = es.bg;
        document.getElementById('modal-badge').style.color        = es.color;
        document.getElementById('modal-badge').style.border       = '1px solid ' + es.dot;

        document.getElementById('modal-title').textContent  = props.action || event.title;
        document.getElementById('modal-owner').textContent  = props.owner || '—';
        document.getElementById('modal-due').textContent    = event.startStr;
        document.getElementById('modal-conf').textContent   = Math.round((props.confidence || 0) * 100) + '%';

        document.getElementById('modal-view-btn').onclick = function() {{
            window.location.href = '/commitments/' + event.id;
        }};

        document.getElementById('cal-modal-overlay').style.display = 'block';
        document.getElementById('cal-modal').style.display          = 'block';
    }}

    window.calCloseModal = function() {{
        document.getElementById('cal-modal-overlay').style.display = 'none';
        document.getElementById('cal-modal').style.display          = 'none';
    }};

    document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape') window.calCloseModal();
    }});

    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initCalendar);
    }} else {{
        setTimeout(initCalendar, 100);
    }}
}})();
</script>
""")