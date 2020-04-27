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
import styled, { supersetTheme } from '@superset-ui/style';
import { ReactComponent as CardViewImg } from 'images/icons/cardview_icon.svg';
import { ReactComponent as ListivewImg } from 'images/icons/listview_icon.svg';

interface Props {
  value: string;
  onChange: (newVal: 'listview' | 'cardview') => any;
}

interface IconProps {
  isSelected: boolean;
  theme: typeof supersetTheme;
}

const Button = styled.button`
  padding: 4px 8px;
  margin: 0 4px;
  background-color: ${(props: IconProps) =>
    props.isSelected ? props.theme.colors.secondary.dark1 : 'transparent'};
  border-radius: ${(props: IconProps) => props.theme.borderRadius};
  border: none;
`;

const CardViewIcon = styled(CardViewImg)`
  fill: ${(props: IconProps) =>
    props.isSelected
      ? props.theme.colors.secondary.light5
      : props.theme.colors.secondary.dark3};
`;

const ListivewIcon = styled(ListivewImg)`
  fill: ${(props: IconProps) =>
    props.isSelected
      ? props.theme.colors.secondary.light5
      : props.theme.colors.secondary.dark3};
`;

export default function ListCardViewtoggle({
  value = 'listview',
  onChange,
}: Props) {
  return (
    <div>
      <Button
        isSelected={value === 'cardview'}
        onClick={() => onChange('cardview')}
      >
        <CardViewIcon isSelected={value === 'cardview'} />
      </Button>
      <Button
        isSelected={value === 'listview'}
        onClick={() => onChange('listview')}
      >
        <ListivewIcon isSelected={value === 'listview'} />
      </Button>
    </div>
  );
}
