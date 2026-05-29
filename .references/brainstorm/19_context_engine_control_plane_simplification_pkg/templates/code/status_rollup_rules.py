"""Centralized status rollup rules.

Move equivalent logic into a production service/helper module.
"""

from enum import Enum


class OperationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


def document_status_from_operation(operation_status: str) -> str:
    if operation_status == OperationStatus.QUEUED:
        return "uploaded"
    if operation_status == OperationStatus.RUNNING:
        return "indexing"
    if operation_status == OperationStatus.SUCCEEDED:
        return "ready"
    if operation_status == OperationStatus.FAILED:
        return "failed"
    if operation_status == OperationStatus.CANCELED:
        return "uploaded"
    raise ValueError(f"Unsupported operation status: {operation_status}")


def domain_state_from_operation(operation_type: str, operation_status: str) -> str:
    if operation_type == "domain_create":
        if operation_status in {"queued", "running"}:
            return "creating"
        if operation_status == "succeeded":
            return "stopped"
        if operation_status == "failed":
            return "failed"

    if operation_type == "domain_start":
        if operation_status in {"queued", "running"}:
            return "starting"
        if operation_status == "succeeded":
            return "running"
        if operation_status == "failed":
            return "failed"

    if operation_type == "domain_stop":
        if operation_status in {"queued", "running"}:
            return "stopping"
        if operation_status == "succeeded":
            return "stopped"
        if operation_status == "failed":
            return "failed"

    if operation_type == "domain_delete":
        if operation_status in {"queued", "running"}:
            return "stopping"
        if operation_status == "succeeded":
            return "deleted"
        if operation_status == "failed":
            return "failed"

    raise ValueError(f"Unsupported operation type/status: {operation_type}/{operation_status}")
