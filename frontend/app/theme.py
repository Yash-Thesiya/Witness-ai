"""
Global theme configuration for Witness UI.
Change colors here — all pages update automatically.
"""

# ─── Core Colors ───────────────────────────────────────────────
PRIMARY = "#4b607f"          # Buttons, active states, links
PRIMARY_HOVER = "#3a4f6e"    # Button hover
PRIMARY_LIGHT = "rgba(75,96,127,0.15)"  # Light tint for cards
PRIMARY_TEXT = "#a8bcce"     # Text on primary bg

SIDEBAR_BG = "#f3701e"       # Sidebar background
SIDEBAR_TEXT = "white"       # Sidebar text
SIDEBAR_ACTIVE = "rgba(0,0,0,0.2)"  # Active nav item
SIDEBAR_HOVER = "rgba(0,0,0,0.12)"  # Hover nav item
SIDEBAR_BORDER = "rgba(0,0,0,0.1)"  # Sidebar border

PAGE_BG = "#e8d8c9"          # Main page background
CARD_BG = "#ffffff"          # Card background
CARD_BORDER = "rgba(0,0,0,0.08)"  # Card border
CARD_BG_SOFT = "#f5ede4"     # Soft card (secondary)

TEXT_PRIMARY = "#1f2937"     # Main text
TEXT_SECONDARY = "#6b7280"   # Muted text
TEXT_MUTED = "#9ca3af"       # Very muted

# ─── Status Colors ─────────────────────────────────────────────
STATUS = {
    "active":    ("#277dff", "rgba(75,96,127,0.12)"),
    "detected":  ("#d97706", "rgba(217,119,6,0.12)"),
    "fulfilled": ("#059669", "rgba(5,150,105,0.12)"),
    "missed":    ("#dc2626", "rgba(220,38,38,0.12)"),
    "modified":  ("#7c3aed", "rgba(124,58,237,0.12)"),
    "blocked":   ("#ea580c", "rgba(234,88,12,0.12)"),
    "cancelled": ("#6b7280", "rgba(107,114,128,0.12)"),
    "confirmed": ("#0891b2", "rgba(8,145,178,0.12)"),
}

STATUS_ICONS = {
    "active": "⚡", "detected": "👁", "fulfilled": "✅",
    "missed": "❌", "modified": "🔄", "blocked": "🚫",
    "cancelled": "⛔", "confirmed": "✓",
}

# ─── Avatar Colors ─────────────────────────────────────────────
AVATAR_COLORS = [
    "#4b607f", "#f3701e", "#059669", "#d97706",
    "#dc2626", "#7c3aed", "#0891b2", "#be185d",
]

