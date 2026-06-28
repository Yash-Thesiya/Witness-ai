"""
Global app state.
Stores JWT token and current user info across pages.
"""

app_state = {
    "token": None,
    "user": None,
}


def get_headers() -> dict:
    """Return auth headers for API calls."""
    if app_state["token"]:
        return {"Authorization": f"Bearer {app_state['token']}"}
    return {}


def is_logged_in() -> bool:
    return app_state["token"] is not None


def logout():
    app_state["token"] = None
    app_state["user"] = None