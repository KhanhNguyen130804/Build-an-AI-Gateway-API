import pytest

from app.core.config import Settings
from app.db.seed import seed_users


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"demo_password": "short"},
        {"second_test_username": "reviewer"},
    ],
)
async def test_invalid_seed_configuration_rejected_before_database_access(overrides):
    values = {
        "demo_password": "fixture-password-long-enough",
        "second_test_password": "another-fixture-long-password",
        **overrides,
    }
    settings = Settings(_env_file=None, **values)
    # Validation must fail before dereferencing a database or inserting either user.
    with pytest.raises(ValueError):
        await seed_users(object(), settings)
