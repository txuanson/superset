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
from enum import Enum
from typing import List, Optional, TypedDict, Union

from flask_appbuilder.security.sqla.models import Role
from flask_login import AnonymousUserMixin


class GuestTokenUser(TypedDict, total=False):
    username: str
    first_name: str
    last_name: str


class GuestTokenResourceType(Enum):
    DASHBOARD = "dashboard"


class GuestTokenResource(TypedDict):
    type: GuestTokenResourceType
    id: Union[str, int]
    rls: Optional[str]


GuestTokenResources = List[GuestTokenResource]


class GuestToken(TypedDict):
    iat: float
    exp: float
    user: GuestTokenUser
    resources: GuestTokenResources


class GuestUser(AnonymousUserMixin):
    """
    Used as the "anonymous" user in case of guest authentication (embedded)
    """

    is_guest_user = True

    def __init__(
        self,
        username: str,
        first_name: str,
        last_name: str,
        roles: List[Role],
        resources: GuestTokenResources,
    ):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.roles = roles
        self.resources = resources
