"""
Dashboard page - Modern Minimal UI
"""
import json
import httpx
from nicegui import ui
from app.state import app_state, is_logged_in, logout
from app.theme import (
    get_base_css, get_sidebar_html,
    PRIMARY, PRIMARY_LIGHT, PRIMARY_HOVER,
    PAGE_BG, CARD_BG, CARD_BG_SOFT, CARD_BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SIDEBAR_BG, STATUS, STATUS_ICONS, AVATAR_COLORS,
)

BACKEND_URL = "http://backend:8000"


def get_dashboard_data(token: str) -> dict:
    try:
        r = httpx.get(
            f"{BACKEND_URL}/commitments/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def get_commitments(token: str) -> list:
    try:
        r = httpx.get(
            f"{BACKEND_URL}/commitments/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def dashboard_page():
    if not is_logged_in():
        ui.navigate.to("/")
        return

    user_email = app_state.get("user", "User")
    user_initial = user_email[0].upper()

    data = get_dashboard_data(app_state["token"])
    all_commitments = get_commitments(app_state["token"])

    active = data.get("active", 0)
    detected = data.get("detected", 0)
    fulfilled = data.get("fulfilled", 0)
    missed = data.get("missed", 0)
    due_soon = data.get("due_soon", 0)
    total = data.get("total", 0)

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    soon_limit = now + timedelta(days=7)

    due_soon_list = []
    for c in all_commitments:
        if c.get("due_date") and c.get("status") not in ["fulfilled", "cancelled"]:
            try:
                due = datetime.fromisoformat(c["due_date"].replace("Z", "+00:00"))
                if due <= soon_limit:
                    days_left = (due - now).days
                    due_soon_list.append({**c, "days_left": max(0, days_left)})
            except Exception:
                pass
    due_soon_list.sort(key=lambda x: x.get("days_left", 999))

    pie_data = []
    if active > 0:
        pie_data.append({"value": active, "name": "Active", "itemStyle": {"color": "#277dff"}})
    if detected > 0:
        pie_data.append({"value": detected, "name": "Detected", "itemStyle": {"color": "#d97706"}})
    if fulfilled > 0:
        pie_data.append({"value": fulfilled, "name": "Fulfilled", "itemStyle": {"color": "#059669"}})
    if missed > 0:
        pie_data.append({"value": missed, "name": "Missed", "itemStyle": {"color": "#dc2626"}})

    pie_json = json.dumps(pie_data)

    ui.add_head_html(get_base_css())
    ui.add_head_html(f"""
<style>
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px; margin-bottom: 20px;
    }}
    .stat-card {{
        background: {CARD_BG};
        border-radius: 14px; padding: 20px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
        position: relative; overflow: hidden;
    }}
    .stat-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .stat-icon {{
        width: 42px; height: 42px; border-radius: 10px;
        display: flex; align-items: center;
        justify-content: center; font-size: 1.2rem;
        margin-bottom: 14px;
    }}
    .stat-label {{
        color: {TEXT_SECONDARY}; font-size: 0.8rem;
        font-weight: 500; margin-bottom: 6px;
    }}
    .stat-value {{
        color: {TEXT_PRIMARY}; font-size: 2rem;
        font-weight: 800; line-height: 1; margin-bottom: 4px;
    }}
    .stat-sub {{ color: {TEXT_MUTED}; font-size: 0.75rem; }}
    .stat-wave {{
        position: absolute; bottom: 0; left: 0; right: 0;
        height: 3px; border-radius: 0 0 14px 14px;
    }}
    .alert-banner {{
        background: {CARD_BG};
        border: 1px solid rgba(220,38,38,0.2);
        border-left: 4px solid #dc2626;
        border-radius: 12px; padding: 14px 20px;
        display: flex; align-items: center;
        justify-content: space-between; margin-bottom: 20px;
    }}
    .content-grid {{
        display: grid;
        grid-template-columns: 1fr 360px; gap: 20px;
    }}
    .section-card {{
        background: {CARD_BG};
        border-radius: 14px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        overflow: hidden; margin-bottom: 20px;
    }}
    .section-header {{
        padding: 18px 20px;
        border-bottom: 1px solid {CARD_BORDER};
        display: flex; align-items: center;
        justify-content: space-between;
    }}
    .section-title {{
        color: {TEXT_PRIMARY}; font-size: 0.95rem; font-weight: 700;
    }}
    .commit-row {{
        display: flex; align-items: center; gap: 12px;
        padding: 13px 20px;
        border-bottom: 1px solid rgba(0,0,0,0.04);
        transition: background 0.15s;
    }}
    .commit-row:hover {{ background: {CARD_BG_SOFT}; }}
    .commit-row:last-child {{ border-bottom: none; }}
    .right-col {{ display: flex; flex-direction: column; gap: 20px; }}
    .overview-card {{
        background: {CARD_BG};
        border-radius: 14px; padding: 20px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    #pie-chart {{ width: 100%; height: 240px; }}
    .due-item {{
        display: flex; align-items: center; gap: 10px;
        padding: 10px 0;
        border-bottom: 1px solid rgba(0,0,0,0.04);
    }}
    .due-item:last-child {{ border-bottom: none; }}
    .days-badge {{
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.72rem; font-weight: 700;
        background: {PRIMARY_LIGHT};
        color: {PRIMARY}; white-space: nowrap;
    }}
    .days-badge.urgent {{
        background: rgba(220,38,38,0.1); color: #dc2626;
    }}
</style>
""")

    # Commitment rows
    commit_rows_html = ""
    for i, c in enumerate(all_commitments[:8]):
        status = c.get("status", "detected")
        color, bg = STATUS.get(status, ("#6b7280", "rgba(107,114,128,0.12)"))
        icon = STATUS_ICONS.get(status, "📋")
        due = c["due_date"][:10] if c.get("due_date") else "No deadline"
        owner_color = AVATAR_COLORS[i % len(AVATAR_COLORS)]

        commit_rows_html += f"""
        <div class="commit-row">
            <div style="width:34px;height:34px;border-radius:50%;
                background:{owner_color};flex-shrink:0;
                display:flex;align-items:center;justify-content:center;
                color:white;font-weight:700;font-size:0.82rem">
                {c['owner'][0].upper()}
            </div>
            <div style="flex:1">
                <div style="color:{TEXT_PRIMARY};font-size:0.85rem;font-weight:500">
                    {c['owner']} — {c['action'][:45]}{'...' if len(c['action'])>45 else ''}
                </div>
                <div style="color:{TEXT_MUTED};font-size:0.75rem;margin-top:2px">
                    Due: {due}
                </div>
            </div>
            <span class="status-badge"
                style="background:{bg};color:{color};border:1px solid {color}33">
                {status.upper()}
            </span>
            <a href="/commitments/{c['id']}"
                style="background:{CARD_BG_SOFT};
                border:1px solid {CARD_BORDER};
                color:{TEXT_SECONDARY};border-radius:6px;
                padding:5px 12px;font-size:0.78rem;
                font-weight:500;cursor:pointer;text-decoration:none">
                View
            </a>
        </div>
        """

    # Due soon rows
    due_soon_html = ""
    for c in due_soon_list[:5]:
        days = c.get("days_left", 0)
        status = c.get("status", "active")
        color, _ = STATUS.get(status, ("#4b607f", ""))
        urgent = "urgent" if days <= 2 else ""
        due_soon_html += f"""
        <div class="due-item">
            <div style="width:8px;height:8px;border-radius:50%;
                background:{color};flex-shrink:0"></div>
            <div style="flex:1">
                <div style="color:{TEXT_PRIMARY};font-size:0.82rem;font-weight:500">
                    {c['owner']} — {c['action'][:35]}{'...' if len(c['action'])>35 else ''}
                </div>
                <div style="color:{TEXT_MUTED};font-size:0.72rem;margin-top:1px">
                    Due: {c['due_date'][:10] if c.get('due_date') else ''}
                </div>
            </div>
            <span class="days-badge {urgent}">
                {days} day{'s' if days!=1 else ''} left
            </span>
        </div>
        """

    # Pie legend
    pie_legend_html = ""
    for item in pie_data:
        pct = round(item["value"] / max(total, 1) * 100)
        c = item["itemStyle"]["color"]
        pie_legend_html += f"""
        <div style="display:flex;align-items:center;
            justify-content:space-between;padding:5px 0">
            <div style="display:flex;align-items:center;gap:8px">
                <div style="width:10px;height:10px;border-radius:50%;
                    background:{c}"></div>
                <span style="color:{TEXT_SECONDARY};font-size:0.8rem">
                    {item['name']}
                </span>
            </div>
            <div style="display:flex;gap:16px">
                <span style="color:{TEXT_PRIMARY};font-size:0.8rem;font-weight:600">
                    {item['value']}
                </span>
                <span style="color:{TEXT_MUTED};font-size:0.8rem">{pct}%</span>
            </div>
        </div>
        """

    pie_legend_html += f"""
    <div style="border-top:1px solid {CARD_BORDER};
        margin-top:8px;padding-top:8px;
        display:flex;justify-content:space-between">
        <span style="color:{TEXT_SECONDARY};font-size:0.8rem;font-weight:600">Total</span>
        <span style="color:{TEXT_PRIMARY};font-size:0.8rem;font-weight:800">{total}</span>
    </div>
    """

    alert_html = "" if due_soon == 0 else f"""
    <div class="alert-banner">
        <div style="display:flex;align-items:center;gap:12px">
            <span style="font-size:1.3rem">🔔</span>
            <div>
                <div style="color:#dc2626;font-weight:600;font-size:0.9rem">
                    {due_soon} commitment{'s' if due_soon>1 else ''} due in next 7 days
                </div>
                <div style="color:{TEXT_MUTED};font-size:0.8rem;margin-top:2px">
                    Stay on track!
                </div>
            </div>
        </div>
        <button class="btn-primary" onclick="window.location.href='/calendar'">
            View Calendar →
        </button>
    </div>
    """

    ui.add_body_html(f"""
{get_sidebar_html("dashboard")}

<div class="main-content">
    <div class="topbar">
        <div>
            <div class="topbar-title">
                Welcome back, {user_email.split('@')[0].capitalize()}! 👋
            </div>
            <div class="topbar-sub">
                Here's what's happening with your commitments today.
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
            <div style="position:relative;
                background:{CARD_BG};
                border:1px solid {CARD_BORDER};
                border-radius:8px;width:36px;height:36px;
                display:flex;align-items:center;
                justify-content:center;cursor:pointer;
                color:{TEXT_SECONDARY}"
                onclick="window.location.href='/commitments'">
                🔔
                <span style="position:absolute;top:-4px;right:-4px;
                    background:#dc2626;color:white;border-radius:50%;
                    width:16px;height:16px;font-size:0.6rem;font-weight:700;
                    display:flex;align-items:center;justify-content:center">
                    {due_soon}
                </span>
            </div>
            <div class="avatar">{user_initial}</div>
        </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
        <div class="stat-card"
            onclick="window.location.href='/commitments?status=active'">
            <div class="stat-icon" style="background:{PRIMARY_LIGHT}">⚡</div>
            <div class="stat-label">Active</div>
            <div class="stat-value">{active}</div>
            <div class="stat-sub">In progress</div>
            <div class="stat-wave" style="background:{"#277dff"}"></div>
        </div>
        <div class="stat-card"
            onclick="window.location.href='/commitments?status=detected'">
            <div class="stat-icon" style="background:rgba(217,119,6,0.12)">👁</div>
            <div class="stat-label">Detected</div>
            <div class="stat-value">{detected}</div>
            <div class="stat-sub">Needs attention</div>
            <div class="stat-wave" style="background:#d97706"></div>
        </div>
        <div class="stat-card"
            onclick="window.location.href='/commitments?status=fulfilled'">
            <div class="stat-icon" style="background:rgba(5,150,105,0.12)">✅</div>
            <div class="stat-label">Fulfilled</div>
            <div class="stat-value">{fulfilled}</div>
            <div class="stat-sub">Completed</div>
            <div class="stat-wave" style="background:#059669"></div>
        </div>
        <div class="stat-card"
            onclick="window.location.href='/commitments?status=missed'">
            <div class="stat-icon" style="background:rgba(220,38,38,0.12)">❌</div>
            <div class="stat-label">Missed</div>
            <div class="stat-value">{missed}</div>
            <div class="stat-sub">Overdue</div>
            <div class="stat-wave" style="background:#dc2626"></div>
        </div>
    </div>

    {alert_html}

    <!-- Content grid -->
    <div class="content-grid">
        <div>
            <div class="section-card">
                <div class="section-header">
                    <span class="section-title">Recent Commitments</span>
                    <button class="btn-secondary"
                        style="padding:5px 14px;font-size:0.78rem"
                        onclick="window.location.href='/commitments'">
                        View All
                    </button>
                </div>
                {commit_rows_html if commit_rows_html else f'''
                <div style="text-align:center;padding:40px;color:{TEXT_MUTED}">
                    <div style="font-size:2rem;margin-bottom:10px">📋</div>
                    <div>No commitments yet.</div>
                    <button class="btn-primary" style="margin-top:12px"
                        onclick="window.location.href='/upload'">
                        Upload Now
                    </button>
                </div>
                '''}
            </div>
        </div>

        <div class="right-col">
            <div class="overview-card">
                <div class="section-header" style="padding:0 0 14px 0;
                    border-bottom:1px solid {CARD_BORDER};margin-bottom:14px">
                    <span class="section-title">✨ Commitment Overview</span>
                </div>
                <div id="pie-chart"></div>
                {pie_legend_html}
            </div>

            <div class="overview-card">
                <div class="section-header" style="padding:0 0 14px 0;
                    border-bottom:1px solid {CARD_BORDER};margin-bottom:14px">
                    <span class="section-title">⏰ Upcoming Due Soon</span>
                </div>
                {due_soon_html if due_soon_html else
                    f'<div style="color:{TEXT_MUTED};font-size:0.85rem">No upcoming deadlines.</div>'
                }
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<script>
(function() {{
    function initChart() {{
        var el = document.getElementById('pie-chart');
        if (!el) {{ setTimeout(initChart, 200); return; }}
        var chart = echarts.init(el);
        chart.setOption({{
            backgroundColor: 'transparent',
            tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}} ({{d}}%)' }},
            legend: {{ show: false }},
            series: [{{
                type: 'pie',
                radius: ['50%', '72%'],
                center: ['50%', '45%'],
                data: {pie_json},
                label: {{
                    show: true, position: 'center',
                    formatter: '{total}\\nTotal',
                    color: '{TEXT_PRIMARY}',
                    fontSize: 22, fontWeight: 'bold',
                    lineHeight: 28,
                }},
                labelLine: {{ show: false }},
                itemStyle: {{
                    borderRadius: 4,
                    borderWidth: 2,
                    borderColor: '{CARD_BG}'
                }}
            }}]
        }});
        window.addEventListener('resize', function() {{ chart.resize(); }});
    }}
    setTimeout(initChart, 100);
}})();
</script>
""")