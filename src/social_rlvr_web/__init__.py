"""RLVR browser-agent research scaffold."""

__all__ = ["BrowserRLVREnv", "TASKS"]

from social_rlvr_web.env import BrowserRLVREnv
from social_rlvr_web.tasks import TASKS

# Import side effect: registers browsergym/social_rlvr.* task ids.
import social_rlvr_web.browsergym_tasks as browsergym_tasks  # noqa: F401, E402
