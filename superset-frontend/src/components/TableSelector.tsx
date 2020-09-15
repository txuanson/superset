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
import React, { useEffect, useState, ReactNode } from 'react';
import { styled, SupersetClient, t } from '@superset-ui/core';
import { AsyncSelect, CreatableSelect, Select } from 'src/components/Select';

import FormLabel from 'src/components/FormLabel';

import DatabaseSelector from './DatabaseSelector';
import RefreshLabel from './RefreshLabel';

const FieldTitle = styled.p`
  color: ${({ theme }) => theme.colors.secondary.light2};
  font-size: ${({ theme }) => theme.typography.sizes.s}px;
  margin: 20px 0 10px 0;
  text-transform: uppercase;
`;

const TableSelectorWrapper = styled.div`
  .fa-refresh {
    padding-left: 9px;
  }

  .refresh-col {
    display: flex;
    align-items: center;
    width: 30px;
  }

  .section {
    padding-bottom: 5px;
    display: flex;
    flex-direction: row;
  }

  .select {
    flex-grow: 1;
  }

  .divider {
    border-bottom: 1px solid ${({ theme }) => theme.colors.secondary.light5};
    margin: 15px 0;
  }
`;

const TableLabel = styled.span`
  white-space: nowrap;
`;

interface TableSelectorProps {
  clearable?: boolean;
  database?: any;
  dbId: number;
  formMode?: boolean;
  getDbList?: (arg0: any) => {};
  handleError: (msg: string) => void;
  isDatabaseSelectEnabled?: boolean;
  onChange?: ({
    dbId,
    schema,
  }: {
    dbId: number;
    schema?: string;
    tableName?: string;
  }) => void;
  onDbChange?: (db: any) => void;
  onSchemaChange?: (arg0?: any) => {};
  onSchemasLoad?: () => void;
  onTableChange?: (tableName: string, schema: string) => void;
  onTablesLoad?: (options: Array<any>) => {};
  schema?: string;
  sqlLabMode?: boolean;
  tableName?: string;
  tableNameSticky?: boolean;
}

