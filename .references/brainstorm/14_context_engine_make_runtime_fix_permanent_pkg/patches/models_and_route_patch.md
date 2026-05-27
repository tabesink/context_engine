# Models/routes patch

Add to `app/lightrag_deploy/models.py`:

```python
class LightRAGDomainRepairResult(BaseModel):
    id: str
    operation: str = "repair"
    status: str
    service_name: str
    message: str | None = None
    storage_backend: str
    postgres_database: str | None = None
    postgres_user: str | None = None
    postgres_role_created: bool | None = None
    postgres_database_created: bool | None = None
    vector_extension_enabled: bool | None = None
    age_extension_enabled: bool | None = None
    warnings: list[str] = Field(default_factory=list)
```

Add to `app/api/routes/lightrag_admin.py`:

```python
@router.post("/admin/lightrag/domains/{domain_id}/repair")
def repair_domain(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
    service: LightRAGDomainService = Depends(get_domain_service),
):
    _ensure_deploy_enabled(service)
    result = _operation_or_404(service.repair, domain_id)
    _audit(session, admin, "lightrag.domain.repaired", service.get_domain(domain_id))
    return result
```

If the repair result is not compatible with `_operation_or_404`, add a dedicated helper.
