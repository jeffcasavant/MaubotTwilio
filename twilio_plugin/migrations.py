from sqlalchemy import select
from sqlalchemy.engine.base import Engine
from alembic.migration import MigrationContext
from alembic.operations import Operations


def run(engine: Engine):
    conn = engine.connect()
    ctx = MigrationContext.configure(conn)
    op = Operations(ctx)
