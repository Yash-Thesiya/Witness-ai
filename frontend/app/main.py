from nicegui import ui

from app.pages.login import login_page
from app.pages.dashboard import dashboard_page
from app.pages.upload import upload_page
from app.pages.commitments import commitments_page, commitment_detail_page
from app.pages.report import report_page
from app.pages.calendar import calendar_page


@ui.page("/")
def index():
    login_page()


@ui.page("/dashboard")
def dashboard():
    dashboard_page()


@ui.page("/upload")
def upload():
    upload_page()


@ui.page("/commitments")
def commitments():
    commitments_page()


@ui.page("/commitments/{commitment_id}")
def commitment_detail(commitment_id: int):
    commitment_detail_page(commitment_id)


@ui.page("/report")
def report():
    report_page()


@ui.page("/calendar")
def calendar():
    calendar_page()


ui.run(
    host="0.0.0.0",
    port=8080,
    title="Witness",
    favicon="👁",
    dark=False,
    reload=True,
)