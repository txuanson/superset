/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { t, SupersetTheme, css } from '@superset-ui/core';
import Icons from 'src/components/Icons';
import { Switch } from 'src/components/Switch';
import { AlertObject } from 'src/views/CRUD/alert/types';
import { UserWithPermissionsAndRoles } from 'src/types/bootstrapTypes';
import { Menu, NoAnimationDropdown } from 'src/common/components';

import DeleteModal from 'src/components/DeleteModal';
import {
  fetchUISpecificReport,
  toggleActive,
  deleteActiveReport,
} from 'src/reports/actions/reportState';
import ReportModal from '..';

const deleteColor = (theme: SupersetTheme) => css`
  color: ${theme.colors.error.base};
`;

export default function HeaderReportActionsDropDown({
  chartId,
  dashboardId,
}: {
  chartId?: number;
  dashboardId?: number;
}) {
  const { reports, user } = useSelector<
    any,
    { reports: [AlertObject]; user: UserWithPermissionsAndRoles }
  >(state => ({
    reports: state.reports,
    user: state.user || state.explore?.user,
  }));
  const [reportId] = Object.keys(reports);
  const report = reports[reportId];
  const [
    currentReportDeleting,
    setCurrentReportDeleting,
  ] = useState<AlertObject | null>(null);

  const dispatch = useDispatch();

  const [showAddModal, setShowAddModal] = useState(false);

  const toggleActiveKey = async (data: AlertObject, checked: boolean) => {
    if (data?.id) {
      dispatch(toggleActive(data, checked));
    }
  };

  const handleReportDelete = (report: AlertObject) => {
    dispatch(deleteActiveReport(report));
    setCurrentReportDeleting(null);
  };

  const canAddReports = useMemo(() => {
    if (!user) {
      // this is in the case that there is an anonymous user.
      return false;
    }
    const roles = Object.keys(user.roles || []);
    const permissions = roles.map(key =>
      user.roles[key].filter(
        perms => perms[0] === 'can_add' && perms[1] === 'AlertModelView',
      ),
    );
    return (
      isFeatureEnabled(FeatureFlag.ALERT_REPORTS) && permissions[0].length > 0
    );
  }, [user]);

  useEffect(() => {
    if (canAddReports) {
      const { userId } = user;
      // this is in case there is an anonymous user.
      if (dashboardId) {
        dispatch(
          fetchUISpecificReport(
            userId,
            'dashboard_id',
            'dashboards',
            dashboardId,
          ),
        );
      } else if (chartId) {
        dispatch(fetchUISpecificReport(userId, 'chart_id', 'charts', chartId));
      }
    }
  }, [user, canAddReports]);

  const menu = () => (
    <Menu selectable={false}>
      <Menu.Item>
        {t('Email reports active')}
        <Switch
          data-test="toggle-active"
          checked={report?.active}
          onClick={(checked: boolean) => toggleActiveKey(report, checked)}
          size="small"
        />
      </Menu.Item>
      <Menu.Item onClick={showReportModal}>{t('Edit email report')}</Menu.Item>
      <Menu.Item
        onClick={() => setCurrentReportDeleting(report)}
        css={deleteColor}
      >
        {t('Delete email report')}
      </Menu.Item>
    </Menu>
  );

  return canAddReports ? (
    report ? (
      <>
        <NoAnimationDropdown
          // ref={ref}
          overlay={menu()}
          trigger={['click']}
          getPopupContainer={(triggerNode: any) =>
            triggerNode.closest('.action-button')
          }
        >
          <span role="button" className="action-button" tabIndex={0}>
            <Icons.Calendar />
          </span>
        </NoAnimationDropdown>
        {currentReportDeleting && (
          <DeleteModal
            description={t(
              'This action will permanently delete %s.',
              currentReportDeleting.name,
            )}
            onConfirm={() => {
              if (currentReportDeleting) {
                handleReportDelete(currentReportDeleting);
              }
            }}
            onHide={() => setCurrentReportDeleting(null)}
            open
            title={t('Delete Report?')}
          />
        )}
      </>
    ) : (
      <>
        <span
          role="button"
          title={t('Schedule email report')}
          tabIndex={0}
          className="action-button"
          onClick={() => setShowAddModal(true)}
        >
          <Icons.Calendar />
        </span>

        <ReportModal
          show={showAddModal}
          onHide={() => setShowAddModal(false)}
          dashboardId={dashboardId}
          chartId={chartId}
        />
      </>
    )
  ) : null;
}
