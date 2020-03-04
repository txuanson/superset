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
import re

from flask_babel import lazy_gettext as _
from marshmallow import fields, Schema, ValidationError
from marshmallow.validate import Length


def validate_python_date_format(value):
    regex = re.compile(
        r"""
        ^(
            epoch_s|epoch_ms|
            (?P<date>%Y(-%m(-%d)?)?)([\sT](?P<time>%H(:%M(:%S(\.%f)?)?)?))?
        )$
        """,
        re.VERBOSE,
    )
    match = regex.match(value or "")
    if not match:
        raise ValidationError(_("Invalid date/timestamp format"))


class DatasetColumnPostSchema(Schema):
    column_name = fields.String(required=True, validate=Length(1, 255))
    verbose_name = fields.String(Length=(1, 1024))
    is_active = fields.Boolean()
    type = fields.String(validate=Length(1, 32))
    groupby = fields.Boolean()
    filterable = fields.Boolean()
    description = fields.String()
    is_dttm = fields.Boolean(default=False)
    expression = fields.String()
    python_date_format = fields.String(
        validate=[Length(1, 255), validate_python_date_format]
    )


class DatasetColumnPutSchema(Schema):
    column_name = fields.String(allow_none=True, validate=Length(1, 255))
    verbose_name = fields.String(allow_none=True, Length=(1, 1024))
    is_active = fields.Boolean()
    type = fields.String(allow_none=True, validate=Length(1, 32))
    groupby = fields.Boolean()
    filterable = fields.Boolean()
    description = fields.String()
    is_dttm = fields.Boolean(default=False)
    expression = fields.String()
    python_date_format = fields.String(
        validate=[Length(1, 255), validate_python_date_format]
    )
