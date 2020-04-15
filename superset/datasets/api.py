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
from typing import Any

import yaml
from flask import g, request, Response
from flask_appbuilder.api import (
    API_FILTERS_RIS_KEY,
    API_PERMISSIONS_RIS_KEY,
    BaseApi,
    expose,
    get_info_schema,
    get_item_schema,
    get_list_schema,
    merge_response_func,
    permission_name,
    protect,
    rison,
    safe,
)
from flask_appbuilder.models.sqla.interface import SQLAInterface

from superset.connectors.sqla.models import SqlaTable, TableColumn
from superset.constants import RouteMethod
from superset.datasets.commands.create import CreateDatasetCommand
from superset.datasets.commands.delete import DeleteDatasetCommand
from superset.datasets.commands.exceptions import (
    DatasetCreateFailedError,
    DatasetDeleteFailedError,
    DatasetForbiddenError,
    DatasetInvalidError,
    DatasetNotFoundError,
    DatasetRefreshFailedError,
    DatasetUpdateFailedError,
)
from superset.datasets.commands.refresh import RefreshDatasetCommand
from superset.datasets.commands.update import UpdateDatasetCommand
from superset.datasets.dao import DatasetDAO
from superset.datasets.schemas import (
    DatasetPostSchema,
    DatasetPutSchema,
    DatasetColumnsPutSchema,
    DatasetColumnsPostSchema,
    get_export_ids_schema,
)
from superset.views.base import DatasourceFilter, generate_download_headers
from superset.views.base_api import BaseSupersetModelRestApi, RelatedFieldFilter
from superset.views.database.filters import DatabaseFilter
from superset.views.filters import FilterRelatedOwners

logger = logging.getLogger(__name__)


