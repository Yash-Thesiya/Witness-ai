"""
Login and Register page — Witness modern UI.
Theme: matches theme.py (orange sidebar, blue-gray primary, beige background)
"""
from nicegui import ui
from app import api
from app.state import app_state


def login_page():

    ui.add_head_html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#e8d8c9 !important; font-family:'Inter',sans-serif; }
.nicegui-content { padding:0 !important; }

.login-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #e8d8c9;
}

/* Decorative left strip — mirrors sidebar orange */
.login-wrapper::before {
    content: '';
    position: fixed;
    left: 0; top: 0;
    width: 6px; height: 100vh;
    background: #f3701e;
}

.login-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 40px 36px;
    width: 420px;
    box-shadow: 0 8px 40px rgba(75,96,127,0.14);
    border: 1.5px solid rgba(0,0,0,0.08);
}

/* Brand */
.brand-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 6px;
}
.brand-icon {
    width: 42px; height: 42px;
    background: #f3701e;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 12px rgba(243,112,30,0.35);
}
.brand-name {
    font-size: 1.6rem;
    font-weight: 800;
    color: #1f2937;
    letter-spacing: -0.02em;
}
.brand-sub {
    text-align: center;
    color: #9ca3af;
    font-size: 0.83rem;
    margin-bottom: 28px;
}

