"""pytest 共享 fixture —— 每个测试跑在独立事务（savepoint）中，结束后回滚。

运行方式（推荐在后端容器内，可直达 db 服务）：
    docker compose -f docker-compose.dev.yml exec -T backend \
        env DATABASE_URL=postgresql://mes_user:mes_password@db:5432/mes_test \
        python -m pytest tests/ -v

前置：容器内 pip install -r requirements-dev.txt
mes_test 库不存在时自动创建（compose 的 POSTGRES_USER 为实例超级用户，具备 CREATEDB）。
审计中间件使用独立 Session 绕过事务回滚，测试期以 AUDIT_LOG_ENABLED=0 关闭。
"""
import os

# 容器内已存在 DATABASE_URL（指向 hotrunner_mes），必须强制覆盖为测试库，
# 否则测试会污染开发库（曾因 setdefault 失效踩坑）。
TEST_DATABASE_URL = os.getenv(
    "MES_TEST_DATABASE_URL",
    "postgresql://mes_user:mes_password@db:5432/mes_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test-only-secret-do-not-use-in-prod"
os.environ["AUDIT_LOG_ENABLED"] = "0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, ProgrammingError


def _ensure_database(url_str: str) -> None:
    """目标库不存在则创建；建库失败必须显式暴露（禁止静默吞错）。"""
    url = make_url(url_str)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
            print(f"[conftest] created test database {url.database}")
    except (OperationalError, ProgrammingError) as e:
        if "already exists" in str(e).lower():
            pass
        else:
            raise RuntimeError(f"创建测试库 {url.database} 失败: {e}") from e
    finally:
        admin.dispose()


_ensure_database(TEST_DATABASE_URL)

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
import models  # noqa: E402

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    yield engine


@pytest.fixture()
def db(db_engine):
    """事务级隔离：session 以 create_savepoint 模式绑定外层事务，
    服务层内部的 db.commit() 只提交 savepoint，测试结束后整体回滚。"""
    connection = db_engine.connect()
    connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    connection.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def make_user(db):
    """直接建用户并发 access token（绕过登录接口，专注业务测试）。"""
    from routers.auth import _create_token

    def _make(username="tester", is_admin=1):
        user = models.User(
            username=username, password_hash="test-hash",
            is_admin=is_admin, is_active=1, token_version=1,
        )
        db.add(user)
        db.flush()
        token = _create_token(user, "access")
        return user, {"Authorization": f"Bearer {token}"}

    return _make
