import React, { useMemo } from 'react';
import './App.css';
import OntoExplorer from './OntoExplorer';
import {
  getDataProps,
  getLinksHierarqy,
  getNodesHierarqy,
  getObjectProps,
} from './api/sparqlQueries';
import { useQueryApi } from './hooks/useApi';
import { createTree } from './lib/util';
import * as lodash from 'lodash';

export default function App() {
  const params = useMemo(() => {
    return {
      empty: {},
      term: 'od',
    };
  }, []);

  const nodeResults = useQueryApi(getNodesHierarqy, params.empty);
  const nodes = useMemo(() => {
    return createTree(
      ({ h }) => h,
      ({ p }) => p,
      (pp) => ({ ...pp, id: pp.h, name: pp.h }),
      nodeResults?.data || []
    );
  }, [nodeResults?.data]);
  const linksResults = useQueryApi(getLinksHierarqy, params.empty);
  const links = useMemo(() => {
    const aa = createTree(
      ({ h }) => h,
      ({ p }) => p,
      (pp) => ({ ...pp, id: pp.h, name: pp.h }),
      linksResults?.data || []
    );
    return aa;
  }, [linksResults?.data]);
  const dataPropsResults = useQueryApi(getDataProps, params.empty);
  const dataProps = useMemo(() => {
    const aa = Object.values(
      lodash.groupBy(dataPropsResults?.data || [], ({ domain }) => domain)
    ).map((dataProps) => ({
      domain: dataProps[0]!.domain,
      dataProps: dataProps.map(({ d }) => d),
    }));
    return aa;
  }, [dataPropsResults?.data]);

  const objectPropsResults = useQueryApi(getObjectProps, params.empty);
  const objectProps = useMemo(() => {
    const aa = (objectPropsResults?.data || []).map(({ dd, rr, pp }) => ({
      domain: dd,
      range: rr,
      prop: pp,
    }));
    return aa;
  }, [objectPropsResults?.data]);

  if (
    linksResults?.status === 'loading' ||
    nodeResults?.status === 'loading' ||
    dataPropsResults?.status === 'loading'
  ) {
    return <div>Loading...</div>;
  }
  if (
    linksResults?.status === 'error' ||
    nodeResults?.status === 'error' ||
    dataPropsResults?.status === 'error'
  ) {
    return <div>Error: {linksResults.error?.message}</div>;
  }
  if (
    linksResults?.status !== 'success' ||
    nodeResults?.status !== 'success' ||
    dataPropsResults?.status !== 'success'
  ) {
    return <div>Error: weird status</div>;
  }

  return (
    <div className="App">
      <OntoExplorer
        schemaGraph={{ nodes, links }}
        dataProps={dataProps}
        objectProps={objectProps}
      />
    </div>
  );
}
