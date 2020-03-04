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

from flask_appbuilder.models.sqla.interface import SQLAInterface
from sqlalchemy.exc import SQLAlchemyError

from superset.connectors.sqla.models import SqlaTable, TableColumn
from superset.extensions import db
from superset.views.base import DatasourceFilter

logger = logging.getLogger(__name__)


class DatasetColumnDAO:
    @staticmethod
    def get_dataset_by_id(dataset_id) -> Optional[SqlaTable]:
        try:
            return db.session.query(TableColumn).filter_by(id=dataset_id).one_or_none()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.error(f"Could not get dataset by id: {e}")
            return None

    @staticmethod
    def validate_uniqueness(dataset_id: int, name: str) -> bool:
        column_query = db.session.query(TableColumn).filter(
            TableColumn.table_id == dataset_id, TableColumn.column_name == name
        )
        return not db.session.query(column_query.exists()).scalar()

    @staticmethod
    def validate_update_uniqueness(dataset_id: int, column_id: int, name: str) -> bool:
        column_query = db.session.query(TableColumn).filter(
            TableColumn.column_name == name,
            TableColumn.table_id == dataset_id,
            TableColumn.id != column_id,
        )
        return not db.session.query(column_query.exists()).scalar()

    @staticmethod
    def find_by_id(model_id: int) -> SqlaTable:
        data_model = SQLAInterface(TableColumn, db.session)
        query = db.session.query(TableColumn)
        query = DatasourceFilter("id", data_model).apply(query, None)
        return query.filter_by(id=model_id).one_or_none()

    @staticmethod
    def create(properties: Dict, commit=True) -> Optional[TableColumn]:
        model = TableColumn()
        for key, value in properties.items():
            setattr(model, key, value)
        try:
            db.session.add(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.error(f"Failed to create dataset column: {e}")
            db.session.rollback()
            return None
        return model

    @staticmethod
    def update(
        model: TableColumn, properties: Dict, commit=True
    ) -> Optional[TableColumn]:
        for key, value in properties.items():
            setattr(model, key, value)
        try:
            db.session.merge(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.error(f"Failed to update dataset column: {e}")
            db.session.rollback()
            return None
        return model

    @staticmethod
    def delete(model: TableColumn, commit=True):
        try:
            db.session.delete(model)
            if commit:
                db.session.commit()
        except SQLAlchemyError as e:  # pragma: no cover
            logger.error(f"Failed to delete dataset column: {e}")
            db.session.rollback()
            return None
        return model