/* Tabs */
.tab-switcher {
    display: flex;
    background: #f5ede4;
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 24px;
    border: 1.5px solid rgba(0,0,0,0.08);
}
.tab-btn {
    flex: 1;
    text-align: center;
    padding: 9px 0;
    border-radius: 7px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    color: #9ca3af;
    border: none;
    background: none;
    font-family: 'Inter', sans-serif;
    transition: all 0.18s;
}
.tab-btn.active {
    background: white;
    color: #4b607f;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

/* Form fields */
.field-group { margin-bottom: 16px; }
.field-label {
    display: block;
    font-size: 0.8rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
}
.field-input {
    width: 100%;
    padding: 11px 14px;
    border: 1.5px solid rgba(0,0,0,0.08);
    border-radius: 9px;
    font-size: 0.875rem;
    font-family: 'Inter', sans-serif;
    color: #1f2937;
    outline: none;
    background: #f5ede4;
    transition: border-color 0.18s, box-shadow 0.18s;
}
.field-input:focus {
    border-color: #4b607f;
    box-shadow: 0 0 0 3px rgba(75,96,127,0.15);
    background: #ffffff;
}
.field-input::placeholder { color: #9ca3af; }

/* Password wrapper */
.pw-wrapper { position: relative; }
.pw-toggle {
    position: absolute; right: 12px; top: 50%;
    transform: translateY(-50%);
    background: none; border: none; cursor: pointer;
    color: #9ca3af; font-size: 1rem; padding: 2px;
}
.pw-toggle:hover { color: #4b607f; }

/* Submit buttons */
.submit-btn {
    width: 100%;
    padding: 12px;
    background: #4b607f;
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    margin-top: 6px;
    transition: background 0.18s, transform 0.1s, box-shadow 0.18s;
    box-shadow: 0 4px 12px rgba(75,96,127,0.3);
}
.submit-btn:hover {
    background: #3a4f6e;
    box-shadow: 0 6px 18px rgba(75,96,127,0.4);
    transform: translateY(-1px);
}
.submit-btn:active { transform: translateY(0); }

.submit-btn.register {
    background: #f3701e;
    box-shadow: 0 4px 12px rgba(243,112,30,0.3);
}
.submit-btn.register:hover {
    background: #d95e10;
    box-shadow: 0 6px 18px rgba(243,112,30,0.4);
}

.error-msg   { color: #dc2626; font-size: 0.78rem; margin-top: 6px; font-weight: 500; }
.success-msg { color: #059669; font-size: 0.78rem; margin-top: 6px; font-weight: 500; }

.panel { display: none; }
.panel.active { display: block; }

.footer-note {
    text-align: center;
    margin-top: 20px;
    font-size: 0.76rem;
    color: #9ca3af;
}
</style>
""")

    ui.add_body_html("""
<div class="login-wrapper">
    <div class="login-card">

        <!-- Brand -->
        <div class="brand-logo">
            <div class="brand-icon">👁</div>
            <span class="brand-name">Witness</span>
        </div>
        <div class="brand-sub">Commitment Tracking System</div>

        <!-- Tab switcher -->
        <div class="tab-switcher">
            <button class="tab-btn active" id="tab-login" onclick="switchTab('login')">Login</button>
            <button class="tab-btn" id="tab-register" onclick="switchTab('register')">Register</button>
        </div>

        <!-- Login Panel -->
        <div class="panel active" id="panel-login">
            <div class="field-group">
                <label class="field-label">Email</label>
                <input class="field-input" id="login-email" type="email" placeholder="you@example.com"
                    onkeydown="if(event.key==='Enter') doLogin()">
            </div>
            <div class="field-group">
                <label class="field-label">Password</label>
                <div class="pw-wrapper">
                    <input class="field-input" id="login-password" type="password" placeholder="Enter your password"
                        onkeydown="if(event.key==='Enter') doLogin()">
                    <button class="pw-toggle" onclick="togglePw('login-password', this)">👁</button>
                </div>
            </div>
            <div id="login-error" class="error-msg"></div>
            <button class="submit-btn" onclick="doLogin()">Login</button>
        </div>

        <!-- Register Panel -->
        <div class="panel" id="panel-register">
            <div class="field-group">
                <label class="field-label">Email</label>
                <input class="field-input" id="reg-email" type="email" placeholder="you@example.com">
            </div>
            <div class="field-group">
                <label class="field-label">Password</label>
                <div class="pw-wrapper">
                    <input class="field-input" id="reg-password" type="password" placeholder="Min. 6 characters"
                        onkeydown="if(event.key==='Enter') doRegister()">
                    <button class="pw-toggle" onclick="togglePw('reg-password', this)">👁</button>
                </div>
            </div>
            <div id="reg-error" class="error-msg"></div>
            <div id="reg-success" class="success-msg"></div>
            <button class="submit-btn register" onclick="doRegister()">Create Account</button>
        </div>

        <div class="footer-note">© 2026 Witness. All rights reserved.</div>
    </div>
</div>

<script>
function switchTab(tab) {
    document.getElementById('panel-login').classList.toggle('active', tab === 'login');
    document.getElementById('panel-register').classList.toggle('active', tab === 'register');
    document.getElementById('tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('tab-register').classList.toggle('active', tab === 'register');
}

function togglePw(id, btn) {
    var inp = document.getElementById(id);
    if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '🙈'; }
    else { inp.type = 'password'; btn.textContent = '👁'; }
}

function doLogin() {
    var email = document.getElementById('login-email').value.trim();
    var password = document.getElementById('login-password').value.trim();
    var errEl = document.getElementById('login-error');
    errEl.textContent = '';

    if (!email || !password) {
        errEl.textContent = 'Email aur password dono required hain.';
        return;
    }

    var btn = event.currentTarget || document.querySelector('#panel-login .submit-btn');
    if (btn) { btn.textContent = 'Logging in...'; btn.disabled = true; }

    fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/dashboard';
        } else {
            errEl.textContent = data.error || 'Login failed.';
            if (btn) { btn.textContent = 'Login'; btn.disabled = false; }
        }
    })
    .catch(() => {
        errEl.textContent = 'Connection error. Please try again.';
        if (btn) { btn.textContent = 'Login'; btn.disabled = false; }
    });
}

function doRegister() {
    var email = document.getElementById('reg-email').value.trim();
    var password = document.getElementById('reg-password').value.trim();
    var errEl = document.getElementById('reg-error');
    var sucEl = document.getElementById('reg-success');
    errEl.textContent = ''; sucEl.textContent = '';

    if (!email || !password) { errEl.textContent = 'Email aur password required hain.'; return; }
    if (password.length < 6) { errEl.textContent = 'Password kam se kam 6 characters ka hona chahiye.'; return; }

    fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            sucEl.textContent = '✅ Account ban gaya! Ab login karo.';
            document.getElementById('reg-email').value = '';
            document.getElementById('reg-password').value = '';
            setTimeout(() => switchTab('login'), 1500);
        } else {
            errEl.textContent = data.error || 'Registration failed.';
        }
    })
    .catch(() => { errEl.textContent = 'Connection error. Please try again.'; });
}
</script>
""")

    # NiceGUI API endpoints for login/register
    from nicegui import app as nicegui_app
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @nicegui_app.post("/api/login")
    async def api_login(request: Request):
        body = await request.json()
        result = api.login(body.get("email", ""), body.get("password", ""))
        if "access_token" in result:
            app_state["token"] = result["access_token"]
            app_state["user"] = body.get("email", "")
            return JSONResponse({"success": True})
        return JSONResponse({"success": False, "error": result.get("error", "Login failed.")})

    @nicegui_app.post("/api/register")
    async def api_register(request: Request):
        body = await request.json()
        result = api.register(body.get("email", ""), body.get("password", ""))
        if "id" in result:
            return JSONResponse({"success": True})
        return JSONResponse({"success": False, "error": result.get("error", "Registration failed.")})