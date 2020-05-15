from flask import g
from superset.extensions import db

from flask import request

from sqlalchemy import event
from sqlalchemy.engine import Engine


def before_request():
    subdomain = request.host.split(".")[0]
    g.shard_id = subdomain
    db.engine.update_execution_options(shard_id=subdomain)


@event.listens_for(Engine, "before_cursor_execute")
def switch_schema(conn, cursor, stmt,
                  params, context, executemany):
    # Avoid infinite recursion
    if stmt.startswith("set search_path to "):
        return
    shard_id = conn._execution_options.get('shard_id', None)
    if shard_id is not None:
        conn.execute(f"set search_path to '{shard_id}'")


def before_first_request(error=None):
    db.engine.update_execution_options(schema_translate_map={None: None})
