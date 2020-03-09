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
from typing import Dict, Optional

from flask import current_app
from flask_appbuilder.models.sqla.interface import SQLAInterface
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from superset.commands.exceptions import (
    CreateFailedError,
    DeleteFailedError,
    UpdateFailedError,
)
from superset.connectors.sqla.models import SqlaTable, SqlMetric, TableColumn
from superset.extensions import db
from superset.models.core import Database
from superset.views.base import DatasourceFilter

logger = logging.getLogger(__name__)


class DatasetDAO:
    @staticmethod
    def get_owner_by_id(owner_id: int) -> Optional[object]:
        return (
            db.session.query(current_app.appbuilder.sm.user_model)
            .filter_by(id=owner_id)
            .one_or_none()
        )

    @staticmethod
    def get_database_by_id(database_id) -> Optional[Database]:
        try:
            return db.session.query(Database).filter_by(id=database_id).one_or_none()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.error(f"Could not get database by id: {e}")
            return None

    @staticmethod
    def validate_table_exists(database: Database, table_name: str, schema: str) -> bool:
        try:
            database.get_table(table_name, schema=schema)
            return True
        except SQLAlchemyError as e:  # pragma: no cover
            logger.error(f"Got an error {e} validating table: {table_name}")
            return False

    @staticmethod
    def validate_uniqueness(database_id: int, name: str) -> bool:
        dataset_query = db.session.query(SqlaTable).filter(
            SqlaTable.table_name == name, SqlaTable.database_id == database_id
        )
        return not db.session.query(dataset_query.exists()).scalar()

    @staticmethod
    def validate_update_uniqueness(
        database_id: int, dataset_id: int, name: str
    ) -> bool:
        dataset_query = db.session.query(SqlaTable).filter(
            SqlaTable.table_name == name,
            SqlaTable.database_id == database_id,
            SqlaTable.id != dataset_id,
        )
        return not db.session.query(dataset_query.exists()).scalar()

    @staticmethod
    def find_by_id(model_id: int) -> SqlaTable:
        data_model = SQLAInterface(SqlaTable, db.session)
        query = db.session.query(SqlaTable)
        query = DatasourceFilter("id", data_model).apply(query, None)
        return query.filter_by(id=model_id).one_or_none()

    @staticmethod
    def create(properties: Dict, commit=True) -> Optional[SqlaTable]:
        """
        Creates a Dataset model on the metadata DB
        """
        model = SqlaTable()
        for key, value in properties.items():
            setattr(model, key, value)
        try:
            db.session.add(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            db.session.rollback()
            raise CreateFailedError(exception=e)
        return model

    @staticmethod
    def update_column(
        model: TableColumn, properties: Dict, commit=True
    ) -> Optional[TableColumn]:
        for key, value in properties.items():
            setattr(model, key, value)
        try:
            db.session.merge(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            db.session.rollback()
            raise UpdateFailedError(exception=e)
        return model

    @staticmethod
    def create_column(properties: Dict, commit=True) -> Optional[TableColumn]:
        """
        Creates a Dataset model on the metadata DB
        """
        model = TableColumn()
        for key, value in properties.items():
            setattr(model, key, value)
        try:
            db.session.add(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            db.session.rollback()
            raise CreateFailedError(exception=e)
        return model

    @staticmethod
    def update(model: SqlaTable, properties: Dict, commit=True) -> Optional[SqlaTable]:
        """
        Updates a Dataset model on the metadata DB
        """
        if "columns" in properties:
            new_columns = list()
            for column in properties.get("columns", []):
                if column.get("id"):
                    column_obj = db.session.query(TableColumn).get(column.get("id"))
                    column_obj = DatasetDAO.update_column(
                        column_obj, column, commit=commit
                    )
                else:
                    column_obj = DatasetDAO.create_column(column, commit=commit)
                new_columns.append(column_obj)
            properties["columns"] = new_columns

        for key, value in properties.items():
            setattr(model, key, value)
        try:
            db.session.merge(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            db.session.rollback()
            raise UpdateFailedError(exception=e)
        return model

    @staticmethod
    def delete(model: SqlaTable, commit=True):
        """
        Deletes a Dataset model on the metadata DB
        """
        try:
            db.session.delete(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.error(f"Failed to delete dataset: {e}")
            db.session.rollback()
            raise DeleteFailedError(exception=e)
        return model

    @staticmethod
    def update_metadata(model: SqlaTable, commit: bool = True) -> None:
        """
        Fetches the metadata for the table and merges it in
        """
        try:
            table = model.get_sqla_table_object()
        except Exception as e:
            logger.exception(e)
            from flask_babel import lazy_gettext as _

            raise Exception(
                _(
                    "Table [{}] doesn't seem to exist in the specified database, "
                    "couldn't fetch column information"
                ).format(model.table_name)
            )

        metric = SqlMetric
        metrics = []
        any_date_col = None
        db_engine_spec = model.database.db_engine_spec
        db_dialect = model.database.get_dialect()
        db_cols = (
            db.session.query(TableColumn)
            .filter(TableColumn.table == model)
            .filter(or_(TableColumn.column_name == col.name for col in table.columns))
        )
        db_cols = {db_col.column_name: db_col for db_col in db_cols}

        for col in table.columns:
            # Map each column type
            try:
                data_type = db_engine_spec.column_datatype_to_string(
                    col.type, db_dialect
                )
            except Exception as e:
                data_type = "UNKNOWN"
                logger.error("Unrecognized data type in {}.{}".format(table, col.name))
                logger.exception(e)

            db_col = db_cols.get(col.name, None)
            # Infer flags
            if not db_col:
                db_col = TableColumn(column_name=col.name, type=data_type)
                db_col.sum = db_col.is_num
                db_col.avg = db_col.is_num
                db_col.is_dttm = db_col.is_time
                db_engine_spec.alter_new_orm_column(db_col)
            else:
                db_col.type = data_type
            db_col.groupby = True
            db_col.filterable = True
            model.columns.append(db_col)
            if not any_date_col and db_col.is_time:
                any_date_col = col.name

        metrics.append(
            metric(
                metric_name="count",
                verbose_name="COUNT(*)",
                metric_type="count",
                expression="COUNT(*)",
            )
        )
        if not model.main_dttm_col:
            model.main_dttm_col = any_date_col
        model.add_missing_metrics(metrics)
        try:
            db.session.merge(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:
            CreateFailedError(exception=e)
