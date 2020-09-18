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
import React, { useCallback, useState } from 'react';
import {
  Panel,
  Row,
  Col,
  Tabs,
  Tab,
  FormControl,
  FormControlProps,
} from 'react-bootstrap';
import { t } from '@superset-ui/core';
import { useQueryParam, StringParam, QueryParamConfig } from 'use-query-params';
import { User } from 'src/types/bootstrapTypes';
import RecentActivity from 'src/profile/components/RecentActivity';
import Favorites from 'src/profile/components/Favorites';
import SavedQueries from './SavedQueries';
import DashboardTable from './DashboardTable';

const { Panel } = Collapse;

interface WelcomeProps {
  user: User;
}

function useSyncQueryState(
  queryParam: string,
  queryParamType: QueryParamConfig<
    string | null | undefined,
    string | undefined
  >,
  defaultState: string,
): [string, (val: string) => void] {
  const [queryState, setQueryState] = useQueryParam(queryParam, queryParamType);
  const [state, setState] = useState(queryState || defaultState);

  const setQueryStateAndState = (val: string) => {
    setQueryState(val);
    setState(val);
  };

  return [state, setQueryStateAndState];
}

function ding(e: any) {
  console.log('event',e);
}

export default function Welcome({ user }: WelcomeProps) {
  const [activeTab, setActiveTab] = useSyncQueryState(
    'activeTab',
    StringParam,
    'all',
  );
  const [dashboardFilter, setDashboardFilter] = useState('Favorite');
  const [searchQuery, setSearchQuery] = useSyncQueryState(
    'search',
    StringParam,
    '',
  );

  const onFormControlChange = useCallback(
    (e: React.FormEvent<FormControl & FormControlProps>) => {
      const { value } = e.currentTarget;
      setSearchQuery((value as string) ?? '');
    },
    [],
  );

  const onTabsSelect = useCallback((e: any) => {
    setActiveTab(e as string);
  }, []);

  return (
    <Collapse defaultActiveKey={['1']}>
      <Panel header={t('Recents')} key="1">
        <SubMenu
          activeChild="Viewed"
          name=""
          // eslint-disable-next-line react/no-children-prop
          children={[
            {
              name: 'Viewed',
              label: t('Viewed'),
              onClick: () => ding('hi?'),
            },
            {
              name: 'Edited',
              label: t('Edited'),
              onClick: ding,
            },
            {
              name: 'Created',
              label: t('Created'),
              onClick: ding,
            },
          ]}
        />
        <RecentActivity user={user} />
      </Panel>

      <Panel header={t('Dashboards')} key="2">
      <SubMenu
          activeChild={dashboardFilter}
          name=""
          // eslint-disable-next-line react/no-children-prop
          children={[
            {
              name: 'Favorite',
              label: t('Favorite'),
              onClick: () => setDashboardFilter('Favorite'),
            },
            {
              name: 'Mine',
              label: t('Mine'),
              onClick: () => setDashboardFilter('Mine'),
            },
          ]}
        />
        <FormControl
          type="text"
          bsSize="sm"
          placeholder="Search"
          value={searchQuery}
          // @ts-ignore React bootstrap types aren't quite right here
          onChange={e => setSearchQuery(e.currentTarget.value)}
        />
        <DashboardTable search={searchQuery} filter={dashboardFilter} />
      </Panel>

      <Panel header={t('Saved Queries')} key="3" >
        <SavedQueries />
      </Panel>
      <Panel header={t('Charts')} key="4" >
        Stuff here!
      </Panel>
    </Collapse>
    /*
    <div className="container welcome">
      <Tabs
        activeKey={activeTab}
        onSelect={onTabsSelect}
        id="uncontrolled-tab-example"
      >
        <Tab eventKey="all" title={t('Dashboards')}>
          <Panel>
            <Panel.Body>
              <Row>
                <Col md={8}>
                  <h2>{t('Dashboards')}</h2>
                </Col>
                <Col md={4}>
                  <FormControl
                    type="text"
                    bsSize="sm"
                    style={{ marginTop: '25px' }}
                    placeholder="Search"
                    value={searchQuery}
                    onChange={onFormControlChange}
                  />
                </Col>
              </Row>
              <hr />
              <DashboardTable search={searchQuery} />
            </Panel.Body>
          </Panel>
        </Tab>
        <Tab eventKey="recent" title={t('Recently Viewed')}>
          <Panel>
            <Panel.Body>
              <Row>
                <Col md={8}>
                  <h2>{t('Recently Viewed')}</h2>
                </Col>
              </Row>
              <hr />
              <RecentActivity user={user} />
            </Panel.Body>
          </Panel>
        </Tab>
        <Tab eventKey="favorites" title={t('Favorites')}>
          <Panel>
            <Panel.Body>
              <Row>
                <Col md={8}>
                  <h2>{t('Favorites')}</h2>
                </Col>
              </Row>
              <hr />
              <Favorites user={user} />
            </Panel.Body>
          </Panel>
        </Tab>
      </Tabs>
    </div>
    */
  );
}
