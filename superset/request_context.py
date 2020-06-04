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
        return g.tenant_id
    return None
    # if request:
    #     return request.host.split('.')[0]
    # return None


tenant_id_proxy = LocalProxy(get_tenant_id)


def before_request():
    subdomain = request.host.split(".")[0]
    g.tenant_id = subdomain

    #print(f"BEFORE {g.tenant_id} {tenant_id_proxy}")


def after_request(response):
    db.engine.update_execution_options(schema_translate_map={None: tenant_id_proxy})
    #db.engine.update_execution_options(schema_translate_map={None: tenant_id_proxy})
    return response


def tenant_switch(metadata_engine):
    @event.listens_for(metadata_engine, "commit")
    def checkout(*args):
        print("CONN")

    @event.listens_for(metadata_engine, 'set_connection_execution_options')
    def receive_set_connection_execution_options(conn, opts):
        #print(f"------ {conn.get_execution_options()}")
        #conn.execution_options(schema_translate_map={None: tenant_id_proxy})
        print(f"SET CONN OPT")

    # @event.listens_for(metadata_engine, 'set_engine_execution_options')
    # def receive_set_connection_execution_options(conn, opts):
    #     print(f"SET ENG OPT {opts}")
    #
    # @event.listens_for(metadata_engine, 'after_execute')
    # def receive_set_connection_execution_options(*kw):
    #     print(f"AFTER EXECUTE")
    #

    @event.listens_for(metadata_engine, "before_cursor_execute", retval=True)
    def before_cursor_switch(conn, cursor, stmt,
                             params, context, executemany):
        print(f"STS:{stmt} {metadata_engine.get_execution_options()}")
        return stmt, params

    # @event.listens_for(metadata_engine, "before_cursor_execute", retval=True)
    # def before_cursor_switch(conn, cursor, stmt,
    #                     params, context, executemany):
    #     if not hasattr(g, "tenant_id"):
    #         return stmt, params
    #     if g.tenant_id is not None:
    #         return f"set search_path to '{g.tenant_id}'; {stmt};", params
    #     return stmt, params


def before_first_request(error=None):
    db.engine.update_execution_options(schema_translate_map={None: tenant_id_proxy})
    # db.engine.update_execution_options(schema_translate_map={None: None})

# SQLAlchemy dialect
# subclassing