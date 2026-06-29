"""
Upload page — Drag & Drop — Themed
"""
import os
import tempfile
import httpx
from nicegui import ui
from app.state import app_state, is_logged_in, logout
from app.theme import get_base_css, get_sidebar_html, PRIMARY, PRIMARY_LIGHT, PRIMARY_HOVER, PAGE_BG, CARD_BG, CARD_BG_SOFT, CARD_BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED

BACKEND_URL = "http://localhost:8000"


def upload_page():
    if not is_logged_in():
        ui.navigate.to("/")
        return

    ui.query("body").style(f"background: {PAGE_BG}")

    try:
        r = httpx.get(
            f"{BACKEND_URL}/uploads/",
            headers={"Authorization": f"Bearer {app_state['token']}"},
            timeout=10,
        )
        uploads = r.json() if r.status_code == 200 else []
    except Exception:
        uploads = []

    uploads_html = ""
    for u in uploads[:10]:
        is_audio = u.get("file_type") == "audio"
        icon = "🎙" if is_audio else "📄"
        icon_bg = f"{PRIMARY_LIGHT}" if is_audio else "rgba(5,150,105,0.12)"
        ps = u.get("processing_status", "pending")
        ps_map = {
            "completed": ("rgba(5,150,105,0.12)", "#059669"),
            "pending": ("rgba(217,119,6,0.12)", "#d97706"),
            "processing": (PRIMARY_LIGHT, PRIMARY),
            "failed": ("rgba(220,38,38,0.12)", "#dc2626"),
        }
        ps_bg, ps_color = ps_map.get(ps, ("rgba(107,114,128,0.12)", "#6b7280"))
        name = u.get("file_name", "")
        if len(name) > 45:
            name = name[:45] + "..."

        uploads_html += f"""
        <div style="display:flex;align-items:center;gap:12px;
            padding:11px 0;border-bottom:1px solid {CARD_BORDER}">
            <div style="width:36px;height:36px;border-radius:8px;
                background:{icon_bg};display:flex;align-items:center;
                justify-content:center;font-size:1rem;flex-shrink:0">
                {icon}
            </div>
            <div style="flex:1">
                <div style="color:{TEXT_PRIMARY};font-size:0.82rem;font-weight:500">
                    {name}
                </div>
                <div style="color:{TEXT_MUTED};font-size:0.72rem;margin-top:1px">
                    {u.get('file_type','').upper()} • {u.get('created_at','')[:10]}
                </div>
            </div>
            <span style="padding:3px 10px;border-radius:20px;
                font-size:0.7rem;font-weight:700;
                background:{ps_bg};color:{ps_color}">
                {ps.upper()}
            </span>
        </div>
        """

    token = app_state["token"]

    ui.add_head_html(get_base_css())
    ui.add_head_html(f"""
<style>
    .upload-grid {{
        display: grid; grid-template-columns: 1fr 1fr;
        gap: 20px; margin-bottom: 24px;
    }}
    .upload-card {{
        background: {CARD_BG};
        border-radius: 14px; padding: 24px;
        border: 1px solid {CARD_BORDER};
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .upload-card-title {{
        color: {TEXT_PRIMARY}; font-size: 0.95rem;
        font-weight: 700; margin-bottom: 4px;
    }}
    .upload-card-sub {{
        color: {TEXT_MUTED}; font-size: 0.8rem; margin-bottom: 18px;
    }}
    .drop-zone {{
        border: 2px dashed {CARD_BORDER};
        border-radius: 12px; padding: 36px 20px;
        text-align: center; cursor: pointer;
        transition: all 0.25s;
        background: {CARD_BG_SOFT};
    }}
    .drop-zone:hover, .drop-zone.dragover {{
        border-color: {PRIMARY};
        background: {PRIMARY_LIGHT};
    }}
    .drop-zone.dragover {{ transform: scale(1.01); }}
    .drop-icon {{ font-size: 2.5rem; margin-bottom: 10px; }}
    .drop-title {{
        color: {TEXT_PRIMARY}; font-size: 0.9rem;
        font-weight: 600; margin-bottom: 5px;
    }}
    .drop-sub {{
        color: {TEXT_MUTED}; font-size: 0.78rem; margin-bottom: 14px;
    }}
    .drop-formats {{
        display: flex; gap: 6px;
        justify-content: center; margin-bottom: 14px;
    }}
    .fmt-badge {{
        background: {PRIMARY_LIGHT};
        color: {PRIMARY}; border-radius: 6px;
        padding: 3px 10px; font-size: 0.72rem; font-weight: 700;
    }}
    .progress-wrap {{
        background: rgba(0,0,0,0.06);
        border-radius: 20px; height: 5px;
        margin: 12px 0; overflow: hidden; display: none;
    }}
    .progress-fill {{
        height: 100%; background: {PRIMARY};
        border-radius: 20px; width: 0%;
        transition: width 0.3s;
    }}
    .upload-msg {{
        margin-top: 10px; padding: 9px 13px;
        border-radius: 8px; font-size: 0.82rem;
        font-weight: 500; display: none;
    }}
    .upload-msg.success {{
        background: rgba(5,150,105,0.1);
        border: 1px solid rgba(5,150,105,0.25);
        color: #059669;
    }}
    .upload-msg.error {{
        background: rgba(220,38,38,0.08);
        border: 1px solid rgba(220,38,38,0.2);
        color: #dc2626;
    }}
    .upload-msg.loading {{
        background: {PRIMARY_LIGHT};
        border: 1px solid rgba(75,96,127,0.2);
        color: {PRIMARY};
    }}
    .hidden-input {{ display: none; }}
</style>
""")

    ui.add_body_html(f"""
{get_sidebar_html("upload")}

<div class="main-content">
    <div class="topbar">
        <div>
            <div class="topbar-title">⬆️ Upload Files</div>
            <div class="topbar-sub">
                Upload transcripts or audio recordings to extract commitments automatically.
            </div>
        </div>
    </div>

    <div class="upload-grid">

        <!-- Transcript -->
        <div class="upload-card">
            <div class="upload-card-title">📄 Transcript Upload</div>
            <div class="upload-card-sub">TXT, PDF, DOCX files supported</div>
            <div class="drop-zone" id="t-drop"
                ondragover="dOver(event,'t-drop')"
                ondragleave="dLeave('t-drop')"
                ondrop="dDrop(event,'transcript')"
                onclick="document.getElementById('t-input').click()">
                <div class="drop-icon">📄</div>
                <div class="drop-title">Drag & Drop your file here</div>
                <div class="drop-sub">or click to browse</div>
                <div class="drop-formats">
                    <span class="fmt-badge">TXT</span>
                    <span class="fmt-badge">PDF</span>
                    <span class="fmt-badge">DOCX</span>
                </div>
                <button class="btn-primary"
                    onclick="event.stopPropagation();
                    document.getElementById('t-input').click()">
                    Browse Files
                </button>
            </div>
            <input type="file" id="t-input" class="hidden-input"
                accept=".txt,.pdf,.docx"
                onchange="fileSelected(event,'transcript')">
            <div class="progress-wrap" id="t-prog-wrap">
                <div class="progress-fill" id="t-prog"></div>
            </div>
            <div class="upload-msg" id="t-msg"></div>
        </div>

        <!-- Audio -->
        <div class="upload-card">
            <div class="upload-card-title">🎙 Audio Upload</div>
            <div class="upload-card-sub">MP3, WAV, M4A files supported</div>
            <div class="drop-zone" id="a-drop"
                ondragover="dOver(event,'a-drop')"
                ondragleave="dLeave('a-drop')"
                ondrop="dDrop(event,'audio')"
                onclick="document.getElementById('a-input').click()">
                <div class="drop-icon">🎙</div>
                <div class="drop-title">Drag & Drop your audio here</div>
                <div class="drop-sub">or click to browse</div>
                <div class="drop-formats">
                    <span class="fmt-badge">MP3</span>
                    <span class="fmt-badge">WAV</span>
                    <span class="fmt-badge">M4A</span>
                </div>
                <button class="btn-primary"
                    onclick="event.stopPropagation();
                    document.getElementById('a-input').click()">
                    Browse Files
                </button>
            </div>
            <input type="file" id="a-input" class="hidden-input"
                accept=".mp3,.wav,.m4a"
                onchange="fileSelected(event,'audio')">
            <div class="progress-wrap" id="a-prog-wrap">
                <div class="progress-fill" id="a-prog"></div>
            </div>
            <div class="upload-msg" id="a-msg"></div>
        </div>
    </div>

    <!-- Recent uploads -->
    <div class="card">
        <div style="display:flex;align-items:center;
            justify-content:space-between;margin-bottom:16px">
            <span style="color:{TEXT_PRIMARY};font-size:0.95rem;font-weight:700">
                📁 Recent Uploads
            </span>
        </div>
        {uploads_html if uploads_html else
            f'<div style="color:{TEXT_MUTED};font-size:0.85rem">No uploads yet.</div>'
        }
    </div>
</div>

<script>
var TOKEN = "{token}";
var API = "https://witness-ai.onrender.com";

function dOver(e, id) {{
    e.preventDefault();
    document.getElementById(id).classList.add('dragover');
}}
function dLeave(id) {{
    document.getElementById(id).classList.remove('dragover');
}}
function dDrop(e, type) {{
    e.preventDefault();
    document.getElementById(type[0] + '-drop').classList.remove('dragover');
    var files = e.dataTransfer.files;
    if (files.length > 0) upload(files[0], type);
}}
function fileSelected(e, type) {{
    if (e.target.files.length > 0) upload(e.target.files[0], type);
}}

function showMsg(type, text, cls) {{
    var el = document.getElementById(type[0] + '-msg');
    el.textContent = text;
    el.className = 'upload-msg ' + cls;
    el.style.display = 'block';
}}

function showProg(type, show) {{
    var wrap = document.getElementById(type[0] + '-prog-wrap');
    var bar = document.getElementById(type[0] + '-prog');
    wrap.style.display = show ? 'block' : 'none';
    if (show) {{
        bar.style.width = '0%';
        setTimeout(function() {{ bar.style.width = '40%'; }}, 100);
        setTimeout(function() {{ bar.style.width = '75%'; }}, 600);
        setTimeout(function() {{ bar.style.width = '90%'; }}, 1200);
    }}
}}

function validate(file, type) {{
    var n = file.name.toLowerCase();
    if (type === 'transcript') {{
        if (!n.endsWith('.txt') && !n.endsWith('.pdf') && !n.endsWith('.docx')) {{
            showMsg('transcript', '❌ Only TXT, PDF, DOCX allowed.', 'error');
            return false;
        }}
    }} else {{
        if (!n.endsWith('.mp3') && !n.endsWith('.wav') && !n.endsWith('.m4a')) {{
            showMsg('audio', '❌ Only MP3, WAV, M4A allowed.', 'error');
            return false;
        }}
    }}
    return true;
}}

function upload(file, type) {{
    if (!validate(file, type)) return;
    var ep = type === 'transcript'
        ? API + '/uploads/transcript'
        : API + '/uploads/audio';

    showMsg(type, '⏳ Uploading ' + file.name + '...', 'loading');
    showProg(type, true);

    var fd = new FormData();
    fd.append('file', file);
    var xhr = new XMLHttpRequest();
    xhr.open('POST', ep);
    xhr.setRequestHeader('Authorization', 'Bearer ' + TOKEN);

    xhr.onload = function() {{
        showProg(type, false);
        if (xhr.status === 201) {{
            var d = JSON.parse(xhr.responseText);
            if (type === 'transcript') {{
                showMsg('transcript',
                    '✅ Uploaded! ' + (d.characters_extracted||0) + ' chars extracted. AI extraction queued...',
                    'success');
            }} else {{
                showMsg('audio',
                    '✅ Audio uploaded! Transcription running in background...',
                    'success');
            }}
            setTimeout(function() {{ location.reload(); }}, 2000);
        }} else {{
            var err = JSON.parse(xhr.responseText);
            showMsg(type, '❌ ' + (err.detail || 'Upload failed'), 'error');
        }}
    }};
    xhr.onerror = function() {{
        showProg(type, false);
        showMsg(type, '❌ Network error. Try again.', 'error');
    }};
    xhr.send(fd);
}}
</script>
""")
