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
import { SupersetClient } from '@superset-ui/core';
import PropTypes from 'prop-types';
import { Menu, Dropdown } from 'src/common/components';
import Button from 'src/components/Button';
import { t, styled } from '@superset-ui/core';
import ModalTrigger from 'src/components/ModalTrigger';
import { CssEditor as AceCssEditor } from 'src/components/AsyncAceEditor';
import injectCustomCss from 'src/dashboard/util/injectCustomCss';


const StyledWrapper = styled.div`
  ${({ theme }) => `
    .css-editor-header {
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      margin-bottom: ${theme.gridUnit * 2}px;

      h5 {
        margin-top: ${theme.gridUnit}px;
      }
    }
    .css-editor {
      border: 1px solid ${theme.colors.grayscale.light1};
    }
  `}
`;

const propTypes = {
  initialCss: PropTypes.string,
  triggerNode: PropTypes.node.isRequired,
  onChange: PropTypes.func,
  templates: PropTypes.array,
  updateCss: PropTypes.func,
};

const defaultProps = {
  initialCss: '',
  onChange: () => {},
};





// constructor(props) {
//   super(props);
//   this.state = {
//     css: props.customCss,
//     cssTemplates: [],
//   };

//   this.changeCss = this.changeCss.bind(this);
//   this.changeRefreshInterval = this.changeRefreshInterval.bind(this);
//   this.handleMenuClick = this.handleMenuClick.bind(this);
// }


// changeCss(css) {
//   this.setState({ css }, () => {
//     injectCustomCss(css);
//   });
//   this.props.onChange();
//   this.props.updateCss(css);
// }



class CssEditor extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      css: props.initialCss,
      templates: [],
    };
    this.changeCss = this.changeCss.bind(this);
    this.changeCssTemplate = this.changeCssTemplate.bind(this);
  }

  componentDidMount() {
    AceCssEditor.preload();
  }

  changeCss(css) {
    this.setState({ css }, () => {
      this.props.onChange(css);
      this.props.updateCss(css);
      injectCustomCss(css);
    });
  }

  changeCssTemplate({ key }) {
    this.changeCss(key);
  }

  UNSAFE_componentWillMount() {
    injectCustomCss(this.state.css);
    SupersetClient.get({ endpoint: '/csstemplateasyncmodelview/api/read' })
      .then(({ json }) => {
        const templates = json.result.map(row => ({
          value: row.template_name,
          css: row.css,
          label: row.template_name,
        }));
        this.setState({ templates });
      })
      .catch(() => {
        this.props.addDangerToast(
          t('An error occurred while fetching available CSS templates'),
        );
      });
  }


  renderTemplateSelector() {
    if (this.state.templates) {
      const menu = (
        <Menu onClick={this.changeCssTemplate}>
          {this.state.templates.map(template => (
            <Menu.Item key={template.css}>{template.label}</Menu.Item>
          ))}
        </Menu>
      );

      return (
        <Dropdown overlay={menu} placement="bottomRight">
          <Button>{t('Load a CSS template')}</Button>
        </Dropdown>
      );
    }
    return null;
  }

  render() {
    return (
        <StyledWrapper>
          <div className="css-editor-header">
            {this.renderTemplateSelector()}
          </div>
          <AceCssEditor
            className="css-editor"
            minLines={12}
            maxLines={30}
            onChange={this.changeCss}
            height="200px"
            width="100%"
            editorProps={{ $blockScrolling: true }}
            enableLiveAutocompletion
            value={this.state.css || ''}
          />
        </StyledWrapper>
    );
  }
}

CssEditor.propTypes = propTypes;
CssEditor.defaultProps = defaultProps;

export default CssEditor;
