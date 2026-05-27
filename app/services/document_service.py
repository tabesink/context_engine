import logging
import re
from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import not_found
from app.domain.models import DocumentStatus
from app.integrations.lightrag_remote_adapter import (
    LightRAGAdapterError,
    LightRAGRemoteAdapter,
    lightrag_http_exception,
)
from app.lightrag_deploy.manifest import DomainManifestStore
from app.lightrag_deploy.settings import LightRAGDeploySettings
from app.services.ai_model_settings_service import AIModelSettingsService
from app.services.model_profile_resolver import ModelProfileResolver
from app.services.secret_crypto import SecretCryptoService
from app.services.lightrag_domain_registry import (
    LightRAGDomainRegistry,
    LightRAGDomainRegistryError,
    lightrag_domain_http_exception,
)
from app.services.file_storage import FileStorage
from app.services.job_service import JobService
from app.storage.repositories.ai_model_settings import AIModelSettingsRepository
from app.storage.repositories.ai_provider_secrets import AIProviderSecretRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow

logger = logging.getLogger(__name__)
_MISSING_SECRET_KEY_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")


class DocumentService:
    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()
        self.documents = DocumentRepository(session)
        self.storage = FileStorage()
        self.domain_registry = LightRAGDomainRegistry(settings=self.settings)
        crypto = SecretCryptoService.from_settings(self.settings)
        ai_settings_repo = AIModelSettingsRepository(session)
        ai_secret_repo = AIProviderSecretRepository(session, crypto)
        self.ai_settings_service = AIModelSettingsService(ai_settings_repo, ai_secret_repo)
        self.profile_resolver = ModelProfileResolver(self.ai_settings_service)
        deploy_settings = LightRAGDeploySettings.from_app_settings(self.settings)
        self.domain_manifest = DomainManifestStore(deploy_settings.manifest_path)

    def upload(
        self,
        *,
        actor_id: str,
        file: UploadFile,
        lightrag_domain_id: str | None = None,
    ) -> tuple[DocumentRow, str | None]:
        return self._upload_remote(
            actor_id=actor_id,
            file=file,
            lightrag_domain_id=lightrag_domain_id,
        )

    def _upload_remote(
        self,
        *,
        actor_id: str,
        file: UploadFile,
        lightrag_domain_id: str | None = None,
    ) -> tuple[DocumentRow, str | None]:
        domain = self._validate_lightrag_domain(lightrag_domain_id)
        domain_id = domain.id
        manifest_domain = self._validate_domain_provider_readiness(domain_id)
        path = self.storage.save_upload(file)
        lightrag_metadata = {
            "enabled": True,
            "domain": domain_id,
            "domain_id": domain_id,
            "status": "queued",
        }
        if manifest_domain is not None and manifest_domain.embedding is not None:
            lightrag_metadata["embedding_profile_id"] = manifest_domain.embedding.profile_id
            lightrag_metadata["embedding_fingerprint"] = manifest_domain.embedding.fingerprint
        metadata = {
            "original_filename": file.filename,
            "semantic_engine": "lightrag",
            "lightrag": lightrag_metadata,
        }
        document = self.documents.create(
            owner_id=actor_id,
            lightrag_domain_id=domain_id,
            filename=file.filename or path.name,
            content_type=file.content_type or "application/octet-stream",
            storage_path=str(path),
            metadata=metadata,
            status=DocumentStatus.INDEXING,
        )
        jobs = JobService(self.session)
        job_id = jobs.enqueue_document_ingest(document_id=document.id)
        self.documents.audit(
            actor_id=actor_id,
            event="document.uploaded",
            target_id=document.id,
            metadata={"filename": document.filename, "engine": "lightrag"},
        )
        return document, job_id

    def _validate_lightrag_domain(self, domain_id: str | None):
        try:
            return self.domain_registry.validate_available(domain_id)
        except LightRAGDomainRegistryError as exc:
            raise lightrag_domain_http_exception(exc) from exc

    def _validate_domain_provider_readiness(self, domain_id: str):
        try:
            domain = self.domain_manifest.get_domain(domain_id)
        except Exception:
            # Legacy tests and manifests can store compact domain entries; keep them upload-compatible.
            return None
        if domain is None:
            return None
        # Keep legacy domains ingestible while still enforcing readiness for snapshot-backed domains.
        if domain.embedding is None:
            return domain
        try:
            self.profile_resolver.resolve_embedding_profile(domain.embedding.profile_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"LightRAG domain '{domain_id}' embedding profile is invalid: {exc}",
            ) from exc
        secret_name = (domain.embedding.api_key_env_var or "").strip()
        if secret_name and not self.ai_settings_service.get_provider_secret_value(secret_name):
            raise HTTPException(
                status_code=400,
                detail=f"LightRAG domain '{domain_id}' is missing required provider secret: {secret_name}",
            )
        return domain

    def get_ready_or_404(self, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document or document.status != DocumentStatus.READY.value:
            raise not_found("Document not found")
        return document

    def delete(self, *, actor_id: str, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        self.documents.mark_deleted(document)
        self.documents.audit(
            actor_id=actor_id,
            event="document.deleted",
            target_id=document.id,
            metadata={"filename": document.filename},
        )
        return document

    def refresh_lightrag_status(self, *, document_id: str) -> DocumentRow:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        lightrag = dict(document.meta.get("lightrag") or {})
        domain_id = lightrag.get("domain_id") or lightrag.get("domain")
        track_id = lightrag.get("track_id")
        if not domain_id or not track_id:
            raise HTTPException(status_code=400, detail="Document has no LightRAG track status")
        try:
            self.domain_registry.validate_available(str(domain_id))
            status_payload = LightRAGRemoteAdapter.for_domain(str(domain_id)).document_status(str(track_id))
        except LightRAGDomainRegistryError as exc:
            raise lightrag_domain_http_exception(exc) from exc
        except LightRAGAdapterError as exc:
            raise lightrag_http_exception(exc) from exc

        status = str(status_payload.get("status") or "")
        if status not in {"indexing", "ready", "failed"}:
            raise HTTPException(status_code=502, detail=f"Unknown LightRAG status: {status!r}")
        normalized_message, missing_provider_secrets = self._normalize_lightrag_failure_message(
            status_payload.get("error")
        )
        updated_lightrag = lightrag | {
            "document_id": status_payload.get("document_id") or lightrag.get("document_id"),
            "track_id": status_payload.get("track_id") or track_id,
            "status": status,
            "message": normalized_message,
            "last_status_check_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        if missing_provider_secrets:
            updated_lightrag["failure_reason"] = "missing_provider_secrets"
            updated_lightrag["missing_provider_secrets"] = missing_provider_secrets
        document = self.documents.update_metadata(
            document,
            document.meta | {"lightrag": updated_lightrag},
        )
        if status == "ready":
            return self.documents.update_status(document, DocumentStatus.READY)
        if status == "failed":
            return self.documents.update_status(
                document,
                DocumentStatus.FAILED,
                error_message=updated_lightrag.get("message"),
            )
        return document

    def refresh_pending_lightrag_statuses(self) -> list[DocumentRow]:
        refreshed: list[DocumentRow] = []
        for document in self.documents.list_lightrag_indexing():
            try:
                refreshed.append(self.refresh_lightrag_status(document_id=document.id))
            except HTTPException as exc:
                if exc.status_code in {400, 404}:
                    refreshed.append(
                        self._mark_poll_refresh_failed(
                            document=document,
                            message=str(exc.detail or "LightRAG status refresh failed"),
                        )
                    )
                    logger.warning(
                        "Marked document %s as failed during poll refresh (status=%s): %s",
                        document.id,
                        exc.status_code,
                        exc.detail,
                    )
                    continue
                logger.warning(
                    "Skipping document %s during poll refresh due to HTTP %s: %s",
                    document.id,
                    exc.status_code,
                    exc.detail,
                )
            except Exception as exc:
                logger.warning(
                    "Skipping document %s during poll refresh due to unexpected error: %s",
                    document.id,
                    exc,
                )
        return refreshed

    def _mark_poll_refresh_failed(self, *, document: DocumentRow, message: str) -> DocumentRow:
        lightrag = dict(document.meta.get("lightrag") or {})
        normalized_message, missing_provider_secrets = self._normalize_lightrag_failure_message(message)
        updated_lightrag = lightrag | {
            "status": "failed",
            "message": normalized_message,
            "last_status_check_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        if missing_provider_secrets:
            updated_lightrag["failure_reason"] = "missing_provider_secrets"
            updated_lightrag["missing_provider_secrets"] = missing_provider_secrets
        document = self.documents.update_metadata(
            document,
            document.meta | {"lightrag": updated_lightrag},
        )
        return self.documents.update_status(
            document,
            DocumentStatus.FAILED,
            error_message=normalized_message,
        )

    def _normalize_lightrag_failure_message(
        self, raw_message: str | None
    ) -> tuple[str | None, list[str] | None]:
        message = str(raw_message).strip() if raw_message is not None else None
        if not message:
            return message, None
        missing_provider_secrets = self._extract_missing_provider_secrets(message)
        if not missing_provider_secrets:
            return message, None
        plural = "s" if len(missing_provider_secrets) > 1 else ""
        friendly = (
            f"Missing provider secret{plural}: {', '.join(missing_provider_secrets)}. "
            "Configure it in AI Settings > Provider secrets and retry ingestion."
        )
        return friendly, missing_provider_secrets

    def _extract_missing_provider_secrets(self, message: str) -> list[str]:
        tokens = _MISSING_SECRET_KEY_PATTERN.findall(message)
        candidates = sorted(
            {
                token
                for token in tokens
                if "_" in token and any(suffix in token for suffix in ("KEY", "TOKEN", "SECRET"))
            }
        )
        if not candidates:
            return []
        normalized = re.sub(r"[\[\]\(\)\{\}'\",:;]", " ", message).strip()
        words = [part for part in normalized.split() if part]
        if words and all(part in candidates for part in words):
            return candidates
        lowered = message.lower()
        if "missing" in lowered and ("key" in lowered or "secret" in lowered or "token" in lowered):
            return candidates
        return []

    def reingest(self, *, actor_id: str, document_id: str) -> str:
        document = self.documents.get(document_id)
        if not document:
            raise not_found("Document not found")
        metadata = dict(document.meta or {})
        metadata["lightrag"] = dict(metadata.get("lightrag") or {}) | {"status": "queued"}
        document = self.documents.update_metadata(document, metadata)
        self.documents.update_status(document, DocumentStatus.INDEXING)
        self.documents.audit(
            actor_id=actor_id,
            event="document.reingest_queued",
            target_id=document_id,
            metadata={},
        )
        return JobService(self.session).enqueue_document_ingest(document_id=document_id)

