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
/* eslint-env browser */
import React from 'react';
import Tabs from 'src/components/Tabs';
import { StickyContainer, Sticky } from 'react-sticky';
import { ParentSize } from '@vx/responsive';

import { t, styled, css } from '@superset-ui/core';

import { JsonEditor } from 'src/components/AsyncAceEditor';
import ColorSchemeControlWrapper from 'src/dashboard/components/ColorSchemeControlWrapper';
import { Select } from 'src/components';
import { Form, FormItem } from 'src/components/Form';
import { Input } from 'src/common/components';
import Button from 'src/components/Button';
import NewColumn from './gridComponents/new/NewColumn';
import NewDivider from './gridComponents/new/NewDivider';
import NewHeader from './gridComponents/new/NewHeader';
import NewRow from './gridComponents/new/NewRow';
import NewTabs from './gridComponents/new/NewTabs';
import NewMarkdown from './gridComponents/new/NewMarkdown';
import SliceAdder from '../containers/SliceAdder';
import CssEditor from './CssEditor';

export interface BCPProps {
  topOffset: number;
  updateCss: () => void;
  onChange: () => void;
  customCss: string;
}

const SUPERSET_HEADER_HEIGHT = 59;

const GeneralTabs = styled(Tabs)`
  line-height: inherit;
  > .ant-tabs-nav {
    margin: 0;
    width: fit-content;
  }
  height: 100%;
`;
const SpecificTabs = styled(Tabs)`
  line-height: inherit;
  background: white;
  padding: 8px;
`;

const StyledJsonEditor = styled(JsonEditor)`
  border-radius: ${({ theme }) => theme.borderRadius}px;
  border: 1px solid ${({ theme }) => theme.colors.secondary.light2};
`;

const BSProperties: React.FC<> = () => (
  <>
    {/* SMOKE AND MIRRORS */}
    <Form
      data-test="dashboard-edit-properties-form"
      // onSubmit={this.submit}
      layout="vertical"
    >
      <h3>{t('Basic information')}</h3>
      <FormItem label={t('Title')}>
        <Input
          data-test="dashboard-title-input"
          name="dashboard_title"
          type="text"
          value="Dashboard Title"
          // onChange={this.onChange}
          disabled={false}
        />
      </FormItem>
      <FormItem label={t('URL slug')}>
        <Input
          name="slug"
          type="text"
          value="Dashboard slug"
          // onChange={this.onChange}
          disabled={false}
        />
        <p className="help-block">{t('A readable URL for your dashboard')}</p>
      </FormItem>
      <h3 style={{ marginTop: '1em' }}>{t('Access')}</h3>
      <FormItem label={t('Owners')}>
        <Select
          allowClear
          ariaLabel={t('Owners')}
          disabled={false}
          name="owners"
          mode="multiple"
          value={[]}
          options={() => new Promise(() => [])}
          // onChange={this.onOwnersChange}
        />
        <p className="help-block">
          {t(
            'Owners is a list of users who can alter the dashboard. Searchable by name or username.',
          )}
        </p>
      </FormItem>
      <h3 style={{ marginTop: '1em' }}>{t('Colors')}</h3>
      <ColorSchemeControlWrapper
        // onChange={this.onColorSchemeChange}
        colorScheme="supersetColors" // TODO Spoof this!
        labelMargin={4}
      />
      <h3 style={{ marginTop: '1em' }}>
        <Button
          buttonStyle="link"
          // onClick={this.toggleAdvanced}
        >
          <i
            className={`fa fa-angle-${
              // isAdvancedOpen ? 'down' : 'right'
              'down'
            }`}
            style={{ minWidth: '1em' }}
          />
          {t('Advanced')}
        </Button>
      </h3>
      <FormItem label={t('JSON metadata')}>
        <StyledJsonEditor
          showLoadingForImport
          name="json_metadata"
          // defaultValue={this.defaultMetadataValue}
          // value={values.json_metadata}
          // onChange={this.onMetadataChange}
          tabSize={2}
          width="100%"
          height="200px"
          wrapEnabled
        />
        <p className="help-block">
          {t(
            'This JSON object is generated dynamically when clicking the save or overwrite button in the dashboard view. It is exposed here for reference and for power users who may want to alter specific parameters.',
          )}
        </p>
      </FormItem>
    </Form>
    {/* END SMOKE AND MIRRORS */}
  </>
);

const BuilderComponentPane: React.FC<BCPProps> = ({
  topOffset = 0,
  updateCss,
  onChange,
  customCss,
}) => (
  <div
    className="dashboard-builder-sidepane"
    style={{
      height: `calc(100vh - ${topOffset + SUPERSET_HEADER_HEIGHT}px)`,
    }}
  >
    <ParentSize>
      {({ height }) => (
        <StickyContainer>
          <Sticky topOffset={-topOffset} bottomOffset={Infinity}>
            {({ style, isSticky }: { style: any; isSticky: boolean }) => (
              <div
                className="viewport"
                style={isSticky ? { ...style, top: topOffset } : null}
              >
                <h5
                  style={{
                    margin: '12px 6px',
                    fontSize: '14px',
                  }}
                >
                  {t('Edit Dashboard')}
                </h5>
                <GeneralTabs type="card">
                  <Tabs.TabPane key={1} tab={t('Content')}>
                    <SpecificTabs
                      id="tabs"
                      className="tabs-components"
                      data-test="dashboard-builder-component-pane-tabs-navigation"
                    >
                      <Tabs.TabPane key={1} tab={t('Components')}>
                        <NewTabs />
                        <NewRow />
                        <NewColumn />
                        <NewHeader />
                        <NewMarkdown />
                        <NewDivider />
                      </Tabs.TabPane>
                      <Tabs.TabPane
                        key={2}
                        tab={t('Charts')}
                        className="tab-charts"
                      >
                        <SliceAdder
                          height={
                            height + (isSticky ? SUPERSET_HEADER_HEIGHT : 0)
                          }
                        />
                      </Tabs.TabPane>
                    </SpecificTabs>
                  </Tabs.TabPane>
                  <Tabs.TabPane key={2} tab={t('Customize')}>
                    <SpecificTabs>
                      <Tabs.TabPane key={1} tab={t('Properties')}>
                        <BSProperties />
                      </Tabs.TabPane>
                      <Tabs.TabPane key={2} tab={t('CSS')}>
                        <CssEditor
                          triggerNode={<span>{t('Edit CSS')}</span>}
                          initialCss={customCss}
                          onChange={onChange}
                          updateCss={updateCss}
                          css={css`
                            position: absolute;
                            top: 0;
                            right: 0;
                            bottom: 0;
                            left: 0;
                          `}
                        />
                      </Tabs.TabPane>
                    </SpecificTabs>
                  </Tabs.TabPane>
                </GeneralTabs>
              </div>
            )}
          </Sticky>
        </StickyContainer>
      )}
    </ParentSize>
  </div>
);

export default BuilderComponentPane;