class DatasetRestApi(BaseSupersetModelRestApi):
    datamodel = SQLAInterface(SqlaTable)
    base_filters = [["id", DatasourceFilter, lambda: []]]

    resource_name = "dataset"
    allow_browser_login = True

    class_permission_name = "TableModelView"
    include_route_methods = RouteMethod.REST_MODEL_VIEW_CRUD_SET | {
        RouteMethod.EXPORT,
        RouteMethod.RELATED,
        "refresh",
    }
    list_columns = [
        "database_name",
        "changed_by_name",
        "changed_by_url",
        "changed_by.username",
        "changed_on",
        "database_name",
        "explore_url",
        "id",
        "schema",
        "table_name",
    ]
    show_columns = [
        "database.database_name",
        "database.id",
        "table_name",
        "sql",
        "filter_select_enabled",
        "fetch_values_predicate",
        "schema",
        "description",
        "main_dttm_col",
        "offset",
        "default_endpoint",
        "cache_timeout",
        "is_sqllab_view",
        "template_params",
        "owners.id",
        "owners.username",
        "owners.first_name",
        "owners.last_name",
        "columns",
        "metrics",
    ]
    add_model_schema = DatasetPostSchema()
    edit_model_schema = DatasetPutSchema()
    add_columns = ["database", "schema", "table_name", "owners"]
    edit_columns = [
        "table_name",
        "sql",
        "filter_select_enabled",
        "fetch_values_predicate",
        "schema",
        "description",
        "main_dttm_col",
        "offset",
        "default_endpoint",
        "cache_timeout",
        "is_sqllab_view",
        "template_params",
        "owners",
        "columns",
        "metrics",
    ]
    openapi_spec_tag = "Datasets"
    related_field_filters = {
        "owners": RelatedFieldFilter("first_name", FilterRelatedOwners),
        "database": "database_name",
    }
    filter_rel_fields = {"database": [["id", DatabaseFilter, lambda: []]]}
    allowed_rel_fields = {"database", "owners"}

    @expose("/", methods=["POST"])
    @protect()
    @safe
    def post(self) -> Response:
        """Creates a new Dataset
        ---
        post:
          description: >-
            Create a new Dataset
          requestBody:
            description: Dataset schema
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/{{self.__class__.__name__}}.post'
          responses:
            201:
              description: Dataset added
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      id:
                        type: number
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
        if not request.is_json:
            return self.response_400(message="Request is not JSON")
        item = self.add_model_schema.load(request.json)
        # This validates custom Schema with custom validations
        if item.errors:
            return self.response_400(message=item.errors)
        try:
            new_model = CreateDatasetCommand(g.user, item.data).run()
            return self.response(201, id=new_model.id, result=item.data)
        except DatasetInvalidError as ex:
            return self.response_422(message=ex.normalized_messages())
        except DatasetCreateFailedError as ex:
            logger.error(f"Error creating model {self.__class__.__name__}: {ex}")
            return self.response_422(message=str(ex))

    @expose("/<pk>", methods=["PUT"])
    @protect()
    @safe
    def put(  # pylint: disable=too-many-return-statements, arguments-differ
        self, pk: int
    ) -> Response:
        """Changes a Dataset
        ---
        put:
          description: >-
            Changes a Dataset
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
          requestBody:
            description: Dataset schema
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/{{self.__class__.__name__}}.put'
          responses:
            200:
              description: Dataset changed
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      id:
                        type: number
                      result:
                        $ref: '#/components/schemas/{{self.__class__.__name__}}.put'
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            403:
              $ref: '#/components/responses/403'
            404:
              $ref: '#/components/responses/404'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        if not request.is_json:
            return self.response_400(message="Request is not JSON")
        item = self.edit_model_schema.load(request.json)
        # This validates custom Schema with custom validations
        if item.errors:
            return self.response_400(message=item.errors)
        try:
            changed_model = UpdateDatasetCommand(g.user, pk, item.data).run()
            return self.response(200, id=changed_model.id, result=item.data)
        except DatasetNotFoundError:
            return self.response_404()
        except DatasetForbiddenError:
            return self.response_403()
        except DatasetInvalidError as ex:
            return self.response_422(message=ex.normalized_messages())
        except DatasetUpdateFailedError as ex:
            logger.error(f"Error updating model {self.__class__.__name__}: {ex}")
            return self.response_422(message=str(ex))

    @expose("/<pk>", methods=["DELETE"])
    @protect()
    @safe
    def delete(self, pk: int) -> Response:  # pylint: disable=arguments-differ
        """Deletes a Dataset
        ---
        delete:
          description: >-
            Deletes a Dataset
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
          responses:
            200:
              description: Dataset delete
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
              $ref: '#/components/responses/403'
            404:
              $ref: '#/components/responses/404'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            DeleteDatasetCommand(g.user, pk).run()
            return self.response(200, message="OK")
        except DatasetNotFoundError:
            return self.response_404()
        except DatasetForbiddenError:
            return self.response_403()
        except DatasetDeleteFailedError as ex:
            logger.error(f"Error deleting model {self.__class__.__name__}: {ex}")
            return self.response_422(message=str(ex))

    @expose("/export/", methods=["GET"])
    @protect()
    @safe
    @rison(get_export_ids_schema)
    def export(self, **kwargs: Any) -> Response:
        """Export dashboards
        ---
        get:
          description: >-
            Exports multiple datasets and downloads them as YAML files
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
              description: Dataset export
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
            500:
              $ref: '#/components/responses/500'
        """
        requested_ids = kwargs["rison"]
        query = self.datamodel.session.query(SqlaTable).filter(
            SqlaTable.id.in_(requested_ids)
        )
        query = self._base_filters.apply_all(query)
        items = query.all()
        ids = [item.id for item in items]
        if len(ids) != len(requested_ids):
            return self.response_404()

        data = [t.export_to_dict() for t in items]
        return Response(
            yaml.safe_dump(data),
            headers=generate_download_headers("yaml"),
            mimetype="application/text",
        )

    @expose("/<pk>/refresh", methods=["PUT"])
    @protect()
    @safe
    def refresh(self, pk: int) -> Response:
        """Refresh a Dataset
        ---
        put:
          description: >-
            Refreshes and updates columns of a dataset
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
          responses:
            200:
              description: Dataset delete
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
              $ref: '#/components/responses/403'
            404:
              $ref: '#/components/responses/404'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            RefreshDatasetCommand(g.user, pk).run()
            return self.response(200, message="OK")
        except DatasetNotFoundError:
            return self.response_404()
        except DatasetForbiddenError:
            return self.response_403()
        except DatasetRefreshFailedError as ex:
            logger.error(f"Error refreshing dataset {self.__class__.__name__}: {ex}")
            return self.response_422(message=str(ex))


