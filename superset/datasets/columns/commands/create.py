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
from typing import Dict

from flask_appbuilder.security.sqla.models import User

from superset.commands.base import BaseCommand
from superset.datasets.columns.commands.exceptions import (
    DatasetColumnCreateFailedError,
    DatasetColumnExistsValidationError,
    DatasetColumnInvalidError,
    DatasetNotFoundValidationError,
)
from superset.datasets.columns.dao import DatasetColumnDAO
from superset.datasets.dao import DatasetDAO


class CreateDatasetColumnCommand(BaseCommand):
    def __init__(self, user: User, data: Dict):
        self._actor = user
        self._properties = data.copy()

    def run(self):
        self.validate()
        dataset = DatasetColumnDAO.create(self._properties)

        if not dataset:
            raise DatasetColumnCreateFailedError()
        return dataset

    def validate(self) -> None:
        exceptions = list()
        dataset_id = self._properties["table"]
        column_name = self._properties["column_name"]

        # Validate uniqueness
        if not DatasetColumnDAO.validate_uniqueness(dataset_id, column_name):
            exceptions.append(DatasetColumnExistsValidationError(column_name))

        # Validate/Populate dataset
        dataset = DatasetDAO.find_by_id(dataset_id)
        if not dataset:
            exceptions.append((DatasetNotFoundValidationError()))
        self._properties["table"] = dataset

        if exceptions:
            exception = DatasetColumnInvalidError()
            exception.add_list(exceptions)
            raise exception
