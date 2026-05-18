from app.domain.models import Evidence
from app.core.config import get_settings
from app.integrations.lightrag_remote_adapter import LightRAGRemoteAdapter


class LightRAGRemoteRetrievalEngine:
    name = "lightrag"

    def __init__(self, adapter: LightRAGRemoteAdapter | None = None):
        self.adapter = adapter or LightRAGRemoteAdapter.for_domain()
        self.domain = get_settings().lightrag_domain

    def retrieve(
        self,
        *,
        query: str,
        mode,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
        lightrag_domain_id: str | None = None,
    ) -> list[Evidence]:
        del user_id
        domain = lightrag_domain_id or self.domain
        adapter = self.adapter
        if lightrag_domain_id is not None:
            adapter = LightRAGRemoteAdapter.for_domain(lightrag_domain_id)
        return adapter.retrieve(
            query=query,
            mode=mode,
            top_k=top_k,
            document_ids=document_ids,
            domain=domain,
        )
