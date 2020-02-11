# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import logging

from flask import g, make_response, request
from flask_appbuilder.api import expose, protect, rison, safe
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import lazy_gettext as _, ngettext
from sqlalchemy.exc import SQLAlchemyError

from superset.constants import RouteMethod
from superset.exceptions import SupersetSecurityException
from superset.models.dashboard import Dashboard
from superset.views.base import check_ownership, generate_download_headers
from superset.views.base_api import BaseSupersetModelRestApi
from superset.views.dashboard.schemas import (
    DashboardPostSchema,
    DashboardPutSchema,
    get_export_ids_schema
)

from .mixin import DashboardMixin

logger = logging.getLogger(__name__)
get_delete_ids_schema = {"type": "array", "items": {"type": "integer"}}


class DashboardRestApi(DashboardMixin, BaseSupersetModelRestApi):
    datamodel = SQLAInterface(Dashboard)
    include_route_methods = RouteMethod.REST_MODEL_VIEW_CRUD_SET | {
        RouteMethod.EXPORT,
        RouteMethod.RELATED,
        "bulk_delete",  # not using RouteMethod since locally defined
    }
    resource_name = "dashboard"
    allow_browser_login = True

    class_permission_name = "DashboardModelView"
    show_columns = [
        "dashboard_title",
        "slug",
        "owners.id",
        "owners.username",
        "position_json",
        "css",
        "json_metadata",
        "published",
        "table_names",
        "charts",
    ]
    order_columns = ["dashboard_title", "changed_on", "published", "changed_by_fk"]
    list_columns = [
        "id",
        "dashboard_title",
        "url",
        "published",
        "changed_by.username",
        "changed_by_name",
        "changed_by_url",
        "changed_on",
    ]

    add_model_schema = DashboardPostSchema()
    edit_model_schema = DashboardPutSchema()

    order_rel_fields = {
        "slices": ("slice_name", "asc"),
        "owners": ("first_name", "asc"),
    }
    filter_rel_fields_field = {"owners": "first_name", "slices": "slice_name"}

    @expose("/", methods=["POST"])
    @protect()
    @safe
    def post(self):
        """Creates a new owned Model
        ---
        post:
          requestBody:
            description: Model schema
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/{{self.__class__.__name__}}.post'
          responses:
            201:
              description: Model added
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      id:
                        type: string
                      result:
                        $ref: '#/components/schemas/{{self.__class__.__name__}}.post'
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        from .commands.create import CreateDashboardCommand, InvalidDashboardError

        if not request.is_json:
            return self.response_400(message="Request is not JSON")
        item = self.add_model_schema.load(request.json)
        # This validates custom Schema with custom validations
        if item.errors:
            return self.response_422(message=item.errors)
        try:
            cmd = CreateDashboardCommand(item)
            new_dashboard = cmd.run()
            return self.response(
                201,
                id=new_dashboard.id,
            )
        except InvalidDashboardError:
            return self.response_422(message=item.errors)
        except Exception as e:
            logger.error(f"Error creating model {self.__class__.__name__}: {e}")
            return self.response_422(message=str(e))

    @expose("/", methods=["DELETE"])
    @protect()
    @safe
    @rison(get_delete_ids_schema)
    def bulk_delete(self, **kwargs):  # pylint: disable=arguments-differ
        """Delete bulk Dashboards
        ---
        delete:
          parameters:
          - in: query
            name: q
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: integer
          responses:
            200:
              description: Dashboard bulk delete
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      message:
                        type: string
            401:
              $ref: '#/components/responses/401'
            403:
              $ref: '#/components/responses/401'
            404:
              $ref: '#/components/responses/404'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        item_ids = kwargs["rison"]
        query = self.datamodel.session.query(Dashboard).filter(
            Dashboard.id.in_(item_ids)
        )
        items = self._base_filters.apply_all(query).all()
        if not items:
            return self.response_404()
        # Check user ownership over the items
        for item in items:
            try:
                check_ownership(item)
            except SupersetSecurityException as e:
                logger.warning(
                    f"Dashboard {item} was not deleted, "
                    f"because the user ({g.user}) does not own it"
                )
                return self.response(403, message=_("No dashboards deleted"))
            except SQLAlchemyError as e:
                logger.error(f"Error checking dashboard ownership {e}")
                return self.response_422(message=str(e))
        # bulk delete, first delete related data
        for item in items:
            try:
                item.slices = []
                item.owners = []
                self.datamodel.session.merge(item)
            except SQLAlchemyError as e:
                logger.error(f"Error bulk deleting related data on dashboards {e}")
                self.datamodel.session.rollback()
                return self.response_422(message=str(e))
        # bulk delete itself
        try:
            self.datamodel.session.query(Dashboard).filter(
                Dashboard.id.in_(item_ids)
            ).delete(synchronize_session="fetch")
        except SQLAlchemyError as e:
            logger.error(f"Error bulk deleting dashboards {e}")
            self.datamodel.session.rollback()
            return self.response_422(message=str(e))
        self.datamodel.session.commit()
        return self.response(
            200,
            message=ngettext(
                f"Deleted %(num)d dashboard",
                f"Deleted %(num)d dashboards",
                num=len(items),
            ),
        )

    @expose("/export/", methods=["GET"])
    @protect()
    @safe
    @rison(get_export_ids_schema)
    def export(self, **kwargs):
        """Export dashboards
        ---
        get:
          parameters:
          - in: query
            name: q
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: integer
          responses:
            200:
              description: Dashboard export
              content:
                text/plain:
                  schema:
                    type: string
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            404:
              $ref: '#/components/responses/404'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        query = self.datamodel.session.query(Dashboard).filter(
            Dashboard.id.in_(kwargs["rison"])
        )
        query = self._base_filters.apply_all(query)
        ids = [item.id for item in query.all()]
        if not ids:
            return self.response_404()
        export = Dashboard.export_dashboards(ids)
        resp = make_response(export, 200)
        resp.headers["Content-Disposition"] = generate_download_headers("json")[
            "Content-Disposition"
        ]
        return resp
