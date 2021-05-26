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
import {
  buildQueryContext,
  GenericDataType,
  QueryObject,
  QueryObjectFilterClause,
} from '@superset-ui/core';
import { BuildQuery } from '@superset-ui/core/lib/chart/registries/ChartBuildQueryRegistrySingleton';
import { DEFAULT_FORM_DATA, PluginFilterSelectQueryFormData } from './types';

const buildQuery: BuildQuery<PluginFilterSelectQueryFormData> = (
  formData: PluginFilterSelectQueryFormData,
  options,
) => {
  const { search, coltypeMap } = options?.ownState || {};
  const { sortAscending, sortMetric } = { ...DEFAULT_FORM_DATA, ...formData };
  return buildQueryContext(formData, baseQueryObject => {
    const { columns = [], filters = [] } = baseQueryObject;
    const extra_filters: QueryObjectFilterClause[] = columns.map(column => {
      if (search && coltypeMap[column] === GenericDataType.STRING) {
        return {
          col: column,
          op: 'ILIKE',
          val: `%${search}%`,
        };
      }
      if (
        search &&
        coltypeMap[column] === GenericDataType.NUMERIC &&
        !Number.isNaN(Number(search))
      ) {
        // for numeric columns we apply a >= where clause
        return {
          col: column,
          op: '>=',
          val: Number(search),
        };
      }
      // if no search is defined, make sure the col value is not null
      return { col: column, op: 'IS NOT NULL' };
    });

    const sortColumns = sortMetric ? [sortMetric] : columns;
    const query: QueryObject[] = [
      {
        ...baseQueryObject,
        apply_fetch_values_predicate: true,
        groupby: columns,
        metrics: sortMetric ? [sortMetric] : [],
        filters: filters.concat(extra_filters),
        orderby:
          sortMetric || sortAscending !== undefined
            ? sortColumns.map(column => [column, !!sortAscending])
            : [],
      },
    ];
    return query;
  });
};

export default buildQuery;
