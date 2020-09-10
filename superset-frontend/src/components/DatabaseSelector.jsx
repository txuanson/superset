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
import React from 'react';
import { styled, SupersetClient, t } from '@superset-ui/core';
import PropTypes from 'prop-types';
import rison from 'rison';
import { AsyncSelect, CreatableSelect, Select } from 'src/components/Select';

import Label from 'src/components/Label';
import FormLabel from 'src/components/FormLabel';

import SupersetAsyncSelect from './AsyncSelect';
import RefreshLabel from './RefreshLabel';
import './TableSelector.less';

const FieldTitle = styled.p`
  color: ${({ theme }) => theme.colors.secondary.light2};
  font-size: ${({ theme }) => theme.typography.sizes.s}px;
  margin: 20px 0 10px 0;
  text-transform: uppercase;
`;

const propTypes = {
  dbId: PropTypes.number.isRequired,
  schema: PropTypes.string,
  onSchemaChange: PropTypes.func,
  onDbChange: PropTypes.func,
  onSchemasLoad: PropTypes.func,
  getDbList: PropTypes.func,
  database: PropTypes.object,
  sqlLabMode: PropTypes.bool,
  formMode: PropTypes.bool,
  onChange: PropTypes.func,
  clearable: PropTypes.bool,
  handleError: PropTypes.func.isRequired,
};

const defaultProps = {
  onDbChange: () => {},
  onSchemaChange: () => {},
  onSchemasLoad: () => {},
  getDbList: () => {},
  onChange: () => {},
  sqlLabMode: true,
  formMode: false,
  clearable: true,
};

export default class DatabaseSelector extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      schemaLoading: false,
      schemaOptions: [],
      dbId: props.dbId,
      schema: props.schema,
    };
    this.onDatabaseChange = this.onDatabaseChange.bind(this);
    this.onSchemaChange = this.onSchemaChange.bind(this);
    this.dbMutator = this.dbMutator.bind(this);
    this.onChange = this.onChange.bind(this);
  }

  componentDidMount() {
    if (this.state.dbId) {
      this.fetchSchemas(this.state.dbId);
    }
  }

  onChange() {
    this.props.onChange({
      dbId: this.state.dbId,
      schema: this.state.schema,
      tableName: this.state.tableName,
    });
  }

  onDatabaseChange(db, force) {
    return this.changeDataBase(db, force);
  }

  onSchemaChange(schemaOpt) {
    return this.changeSchema(schemaOpt);
  }

  dbMutator(data) {
    this.props.getDbList(data.result);
    if (data.result.length === 0) {
      this.props.handleError(
        t("It seems you don't have access to any database"),
      );
    }
    return data.result.map(row => ({
      ...row,
      // label is used for the typeahead
      label: `${row.backend} ${row.database_name}`,
    }));
  }

  fetchSchemas(dbId, forceRefresh = false) {
    const actualDbId = dbId || this.props.dbId;
    if (actualDbId) {
      this.setState({ schemaLoading: true });
      const queryParams = rison.encode({
        force: Boolean(forceRefresh),
      });
      const endpoint = `/api/v1/database/${actualDbId}/schemas/?q=${queryParams}`;
      return SupersetClient.get({ endpoint })
        .then(({ json }) => {
          const schemaOptions = json.result.map(s => ({
            value: s,
            label: s,
            title: s,
          }));
          this.setState({ schemaOptions, schemaLoading: false });
          this.props.onSchemasLoad(schemaOptions);
        })
        .catch(() => {
          this.setState({ schemaLoading: false, schemaOptions: [] });
          this.props.handleError(t('Error while fetching schema list'));
        });
    }
    return Promise.resolve();
  }

  changeDataBase(db, force = false) {
    const dbId = db ? db.id : null;
    this.setState({ schemaOptions: [] });
    this.props.onSchemaChange(null);
    this.props.onDbChange(db);
    this.fetchSchemas(dbId, force);
    this.setState({ dbId, schema: null }, this.onChange);
  }

  changeSchema(schemaOpt, force = false) {
    const schema = schemaOpt ? schemaOpt.value : null;
    this.props.onSchemaChange(schema);
    this.setState({ schema }, () => {
      this.onChange();
    });
  }

  renderDatabaseOption(db) {
    return (
      <span title={db.database_name}>
        <Label bsStyle="default">{db.backend}</Label>
        {db.database_name}
      </span>
    );
  }

  renderSelectRow(select, refreshBtn) {
    return (
      <div className="section">
        <span className="select">{select}</span>
        <span className="refresh-col">{refreshBtn}</span>
      </div>
    );
  }

  renderDatabaseSelect() {
    const queryParams = rison.encode({
      order_columns: 'database_name',
      order_direction: 'asc',
      page: 0,
      page_size: -1,
      ...(this.props.formMode
        ? {}
        : {
            filters: [
              {
                col: 'expose_in_sqllab',
                opr: 'eq',
                value: true,
              },
            ],
          }),
    });

    return this.renderSelectRow(
      <SupersetAsyncSelect
        dataEndpoint={`/api/v1/database/?q=${queryParams}`}
        onChange={this.onDatabaseChange}
        onAsyncError={() =>
          this.props.handleError(t('Error while fetching database list'))
        }
        clearable={false}
        value={this.state.dbId}
        valueKey="id"
        valueRenderer={db => (
          <div>
            <span className="text-muted m-r-5">{t('Database:')}</span>
            {this.renderDatabaseOption(db)}
          </div>
        )}
        optionRenderer={this.renderDatabaseOption}
        mutator={this.dbMutator}
        placeholder={t('Select a database')}
        autoSelect
      />,
    );
  }

  renderSchemaSelect() {
    const refresh = !this.props.formMode && (
      <RefreshLabel
        onClick={() => this.onDatabaseChange({ id: this.props.dbId }, true)}
        tooltipContent={t('Force refresh schema list')}
      />
    );
    return this.renderSelectRow(
      <Select
        name="select-schema"
        placeholder={t('Select a schema (%s)', this.state.schemaOptions.length)}
        options={this.state.schemaOptions}
        value={this.props.schema}
        valueRenderer={o => (
          <div>
            <span className="text-muted">{t('Schema:')}</span> {o.label}
          </div>
        )}
        isLoading={this.state.schemaLoading}
        autosize={false}
        onChange={this.onSchemaChange}
      />,
      refresh,
    );
  }

  render() {
    return (
      <div className="DatabaseSelector">
        {this.props.formMode && <FieldTitle>{t('datasource')}</FieldTitle>}
        {this.renderDatabaseSelect()}
        {this.props.formMode && <FieldTitle>{t('schema')}</FieldTitle>}
        {this.renderSchemaSelect()}
      </div>
    );
  }
}
DatabaseSelector.propTypes = propTypes;
DatabaseSelector.defaultProps = defaultProps;
