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
const packageConfig = require('./package.json');

module.exports = {
  sourceMaps: true,
  sourceType: 'module',
  retainLines: true,
  presets: [
    [
      '@babel/preset-env',
      {
        corejs: 3,
        useBuiltIns: 'usage',
        loose: true,
        shippedProposals: true,
        modules: false,
        targets: packageConfig.browserslist,
      },
    ],
    '@babel/preset-react',
  ],
  plugins: [
    'lodash',
    '@babel/plugin-syntax-dynamic-import',
    '@babel/plugin-proposal-class-properties',
    '@babel/plugin-proposal-optional-chaining',
    ['@babel/plugin-transform-runtime', { corejs: 3 }],
    'react-hot-loader/babel',
  ],
  overrides: [
    {
      test: /\.tsx?/,
      presets: [
        ['@babel/preset-typescript', { isTSX: true, allExtensions: true }],
      ],
    },
  ],
  env: {
    // Setup a different config for tests as they run in node instead of a browser
    test: {
      presets: [
        [
          '@babel/preset-env',
          {
            useBuiltIns: 'usage',
            corejs: 3,
            loose: true,
            shippedProposals: true,
            targets: { node: 'current' },
            modules: 'commonjs',
          },
        ],
      ],
      plugins: ['babel-plugin-dynamic-import-node'],
    },
  },
};
