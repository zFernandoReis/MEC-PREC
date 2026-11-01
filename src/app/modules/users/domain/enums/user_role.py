from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    CLIENT = "client"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    