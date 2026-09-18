import React, { useState, useMemo, useCallback, useEffect } from 'react';
import Graph from './Graph';
import CreateNodeModal from './CreateNodeModal';
import CreateLinkModal from './CreateLinkModal';
import {
  deleteLinks,
  deleteNodes,
  getExistingRelations,
  getNeighbors,
} from './api/sparqlQueries';
import { flattenForest, normalizeKinds } from './lib/util';
import {
  DataProp,
  Neighborhood,
  SemanticGraphData,
  SemanticGraphNode,
  SemanticGraphLink,
  Tree,
} from './types';
import { List as ImmutableList, Set as ImmutableSet } from 'immutable';

// ToDo: Eliminar la dependencia de schemaGraph
export default function InstanceExplorer({
  schemaGraph,
  dataProps,
  objectProps,
  selectedLinkKinds,
  selectedNodeKinds,
  nodeColorFunction,
  linkColorFunction,
  setSelectedInstances,
  valueSelectedInstances,
}: {
  schemaGraph: { nodes: Tree[]; links: Tree[] };
  dataProps: { domain: string; dataProps: string[] }[];
  objectProps: { domain: string; range: string; prop: string }[];
  selectedLinkKinds: string[];
  selectedNodeKinds: string[];
  nodeColorFunction: (kind: string) => string;
  linkColorFunction: (kind: string) => string;
  setSelectedInstances: React.Dispatch<React.SetStateAction<SemanticGraphData>>;
  valueSelectedInstances: SemanticGraphData;
}) {
  const [valueInCreationLink, setInCreationLink] = useState<{
    source: SemanticGraphNode;
    target: SemanticGraphNode;
  } | null>(null);
  const [hiddenNodeIds, setHiddenNodeIds] = useState<string[]>([]);
  const [hiddenLinkIds, setHiddenLinkIds] = useState<
    SemanticGraphLink<string>[]
  >([]);
  const [selectedNodeIds, setSelectedNodeIds] =
    useState<ImmutableSet<string>>(ImmutableSet());
  const [selectedLinkIds, setSelectedLinkIds] = useState<
    SemanticGraphLink<string>[]
  >([]);
  const [isAddNodeModalOpen, setIsAddNodeModalOpen] = useState(false);
  const entityDataPropsMapping = useMemo(() => {
    return new Map(
      dataProps.map(({ domain, dataProps }) => [domain, dataProps])
    );
  }, [dataProps]);
  const objectPropsMapping = useMemo(() => {
    return new Map(
      objectProps.map(({ domain, range, prop }) => [
        prop,
        [domain, range] as const,
      ])
    );
  }, [objectProps]);
  const subjectToObjectPropsMapping = useMemo(() => {
    return new Map(
      objectProps.map(({ domain, range, prop }) => [
        domain,
        [prop, range] as const,
      ])
    );
  }, [objectProps]);

  const handleDeleteSelected = useCallback(() => {
    if (selectedNodeIds.size > 0 || selectedLinkIds.length > 0) {
      setHiddenNodeIds((prev) => [...prev, ...selectedNodeIds.toArray()]);
      setHiddenLinkIds((prev) => [...prev, ...selectedLinkIds]);
      setSelectedNodeIds(ImmutableSet());
      setSelectedLinkIds([]);
    }
  }, [
    selectedNodeIds,
    selectedLinkIds,
    setHiddenNodeIds,
    setHiddenLinkIds,
    setSelectedNodeIds,
    setSelectedLinkIds,
  ]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Delete') {
        handleDeleteSelected();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleDeleteSelected]);

  const handleAddNode = useCallback(
    (newNode: SemanticGraphNode) => {
      setSelectedInstances((prev) => {
        const newMap = new Map(prev);
        newMap.set(newNode.id, {
          ...newNode,
          links: [],
        });
        return newMap;
      });
    },
    [setSelectedInstances]
  );

  const availableNodeKinds = useMemo(() => {
    const flattenNodeKinds = flattenForest(
      ({ item, children }) => ({ item, children }),
      schemaGraph.nodes
    );
    return [...new Set(flattenNodeKinds.map(({ item }) => item.id))];
  }, [schemaGraph.nodes]);

  const onNewLink = useCallback(
    (sourceId: string, targetId: string) => {
      const source = valueSelectedInstances.get(sourceId);
      if (!source) {
        throw new Error('Source node not found');
      }
      const target = valueSelectedInstances.get(targetId);
      if (!target) {
        throw new Error('Target node not found');
      }
      setInCreationLink({ source, target });
    },
    [setInCreationLink, valueSelectedInstances]
  );

  return (
    <>
      <div>
        <Graph
          width={1400}
          height={1000}
          hiddenNodeIds={hiddenNodeIds}
          hiddenLinkIds={hiddenLinkIds}
          graphData={valueSelectedInstances}
          selectedNodeKinds={selectedNodeKinds}
          selectedLinkKinds={selectedLinkKinds}
          selectedNodeIds={selectedNodeIds}
          selectedLinkIds={selectedLinkIds}
          onSelectionChange={setSelectedNodeIds}
          onLinkSelectionChange={setSelectedLinkIds}
          nodeColorFunction={nodeColorFunction}
          linkColorFunction={linkColorFunction}
          onNodeLoading={useCallback(
            async (
              node: SemanticGraphNode,
              internalNodes: Map<string, SemanticGraphNode>
            ) => {
              const { types, relations, inverseRelations } = await getNeighbors(
                node.id
              );

              const validDataPropsAux = types.map((type) => {
                return entityDataPropsMapping.get(type) || [];
              });
              const validDataProps = validDataPropsAux[0]
                ? validDataPropsAux[0].concat(...validDataPropsAux.slice(1))
                : [];

              const rels: DataProp[] = relations.map(({ p, o }) => ({
                key: p,
                value: o,
              }));
              const mergedAux = [...node.dataProps, ...rels]
                .filter(({ key }) => validDataProps.includes(key))
                .map(
                  ({ key, value }) =>
                    [JSON.stringify([key, value]), { key, value }] as const
                );
              mergedAux.sort((a, b) => a[0].localeCompare(b[0]));
              const dataPropsMap = new Map(mergedAux);
              const dataProps = Array.from(dataPropsMap.values());
              const existingRelations = await getExistingRelations(
                Array.from(internalNodes.values()).map(({ id }) => id)
              );
              console.log('existingRelations', existingRelations);
              setSelectedInstances((prev) => {
                const newMap = new Map(prev);
                const links: Neighborhood[] = [];
                let newNode = newMap.get(node.id);
                if (!newNode) {
                  throw new Error('Clicked node not found');
                }
                newNode.dataProps = dataProps;
                newNode.kind = types;
                newNode.links = links;
                relations.forEach(({ p, o }) => {
                  const domainRange = objectPropsMapping.get(p);
                  if (!domainRange || !domainRange[0] || !domainRange[1]) {
                    return;
                  }
                  if (newMap.has(o)) {
                    return;
                  }
                  // const domain = domainRange[0];
                  const range = domainRange[1];
                  newMap.set(o, {
                    id: o,
                    dataProps: [],
                    kind: [range],
                    links: [],
                  });
                });
                inverseRelations.forEach(({ p, s }) => {
                  const domainRange = objectPropsMapping.get(p);
                  if (!domainRange || !domainRange[0] || !domainRange[1]) {
                    throw new Error('mapping not found');
                  }
                  const domain = domainRange[0];
                  let source = newMap.get(s);
                  if (!source) {
                    source = {
                      id: s,
                      dataProps: [],
                      kind: [domain],
                      links: [],
                    };
                    newMap.set(s, source);
                  }
                  const oldLink = source.links.find(
                    ({ target: tt }) => tt.id === newNode.id
                  );
                  if (!oldLink) {
                    source.links.push({ target: newNode, kind: [p] });
                  } else {
                    oldLink.kind = normalizeKinds([...oldLink.kind, p]);
                  }
                });
                // ToDo: Have to remove or merge duplicates
                relations.forEach(({ p, o }) => {
                  const target = newMap.get(o);
                  if (!target) {
                    return;
                  }
                  const oldLink = links.find(
                    ({ target: tt }) => tt.id === target.id
                  );
                  if (!oldLink) {
                    links.push({ target, kind: [p] });
                  } else {
                    oldLink.kind = normalizeKinds([...oldLink.kind, p]);
                  }
                });
                return newMap;
              });
              // return {dataProps, kind: types, neighborhood: relations.map(({p, o}) => ({target: o, kind: [p]}))};
            },
            [setSelectedInstances, entityDataPropsMapping, objectPropsMapping]
          )}
          onNewLink={onNewLink}
        />
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            marginTop: '20px',
            marginBottom: '20px',
          }}
        >
          <button
            onClick={() => setIsAddNodeModalOpen(true)}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            Add New Node
          </button>
          <button
            onClick={() => {
              const nodesToDelete = selectedNodeIds
                .toArray()
                .map((id) => {
                  const node = valueSelectedInstances.get(id);
                  if (!node) {
                    return null;
                  }
                  // ToDo: Filter those not found
                  return { id, kind: node.kind };
                })
                .filter((nn) => nn !== null);
              deleteNodes(nodesToDelete);
              // ToDo: Remove from graph too
            }}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            Delete Selected Nodes
          </button>
          <button
            onClick={() => {
              deleteLinks(
                selectedLinkIds.map((link) => ({
                  source: link.source,
                  target: link.target,
                  kind: link.kind,
                }))
              );
              // ToDo: Remove from graph too
            }}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            Delete Selected Links
          </button>
          <button
            onClick={handleDeleteSelected}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            Hide Selected
          </button>
          <button
            onClick={() => {
              setHiddenNodeIds([]);
              setHiddenLinkIds([]);
            }}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            Show All Hidden ({hiddenNodeIds.length + hiddenLinkIds.length})
          </button>
        </div>
      </div>

      <CreateNodeModal
        isOpen={isAddNodeModalOpen}
        onClose={() => setIsAddNodeModalOpen(false)}
        onSubmit={handleAddNode}
        availableNodeKinds={availableNodeKinds}
        entityDataPropsMapping={entityDataPropsMapping}
      />
      <CreateLinkModal
        inCreationLink={valueInCreationLink}
        onClose={() => setInCreationLink(null)}
        subjectToObjectPropsMapping={subjectToObjectPropsMapping}
        onSubmit={useCallback(
          (
            inSource: SemanticGraphNode,
            inTarget: SemanticGraphNode,
            kind: string[]
          ) => {
            setSelectedInstances((prev) => {
              const newMap = new Map(prev);
              const source = newMap.get(inSource.id);
              if (!source) {
                throw new Error('Source node not found');
              }
              const target = newMap.get(inTarget.id);
              if (!target) {
                throw new Error('Target node not found');
              }
              const newLink = {
                source,
                target,
                kind,
              };
              source.links.push(newLink);
              return newMap;
            });
          },
          [setSelectedInstances]
        )}
      />
    </>
  );
}
