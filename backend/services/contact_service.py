from __future__ import annotations

from datetime import datetime
from typing import List

from ..models.schemas import Contact


class ContactService:
    def __init__(self) -> None:
        self._contacts: List[Contact] = []

    def add_contact(
        self,
        full_name: str,
        email: str,
        phone: str | None,
        message: str | None,
    ) -> Contact:
        contact = Contact(
            id=f"contact_{len(self._contacts) + 1}",
            full_name=full_name,
            email=email,
            phone=phone,
            message=message,
            created_at=datetime.utcnow(),
        )
        self._contacts.append(contact)
        return contact

    def list_contacts(self) -> List[Contact]:
        return list(self._contacts)


contact_service = ContactService()
