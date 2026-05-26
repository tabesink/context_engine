from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.tables import AIModelProfileRow, AIModelSettingsRow


class AIModelSettingsRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_profiles(self) -> list[AIModelProfileRow]:
        query = select(AIModelProfileRow).order_by(
            AIModelProfileRow.kind.asc(),
            AIModelProfileRow.display_name.asc(),
            AIModelProfileRow.id.asc(),
        )
        return list(self.session.scalars(query).all())

    def get_profile(self, profile_id: str) -> AIModelProfileRow | None:
        return self.session.get(AIModelProfileRow, profile_id)

    def create_profile(self, profile: AIModelProfileRow) -> AIModelProfileRow:
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def update_profile(self, profile: AIModelProfileRow) -> AIModelProfileRow:
        profile.updated_at = datetime.now(UTC)
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def get_settings(self) -> AIModelSettingsRow | None:
        return self.session.get(AIModelSettingsRow, 1)

    def set_defaults(
        self,
        *,
        llm_profile_id: str,
        embedding_profile_id: str,
        updated_by_user_id: str | None = None,
    ) -> AIModelSettingsRow:
        settings = self.get_settings()
        if settings is None:
            settings = AIModelSettingsRow(
                id=1,
                default_llm_profile_id=llm_profile_id,
                default_embedding_profile_id=embedding_profile_id,
                updated_by_user_id=updated_by_user_id,
            )
        else:
            settings.default_llm_profile_id = llm_profile_id
            settings.default_embedding_profile_id = embedding_profile_id
            settings.updated_by_user_id = updated_by_user_id
            settings.updated_at = datetime.now(UTC)
        self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return settings

