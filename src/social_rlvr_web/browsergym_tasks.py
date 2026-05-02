from __future__ import annotations

from typing import Any

import playwright.sync_api
from browsergym.core.registration import register_task
from browsergym.core.task import AbstractBrowserTask

from social_rlvr_web.local_app import LocalAppServer
from social_rlvr_web.tasks import TASKS, TaskSpec, fetch_state, reset_state


class SocialRLVRBrowserGymTask(AbstractBrowserTask):
    """BrowserGym task backed by local RLVR verifiers."""

    task_id: str = ""
    port: int = 8780

    @classmethod
    def get_task_id(cls) -> str:
        return f"social_rlvr.{cls.task_id}"

    def __init__(self, seed: int, port: int | None = None) -> None:
        super().__init__(seed)
        self.spec: TaskSpec = TASKS[self.task_id]
        self.server = LocalAppServer(port=port or self.port)
        self.base_url = self.server.base_url
        self.steps = 0
        self.viewport = {"width": 1280, "height": 900}
        self.slow_mo = 100
        self.timeout = 5000

    def setup(self, page: playwright.sync_api.Page) -> tuple[str, dict[str, Any]]:
        self.server.start()
        reset_state(self.base_url)
        self.steps = 0
        page.goto(f"{self.base_url}{self.spec.start_path}", wait_until="domcontentloaded")
        return self.spec.instruction, {"task_id": self.spec.task_id, "base_url": self.base_url}

    def validate(
        self, page: playwright.sync_api.Page, chat_messages: list[str]
    ) -> tuple[float, bool, str, dict[str, Any]]:
        del page, chat_messages
        self.steps += 1
        state = fetch_state(self.base_url)
        success, message = self.spec.verifier(state)
        max_steps_reached = self.steps >= self.spec.max_steps
        done = success or max_steps_reached
        reward = 1.0 if success else 0.0
        info = {
            "success": success,
            "verifier_message": message,
            "state": state,
            "steps": self.steps,
            "max_steps_reached": max_steps_reached,
        }
        return reward, done, "", info

    def teardown(self) -> None:
        self.server.stop()


class MessageTask(SocialRLVRBrowserGymTask):
    task_id = "messages.last_five_new_year"
    port = 8781


class GalleryTask(SocialRLVRBrowserGymTask):
    task_id = "gallery.aesthetic_travel_to_meera"
    port = 8782


class ReportTask(SocialRLVRBrowserGymTask):
    task_id = "report.extract_tracking_code"
    port = 8783


class PriorityFollowupTask(SocialRLVRBrowserGymTask):
    task_id = "orders.priority_followup"
    port = 8784


class TeamScheduleTask(SocialRLVRBrowserGymTask):
    task_id = "schedule.design_review_shared_slot"
    port = 8785


def register_social_rlvr_tasks() -> None:
    for task_class in (MessageTask, GalleryTask, ReportTask, PriorityFollowupTask, TeamScheduleTask):
        try:
            register_task(
                task_class.get_task_id(),
                task_class,
                nondeterministic=False,
            )
        except Exception as exc:
            if "Cannot re-register id" not in str(exc):
                raise


register_social_rlvr_tasks()
