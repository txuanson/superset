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
from flask_babel import lazy_gettext as _
from marshmallow.validate import ValidationError

from superset.commands.exceptions import (
    CommandException,
    CommandInvalidError,
    CreateFailedError,
    DeleteFailedError,
    ForbiddenError,
    UpdateFailedError,
)


class DatasetNotFoundValidationError(ValidationError):
    """
    Marshmallow validation error for dataset does not exist
    """

    def __init__(self):
        super().__init__(_("Dataset does not exist"), field_names=["table"])


class DatasetColumnExistsValidationError(ValidationError):
    """
    Marshmallow validation error for dataset column already exists
    """

    def __init__(self, column_name: str):
        super().__init__(
            _("Dataset column %(name)s already exists", name=column_name),
            field_names=["column_name"],
        )


class DatasetColumnNotFoundError(CommandException):
    message = "Dataset column not found."


class DatasetColumnInvalidError(CommandInvalidError):
    message = _("Dataset column parameters are invalid.")


class DatasetColumnCreateFailedError(CreateFailedError):
    message = _("Dataset column could not be created.")


class DatasetColumnUpdateFailedError(UpdateFailedError):
    message = _("Dataset column could not be updated.")


class DatasetColumnDeleteFailedError(DeleteFailedError):
    message = _("Dataset column could not be deleted.")


class DatasetColumnForbiddenError(ForbiddenError):
    message = _("Changing this dataset is forbidden")
