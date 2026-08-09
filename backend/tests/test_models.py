from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Budget, Receipt, User


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def test_schema_defines_core_entities():
    tables = set(Base.metadata.tables.keys())
    assert {"users", "receipts", "budgets"}.issubset(tables)


def test_deleting_user_with_dependents_leaves_no_orphaned_records():
    session = _make_session()
    user = User(email="alex@example.com")
    session.add(user)
    session.flush()

    session.add(Receipt(user_id=user.id, amount=12.5, description="Coffee"))
    session.add(Budget(user_id=user.id, period="monthly", target_amount=500))
    session.commit()

    session.delete(user)
    session.commit()

    assert session.query(Receipt).count() == 0
    assert session.query(Budget).count() == 0
    session.close()


def test_deleting_user_with_no_dependents_succeeds_cleanly():
    session = _make_session()
    user = User(email="jamie@example.com")
    session.add(user)
    session.commit()

    session.delete(user)
    session.commit()

    assert session.query(User).count() == 0
    session.close()
