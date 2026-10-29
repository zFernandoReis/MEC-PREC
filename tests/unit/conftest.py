import pytest
from types import SimpleNamespace

from app.main import create_app
from app.shared.infrastructure.security.dependencies import get_current_user, require_admin


@pytest.fixture
def authenticated_app():
    """Isola os testes de negócio; os testes de segurança usam as dependências reais."""
    def build(*args, **kwargs):
        application = create_app(*args, **kwargs)
        application.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            user=SimpleNamespace(id=1, role="admin")
        )
        application.dependency_overrides[require_admin] = lambda: None
        return application
    return build
