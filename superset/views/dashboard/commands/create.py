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
from typing import List, Tuple

from flask import g

from marshmallow import UnmarshalResult, ValidationError
from superset.views.dashboard.dao import DashboardDAO


class BaseCommand:
    def run(self):
        raise NotImplementedError


class MissingDashboardError(Exception):
    pass


class UpdateFailedError(Exception):
    pass


class InvalidDashboardError(Exception):
    pass


class CreateDashboardCommand(BaseCommand):
    def __init__(self, unmarshal: UnmarshalResult):
        self._actor = g.user
        self._properties = unmarshal.data
        self._errors = unmarshal.errors

    def run(self):
        valid, exceptions = self._is_dashboard_valid()
        if not valid:
            for exception in exceptions:
                self._errors.update(exception.normalized_messages())
            raise InvalidDashboardError("Dashboard parameters are invalid.")

        dashboard = DashboardDAO.create(self._properties)

        if not dashboard:
            raise UpdateFailedError("Dashboard could not be updated.")
        return dashboard

    def _is_dashboard_valid(self) -> Tuple[bool, List[ValidationError]]:
        valid = True
        exceptions = list()

        # Validate slug
        if "slug" in self._properties:
            if not DashboardDAO.validate_slug_uniqueness(self._properties["slug"]):
                exceptions.append(
                    ValidationError("slug must be unique", field_names=["slug"])
                )
                valid = False

        # Validate/update owners
        owners = list()
        if "owners" not in self._properties:
            self._properties["owners"] = [self._actor]
            return valid, exceptions
        for owner_id in self._properties["owners"]:
            owner = DashboardDAO.validate_owner(owner_id)
            if not owner:
                exceptions.append(
                    ValidationError("owners are invalid", field_names=["owners"])
                )
                valid = False
                break
            owners.append(owner)
        self._properties["owners"] = owners
        return valid, exceptions
