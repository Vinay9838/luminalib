from typing import Any
from uuid import UUID

from celery import current_task, states
from celery.result import AsyncResult


class TaskService:
    PROGRESS_STATE = "PROGRESS"

    def __init__(self, request_id: UUID):
        self.res = AsyncResult(str(request_id))

    @property
    def is_successful(self) -> bool:
        return self.res.status == states.SUCCESS

    @property
    def is_failed(self) -> bool:
        return self.res.status in states.EXCEPTION_STATES

    @property
    def progress(self) -> float:
        result = self.res.result
        result_data = result.get("data")
        progress = 0.0
        if result_data:
            current_count = result_data.get("current")
            total_count = result_data.get("total")
            if current_count and total_count:
                progress = round(current_count / total_count * 100, 2)
        return progress

    def get_progress_info(self) -> tuple[str, float | None]:
        if self.res.status == states.REVOKED:
            return "ABORTED", None
        elif self.res.status == states.EXCEPTION_STATES:
            return "ERROR", None
        elif self.res.status == states.UNREADY_STATES:
            return "PROGRESS", 0.0
        elif self.res.status == self.PROGRESS_STATE:
            return "PROGRESS", self.progress
        elif self.res.status == states.SUCCESS:
            return "COMPLETE", 100.0
        else:
            return "ERROR", None

    def wait(self, timeout: float = None) -> bool:
        try:
            self.res.get(timeout=timeout, propagate=False)
        except self.res.TimeoutError:
            return False
        else:
            return True

    def get_result(self) -> Any | None:
        if self.is_successful:
            return self.res.result
        else:
            return None

    def abort_task(self) -> Any | None:
        if self.is_successful or self.is_failed:
            return False
        else:
            self.res.revoke(terminate=True)
            return True

    @classmethod
    def update_progress(cls, current: float, total: float):
        if not current_task.request.called_directly:
            current_task.update_state(
                state=cls.PROGRESS_STATE,
                meta={"data": {"current": current, "total": total}},
            )