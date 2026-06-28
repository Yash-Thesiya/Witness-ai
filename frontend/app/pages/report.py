"""
Accountability Report - Themed
"""
import httpx
from nicegui import ui
from app.state import app_state, is_logged_in, logout
from app.theme import (
    get_base_css, get_sidebar_html,
    PRIMARY, PRIMARY_LIGHT, PRIMARY_HOVER,
    PAGE_BG, CARD_BG, CARD_BG_SOFT, CARD_BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    AVATAR_COLORS,
)

BACKEND_URL = "http://backend:8000"


def get_report(token: str) -> dict:
    try:
        r = httpx.get(
            f"{BACKEND_URL}/commitments/report/accountability",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def report_page():
    if not is_logged_in():
        ui.navigate.to("/")
        return

    ui.query("body").style(f"background: {PAGE_BG}")

    data = get_report(app_state["token"])
    summary = data.get("summary", {})
    report = data.get("report", [])
    user_initial = app_state.get("user", "U")[0].upper()

    from datetime import datetime
    date_str = datetime.now().strftime("%b %d, %Y")

    total_owners = summary.get("total_owners", 0)
    total_commitments = summary.get("total_commitments", 0)
    total_fulfilled = summary.get("overall_fulfilled", 0)
    total_missed = summary.get("overall_missed", 0)

    rows_html = ""
    for i, o in enumerate(report):
        name = o["owner"]
        color = AVATAR_COLORS[i % len(AVATAR_COLORS)]
        rate = o["fulfillment_rate"]

        if rate >= 80:
            bar_c, rate_c = "#059669", "#059669"
        elif rate >= 50:
            bar_c, rate_c = "#d97706", "#d97706"
        elif rate > 0:
            bar_c, rate_c = "#dc2626", "#dc2626"
        else:
            bar_c, rate_c = CARD_BORDER, TEXT_MUTED

        rows_html += f"""
        <tr class="data-row owner-row" data-name="{name.lower()}">
            <td>
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="width:32px;height:32px;border-radius:50%;
                        background:{color};color:white;font-weight:700;
                        font-size:0.78rem;display:flex;align-items:center;
                        justify-content:center;flex-shrink:0">
                        {name[0].upper()}
                    </div>
                    <span style="color:{TEXT_PRIMARY};font-size:0.85rem;
                        font-weight:600">{name}</span>
                </div>
            </td>
            <td style="text-align:center;color:{TEXT_SECONDARY};
                font-size:0.85rem;font-weight:600">{o['total']}</td>
            <td style="text-align:center;color:{"#277dff"};
                font-size:0.85rem;font-weight:600">
                {o['active'] + o.get('detected',0)}
            </td>
            <td style="text-align:center;color:#059669;
                font-size:0.85rem;font-weight:600">{o['fulfilled']}</td>
            <td style="text-align:center;color:#dc2626;
                font-size:0.85rem;font-weight:600">{o['missed']}</td>
            <td style="text-align:center;color:#7c3aed;
                font-size:0.85rem;font-weight:600">{o['modified']}</td>
            <td style="min-width:160px">
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="flex:1;background:rgba(0,0,0,0.07);
                        border-radius:20px;height:5px;overflow:hidden">
                        <div style="width:{min(rate,100)}%;height:100%;
                            background:{bar_c};border-radius:20px">
                        </div>
                    </div>
                    <span style="font-size:0.82rem;font-weight:700;
                        color:{rate_c};min-width:38px;text-align:right">
                        {rate}%
                    </span>
                </div>
            </td>
            <td style="text-align:center">
                <button onclick="window.location.href='/commitments?owner={name}'"
                    style="background:none;border:none;
                    color:{TEXT_MUTED};cursor:pointer;
                    font-size:1rem;padding:4px 6px;border-radius:4px"
                    onmouseover="this.style.background='{CARD_BG_SOFT}'"
                    onmouseout="this.style.background='none'">
                    ⋮
                </button>
            </td>
        </tr>
        """

    ui.add_head_html(get_base_css())
    ui.add_head_html(f"""
<style>
    .stat-cards {{
        display: grid;
        grid-template-columns: repeat(4,1fr);
        gap: 16px; margin-bottom: 24px;
    }}
    .s-card {{
        background: {CARD_BG};
        border-radius: 14px; padding: 20px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        position: relative; overflow: hidden;
    }}
    .s-card-label {{
        color: {TEXT_SECONDARY};
        font-size: 0.8rem; font-weight: 500; margin-bottom: 10px;
        display: flex; align-items: center;
        justify-content: space-between;
    }}
    .s-card-icon {{
        width: 36px; height: 36px; border-radius: 8px;
        display: flex; align-items: center;
        justify-content: center; font-size: 1rem;
    }}
    .s-card-value {{
        font-size: 2rem; font-weight: 800;
        color: {TEXT_PRIMARY}; line-height: 1; margin-bottom: 6px;
    }}
    .s-card-sub {{ color: {TEXT_MUTED}; font-size: 0.75rem; }}
    .s-wave {{
        position: absolute; bottom: 0; left: 0; right: 0;
        height: 3px; border-radius: 0 0 14px 14px;
    }}
    .table-card {{
        background: {CARD_BG};
        border-radius: 14px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        overflow: hidden;
    }}
    .t-header {{
        padding: 18px 22px;
        border-bottom: 1px solid {CARD_BORDER};
        display: flex; align-items: center;
        justify-content: space-between;
    }}
    .t-footer {{
        padding: 13px 22px;
        border-top: 1px solid {CARD_BORDER};
        display: flex; align-items: center;
        justify-content: space-between;
    }}
    .owner-row {{ cursor: default; }}
</style>
""")

    ui.add_body_html(f"""
{get_sidebar_html("report")}

<div class="main-content">

    <!-- Topbar -->
    <div class="topbar">
        <div style="display:flex;align-items:center;gap:14px">
            <div style="width:44px;height:44px;
                background:{PRIMARY_LIGHT};border-radius:10px;
                display:flex;align-items:center;
                justify-content:center;font-size:1.3rem">
                📊
            </div>
            <div>
                <div class="topbar-title">Accountability Report ✨</div>
                <div class="topbar-sub">
                    Track commitment ownership and completion.
                </div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
            <div style="background:{CARD_BG};
                border:1px solid {CARD_BORDER};
                border-radius:8px;padding:7px 13px;
                color:{TEXT_SECONDARY};font-size:0.82rem;
                display:flex;align-items:center;gap:6px">
                📅 {date_str}
            </div>
            <button class="btn-secondary"
                style="font-size:0.82rem"
                onclick="exportCSV()">
                ⬆ Export CSV
            </button>
            <div class="avatar">{user_initial}</div>
        </div>
    </div>

    <!-- Stat cards -->
    <div class="stat-cards">
        <div class="s-card">
            <div class="s-card-label">
                Total Owners
                <div class="s-card-icon"
                    style="background:{PRIMARY_LIGHT}">👥</div>
            </div>
            <div class="s-card-value">{total_owners}</div>
            <div class="s-card-sub">— No change</div>
            <div class="s-wave" style="background:{"#277dff"}"></div>
        </div>
        <div class="s-card">
            <div class="s-card-label">
                Total Commitments
                <div class="s-card-icon"
                    style="background:{PRIMARY_LIGHT}">📋</div>
            </div>
            <div class="s-card-value">{total_commitments}</div>
            <div class="s-card-sub" style="color:#059669">↑ Active tracking</div>
            <div class="s-wave" style="background:{PRIMARY}"></div>
        </div>
        <div class="s-card">
            <div class="s-card-label">
                Total Fulfilled
                <div class="s-card-icon"
                    style="background:rgba(5,150,105,0.1)">✅</div>
            </div>
            <div class="s-card-value"
                style="color:#059669">{total_fulfilled}</div>
            <div class="s-card-sub" style="color:#059669">↑ Completed</div>
            <div class="s-wave" style="background:#059669"></div>
        </div>
        <div class="s-card">
            <div class="s-card-label">
                Total Missed
                <div class="s-card-icon"
                    style="background:rgba(220,38,38,0.08)">❌</div>
            </div>
            <div class="s-card-value"
                style="color:#dc2626">{total_missed}</div>
            <div class="s-card-sub">— Overdue</div>
            <div class="s-wave" style="background:#dc2626"></div>
        </div>
    </div>

    <!-- Table -->
    <div class="table-card">
        <div class="t-header">
            <div style="display:flex;align-items:center;gap:10px">
                <span style="font-size:1rem">👥</span>
                <span style="color:{TEXT_PRIMARY};font-size:0.95rem;
                    font-weight:700">Per Owner Breakdown</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
                <div class="search-wrap" style="min-width:180px">
                    <span style="color:{TEXT_MUTED}">🔍</span>
                    <input placeholder="Search owner..."
                        oninput="filterOwners(this.value)">
                </div>
            </div>
        </div>

        <table class="data-table">
            <thead>
                <tr>
                    <th style="width:200px">Owner</th>
                    <th style="text-align:center">Total</th>
                    <th style="text-align:center">Active</th>
                    <th style="text-align:center">Fulfilled</th>
                    <th style="text-align:center">Missed</th>
                    <th style="text-align:center">Modified</th>
                    <th style="min-width:170px">Fulfillment Rate</th>
                    <th style="width:40px"></th>
                </tr>
            </thead>
            <tbody id="owner-tbody">
                {rows_html if rows_html else f'''
                <tr><td colspan="8" style="text-align:center;
                    padding:40px;color:{TEXT_MUTED}">
                    No data yet. Upload transcripts to get started!
                </td></tr>
                '''}
            </tbody>
        </table>

        <div class="t-footer">
            <span style="color:{TEXT_MUTED};font-size:0.8rem">
                Showing {len(report)} owners
            </span>
        </div>
    </div>
</div>

<script>
function filterOwners(q) {{
    q = q.toLowerCase();
    document.querySelectorAll('.owner-row').forEach(function(r) {{
        r.style.display =
            r.getAttribute('data-name').includes(q) ? '' : 'none';
    }});
}}

function exportCSV() {{
    var rows = [['Owner','Total','Active','Fulfilled',
        'Missed','Modified','Rate']];
    document.querySelectorAll('.owner-row').forEach(function(r) {{
        var cells = r.querySelectorAll('td');
        rows.push([
            cells[0].querySelector('span:last-child').textContent.trim(),
            cells[1].textContent.trim(),
            cells[2].textContent.trim(),
            cells[3].textContent.trim(),
            cells[4].textContent.trim(),
            cells[5].textContent.trim(),
            cells[6].querySelector('span').textContent.trim(),
        ]);
    }});
    var csv = rows.map(function(r) {{
        return r.map(function(c) {{
            return '"' + c.replace(/"/g,'""') + '"';
        }}).join(',');
    }}).join('\\n');
    var blob = new Blob([csv], {{type:'text/csv'}});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = 'witness-report.csv';
    a.click(); URL.revokeObjectURL(url);
}}
</script>
""")