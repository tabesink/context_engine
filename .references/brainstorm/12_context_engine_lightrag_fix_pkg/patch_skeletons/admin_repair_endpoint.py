"""
Patch skeleton for app/api/admin/lightrag_admin.py and app/lightrag_deploy/service.py

Goal:
Add an admin repair endpoint that regenerates and restarts a managed domain, then probes runtime reachability.
"""

from fastapi import APIRouter, HTTPException

from app.lightrag_deploy.service import LightRAGDomainService
from app.services.lightrag_domain_health import LightRAGDomainHealthProbe

router = APIRouter()


@router.post("/admin/lightrag/domains/{domain_id}/repair")
def repair_lightrag_domain(domain_id: str):
    service = LightRAGDomainService()
    health_probe = LightRAGDomainHealthProbe()

    try:
        domain = service.get_domain(domain_id)
        service.regenerate(domain_id)

        # Choose recreate or up depending on current service semantics.
        # Recreate is safer for stale networking; up is less disruptive.
        operation = service.recreate(domain_id)

        health = health_probe.check(domain_id)

        # Add a real service method for this instead of mutating manifest here.
        # service.persist_health(domain_id, health)

        status = "running" if health.ok else "unhealthy"

        return {
            "domain_id": domain.id,
            "service_name": domain.service_name,
            "host_base_url": domain.host_base_url,
            "container_base_url": domain.container_base_url,
            "runtime_base_url": health.base_url,
            "docker_operation": operation.status,
            "health": {
                "ok": health.ok,
                "reason": health.reason,
                "detail": health.detail,
                "status_code": health.status_code,
            },
            "status": status,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
