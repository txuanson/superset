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
import PropTypes from 'prop-types';
import { ButtonGroup } from 'react-bootstrap';
import { t, styled } from '@superset-ui/core';

import { Tooltip } from 'src/common/components/Tooltip';
import Button from 'src/components/Button';

const propTypes = {
  canAdd: PropTypes.bool.isRequired,
  onQuery: PropTypes.func.isRequired,
  onSave: PropTypes.func,
  onStop: PropTypes.func,
  loading: PropTypes.bool,
  chartIsStale: PropTypes.bool,
  errorMessage: PropTypes.node,
};

const defaultProps = {
  onStop: () => {},
  onSave: () => {},
};

const Styles = styled.div`
  justify-content: space-around;
  display: flex;
  flex-shrink: 0;
  flex-direction: row;
  align-items: center;
  padding: ${({ theme }) => 2 * theme.gridUnit}px;
  border-top: 1px solid ${({ theme }) => theme.colors.grayscale.light2};
  .btn {
    /* just to make sure buttons don't jiggle */
    width: 100px;
  }
`;

export default function QueryAndSaveBtns({
  canAdd,
  onQuery,
  onSave,
  onStop,
  loading,
  chartIsStale,
  errorMessage,
}) {
  let qryButtonStyle = 'primary';
  if (errorMessage) {
    qryButtonStyle = 'danger';
  } else if (chartIsStale) {
    qryButtonStyle = 'primary';
  }

  const saveButtonDisabled = errorMessage ? true : loading;
  const qryOrStopButton = loading ? (
    <Button
      onClick={onStop}
      buttonStyle="warning"
      buttonSize="small"
      disabled={!canAdd}
    >
      <i className="fa fa-stop-circle-o" /> {t('Stop')}
    </Button>
  ) : (
    <Button
      buttonSize="small"
      onClick={onQuery}
      buttonStyle={qryButtonStyle}
      disabled={!!errorMessage}
      data-test="run-query-button"
    >
      <i className="fa fa-bolt" /> {t('Run')}
    </Button>
  );

  return (
    <Styles>
      <div>
        <ButtonGroup className="query-and-save">
          {qryOrStopButton}
          <Button
            buttonStyle="secondary"
            buttonSize="small"
            data-target="#save_modal"
            data-toggle="modal"
            disabled={saveButtonDisabled}
            onClick={onSave}
            data-test="query-save-button"
          >
            <i className="fa fa-plus-circle" /> {t('Save')}
          </Button>
        </ButtonGroup>
        {errorMessage && (
          <span>
            {' '}
            <Tooltip
              id="query-error-tooltip"
              placement="right"
              title={errorMessage}
            >
              <i className="fa fa-exclamation-circle text-danger fa-lg" />
            </Tooltip>
          </span>
        )}
      </div>
    </Styles>
  );
}

QueryAndSaveBtns.propTypes = propTypes;
QueryAndSaveBtns.defaultProps = defaultProps;
