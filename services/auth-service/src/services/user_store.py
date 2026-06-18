"""Auth service — in-memory user store (replaced by PostgreSQL in Phase 1.4)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4


class UserRecord:
    def __init__(self, email: str, password_hash: str, display_name: str) -> None:
        self.id: UUID = uuid4()
        self.email: str = email
        self.password_hash: str = password_hash
        self.display_name: str = display_name
        self.role: str = "developer"
        self.created_at: datetime = datetime.now(UTC)


class InMemoryUserStore:
    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}

    def get_by_email(self, email: str) -> UserRecord | None:
        return self._users.get(email.lower())

    def create(self, email: str, password_hash: str, display_name: str) -> UserRecord:
        user = UserRecord(email.lower(), password_hash, display_name)
        self._users[email.lower()] = user
        return user


user_store = InMemoryUserStore()
