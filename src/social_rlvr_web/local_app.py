from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from threading import Thread
from typing import Any

from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from werkzeug.serving import BaseWSGIServer, make_server

from social_rlvr_web.variants import CONTACTS, get_task_variant


@dataclass
class AppState:
    task_id: str = "report.extract_tracking_code"
    variant_id: str = "train_000"
    expected: dict[str, Any] = field(default_factory=dict)
    page_data: dict[str, Any] = field(default_factory=dict)
    messages: list[dict[str, str]] = field(default_factory=list)
    shared_images: list[dict[str, str]] = field(default_factory=list)
    reports: list[dict[str, str]] = field(default_factory=list)
    followups: list[dict[str, str]] = field(default_factory=list)
    meetings: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "messages": deepcopy(self.messages),
            "shared_images": deepcopy(self.shared_images),
            "reports": deepcopy(self.reports),
            "followups": deepcopy(self.followups),
            "meetings": deepcopy(self.meetings),
            "task_id": self.task_id,
            "variant_id": self.variant_id,
            "expected": deepcopy(self.expected),
            "page_data": deepcopy(self.page_data),
        }


def state_for_variant(task_id: str, variant_id: str) -> AppState:
    variant = get_task_variant(task_id, variant_id)
    return AppState(
        task_id=task_id,
        variant_id=variant.variant_id,
        expected=deepcopy(variant.expected),
        page_data=deepcopy(variant.page_data),
    )