export default function TableSelector({
  database,
  dbId,
  formMode = false,
  getDbList,
  handleError,
  onChange,
  onDbChange,
  onSchemaChange,
  onSchemasLoad,
  onTableChange,
  onTablesLoad,
  schema,
  sqlLabMode = true,
  tableName,
  tableNameSticky = true,
}: TableSelectorProps) {
  const [currentSchema, setCurrentSchema] = useState<string | undefined>(
    schema,
  );
  const [currentTableName, setCurrentTableName] = useState<string | undefined>(
    tableName,
  );
  const [tableLoading, setTableLoading] = useState(false);
  const [tableOptions, setTableOptions] = useState([]);

  function fetchTables(
    dbId?: number,
    schema?: string,
    forceRefresh = false,
    substr = 'undefined',
  ) {
    const databaseId = dbId;
    const dbSchema = currentSchema || schema;
    const encodedSchema = dbSchema && encodeURIComponent(dbSchema);
    const encodedSubstr = encodeURIComponent(substr);
    if (databaseId && dbSchema) {
      setTableLoading(true);
      setTableOptions([]);
      const endpoint = encodeURI(
        `/superset/tables/${databaseId}/${encodedSchema}/${encodedSubstr}/${!!forceRefresh}/`,
      );
      return SupersetClient.get({ endpoint })
        .then(({ json }) => {
          const options = json.options.map((o: any) => ({
            value: o.value,
            schema: o.schema,
            label: o.label,
            title: o.title,
            type: o.type,
          }));
          setTableLoading(false);
          setTableOptions(options);
          if (onTablesLoad) {
            onTablesLoad(json.options);
          }
        })
        .catch(() => {
          setTableLoading(false);
          setTableOptions([]);
          handleError(t('Error while fetching table list'));
        });
    }
    setTableLoading(false);
    setTableOptions([]);
    return Promise.resolve();
  }

  useEffect(() => {
    if (dbId) {
      fetchTables();
    }
  }, [dbId]);

  function onSelectionChange() {
    if (onChange) {
      onChange({
        dbId,
        schema: currentSchema,
        tableName: currentTableName,
      });
    }
  }

  function getTableNamesBySubStr(substr = 'undefined') {
    if (!dbId || !substr) {
      const options: any[] = [];
      return Promise.resolve({ options });
    }
    const encodedSchema = encodeURIComponent(schema || '');
    const encodedSubstr = encodeURIComponent(substr);
    return SupersetClient.get({
      endpoint: encodeURI(
        `/superset/tables/${dbId}/${encodedSchema}/${encodedSubstr}`,
      ),
    }).then(({ json }) => {
      const options = json.options.map((o: any) => ({
        value: o.value,
        schema: o.schema,
        label: o.label,
        title: o.title,
        type: o.type,
      }));
      return { options };
    });
  }

  function changeTable(tableOpt: any) {
    if (!tableOpt) {
      setCurrentTableName('');
      return;
    }
    const schemaName = tableOpt.schema;
    const tableOptTableName = tableOpt.value;
    if (tableNameSticky) {
      onSelectionChange();
      setCurrentTableName(tableOptTableName);
    }
    if (onTableChange) {
      onTableChange(tableOptTableName, schemaName);
    }
  }

  function changeSchema(schemaOpt: any, force = false) {
    const schema = schemaOpt ? schemaOpt.value : null;
    if (onSchemaChange) {
      onSchemaChange(schema);
    }
    setCurrentSchema(schema);
    onSelectionChange();
    fetchTables(dbId, currentSchema, force);
  }

  function renderTableOption(option: any) {
    return (
      <TableLabel title={option.label}>
        <span className="m-r-5">
          <small className="text-muted">
            <i
              className={`fa fa-${option.type === 'view' ? 'eye' : 'table'}`}
            />
          </small>
        </span>
        {option.label}
      </TableLabel>
    );
  }

  function renderSelectRow(select: ReactNode, refreshBtn: ReactNode) {
    return (
      <div className="section">
        <span className="select">{select}</span>
        <span className="refresh-col">{refreshBtn}</span>
      </div>
    );
  }

  function renderDatabaseSelector() {
    return (
      <DatabaseSelector
        dbId={dbId}
        schema={currentSchema}
        onSchemaChange={onSchemaChange}
        onDbChange={onDbChange}
        onSchemasLoad={onSchemasLoad}
        getDbList={getDbList}
        getTableList={fetchTables}
        formMode={formMode}
        onChange={onSelectionChange}
        handleError={handleError}
      />
    );
  }

  function renderTableSelect() {
    let tableSelectPlaceholder;
    let tableSelectDisabled = false;
    if (database && database.allow_multi_schema_metadata_fetch) {
      tableSelectPlaceholder = t('Type to search ...');
    } else {
      tableSelectPlaceholder = t('Select table ');
      tableSelectDisabled = true;
    }
    const options = tableOptions;

    let select = null;
    if (currentSchema && !formMode) {
      select = (
        <Select
          name="select-table"
          isLoading={tableLoading}
          ignoreAccents={false}
          placeholder={t('Select table or type table name')}
          autosize={false}
          onChange={changeTable}
          options={options}
          value={currentTableName}
          optionRenderer={renderTableOption}
        />
      );
    } else if (formMode) {
      select = (
        <CreatableSelect
          name="select-table"
          isLoading={tableLoading}
          ignoreAccents={false}
          placeholder={t('Select table or type table name')}
          autosize={false}
          onChange={changeTable}
          options={options}
          value={currentTableName}
          optionRenderer={renderTableOption}
        />
      );
    } else {
      select = (
        <AsyncSelect
          name="async-select-table"
          placeholder={tableSelectPlaceholder}
          isDisabled={tableSelectDisabled}
          autosize={false}
          onChange={changeTable}
          value={currentTableName}
          loadOptions={getTableNamesBySubStr}
          optionRenderer={renderTableOption}
        />
      );
    }
    const refresh = !formMode && (
      <RefreshLabel
        onClick={() => changeSchema({ value: schema }, true)}
        tooltipContent={t('Force refresh table list')}
      />
    );
    return renderSelectRow(select, refresh);
  }

  function renderSeeTableLabel() {
    return (
      <div className="section">
        <FormLabel>
          {t('See table schema')}{' '}
          {schema && (
            <small>
              ({tableOptions.length} in <i>{schema}</i>)
            </small>
          )}
        </FormLabel>
      </div>
    );
  }

  return (
    <TableSelectorWrapper>
      {renderDatabaseSelector()}
      {!formMode && <div className="divider" />}
      {sqlLabMode && renderSeeTableLabel()}
      {formMode && <FieldTitle>{t('Table')}</FieldTitle>}
      {renderTableSelect()}
    </TableSelectorWrapper>
  );
}
