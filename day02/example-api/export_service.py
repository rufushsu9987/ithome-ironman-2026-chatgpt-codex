"""可驗收的訂單 CSV 匯出範例（僅使用 Python 標準函式庫）。"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Callable


@dataclass(frozen=True)
class User:
    user_id: str
    tenant_id: str
    role: str


@dataclass(frozen=True)
class Order:
    order_id: str
    tenant_id: str
    ordered_on: date
    amount: int


@dataclass
class ExportJob:
    job_id: str
    tenant_id: str
    request_id: str
    start_date: date
    end_date: date
    status: str = "queued"
    object_key: str | None = None


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    body: dict


@dataclass
class InMemoryState:
    orders: list[Order] = field(default_factory=list)
    jobs: dict[str, ExportJob] = field(default_factory=dict)
    idempotency: dict[tuple[str, str], str] = field(default_factory=dict)
    queue: list[str] = field(default_factory=list)
    objects: dict[str, bytes] = field(default_factory=dict)
    audit_log: list[dict] = field(default_factory=list)


class ExportService:
    """對應 POST /exports 的應用服務。"""

    def __init__(
        self,
        state: InMemoryState,
        job_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.state = state
        self.job_id_factory = job_id_factory or (lambda: str(uuid.uuid4()))

    def create_export(
        self,
        *,
        user: User,
        tenant_id: str,
        request_id: str,
        start_date: date,
        end_date: date,
    ) -> ApiResponse:
        if user.role != "tenant_admin" or user.tenant_id != tenant_id:
            self._audit("export.rejected", user.user_id, tenant_id, "forbidden")
            return ApiResponse(403, {"error": "forbidden"})

        if not request_id.strip():
            return ApiResponse(422, {"field": "request_id", "error": "required"})

        days = (end_date - start_date).days + 1
        if days < 1 or days > 31:
            return ApiResponse(
                422,
                {"field": "date_range", "error": "must_be_between_1_and_31_days"},
            )

        key = (tenant_id, request_id)
        if key in self.state.idempotency:
            job_id = self.state.idempotency[key]
            return ApiResponse(202, {"job_id": job_id, "reused": True})

        job_id = self.job_id_factory()
        job = ExportJob(job_id, tenant_id, request_id, start_date, end_date)
        self.state.jobs[job_id] = job
        self.state.idempotency[key] = job_id
        self.state.queue.append(job_id)
        self._audit("export.created", user.user_id, tenant_id, job_id)
        return ApiResponse(202, {"job_id": job_id, "reused": False})

    def _audit(self, event: str, actor: str, tenant_id: str, detail: str) -> None:
        self.state.audit_log.append(
            {"event": event, "actor": actor, "tenant_id": tenant_id, "detail": detail}
        )


class ExportWorker:
    """從佇列取出工作，僅匯出工作所屬租戶的資料。"""

    def __init__(self, state: InMemoryState) -> None:
        self.state = state

    def process_next(self) -> ExportJob | None:
        if not self.state.queue:
            return None

        job_id = self.state.queue.pop(0)
        job = self.state.jobs[job_id]
        rows = [
            order
            for order in self.state.orders
            if order.tenant_id == job.tenant_id
            and job.start_date <= order.ordered_on <= job.end_date
        ]

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["order_id", "ordered_on", "amount"])
        for order in rows:
            writer.writerow([order.order_id, order.ordered_on.isoformat(), order.amount])

        key = f"exports/{job.tenant_id}/{job.job_id}.csv"
        self.state.objects[key] = buffer.getvalue().encode("utf-8")
        job.object_key = key
        job.status = "completed"
        self.state.audit_log.append(
            {
                "event": "export.completed",
                "actor": "worker",
                "tenant_id": job.tenant_id,
                "detail": job.job_id,
            }
        )
        return job

    def create_download_url(self, job_id: str, ttl_seconds: int = 600) -> str:
        job = self.state.jobs[job_id]
        if job.status != "completed" or not job.object_key:
            raise ValueError("export_not_ready")
        return f"https://download.example/{job.object_key}?ttl={ttl_seconds}"
