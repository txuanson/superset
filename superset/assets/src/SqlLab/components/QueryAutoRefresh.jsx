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
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { SupersetClient } from '@superset-ui/connection';

import * as Actions from '../actions/sqlLab';

const QUERY_UPDATE_FREQ = 500;
const QUERY_UPDATE_FREQ_MAX = 5000;
const QUERY_UPDATE_BUFFER_MS = 5000;
const MAX_QUERY_AGE_TO_POLL = 21600000;
const QUERY_TIMEOUT_LIMIT = 10000;

class QueryAutoRefresh extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      offline: props.offline,
    };
  }
  componentWillMount() {
    console.log('queryautorefresh componentWillMount', this.props);
    if(this.shouldCheckForQueries()) this.startTimer();
  }
  componentDidUpdate(prevProps) {
    console.log('queryautorefresh componentDidUpdate', prevProps, this.props);
    if (prevProps.offline !== this.state.offline) {
      this.props.actions.setUserOffline(this.state.offline);
    }
    if(this.shouldCheckForQueries()) this.startTimer();
  }
  componentWillUnmount() {
    this.stopTimer();
  }
  shouldCheckForQueries() {
    // if there are started or running queries, this method should return true
    const { queries, queryEditorId } = this.props;
    const now = new Date().getTime();
    const isQueryRunning = q => (
      ['running', 'started', 'pending', 'fetching'].indexOf(q.state) >= 0
    );

    const editorQueries = Object.values(queries).filter(q => q.sqlEditorId === queryEditorId);
    console.log('shouldCheckForQueries query: ', editorQueries);
    // return query && isQueryRunning(query) && now - query.startDttm < MAX_QUERY_AGE_TO_POLL;

    return (
      editorQueries.some(
        q => isQueryRunning(q) &&
        now - q.startDttm < MAX_QUERY_AGE_TO_POLL,
      )
    );
  }
  startTimer(retry_count = 0) {
    if (!this.timer) {
    //    const fn = (retry_count) => {
    //     const delay = QUERY_UPDATE_FREQ*(retry_count*50); // increment by multiples of 50ms
    //     console.log("**delay", delay);
    //     return setTimeout(this.stopwatch.bind(this), delay)
    //   }
    //   this.timer = fn(QUERY_UPDATE_FREQ, 0)
      // this.timer = setInterval(this.stopwatch.bind(this), QUERY_UPDATE_FREQ);

      const delay = Math.min(QUERY_UPDATE_FREQ+(retry_count*50), QUERY_UPDATE_FREQ_MAX); // increment by multiples of 50ms to QUERY_UPDATE_FREQ_MAX
      console.log("retry_count", retry_count, "**delay", delay);
      this.timer = setTimeout(this.stopwatch.bind(this, retry_count), QUERY_UPDATE_FREQ);
    }
  }
  stopTimer() {
    // clearInterval(this.timer);
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
  }
  stopwatch(retry_count = 0) {
    console.log('polling async queries');
    // only poll /superset/queries/ if there are started or running queries
    if (this.shouldCheckForQueries()) {
      console.log('shouldCheckForQueries');
      SupersetClient.get({
        endpoint: `/superset/queries/${this.props.queriesLastUpdate - QUERY_UPDATE_BUFFER_MS}`,   // TODO: new endpoint to fetch only current query
        timeout: QUERY_TIMEOUT_LIMIT,
      }).then(({ json }) => {
        console.log('***** queries', json);
        if (Object.keys(json).length > 0) {
          this.props.actions.refreshQueries(json);  // TODO: refresh only single query for this editor? How does this work with Beto's server-side state?
        }
        this.setState({ offline: false });
      }).catch(() => {
        this.setState({ offline: true });
      }).finally(() => {
        this.stopTimer()
        this.startTimer(++retry_count);
      });
    } else {
      this.stopTimer();
      this.setState({ offline: false });
    }
  }
  render() {
    return null;
  }
}
QueryAutoRefresh.propTypes = {
  offline: PropTypes.bool.isRequired,
  queries: PropTypes.object.isRequired,
  actions: PropTypes.object.isRequired,
  queriesLastUpdate: PropTypes.number.isRequired,
};

function mapStateToProps({ sqlLab }) {
  return {
    offline: sqlLab.offline,
    queries: sqlLab.queries,
    queriesLastUpdate: sqlLab.queriesLastUpdate,
  };
}

function mapDispatchToProps(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
  };
}

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(QueryAutoRefresh);
