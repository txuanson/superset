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

from flask import g, request, Response
from flask_appbuilder import permission_name
from flask_appbuilder.api import (
    BaseApi,
    expose,
    get_info_schema,
    get_item_schema,
    get_list_schema,
    merge_response_func,
    protect,
    rison,
    safe,
)
from flask_appbuilder.api.schemas import API_FILTERS_RIS_KEY, API_PERMISSIONS_RIS_KEY
from flask_appbuilder.models.sqla.interface import SQLAInterface

from superset.connectors.sqla.models import TableColumn
from superset.constants import RouteMethod
from superset.datasets.columns.commands.create import CreateDatasetColumnCommand
from superset.datasets.columns.commands.delete import DeleteDatasetColumnCommand
from superset.datasets.columns.commands.exceptions import (
    DatasetColumnCreateFailedError,
    DatasetColumnDeleteFailedError,
    DatasetColumnForbiddenError,
    DatasetColumnInvalidError,
    DatasetColumnNotFoundError,
    DatasetColumnUpdateFailedError,
)
from superset.datasets.columns.commands.update import UpdateDatasetColumnCommand
from superset.datasets.columns.schemas import (
    DatasetColumnPostSchema,
    DatasetColumnPutSchema,
)
from superset.datasets.dao import DatasetDAO
from superset.views.base_api import BaseSupersetModelRestApi

logger = logging.getLogger(__name__)


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
    add_model_schema = DatasetColumnPostSchema()
    edit_model_schema = DatasetColumnPutSchema()

    add_columns = show_columns + ["table"]
    edit_columns = show_columns + ["table"]

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
    def get(  # pylint: disable=arguments-differ
        self, pk: int, column_id: int, **kwargs
    ) -> Response:
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

    @expose("/<int:pk>/column/", methods=["POST"])
    @protect()
    @safe
    def post(self, pk: int) -> Response:  # pylint: disable=arguments-differ
        """Add a column to a dataset
        ---
        post:
          description: >-
            Add a column to a dataset
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
            description: The dataset id
          requestBody:
            description: Model schema
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/{{self.__class__.__name__}}.post'
          responses:
            201:
              description: Item inserted
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
            403:
              $ref: '#/components/responses/403'
            422:
              $ref: '#/components/responses/422'
            500:
              $ref: '#/components/responses/500'
        """
        if not request.is_json:
            return self.response_400(message="Request is not JSON")
        item = self.add_model_schema.load(request.json)
        item.data["table"] = pk
        # This validates custom Schema with custom validations
        if item.errors:
            return self.response_400(message=item.errors)
        try:
            new_model = CreateDatasetColumnCommand(g.user, item.data).run()
            return self.response(201, id=new_model.id, result=item.data)
        except DatasetColumnInvalidError as e:
            return self.response_422(message=e.normalized_messages())
        except DatasetColumnCreateFailedError as e:
            logger.error(f"Error creating model {self.__class__.__name__}: {e}")
            return self.response_422(message=str(e))

    @expose("/<int:pk>/column/<column_id>", methods=["PUT"])
    @protect()
    @safe
    def put(  # pylint: disable=arguments-differ,too-many-return-statements
        self, pk: int, column_id: int
    ) -> Response:
        """Change a column from a dataset
        ---
        put:
          description: >-
            Change a column from a dataset
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
            description: The dataset id
          - in: path
            schema:
              type: integer
            name: column_id
            description: The column id
          requestBody:
            description: Model schema
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/{{self.__class__.__name__}}.put'
          responses:
            200:
              description: Item changed
              content:
                application/json:
                  schema:
                    type: object
                    properties:
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
        item.data["table"] = pk
        try:
            changed_model = UpdateDatasetColumnCommand(
                g.user, column_id, item.data
            ).run()
            return self.response(200, id=changed_model.id, result=item.data)
        except DatasetColumnNotFoundError:
            return self.response_404()
        except DatasetColumnInvalidError as e:
            return self.response_422(message=e.normalized_messages())
        except DatasetColumnForbiddenError:
            return self.response_403()
        except DatasetColumnUpdateFailedError as e:
            logger.error(f"Error updating model {self.__class__.__name__}: {e}")
            return self.response_422(message=str(e))

    @expose("/<int:pk>/column/<column_id>", methods=["DELETE"])
    @protect()
    @safe
    def delete(  # pylint: disable=arguments-differ
        self, pk: int, column_id: int  # pylint: disable=unused-argument
    ) -> Response:
        """Delete a column from a dataset
        ---
        delete:
          description: >-
            Delete a column from a dataset
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
          - in: path
            schema:
              type: integer
            name: column_id
            description: The column id
          responses:
            200:
              description: Item deleted
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      message:
                        type: string
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
            DeleteDatasetColumnCommand(g.user, column_id).run()
            return self.response(200, message="OK")
        except DatasetColumnNotFoundError:
            return self.response_404()
        except DatasetColumnForbiddenError:
            return self.response_403()
        except DatasetColumnDeleteFailedError as e:
            logger.error(f"Error deleting model {self.__class__.__name__}: {e}")
            return self.response_422(message=str(e))
