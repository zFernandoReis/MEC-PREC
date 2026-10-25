from sqlalchemy import create_engine, inspect, text

from app.bootstrap.migrate_user_passwords import migrate_password_columns


def test_migration_adds_user_columns_and_preserves_legacy_hashes():
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
            connection.execute(text("INSERT INTO users VALUES (1), (2)"))
            connection.execute(text("""
                CREATE TABLE user_credentials (
                    user_id INTEGER PRIMARY KEY, password_hash VARCHAR(255), token_version INTEGER
                )
            """))
            connection.execute(text("INSERT INTO user_credentials VALUES (1, 'existing-hash', 8)"))
            migrate_password_columns(connection)
            assert connection.execute(text(
                "SELECT id, password_hash, token_version FROM users ORDER BY id"
            )).all() == [(1, "existing-hash", 8), (2, None, 0)]
            assert not inspect(connection).has_table("user_credentials")
            migrate_password_columns(connection)
            assert connection.scalar(text("SELECT password_hash FROM users WHERE id=1")) == "existing-hash"
    finally:
        engine.dispose()


def test_migration_preserves_password_already_defined_in_users():
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE users (id INTEGER PRIMARY KEY, password_hash VARCHAR(255), token_version INTEGER)
            """))
            connection.execute(text("INSERT INTO users VALUES (1, 'new-hash', 10)"))
            connection.execute(text("""
                CREATE TABLE user_credentials (
                    user_id INTEGER PRIMARY KEY, password_hash VARCHAR(255), token_version INTEGER
                )
            """))
            connection.execute(text("INSERT INTO user_credentials VALUES (1, 'old-hash', 8)"))
            migrate_password_columns(connection)
            assert connection.execute(text("SELECT password_hash, token_version FROM users")).one() == ("new-hash", 10)
    finally:
        engine.dispose()
