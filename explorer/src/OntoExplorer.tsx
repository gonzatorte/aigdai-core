import React, { useState, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import CollapsibleMenu from './CollapsibleMenu';
import SelectableList, { Item } from './SelectableList';
import SelectableTree from './SelectableTree';
import { searchEntity, executeRawSparqlQuery } from './api/sparqlQueries';
import { dfsApplyForrest, flattenForest } from './lib/util';
import { SemanticGraphData, SemanticGraphLink, Tree } from './types';
import { Map as InmutableMap, List, Set as ImmutableSet } from 'immutable';
import InstanceExplorer from './InstanceExplorer';
import SchemaExplorer from './SchemaExplorer';
import SparqlQueryModal from './SparqlQueryModal';

type NamedEntity = { id: string; kindStr: string; nameAttr: string };

const ENTITY_ONTOLOGY_CONFIGS: NamedEntity[] = [
  {
    id: 'repositorio',
    kindStr: 'repositorio',
    nameAttr: 'tiene_nombre_repositorio',
  },
  {
    id: 'disciplina',
    kindStr: 'disciplina',
    nameAttr: 'nombre_de_disciplina',
  },
  {
    id: 'locacion',
    kindStr: 'locacion',
    nameAttr: 'nombre_de_locacion',
  },
  {
    id: 'estandar',
    kindStr: 'estandar',
    nameAttr: 'tiene_nombre_estandar',
  },
  {
    id: 'organizacion',
    kindStr: 'organizacion',
    nameAttr: 'tiene_nombre_organizacion',
  },
  {
    id: 'politica',
    kindStr: 'politica',
    nameAttr: 'tiene_nombre_politica',
  },
];

function EntitySelector({
  item,
  valueSelectedInstances,
  setSelectedInstances,
}: {
  item: NamedEntity;
  valueSelectedInstances: SemanticGraphData;
  setSelectedInstances: React.Dispatch<React.SetStateAction<SemanticGraphData>>;
}) {
  const onSelectionChange = useCallback(
    (selected: Item) => {
      setSelectedInstances((prev) => {
        const newMap = new Map(prev);
        if (newMap.has(selected.id)) {
          // ToDo: Also have to delete others nodes links. Should I copy every node again?
          newMap.delete(selected.id);
        } else {
          newMap.set(selected.id, {
            id: selected.id,
            dataProps: [],
            kind: [item.kindStr],
            links: [],
          });
        }
        // ToDo: Update again once all relations are loaded?
        // getExistingRelations(Array.from(newMap.values()).map(({id}) => id));
        return newMap;
      });
    },
    [item.kindStr, setSelectedInstances]
  );
  const onLoadMore = useCallback(
    (term: string, nextTo?: string) =>
      searchEntity(item.kindStr, item.nameAttr, term, nextTo).then((items) =>
        items.map(({ idd, name }) => ({ id: idd, title: name }))
      ),
    [item.kindStr, item.nameAttr]
  );
  const selectedItems = useMemo(() => {
    return Array.from(valueSelectedInstances.keys()).map((kk) => kk);
  }, [valueSelectedInstances]);
  return (
    <div style={{ marginBottom: '30px' }} key={item.id}>
      <h3
        style={{
          margin: '0 0 15px 0',
          fontSize: '16px',
          fontWeight: 'bold',
          color: '#ecf0f1',
        }}
      >
        {item.id} Filters
      </h3>
      <SelectableList
        selectedItems={selectedItems}
        onSelectionChange={onSelectionChange}
        searchPlaceholder={`Search ${item.id}`}
        onLoadMore={onLoadMore}
        maxHeight={200}
      />
    </div>
  );
}

export default function OntoExplorer({
  schemaGraph,
  dataProps,
  objectProps,
}: {
  schemaGraph: { nodes: Tree[]; links: Tree[] };
  dataProps: { domain: string; dataProps: string[] }[];
  objectProps: { domain: string; range: string; prop: string }[];
}) {
  const [valueSelectedInstances, setSelectedInstances] =
    useState<SemanticGraphData>(new Map([]));
  const [isSparqlModalOpen, setIsSparqlModalOpen] = useState(false);

  // ToDo: Optimize this
  const { nodeKindItems, nodeColorScale } = useMemo(() => {
    const flattenNodeKinds = flattenForest(
      ({ item, children }) => ({ item, children }),
      schemaGraph.nodes
    );
    const nodeKindsFromData = [
      ...new Set(flattenNodeKinds.map(({ item }) => item.id)),
    ];
    const nodeColorScale = d3
      .scaleOrdinal<string, string>()
      .domain(nodeKindsFromData)
      .range(d3.schemeCategory10);

    return {
      nodeKindItems: dfsApplyForrest(
        (item) => ({
          id: item.id,
          title: item.id,
          description: item.id,
          color: nodeColorScale(item.id),
        }),
        schemaGraph.nodes
      ),
      nodeColorScale,
      flattenNodeKinds,
    };
  }, [schemaGraph.nodes]);

  // ToDo: Optimize this
  const { linkKindItems, linkColorScale } = useMemo(() => {
    const flattenLinkKinds = flattenForest(
      ({ item, children }) => ({ item, children }),
      schemaGraph.links
    );
    const linkKindsFromData = [
      ...new Set(flattenLinkKinds.map(({ item }) => item.id)),
    ];
    const linkColorScale = d3
      .scaleOrdinal<string, string>()
      .domain(linkKindsFromData)
      .range(d3.schemeSet2);
    return {
      linkKindItems: dfsApplyForrest<
        Tree<SemanticGraphLink<string>>,
        { id: string; title: string; description: string; color: string }
      >(
        (item) => ({
          id: item.id,
          title: item.id,
          description: item.id,
          color: linkColorScale(item.id),
        }),
        schemaGraph.links
      ),
      linkColorScale,
      flattenLinkKinds,
    };
  }, [schemaGraph.links]);

  const nodeKindItemsList = useMemo(
    () => List<Tree>(nodeKindItems),
    [nodeKindItems]
  );
  const initialSimpleGraph = useMemo(() => {
    const flatternNodes = flattenForest(
      (node) => node.item,
      Array.from(nodeKindItemsList)
    );
    const nodes = List(
      flatternNodes.map((item) => {
        const nodeId = item.id;
        const rr = InmutableMap({
          id: nodeId,
          dataProps: List(
            dataProps.find((dp) => dp.domain === nodeId)?.dataProps || []
          ),
        });
        return rr;
      })
    );

    const flatternLinks = InmutableMap(
      linkKindItems.map((dd) => [dd.item.id, dd.item])
    );
    const nodeMap = InmutableMap(nodes.map((node) => [node.get('id'), node]));
    const links = List(
      ImmutableSet(
        objectProps
          .map((objProp) => {
            const link = flatternLinks.get(objProp.prop);
            if (!link) {
              return null;
            }
            const sourceNode = nodeMap.get(objProp.domain);
            const targetNode = nodeMap.get(objProp.range);
            if (!sourceNode || !targetNode) {
              return null;
            }
            return InmutableMap({
              id: objProp.prop,
              source: objProp.domain,
              target: objProp.range,
            });
          })
          .filter((ll) => ll !== null)
      )
    );

    return InmutableMap({ nodes, links });
  }, [linkKindItems, nodeKindItemsList, objectProps, dataProps]);

  const [selectedLinkKinds, setSelectedLinkKinds] = useState<string[]>(
    initialSimpleGraph.toJS().links.map((node) => node.id)
  );
  const [selectedNodeKinds, setSelectedNodeKinds] = useState<string[]>(
    initialSimpleGraph.toJS().nodes.map((link) => link.id)
  );

  const nodeColorFunction = useCallback(
    (kind: string) => nodeColorScale(kind),
    [nodeColorScale]
  );
  const linkColorFunction = useCallback(
    (kind: string) => linkColorScale(kind),
    [linkColorScale]
  );

  return (
    <>
      <div style={{ position: 'relative' }}>
        <CollapsibleMenu
          title="Instance Controls"
          defaultOpen={true}
          position="right"
          width={500}
        >
          <div style={{ marginBottom: '20px' }}>
            <button
              onClick={() => setIsSparqlModalOpen(true)}
              style={{
                width: '100%',
                padding: '12px 16px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
              }}
            >
              Open SPARQL Query Editor
            </button>
          </div>
          {ENTITY_ONTOLOGY_CONFIGS.map((item) => {
            return (
              <EntitySelector
                key={item.id}
                item={item}
                valueSelectedInstances={valueSelectedInstances}
                setSelectedInstances={setSelectedInstances}
              />
            );
          })}
        </CollapsibleMenu>
        <CollapsibleMenu
          title="Schema Controls"
          defaultOpen={false}
          position="left"
          width={500}
        >
          <div style={{ marginBottom: '30px' }}>
            <h3
              style={{
                margin: '0 0 15px 0',
                fontSize: '16px',
                fontWeight: 'bold',
                color: '#ecf0f1',
              }}
            >
              Link Filters
            </h3>
            <SelectableTree
              trees={linkKindItems}
              selectedItems={selectedLinkKinds}
              onSelectionSet={(selectedIds) =>
                setSelectedLinkKinds(selectedIds)
              }
              onSelectionChange={(selectedId) =>
                setSelectedLinkKinds((prev) =>
                  prev.includes(selectedId)
                    ? prev.filter((id) => id !== selectedId)
                    : [...prev, selectedId]
                )
              }
              maxHeight={400}
            />
          </div>
          <div style={{ marginBottom: '30px' }}>
            <h3
              style={{
                margin: '0 0 15px 0',
                fontSize: '16px',
                fontWeight: 'bold',
                color: '#ecf0f1',
              }}
            >
              Node Filters
            </h3>
            <SelectableTree
              trees={nodeKindItems}
              selectedItems={selectedNodeKinds}
              onSelectionSet={(selectedIds) =>
                setSelectedNodeKinds(selectedIds)
              }
              onSelectionChange={(selectedId) =>
                setSelectedNodeKinds((prev) =>
                  prev.includes(selectedId)
                    ? prev.filter((id) => id !== selectedId)
                    : [...prev, selectedId]
                )
              }
              maxHeight={400}
            />
          </div>
        </CollapsibleMenu>
      </div>
      <InstanceExplorer
        schemaGraph={schemaGraph}
        dataProps={dataProps}
        objectProps={objectProps}
        selectedLinkKinds={selectedLinkKinds}
        selectedNodeKinds={selectedNodeKinds}
        setSelectedInstances={setSelectedInstances}
        valueSelectedInstances={valueSelectedInstances}
        nodeColorFunction={nodeColorFunction}
        linkColorFunction={linkColorFunction}
      />
      <SchemaExplorer
        schemaGraphData={initialSimpleGraph}
        selectedLinkKinds={selectedLinkKinds}
        selectedNodeKinds={selectedNodeKinds}
        setSelectedLinkKinds={setSelectedLinkKinds}
        setSelectedNodeKinds={setSelectedNodeKinds}
        nodeColorFunction={nodeColorFunction}
        linkColorFunction={linkColorFunction}
        nodeKindItems={nodeKindItemsList}
      />
      <SparqlQueryModal
        isOpen={isSparqlModalOpen}
        onClose={() => setIsSparqlModalOpen(false)}
        onExecuteQuery={useCallback(async (query: string) => {
          const dd = await executeRawSparqlQuery(query);
          console.log(dd);
          // setSelectedInstances((prev) => {
          //   const newMap = new Map(prev);
          //   if (newMap.has(selected.id)) {
          //     // ToDo: Also have to delete others nodes links. Should I copy every node again?
          //     newMap.delete(selected.id);
          //   } else {
          //     newMap.set(selected.id, {
          //       id: selected.id,
          //       dataProps: [],
          //       kind: [item.kindStr],
          //       links: [],
          //     });
          //   }
          //   // ToDo: Update again once all relations are loaded?
          //   // getExistingRelations(Array.from(newMap.values()).map(({id}) => id));
          //   return newMap;
          // });
          return dd;
        }, [])}
      />
    </>
  );
}
