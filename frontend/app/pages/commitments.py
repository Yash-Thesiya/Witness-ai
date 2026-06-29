"""
Commitments Explorer + Detail - Themed
"""
import httpx
from nicegui import ui
from app.state import app_state, is_logged_in, logout
from app.theme import (
    get_base_css, get_sidebar_html,
    PRIMARY, PRIMARY_LIGHT, PRIMARY_HOVER,
    PAGE_BG, CARD_BG, CARD_BG_SOFT, CARD_BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS, STATUS_ICONS, AVATAR_COLORS,
)

import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def get_commitments(token, status=None, owner=None, search=None):
    try:
        params = {}
        if status: params["status"] = status
        if owner: params["owner"] = owner
        if search: params["search"] = search
        r = httpx.get(
            f"{BACKEND_URL}/commitments/",
            headers={"Authorization": f"Bearer {token}"},
            params=params, timeout=10,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def get_commitment_detail(token, commitment_id):
    try:
        r = httpx.get(
            f"{BACKEND_URL}/commitments/{commitment_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def commitments_page():
    if not is_logged_in():
        ui.navigate.to("/")
        return

    ui.query("body").style(f"background: {PAGE_BG}")
    user_initial = app_state.get("user", "U")[0].upper()
    commitments = get_commitments(app_state["token"])

    rows_html = ""
    for i, c in enumerate(commitments):
        status = c.get("status", "detected")
        color, bg = STATUS.get(status, ("#6b7280", "rgba(107,114,128,0.12)"))
        icon = STATUS_ICONS.get(status, "📋")
        due = c["due_date"][:10] if c.get("due_date") else "No deadline"
        action = c["action"][:50] + ("..." if len(c["action"]) > 50 else "")
        owner = c["owner"]
        owner_color = AVATAR_COLORS[i % len(AVATAR_COLORS)]
        conf = int((c.get("confidence_score") or 0) * 100)

        rows_html += f"""
        <tr class="data-row"
            data-status="{status}"
            data-owner="{owner.lower()}"
            data-action="{c['action'].lower()}">
            <td>
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="width:32px;height:32px;border-radius:50%;
                        background:{owner_color};color:white;
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:0.78rem;flex-shrink:0">
                        {owner[0].upper()}
                    </div>
                    <span style="color:{TEXT_PRIMARY};font-size:0.85rem;
                        font-weight:600">{owner}</span>
                </div>
            </td>
            <td style="color:{TEXT_SECONDARY};font-size:0.83rem">
                <div style="display:flex;align-items:center;gap:7px">
                    <span>{icon}</span><span>{action}</span>
                </div>
            </td>
            <td style="color:{TEXT_SECONDARY};font-size:0.83rem;
                text-align:center">{due}</td>
            <td style="text-align:center">
                <span style="padding:4px 11px;border-radius:20px;
                    font-size:0.7rem;font-weight:700;
                    background:{bg};color:{color};
                    border:1px solid {color}33">
                    {status.upper()}
                </span>
            </td>
            <td style="text-align:center">
                <div style="display:flex;align-items:center;
                    gap:6px;justify-content:center">
                    <div style="width:48px;height:4px;
                        background:rgba(0,0,0,0.08);
                        border-radius:2px;overflow:hidden">
                        <div style="width:{conf}%;height:100%;
                            background:{PRIMARY};border-radius:2px">
                        </div>
                    </div>
                    <span style="color:{TEXT_MUTED};font-size:0.75rem">
                        {conf}%
                    </span>
                </div>
            </td>
            <td style="text-align:center">
                <button onclick="window.location.href='/commitments/{c['id']}'"
                    style="background:{PRIMARY_LIGHT};
                    border:1px solid rgba(75,96,127,0.2);
                    color:{PRIMARY};border-radius:6px;
                    padding:5px 13px;font-size:0.78rem;
                    font-weight:600;cursor:pointer">
                    View →
                </button>
            </td>
        </tr>
        """

    ui.add_head_html(get_base_css())
    ui.add_head_html(f"""
<style>
    .filter-bar {{
        background: {CARD_BG};
        border-radius: 12px; padding: 14px 18px;
        border: 1px solid {CARD_BORDER};
        display: flex; align-items: center;
        gap: 10px; flex-wrap: wrap; margin-bottom: 18px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }}
    .table-wrap {{
        background: {CARD_BG};
        border-radius: 14px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        overflow: hidden;
    }}
    .table-head {{
        padding: 16px 20px;
        border-bottom: 1px solid {CARD_BORDER};
        display: flex; align-items: center;
        justify-content: space-between;
    }}
    .count-badge {{
        background: {PRIMARY_LIGHT};
        color: {PRIMARY}; border-radius: 20px;
        padding: 2px 10px; font-size: 0.75rem; font-weight: 700;
    }}
    .data-row {{ cursor: default; }}
    .data-row:hover td {{ background: {CARD_BG_SOFT}; }}
    .table-foot {{
        padding: 12px 20px;
        border-top: 1px solid {CARD_BORDER};
    }}
    .empty-box {{
        text-align: center; padding: 52px 20px;
    }}
</style>
""")

    ui.add_body_html(f"""
{get_sidebar_html("commitments")}

<div class="main-content">
    <div class="topbar">
        <div>
            <div class="topbar-title">📋 Commitments</div>
            <div class="topbar-sub">
                Track and manage all extracted commitments.
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
            <button class="btn-primary"
                onclick="window.location.href='/upload'">
                + Upload New
            </button>
            <div class="avatar">{user_initial}</div>
        </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
        <div class="search-wrap" style="flex:2;min-width:180px">
            <span style="color:{TEXT_MUTED}">🔍</span>
            <input id="s-search" placeholder="Search action..."
                onkeydown="if(event.key==='Enter') applyF()">
        </div>
        <div class="search-wrap" style="flex:1;min-width:140px">
            <span style="color:{TEXT_MUTED}">👤</span>
            <input id="s-owner" placeholder="Owner..."
                onkeydown="if(event.key==='Enter') applyF()">
        </div>
        <select class="select-field" id="s-status">
            <option value="">All Status</option>
            <option value="detected">Detected</option>
            <option value="active">Active</option>
            <option value="fulfilled">Fulfilled</option>
            <option value="missed">Missed</option>
            <option value="modified">Modified</option>
            <option value="blocked">Blocked</option>
            <option value="cancelled">Cancelled</option>
        </select>
        <button class="btn-primary" onclick="applyF()">Search</button>
        <button class="btn-secondary" onclick="clearF()">✕ Clear</button>
    </div>

    <!-- Table -->
    <div class="table-wrap">
        <div class="table-head">
            <div style="display:flex;align-items:center;gap:8px">
                <span style="color:{TEXT_PRIMARY};font-size:0.95rem;font-weight:700">
                    All Commitments
                </span>
                <span class="count-badge" id="c-count">{len(commitments)}</span>
            </div>
        </div>

        <table class="data-table">
            <thead>
                <tr>
                    <th style="width:170px">Owner</th>
                    <th>Action</th>
                    <th style="width:115px;text-align:center">Due Date</th>
                    <th style="width:125px;text-align:center">Status</th>
                    <th style="width:115px;text-align:center">Confidence</th>
                    <th style="width:90px;text-align:center">Detail</th>
                </tr>
            </thead>
            <tbody id="c-tbody">
                {rows_html if rows_html else f'''
                <tr><td colspan="6">
                    <div class="empty-box">
                        <div style="font-size:2.5rem;margin-bottom:10px">📋</div>
                        <div style="color:{TEXT_PRIMARY};font-weight:600;
                            font-size:0.95rem;margin-bottom:6px">
                            No commitments yet
                        </div>
                        <div style="color:{TEXT_MUTED};font-size:0.82rem;
                            margin-bottom:16px">
                            Upload a transcript or audio to get started
                        </div>
                        <button class="btn-primary"
                            onclick="window.location.href='/upload'">
                            Upload Now
                        </button>
                    </div>
                </td></tr>
                '''}
            </tbody>
        </table>

        <div class="table-foot">
            <span style="color:{TEXT_MUTED};font-size:0.8rem" id="c-foot">
                Showing {len(commitments)} commitments
            </span>
        </div>
    </div>
</div>

<script>
function applyF() {{
    var s = document.getElementById('s-search').value.toLowerCase();
    var o = document.getElementById('s-owner').value.toLowerCase();
    var st = document.getElementById('s-status').value;
    var rows = document.querySelectorAll('.data-row');
    var n = 0;
    rows.forEach(function(r) {{
        var show = (!s || r.dataset.action.includes(s))
            && (!o || r.dataset.owner.includes(o))
            && (!st || r.dataset.status === st);
        r.style.display = show ? '' : 'none';
        if (show) n++;
    }});
    document.getElementById('c-count').textContent = n;
    document.getElementById('c-foot').textContent = 'Showing ' + n + ' commitments';
}}

function clearF() {{
    document.getElementById('s-search').value = '';
    document.getElementById('s-owner').value = '';
    document.getElementById('s-status').value = '';
    document.querySelectorAll('.data-row').forEach(function(r) {{
        r.style.display = '';
    }});
    var total = document.querySelectorAll('.data-row').length;
    document.getElementById('c-count').textContent = total;
    document.getElementById('c-foot').textContent = 'Showing ' + total + ' commitments';
}}
</script>
""")


def commitment_detail_page(commitment_id: int):
    if not is_logged_in():
        ui.navigate.to("/")
        return

    ui.query("body").style(f"background: {PAGE_BG}")
    c = get_commitment_detail(app_state["token"], commitment_id)

    if not c:
        ui.add_head_html(get_base_css())
        ui.add_body_html(f"""
{get_sidebar_html("commitments")}
<div class="main-content">
    <div style="color:#dc2626;margin-top:40px">❌ Commitment not found.</div>
    <button class="btn-secondary" style="margin-top:12px"
        onclick="window.location.href='/commitments'">← Back</button>
</div>
""")
        return

    status = c.get("status", "detected")
    color, bg = STATUS.get(status, ("#6b7280", "rgba(107,114,128,0.12)"))
    due = c["due_date"][:10] if c.get("due_date") else "No deadline"
    conf = int((c.get("confidence_score") or 0) * 100)

    VALID_NEXT = {
        "detected": ["active", "fulfilled", "cancelled"],
        "confirmed": ["active", "fulfilled", "cancelled"],
        "active": ["modified", "blocked", "fulfilled", "missed", "cancelled"],
        "modified": ["active", "fulfilled", "cancelled"],
        "blocked": ["active", "fulfilled", "cancelled"],
        "missed": ["fulfilled"],
        "fulfilled": [], "cancelled": [],
    }

    BTN_LABELS = {
        "active": ("✅ Confirm & Activate", "#277dff"),
        "fulfilled": ("🎉 Mark Fulfilled", "#059669"),
        "cancelled": ("❌ Cancel", "#dc2626"),
        "blocked": ("🚫 Mark Blocked", "#ea580c"),
        "missed": ("⏰ Mark Missed", "#b91c1c"),
        "modified": ("🔄 Mark Modified", "#7c3aed"),
    }

    STATUS_DESC = {
        "detected": "AI has extracted this commitment. Confirm it or it will auto-activate in 2 hours.",
        "active": "Actively being tracked.",
        "modified": "Deadline or details have been updated.",
        "blocked": "There is a blocker preventing completion.",
        "missed": "Due date has passed.",
        "fulfilled": "✅ Completed! Terminal state.",
        "cancelled": "⛔ Cancelled. Terminal state.",
    }

    btns_html = ""
    for ns in VALID_NEXT.get(status, []):
        label, btn_c = BTN_LABELS.get(ns, (ns.upper(), PRIMARY))
        btns_html += f"""
        <button onclick="updateStatus('{ns}')"
            style="background:{btn_c};color:white;border:none;
            border-radius:8px;padding:9px 16px;font-size:0.82rem;
            font-weight:600;cursor:pointer;transition:opacity 0.2s"
            onmouseover="this.style.opacity='0.85'"
            onmouseout="this.style.opacity='1'">
            {label}
        </button>
        """

    if not btns_html:
        btns_html = f"""
        <div style="color:{TEXT_MUTED};font-size:0.85rem;
            background:{CARD_BG_SOFT};border-radius:8px;padding:11px 14px">
            Terminal state — koi aur action nahi.
        </div>
        """

    auto_notice = ""
    if status == "detected":
        auto_notice = f"""
        <div style="margin-top:12px;padding:10px 14px;
            background:rgba(217,119,6,0.08);
            border:1px solid rgba(217,119,6,0.2);
            border-radius:8px;display:flex;align-items:center;gap:8px">
            <span>⏰</span>
            <span style="color:#d97706;font-size:0.8rem">
                If no action is taken within 2 hours, the system will automatically mark this commitment as ACTIVE.
            </span>
        </div>
        """

    # Timeline
    tl_html = ""
    for evt in c.get("events", []):
        evt_time = evt["created_at"][:19].replace("T", " ")
        evt_type = evt["event_type"].upper()
        data_html = ""
        for k, v in (evt.get("event_data") or {}).items():
            if v and k != "source":
                data_html += f"""
                <div style="color:{TEXT_MUTED};font-size:0.75rem;margin-top:2px">
                    <span style="color:{TEXT_SECONDARY}">{k}:</span> {v}
                </div>
                """
        tl_html += f"""
        <div style="display:flex;gap:12px;padding:11px 0;
            border-bottom:1px solid {CARD_BORDER}">
            <div style="display:flex;flex-direction:column;align-items:center">
                <div style="width:9px;height:9px;border-radius:50%;
                    background:{PRIMARY};margin-top:4px;flex-shrink:0"></div>
                <div style="width:1px;flex:1;background:{CARD_BORDER};
                    margin-top:4px"></div>
            </div>
            <div style="flex:1;padding-bottom:4px">
                <div style="display:flex;align-items:center;
                    justify-content:space-between;margin-bottom:3px">
                    <span style="color:{TEXT_PRIMARY};font-size:0.82rem;
                        font-weight:600">{evt_type}</span>
                    <span style="color:{TEXT_MUTED};font-size:0.72rem">
                        {evt_time}
                    </span>
                </div>
                {data_html}
            </div>
        </div>
        """

    if not tl_html:
        tl_html = f"""
        <div style="color:{TEXT_MUTED};font-size:0.85rem;
            text-align:center;padding:20px">
            No timeline events yet.
        </div>
        """

    ui.add_head_html(get_base_css())
    ui.add_body_html(f"""
{get_sidebar_html("commitments")}

<div class="main-content">
    <div style="margin-bottom:20px">
        <button class="btn-secondary"
            style="margin-bottom:14px;font-size:0.8rem"
            onclick="window.location.href='/commitments'">
            ← Back to Commitments
        </button>
        <div class="topbar-title">Commitment Detail</div>
        <div class="topbar-sub">View and manage this commitment.</div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 340px;gap:20px">

        <!-- Left -->
        <div style="display:flex;flex-direction:column;gap:16px">

            <!-- Summary -->
            <div class="card">
                <div style="color:{TEXT_MUTED};font-size:0.72rem;
                    font-weight:700;text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:14px">
                    Summary
                </div>
                <div style="display:flex;align-items:center;
                    gap:8px;margin-bottom:18px">
                    <span style="padding:4px 12px;border-radius:20px;
                        font-size:0.75rem;font-weight:700;
                        background:{bg};color:{color};
                        border:1px solid {color}33">
                        {status.upper()}
                    </span>
                    <span style="color:{TEXT_MUTED};font-size:0.8rem">
                        {STATUS_DESC.get(status,'')}
                    </span>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                    <div style="background:{CARD_BG_SOFT};
                        border-radius:10px;padding:13px">
                        <div style="color:{TEXT_MUTED};font-size:0.72rem;
                            margin-bottom:4px">👤 Owner</div>
                        <div style="color:{TEXT_PRIMARY};font-size:0.9rem;
                            font-weight:700">{c.get('owner','')}</div>
                    </div>
                    <div style="background:{CARD_BG_SOFT};
                        border-radius:10px;padding:13px">
                        <div style="color:{TEXT_MUTED};font-size:0.72rem;
                            margin-bottom:4px">📅 Due Date</div>
                        <div style="color:{TEXT_PRIMARY};font-size:0.9rem;
                            font-weight:700">{due}</div>
                    </div>
                    <div style="background:{CARD_BG_SOFT};
                        border-radius:10px;padding:13px;grid-column:span 2">
                        <div style="color:{TEXT_MUTED};font-size:0.72rem;
                            margin-bottom:4px">📋 Action</div>
                        <div style="color:{TEXT_PRIMARY};font-size:0.9rem;
                            font-weight:600">{c.get('action','')}</div>
                    </div>
                    <div style="background:{CARD_BG_SOFT};
                        border-radius:10px;padding:13px">
                        <div style="color:{TEXT_MUTED};font-size:0.72rem;
                            margin-bottom:6px">🎯 Confidence</div>
                        <div style="display:flex;align-items:center;gap:8px">
                            <div style="flex:1;height:4px;
                                background:rgba(0,0,0,0.08);
                                border-radius:2px;overflow:hidden">
                                <div style="width:{conf}%;height:100%;
                                    background:{PRIMARY};border-radius:2px">
                                </div>
                            </div>
                            <span style="color:{TEXT_PRIMARY};font-size:0.85rem;
                                font-weight:700">{conf}%</span>
                        </div>
                    </div>
                    <div style="background:{CARD_BG_SOFT};
                        border-radius:10px;padding:13px">
                        <div style="color:{TEXT_MUTED};font-size:0.72rem;
                            margin-bottom:4px">🆔 ID</div>
                        <div style="color:{TEXT_PRIMARY};font-size:0.9rem;
                            font-weight:700">#{commitment_id}</div>
                    </div>
                </div>
            </div>

            <!-- Status Update -->
            <div class="card">
                <div style="color:{TEXT_MUTED};font-size:0.72rem;
                    font-weight:700;text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:14px">
                    Update Status
                </div>
                <input type="text" id="note-input"
                    class="input-field"
                    placeholder="Add a note (optional)..."
                    style="margin-bottom:12px">
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                    {btns_html}
                </div>
                {auto_notice}
                <div id="status-result"
                    style="margin-top:10px;display:none;
                    padding:9px 13px;border-radius:8px;
                    font-size:0.82rem;font-weight:500">
                </div>
            </div>
        </div>

        <!-- Timeline -->
        <div class="card" style="height:fit-content">
            <div style="color:{TEXT_MUTED};font-size:0.72rem;
                font-weight:700;text-transform:uppercase;
                letter-spacing:0.06em;margin-bottom:14px">
                📅 Timeline
            </div>
            {tl_html}
        </div>
    </div>
</div>

<script>
var CID = {commitment_id};
var TOKEN = "{app_state['token']}";
var API = "http://localhost:8000";

function updateStatus(ns) {{
    var note = document.getElementById('note-input').value;
    var res = document.getElementById('status-result');
    res.style.display = 'block';
    res.style.background = '{PRIMARY_LIGHT}';
    res.style.border = '1px solid rgba(75,96,127,0.2)';
    res.style.color = '{PRIMARY}';
    res.textContent = '⏳ Updating...';

    fetch(API + '/commitments/' + CID + '/status', {{
        method: 'PATCH',
        headers: {{
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + TOKEN,
        }},
        body: JSON.stringify({{ status: ns, note: note }}),
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
        if (d.error || d.detail) {{
            res.style.background = 'rgba(220,38,38,0.08)';
            res.style.border = '1px solid rgba(220,38,38,0.2)';
            res.style.color = '#dc2626';
            res.textContent = '❌ ' + (d.error || d.detail);
        }} else {{
            res.style.background = 'rgba(5,150,105,0.08)';
            res.style.border = '1px solid rgba(5,150,105,0.2)';
            res.style.color = '#059669';
            res.textContent = '✅ Status updated to ' + ns.toUpperCase();
            setTimeout(function() {{ location.reload(); }}, 1000);
        }}
    }})
    .catch(function() {{
        res.style.background = 'rgba(220,38,38,0.08)';
        res.style.color = '#dc2626';
        res.textContent = '❌ Network error.';
    }});
}}
</script>
""")
