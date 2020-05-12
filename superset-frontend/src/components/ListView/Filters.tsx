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
import React, { useState, useEffect } from 'react';
import styled from '@superset-ui/style';
import { withTheme } from 'emotion-theming';
import { debounce } from 'lodash';

import StyledSelect from 'src/components/StyledSelect';
import SearchInput from 'src/components/SearchInput';
import { Filter, Filters, FilterValue, InternalFilter } from './types';

interface BaseFilter {
  Header: string;
  initialValue: any;
}
interface SelectFilterProps extends BaseFilter {
  onSelect: (selected: any) => any;
  selects: Filter['selects'];
  emptyLabel?: string;
}

interface SelectFilterAsyncProps extends SelectFilterProps {
  fetchSelects?: Filter['fetchSelects'];
}

const FilterContainer = styled.div`
  display: inline-flex;
  margin-right: 8px;
`;

const Title = styled.span`
  font-weight: bold;
`;

const CLEAR_SELECT_FILTER_VALUE = 'CLEAR_SELECT_FILTER_VALUE';

function SelectFilter({
  Header,
  selects = [],
  emptyLabel = 'None',
  initialValue,
  onSelect,
}: SelectFilterProps) {
  const clearFilterSelect = {
    label: emptyLabel,
    value: CLEAR_SELECT_FILTER_VALUE,
  };

  const options = React.useMemo(() => [clearFilterSelect, ...selects], [
    emptyLabel,
    selects,
  ]);

  const [value, setValue] = useState(
    typeof initialValue === 'undefined'
      ? clearFilterSelect.value
      : initialValue,
  );

  const onChange = (selected: { label: string; value: any } | null) => {
    if (selected === null) return;
    setValue(selected.value);
    onSelect(
      selected.value === CLEAR_SELECT_FILTER_VALUE ? undefined : selected.value,
    );
  };

  return (
    <FilterContainer>
      <Title>{Header}:</Title>
      <StyledSelect
        data-test="filters-select"
        value={value}
        options={options}
        onChange={onChange}
        clearable={false}
      />
    </FilterContainer>
  );
}

const DEFAULT_PAGE_SIZE = 20;
function SelectFilterAsync({
  Header,
  emptyLabel = 'None',
  initialValue,
  onSelect,
  fetchSelects,
}: SelectFilterAsyncProps) {
  const clearFilterSelect = {
    label: emptyLabel,
    value: CLEAR_SELECT_FILTER_VALUE,
  };

  const [options = [], setOptions] = useState<Filter['selects']>([
    clearFilterSelect,
  ]);
  const [pageIndex, setPageIndex] = useState<number>(0);
  const [filterValue, setFilterValue] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const fetchAndSaveSelects = async () => {
    if (!fetchSelects) return;
    const loadingTimeout = setTimeout(() => setLoading(true), 500);
    const fetchedSelectValues = await fetchSelects(
      pageIndex,
      DEFAULT_PAGE_SIZE,
      filterValue,
    );
    clearTimeout(loadingTimeout);
    setPageIndex(pageIndex + 1);
    setOptions([...options, ...fetchedSelectValues]);
    setLoading(false);
  };

  const filterSelects = debounce(async (val: string) => {
    if (filterValue === val) return;
    setFilterValue(val);
    if (!fetchSelects) return;
    const loadingTimeout = setTimeout(() => setLoading(true), 500);
    const fetchedSelectValues = await fetchSelects(0, DEFAULT_PAGE_SIZE, val);
    clearTimeout(loadingTimeout);
    setPageIndex(1);
    const head =
      clearFilterSelect.label.toLowerCase().indexOf(val.toLowerCase()) >= 0 ||
      !val
        ? [clearFilterSelect]
        : [];
    setOptions([...head, ...fetchedSelectValues]);
    setLoading(false);
  }, 250);

  useEffect(() => {
    fetchAndSaveSelects();
  }, []);

  const [value, setValue] = useState(
    typeof initialValue === 'undefined'
      ? clearFilterSelect.value
      : initialValue,
  );

  const onChange = (selected: { label: string; value: any } | null) => {
    if (selected === null) return;
    setValue(selected.value);
    onSelect(
      selected.value === CLEAR_SELECT_FILTER_VALUE ? undefined : selected.value,
    );
  };

  return (
    <FilterContainer>
      <Title>{Header}:</Title>
      <StyledSelect
        data-test="filters-select"
        value={value}
        onChange={onChange}
        options={options}
        onMenuScrollToBottom={fetchAndSaveSelects}
        onInputChange={val => {
          filterSelects(val);
          return val;
        }}
        filterOptions={() => options}
        placeholder={initialValue || emptyLabel}
        isLoading={loading}
        clearable={false}
      />
    </FilterContainer>
  );
}

interface SearchHeaderProps extends BaseFilter {
  Header: string;
  onSubmit: (val: string) => void;
}

function SearchFilter({ Header, initialValue, onSubmit }: SearchHeaderProps) {
  const [value, setValue] = useState(initialValue || '');
  const handleSubmit = () => onSubmit(value);
  const onClear = () => {
    setValue('');
    onSubmit('');
  };

  return (
    <FilterContainer>
      <SearchInput
        data-test="filters-search"
        placeholder={Header}
        value={value}
        onChange={e => {
          setValue(e.currentTarget.value);
        }}
        onSubmit={handleSubmit}
        onClear={onClear}
      />
    </FilterContainer>
  );
}

interface UIFiltersProps {
  filters: Filters;
  internalFilters: InternalFilter[];
  updateFilterValue: (id: number, value: FilterValue['value']) => void;
}

const FilterWrapper = styled.div`
  padding: 24px 16px 8px;
`;

function UIFilters({
  filters,
  internalFilters = [],
  updateFilterValue,
}: UIFiltersProps) {
  return (
    <FilterWrapper>
      {filters.map(
        ({ Header, input, selects, unfilteredLabel, fetchSelects }, index) => {
          const initialValue =
            internalFilters[index] && internalFilters[index].value;
          if (input === 'select') {
            if (typeof fetchSelects === 'function') {
              return (
                <SelectFilterAsync
                  key={Header}
                  Header={Header}
                  selects={selects}
                  emptyLabel={unfilteredLabel}
                  initialValue={initialValue}
                  fetchSelects={fetchSelects}
                  onSelect={(value: any) => updateFilterValue(index, value)}
                />
              );
            }

            return (
              <SelectFilter
                key={Header}
                Header={Header}
                selects={selects}
                emptyLabel={unfilteredLabel}
                initialValue={initialValue}
                onSelect={(value: any) => updateFilterValue(index, value)}
              />
            );
          }
          if (input === 'search') {
            return (
              <SearchFilter
                key={Header}
                Header={Header}
                initialValue={initialValue}
                onSubmit={(value: string) => updateFilterValue(index, value)}
              />
            );
          }
          return null;
        },
      )}
    </FilterWrapper>
  );
}

export default withTheme(UIFilters);
