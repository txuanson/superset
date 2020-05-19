from flask import g
from superset.extensions import db

from flask import request

from sqlalchemy import event
from sqlalchemy.orm.query import Query
from sqlalchemy.pool import Pool
from sqlalchemy.engine import Engine


def before_request():
    subdomain = request.host.split(".")[0]
    g.tenant_id = subdomain


def tenant_switch(some_engine):
    @event.listens_for(some_engine, "before_cursor_execute", retval=True)
    def before_cursor_switch(conn, cursor, stmt,
                        params, context, executemany):
        # Avoid infinite recursion
        if not hasattr(g, "tenant_id"):
            return stmt, params
        if g.tenant_id is not None:
            return f"set search_path to '{g.tenant_id}'; {stmt};", params
        return stmt, params


def before_first_request(error=None):
    db.engine.update_execution_options(schema_translate_map={None: None})
