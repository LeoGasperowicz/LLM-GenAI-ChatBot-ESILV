from typing import List
from ..models.schemas import ContactInfo


class ContactService:
    """
    Service simple pour stocker des contacts.
    Pour un vrai projet, remplace par une base de données (PostgreSQL, etc.).
    """

    def __init__(self):
        self._contacts: List[ContactInfo] = []

    def add_contact(self, contact: ContactInfo) -> ContactInfo:
        self._contacts.append(contact)
        return contact

    def list_contacts(self) -> List[ContactInfo]:
        return list(self._contacts)


contact_service = ContactService()