# ─── Common CSS ────────────────────────────────────────────────
def get_base_css() -> str:
    return f"""
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: {PAGE_BG} !important; font-family: 'Inter', sans-serif; }}
    .nicegui-content {{ padding: 0 !important; }}

    /* ── Sidebar ── */
    .sidebar {{
        position: fixed; left: 0; top: 0;
        width: 240px; height: 100vh;
        background: {SIDEBAR_BG};
        display: flex; flex-direction: column;
        padding: 24px 0; z-index: 100;
        border-right: 1px solid {SIDEBAR_BORDER};
        box-shadow: 4px 0 20px rgba(0,0,0,0.1);
    }}
    .sidebar-logo {{
        display: flex; align-items: center; gap: 10px;
        padding: 0 20px 28px 20px;
        border-bottom: 1px solid {SIDEBAR_BORDER};
    }}
    .sidebar-logo-icon {{
        width: 38px; height: 38px;
        background: rgba(255,255,255,0.2);
        border-radius: 10px; backdrop-filter: blur(10px);
        display: flex; align-items: center;
        justify-content: center; font-size: 20px;
    }}
    .sidebar-logo-text {{
        font-size: 1.2rem; font-weight: 800;
        color: white; letter-spacing: -0.02em;
    }}
    .sidebar-nav {{
        padding: 20px 12px; flex: 1;
        display: flex; flex-direction: column; gap: 4px;
        overflow-y: auto;
    }}
    .nav-item {{
        display: flex; align-items: center; gap: 12px;
        padding: 10px 14px; border-radius: 10px;
        cursor: pointer; color: rgba(255,255,255,0.8);
        font-size: 0.88rem; font-weight: 500;
        transition: all 0.2s; text-decoration: none;
    }}
    .nav-item:hover {{
        background: {SIDEBAR_HOVER};
        color: white;
    }}
    .nav-item.active {{
        background: {SIDEBAR_ACTIVE};
        color: white; font-weight: 700;
    }}
    .nav-icon {{ font-size: 1rem; width: 20px; text-align: center; }}
    .sidebar-bottom {{
        padding: 16px 12px;
        border-top: 1px solid {SIDEBAR_BORDER};
    }}

    /* ── Main ── */
    .main-content {{
        margin-left: 240px; padding: 28px 32px;
        min-height: 100vh; background: {PAGE_BG};
    }}

    /* ── Cards ── */
    .card {{
        background: {CARD_BG};
        border-radius: 14px; padding: 24px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .card-soft {{
        background: {CARD_BG_SOFT};
        border-radius: 14px; padding: 24px;
        border: 1px solid {CARD_BORDER};
    }}

    /* ── Buttons ── */
    .btn-primary {{
        background: {PRIMARY}; color: white;
        border: none; border-radius: 8px;
        padding: 9px 20px; font-size: 0.85rem;
        font-weight: 600; cursor: pointer;
        transition: background 0.2s;
    }}
    .btn-primary:hover {{ background: {PRIMARY_HOVER}; }}
    .btn-secondary {{
        background: {CARD_BG_SOFT};
        border: 1px solid {CARD_BORDER};
        color: {TEXT_SECONDARY}; border-radius: 8px;
        padding: 9px 20px; font-size: 0.85rem;
        font-weight: 600; cursor: pointer;
        transition: all 0.2s;
    }}
    .btn-secondary:hover {{
        background: {CARD_BG};
        color: {TEXT_PRIMARY};
    }}

    /* ── Topbar ── */
    .topbar {{
        display: flex; align-items: center;
        justify-content: space-between; margin-bottom: 24px;
    }}
    .topbar-title {{
        color: {TEXT_PRIMARY}; font-size: 1.4rem;
        font-weight: 800; letter-spacing: -0.02em;
    }}
    .topbar-sub {{
        color: {TEXT_SECONDARY}; font-size: 0.82rem; margin-top: 2px;
    }}

    /* ── Avatar ── */
    .avatar {{
        width: 36px; height: 36px;
        background: {PRIMARY}; border-radius: 50%;
        display: flex; align-items: center;
        justify-content: center; color: white;
        font-weight: 700; font-size: 0.9rem; cursor: pointer;
    }}

    /* ── Table ── */
    .data-table {{ width: 100%; border-collapse: collapse; }}
    .data-table th {{
        padding: 11px 16px; text-align: left;
        color: {TEXT_MUTED}; font-size: 0.75rem;
        font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.05em;
        background: {CARD_BG_SOFT};
        border-bottom: 1px solid {CARD_BORDER};
    }}
    .data-table td {{
        padding: 13px 16px;
        border-bottom: 1px solid rgba(0,0,0,0.04);
        color: {TEXT_PRIMARY}; font-size: 0.85rem;
    }}
    .data-table tr:last-child td {{ border-bottom: none; }}
    .data-table tr:hover td {{ background: {CARD_BG_SOFT}; }}

    /* ── Status Badge ── */
    .status-badge {{
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.72rem; font-weight: 700;
        display: inline-block;
    }}

    /* ── Input ── */
    .input-field {{
        width: 100%;
        background: {CARD_BG_SOFT};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px; padding: 9px 14px;
        color: {TEXT_PRIMARY}; font-size: 0.85rem;
        outline: none; transition: border 0.2s;
    }}
    .input-field:focus {{
        border-color: {PRIMARY};
        box-shadow: 0 0 0 3px {PRIMARY_LIGHT};
    }}
    .input-field::placeholder {{ color: {TEXT_MUTED}; }}

    /* ── Search box ── */
    .search-wrap {{
        display: flex; align-items: center; gap: 8px;
        background: {CARD_BG_SOFT};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px; padding: 8px 14px;
    }}
    .search-wrap input {{
        background: none; border: none; outline: none;
        color: {TEXT_PRIMARY}; font-size: 0.85rem; width: 100%;
    }}
    .search-wrap input::placeholder {{ color: {TEXT_MUTED}; }}

    /* ── Select ── */
    .select-field {{
        background: {CARD_BG_SOFT};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px; padding: 8px 14px;
        color: {TEXT_PRIMARY}; font-size: 0.82rem;
        outline: none; cursor: pointer;
    }}
    .select-field option {{ background: {CARD_BG}; }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(0,0,0,0.15); border-radius: 3px;
    }}
</style>
"""

def get_sidebar_html(active_page: str = "") -> str:
    pages = [
        ("dashboard", "📊", "Dashboard"),
        ("commitments", "📋", "Commitments"),
        ("calendar", "📅", "Calendar"),
        ("upload", "⬆️", "Upload"),
        ("report", "📈", "Report"),
    ]

    nav_items = ""
    for page_id, icon, label in pages:
        active_class = "active" if active_page == page_id else ""
        nav_items += f"""
        <a class="nav-item {active_class}" href="/{page_id}">
            <span class="nav-icon">{icon}</span> {label}
        </a>
        """

    return f"""
<div class="sidebar">
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">👁</div>
        <span class="sidebar-logo-text">Witness</span>
    </div>
    <nav class="sidebar-nav">
        {nav_items}
    </nav>
    <div class="sidebar-bottom">
        <a class="nav-item" href="/"
            style="color:rgba(255,255,255,0.7)">
            <span class="nav-icon">🚪</span> Logout
        </a>
    </div>
</div>
"""