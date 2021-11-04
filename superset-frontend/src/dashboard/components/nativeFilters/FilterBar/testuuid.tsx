import queryString from 'query-string';
import rison from 'rison';

const store = [];
export const postUuid = (obj) => {
  store.push(obj);
  return 400;
}

const queryStr = `native_filters=%28NATIVE_FILTER-j3N16zQ81%3A%28__cache%3A%28label%3A%271.+Phase+I%2C+3.+Phase+III%2C+2.+Phase+II+or+Combined+I%2FII%2C+0.+Pre-clinical%27%2CvalidateStatus%3A%21f%2Cvalue%3A%21%28%271.+Phase+I%27%2C%273.+Phase+III%27%2C%272.+Phase+II+or+Combined+I%2FII%27%2C%270.+Pre-clinical%27%29%29%2CextraFormData%3A%28filters%3A%21%28%28col%3Aclinical_stage%2Cop%3AIN%2Cval%3A%21%28%271.+Phase+I%27%2C%273.+Phase+III%27%2C%272.+Phase+II+or+Combined+I%2FII%27%2C%270.+Pre-clinical%27%29%29%29%29%2CfilterState%3A%28label%3A%271.+Phase+I%2C+3.+Phase+III%2C+2.+Phase+II+or+Combined+I%2FII%2C+0.+Pre-clinical%27%2CvalidateStatus%3A%21f%2Cvalue%3A%21%28%271.+Phase+I%27%2C%273.+Phase+III%27%2C%272.+Phase+II+or+Combined+I%2FII%27%2C%270.+Pre-clinical%27%29%29%2Cid%3ANATIVE_FILTER-j3N16zQ81%2CownState%3A%28%29%29%29`;
export const getUuid = (uuid) => {
  const obj = queryString.parse(queryStr);
  const nativeFiltersObj = rison.decode(obj['native_filters']);
  console.log('nativeFitlersObj', nativeFiltersObj)
  if (uuid) return nativeFiltersObj;
  // return null;
}