class DatasetColumnRestApi(BaseSupersetModelRestApi):
    datamodel = SQLAInterface(TableColumn)

    resource_name = "dataset"
    allow_browser_login = True
    class_permission_name = "TableModelView"
    include_route_methods = RouteMethod.REST_MODEL_VIEW_CRUD_SET | {RouteMethod.RELATED}
    openapi_spec_tag = "Datasets"

    list_columns = [
        "column_name",
        "verbose_name",
        "type",
        "groupby",
        "filterable",
        "is_dttm",
    ]

    show_columns = [
        "column_name",
        "verbose_name",
        "description",
        "type",
        "groupby",
        "filterable",
        "expression",
        "is_dttm",
        "python_date_format",
    ]
    add_columns = show_columns + ["table"]
    edit_columns = show_columns + ["table"]

    add_model_schema = DatasetColumnsPostSchema()
    edit_model_schema = DatasetColumnsPutSchema()

    # validators_columns = {
    #     "column_name": validate_table_column_name,
    #     "python_date_format": validate_python_date_format,
    # }

    @expose("/column/_info", methods=["GET"])
    @protect()
    @safe
    @rison(get_info_schema)
    @permission_name("info")
    @merge_response_func(
        BaseApi.merge_current_user_permissions, API_PERMISSIONS_RIS_KEY
    )
    @merge_response_func(
        BaseSupersetModelRestApi.merge_search_filters, API_FILTERS_RIS_KEY
    )
    def info(self, **kwargs) -> Response:
        """ CRUD REST meta data containing user permissions and filters
        ---
        get:
          description: >-
            CRUD REST meta data containing user permissions and filters for this
            resource
          parameters:
          - $ref: '#/components/parameters/get_info_schema'
          responses:
            200:
              description: Item from Model
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      filters:
                        type: object
                      permissions:
                        type: array
                        items:
                          type: string
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        return self.info_headless(**kwargs)

    @expose("/<pk>/column/", methods=["GET"])
    @protect()
    @safe
    @rison(get_list_schema)
    def get_list(self, pk: int, **kwargs):  # pylint: disable=arguments-differ
        """Get list of columns from a dataset
        ---
        get:
          description: >-
            Query columns from a dataset, accepts filters, ordering and pagination
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
            description: The dataset id
            required: true
          - $ref: '#/components/parameters/get_list_schema'
          responses:
            200:
              description: Items from Model
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      ids:
                        type: array
                        items:
                          type: string
                      count:
                        type: number
                      result:
                        type: array
                        items:
                          $ref:
                            '#/components/schemas/{{self.__class__.__name__}}.get_list'
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        item = DatasetDAO.find_by_id(pk)
        if not item:
            return self.response_404()
        filters = kwargs["rison"].get("filters", [])
        filters.append({"col": "table", "opr": "rel_o_m", "value": pk})
        kwargs["rison"]["filters"] = filters
        return self.get_list_headless(**kwargs)

    @expose("/<int:pk>/column/<column_id>", methods=["GET"])
    @protect()
    @safe
    @rison(get_item_schema)
    def get(
        self, pk: int, column_id: int, **kwargs
    ):  # pylint: disable=arguments-differ
        """Get column from a dataset
        ---
        get:
          description: >-
            Get a column from a dataset
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
            description: The dataset id
            required: true
          - in: path
            schema:
              type: integer
            name: column_id
          - $ref: '#/components/parameters/get_item_schema'
          responses:
            200:
              description: Items from Model
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      ids:
                        type: array
                        items:
                          type: string
                      result:
                          type: array
                          items:
                            $ref: '#/components/schemas/{{self.__class__.__name__}}.get'
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        item = DatasetDAO.find_by_id(pk)
        if not item:
            return self.response_404()
        return self.get_headless(column_id, **kwargs)