BASE_CSS = """
body { font-family: Arial, sans-serif; margin: 0; color: #1d1d1f; background: #f7f7f2; }
header { background: #234; color: white; padding: 18px 28px; }
main { max-width: 980px; margin: 0 auto; padding: 24px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.panel, .card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }
button, input, textarea, select { font: inherit; }
button { border: 0; background: #0f766e; color: white; border-radius: 6px; padding: 10px 12px; cursor: pointer; }
input, textarea, select { width: 100%; box-sizing: border-box; border: 1px solid #bbb; border-radius: 6px; padding: 9px; margin: 6px 0 12px; }
.image { height: 132px; border-radius: 8px; margin-bottom: 10px; border: 1px solid rgba(0,0,0,.15); }
.muted { color: #666; font-size: 14px; }
.row { display: flex; gap: 10px; align-items: center; }
.row > * { flex: 1; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 18px; }
th, td { border-bottom: 1px solid #ddd; padding: 9px; text-align: left; }
fieldset { border: 1px solid #ddd; border-radius: 6px; margin: 6px 0 12px; }
fieldset label { display: block; margin: 8px 0; }
input[type="checkbox"] { width: auto; margin-right: 8px; }
"""


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["STATE"] = AppState()

    @app.get("/")
    def index():
        return render_template_string(
            """
            <style>{{ css }}</style>
            <header><h1>Social-RLVR Local Web</h1></header>
            <main>
              <div class="grid">
                <a class="card" href="/messages">Multi-step messages</a>
                <a class="card" href="/gallery">Visual retrieval</a>
                <a class="card" href="/report">Data extraction</a>
                <a class="card" href="/orders">Priority follow-up</a>
                <a class="card" href="/schedule">Team scheduling</a>
              </div>
            </main>
            """,
            css=BASE_CSS,
        )

    @app.get("/messages")
    def messages():
        variant = get_task_variant("messages.last_five_new_year", app.config["STATE"].variant_id)
        return render_template_string(
            """
            <style>{{ css }}</style>
            <header><h1>Friends</h1><p>{{ instruction }}</p></header>
            <main>
              <form method="post" action="/send-message" class="panel">
                <label>Friend</label>
                <select name="recipient">
                  {% for contact in contacts %}
                    <option value="{{ contact }}">{{ loop.index }}. {{ contact }}</option>
                  {% endfor %}
                </select>
                <label>Message</label>
                <textarea name="text" rows="3"></textarea>
                <button type="submit">Send message</button>
              </form>
              <section class="panel">
                <h2>Sent</h2>
                {% for msg in state.messages %}
                  <p>{{ msg.recipient }}: {{ msg.text }}</p>
                {% else %}
                  <p class="muted">No messages yet.</p>
                {% endfor %}
              </section>
            </main>
            """,
            contacts=CONTACTS,
            css=BASE_CSS,
            instruction=variant.instruction,
            state=app.config["STATE"],
        )

    @app.post("/send-message")
    def send_message():
        app.config["STATE"].messages.append(
            {
                "recipient": request.form.get("recipient", ""),
                "text": request.form.get("text", ""),
            }
        )
        return redirect(url_for("messages"))

    @app.get("/gallery")
    def gallery():
        variant = get_task_variant("gallery.aesthetic_travel_to_meera", app.config["STATE"].variant_id)
        return render_template_string(
            """
            <style>{{ css }}</style>
            <header><h1>Image Gallery</h1><p>{{ instruction }}</p></header>
            <main class="grid">
              {% for image in images %}
                <form method="post" action="/share-image" class="card">
                  <div class="image" style="background: {{ image.gradient }}"></div>
                  <h2>{{ image.title }}</h2>
                  <p class="muted">Tags: {{ ", ".join(image.tags) }}</p>
                  <input type="hidden" name="image_id" value="{{ image.id }}">
                  <label>Recipient</label>
                  <select name="recipient">
                    {% for contact in contacts %}
                      <option value="{{ contact }}">{{ contact }}</option>
                    {% endfor %}
                  </select>
                  <button type="submit">Share image</button>
                </form>
              {% endfor %}
            </main>
            """,
            contacts=CONTACTS,
            css=BASE_CSS,
            images=variant.page_data["images"],
            instruction=variant.instruction,
        )

    @app.post("/share-image")
    def share_image():
        app.config["STATE"].shared_images.append(
            {
                "image_id": request.form.get("image_id", ""),
                "recipient": request.form.get("recipient", ""),
            }
        )
        return redirect(url_for("gallery"))

    @app.get("/report")
    def report():
        variant = get_task_variant("report.extract_tracking_code", app.config["STATE"].variant_id)
        return render_template_string(
            """
            <style>{{ css }}</style>
            <header><h1>Project Report</h1><p>{{ instruction }}</p></header>
            <main>
              <section class="panel">
                <h2>Order Details</h2>
                <p>Order owner: {{ page_data.owner }}</p>
                <p>Invoice total: Rs. {{ page_data.invoice_total }}</p>
                <p>Shipment tracking code: <strong>{{ page_data.tracking_code }}</strong></p>
              </section>
              <form method="post" action="/submit-report" class="panel">
                <label>Tracking code</label>
                <input name="tracking_code" placeholder="Enter extracted value">
                <button type="submit">Submit report</button>
              </form>
            </main>
            """,
            css=BASE_CSS,
            instruction=variant.instruction,
            page_data=variant.page_data,
        )

    @app.post("/submit-report")
    def submit_report():
        app.config["STATE"].reports.append(
            {"tracking_code": request.form.get("tracking_code", "").strip()}
        )
        return redirect(url_for("report"))

    @app.get("/orders")
    def orders():
        variant = get_task_variant("orders.priority_followup", app.config["STATE"].variant_id)
        return render_template_string(
            """
            <style>{{ css }}</style>
            <header><h1>Order Follow-up</h1><p>{{ instruction }}</p></header>
            <main>
              <section class="panel">
                <h2>Queue</h2>
                <table>
                  <thead>
                    <tr><th>Owner</th><th>Priority</th><th>Reference</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {% for order in orders %}
                      <tr>
                        <td>{{ order.owner }}</td>
                        <td>{{ order.priority }}</td>
                        <td>{{ order.reference }}</td>
                        <td>{{ order.status }}</td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </section>
              <form method="post" action="/create-followup" class="panel">
                <label>Recipient</label>
                <select name="recipient">
                  {% for contact in contacts %}
                    <option value="{{ contact }}">{{ contact }}</option>
                  {% endfor %}
                </select>
                <label>Reference code</label>
                <input name="reference" placeholder="Copy the exact reference">
                <label>Note</label>
                <textarea name="note" rows="3"></textarea>
                <button type="submit">Create follow-up</button>
              </form>
            </main>
            """,
            contacts=CONTACTS,
            css=BASE_CSS,
            instruction=variant.instruction,
            orders=variant.page_data["orders"],
        )

    @app.post("/create-followup")
    def create_followup():
        app.config["STATE"].followups.append(
            {
                "recipient": request.form.get("recipient", ""),
                "reference": request.form.get("reference", "").strip(),
                "note": request.form.get("note", "").strip(),
            }
        )
        return redirect(url_for("orders"))

    @app.get("/schedule")
    def schedule():
        variant = get_task_variant("schedule.design_review_shared_slot", app.config["STATE"].variant_id)
        return render_template_string(
            """
            <style>{{ css }}</style>
            <header><h1>Team Calendar</h1><p>{{ instruction }}</p></header>
            <main>
              <section class="panel">
                <h2>Availability</h2>
                <table>
                  <thead>
                    <tr><th>Person</th>{% for slot in slots %}<th>{{ slot }}</th>{% endfor %}</tr>
                  </thead>
                  <tbody>
                    {% for row in availability %}
                      <tr><td>{{ row.person }}</td>{% for slot in slots %}<td>{{ row[slot] }}</td>{% endfor %}</tr>
                    {% endfor %}
                  </tbody>
                </table>
              </section>
              <form method="post" action="/create-meeting" class="panel">
                <label>Meeting title</label>
                <input name="title" placeholder="Title">
                <label>Slot</label>
                <select name="slot">
                  {% for slot in slots %}
                    <option value="{{ slot }}">{{ slot }}</option>
                  {% endfor %}
                </select>
                <fieldset>
                  <legend>Attendees</legend>
                  {% for contact in contacts %}
                    <label><input type="checkbox" name="attendees" value="{{ contact }}"> {{ contact }}</label>
                  {% endfor %}
                </fieldset>
                <button type="submit">Create meeting</button>
              </form>
            </main>
            """,
            contacts=CONTACTS,
            css=BASE_CSS,
            availability=variant.page_data["availability"],
            instruction=variant.instruction,
            slots=variant.page_data["slots"],
        )

    @app.post("/create-meeting")
    def create_meeting():
        app.config["STATE"].meetings.append(
            {
                "title": request.form.get("title", "").strip(),
                "slot": request.form.get("slot", ""),
                "attendees": request.form.getlist("attendees"),
            }
        )
        return redirect(url_for("schedule"))

    @app.post("/api/reset")
    def reset():
        payload = request.get_json(silent=True) or {}
        task_id = payload.get("task_id") or "report.extract_tracking_code"
        variant_id = payload.get("variant_id") or "train_000"
        app.config["STATE"] = state_for_variant(task_id, variant_id)
        return jsonify({"ok": True})

    @app.get("/api/state")
    def state():
        return jsonify(app.config["STATE"].as_dict())

    @app.post("/api/snapshot")
    def snapshot():
        return jsonify({"state": app.config["STATE"].as_dict()})

    @app.post("/api/restore")
    def restore():
        payload = request.get_json(force=True)
        state_payload = payload.get("state", payload)
        app.config["STATE"] = AppState(
            task_id=state_payload.get("task_id", "report.extract_tracking_code"),
            variant_id=state_payload.get("variant_id", "train_000"),
            expected=state_payload.get("expected", {}),
            page_data=state_payload.get("page_data", {}),
            messages=state_payload.get("messages", []),
            shared_images=state_payload.get("shared_images", []),
            reports=state_payload.get("reports", []),
            followups=state_payload.get("followups", []),
            meetings=state_payload.get("meetings", []),
        )
        return jsonify({"ok": True})

    return app


class LocalAppServer:
    def __init__(self, port: int = 8765):
        self.port = port
        self.app = create_app()
        self.server: BaseWSGIServer | None = None
        self.thread: Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        if self.server is not None:
            return
        self.server = make_server("127.0.0.1", self.port, self.app)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server = None
