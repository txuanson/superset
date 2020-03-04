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
from typing import Dict, List, Optional

from flask_appbuilder.security.sqla.models import User
from marshmallow import ValidationError

from superset.commands.base import BaseCommand
from superset.connectors.sqla.models import TableColumn
from superset.datasets.columns.commands.exceptions import (
    DatasetColumnExistsValidationError,
    DatasetColumnForbiddenError,
    DatasetColumnInvalidError,
    DatasetColumnNotFoundError,
    DatasetColumnUpdateFailedError,
)
from superset.datasets.columns.dao import DatasetColumnDAO
from superset.exceptions import SupersetSecurityException
from superset.views.base import check_ownership


class UpdateDatasetColumnCommand(BaseCommand):
    def __init__(self, user: User, model_id: int, data: Dict):
        self._actor = user
        self._model_id = model_id
        self._properties = data.copy()
        self._model: Optional[TableColumn] = None

    def run(self):
        self.validate()
        dataset = DatasetColumnDAO.update(self._model, self._properties)

        if not dataset:
            raise DatasetColumnUpdateFailedError()
        return dataset

    def validate(self) -> None:
        exceptions: List[ValidationError] = list()
        # Validate/populate model exists
        self._model = DatasetColumnDAO.find_by_id(self._model_id)
        if not self._model:
            raise DatasetColumnNotFoundError()

        # Validate/Populate database not allowed to change
        table_id = self._properties.get("table")
        if table_id and table_id != self._model.table_id:
            raise DatasetColumnNotFoundError()
        self._properties["table"] = self._model.table

        # Validate uniqueness
        column_name = self._properties.get("column_name")
        if not DatasetColumnDAO.validate_update_uniqueness(
            self._model.table_id, self._model_id, column_name
        ):
            exceptions.append(DatasetColumnExistsValidationError(column_name))
        # Check ownership
        try:
            check_ownership(self._model.table)
        except SupersetSecurityException:
            raise DatasetColumnForbiddenError()
        if exceptions:
            exception = DatasetColumnInvalidError()
            exception.add_list(exceptions)
            raise exception
