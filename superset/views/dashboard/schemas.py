import json

from marshmallow import fields, Schema, ValidationError
from marshmallow.validate import Length

from superset.exceptions import SupersetException
from superset.models.dashboard import Dashboard
from superset.utils import core as utils


class DashboardJSONMetadataSchema(Schema):
    timed_refresh_immune_slices = fields.List(fields.Integer())
    filter_scopes = fields.Dict()
    expanded_slices = fields.Dict()
    refresh_frequency = fields.Integer()
    default_filters = fields.Str()
    filter_immune_slice_fields = fields.Dict()
    stagger_refresh = fields.Boolean()
    stagger_time = fields.Integer()


def validate_json(value):
    try:
        utils.validate_json(value)
    except SupersetException:
        raise ValidationError("JSON not valid")


def validate_json_metadata(value):
    if not value:
        return
    try:
        value_obj = json.loads(value)
    except json.decoder.JSONDecodeError:
        raise ValidationError("JSON not valid")
    errors = DashboardJSONMetadataSchema(strict=True).validate(value_obj, partial=False)
    if errors:
        raise ValidationError(errors)


class DashboardPostSchema(Schema):
    __class_model__ = Dashboard

    dashboard_title = fields.String(allow_none=True, validate=Length(0, 500))
    slug = fields.String(
        allow_none=True, validate=[Length(1, 255)]
    )
    owners = fields.List(fields.Integer())
    position_json = fields.String(validate=validate_json)
    css = fields.String()
    json_metadata = fields.String(validate=validate_json_metadata)
    published = fields.Boolean()


class DashboardPutSchema(Schema):
    dashboard_title = fields.String(allow_none=True, validate=Length(0, 500))
    slug = fields.String(allow_none=True, validate=Length(0, 255))
    owners = fields.List(fields.Integer())
    position_json = fields.String(validate=validate_json)
    css = fields.String()
    json_metadata = fields.String(validate=validate_json_metadata)
    published = fields.Boolean()


get_export_ids_schema = {"type": "array", "items": {"type": "integer"}}
