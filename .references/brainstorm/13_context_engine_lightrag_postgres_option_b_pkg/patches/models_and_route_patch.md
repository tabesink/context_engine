# Models and Route Patch Guidance

## app/lightrag_deploy/models.py

Add:

```python
class LightRAGDomainRepairResult(BaseModel):
    id: str
    operation: str = "repair"
    status: str
    service_name: str
    storage_backend: str
    postgres_database: str | None = None
    postgres_user: str | None = None
    postgres_role_exists: bool | None = None
    postgres_database_exists: bool | None = None
    extensions: dict[str, dict[str, str | None]] = Field(default_factory=dict)
    message: str | None = None
```

## app/api/routes/lightrag_admin.py

Add import:

```python
LightRAGDomainRepairResult
```

Add endpoint:

```python
@router.post("/admin/lightrag/domains/{domain_id}/repair")
def repair_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
) -> LightRAGDomainRepairResult:
    _ensure_deploy_enabled(service)
    try:
        result = service.repair(domain_id)
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _audit(session, admin, "lightrag.domain.repaired", service.get_domain(domain_id))

    if result.status != "succeeded":
        raise HTTPException(
            status_code=502,
            detail=result.model_dump(),
        )
    return result
```
