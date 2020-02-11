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
from typing import Dict, Optional

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from superset.views.dashboard.filters import DashboardFilter
from superset.models.dashboard import Dashboard
from superset import db

import logging


logger = logging.getLogger(__name__)


class BaseDAO:
    pass


class DashboardDAO(BaseDAO):

    @staticmethod
    def validate_slug_uniqueness(slug: str) -> bool:
        return not (
            db.session.query(Dashboard.id)
            .filter_by(slug=slug)
            .one_or_none()
        )

    @staticmethod
    def validate_owner(owner_id: id) -> Optional[object]:
        return db.session.query(
                    current_app.appbuilder.sm.user_model
                ).filter_by(id=owner_id).one_or_none()

    @staticmethod
    def find(dashboard_id: int) -> Dashboard:
        query = DashboardFilter("slice", None).apply(db.session.query(Dashboard), None)
        return query.filter(id=dashboard_id).one_or_none()

    @staticmethod
    def create(dashboard_params: Dict) -> Optional[Dashboard]:
        dashboard = Dashboard()
        for key, value in dashboard_params.items():
            setattr(dashboard, key, value)
        try:
            db.session.add(dashboard)
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to update dashboard: {e}")
            db.session.rollback()
            return None
        return dashboard
