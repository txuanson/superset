from flask import g
from superset.extensions import db

from flask import request
from werkzeug.local import LocalProxy

from sqlalchemy import event
from sqlalchemy.orm.query import Query
from sqlalchemy.pool import Pool
from sqlalchemy.engine import Engine


def get_tenant_id():
    if hasattr(g, "tenant_id"):
        print(f"Tenant:{g.tenant_id}")
        return g.tenant_id
    print(f"Tenant:None")
    return None


tenant_id_proxy = LocalProxy(get_tenant_id)


def before_request():
    subdomain = request.host.split(".")[0]
    g.tenant_id = subdomain


# def tenant_switch(metadata_engine):
#     @event.listens_for(metadata_engine, "before_cursor_execute", retval=True)
#     def before_cursor_switch(conn, cursor, stmt,
#                         params, context, executemany):
#         if not hasattr(g, "tenant_id"):
#             return stmt, params
#         if g.tenant_id is not None:
#             return f"set search_path to '{g.tenant_id}'; {stmt};", params
#         return stmt, params


# def tenant_switch(metadata_engine):
#     @event.listens_for(metadata_engine, "engine_connect")
#     def checkout(*args):
#         print("CONN")
#         if hasattr(g, "tenant_id"):
#             print(f"CHANGING {g.tenant_id}")
#             db.engine.update_execution_options(schema_translate_map={None: g.tenant_id})


def before_first_request(error=None):
    db.engine.update_execution_options(schema_translate_map={None: tenant_id_proxy})
