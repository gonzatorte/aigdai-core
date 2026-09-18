import React, { useState, useMemo, useCallback } from 'react';
import { flattenForest, removeNodesFromForest } from './lib/util';
import { Tree } from './types';
import SchemaGraph, { SimpleLink } from './SchemaGraph';
import { Map as InmutableMap, List, Set as ImmutableSet } from 'immutable';
import type Immutable from 'immutable';

export default function SchemaExplorer({
  schemaGraphData,
  selectedLinkKinds,
  selectedNodeKinds,
  setSelectedLinkKinds,
  setSelectedNodeKinds,
  nodeColorFunction,
  linkColorFunction,
  nodeKindItems,
}: {
  schemaGraphData: Immutable.MapOf<{
    nodes: List<
      Immutable.MapOf<{
        id: string;
        dataProps: List<string>;
      }>
    >;
    links: List<
      Immutable.MapOf<{
        id: string;
        source: string;
        target: string;
      }>
    >;
  }>;
  selectedLinkKinds: string[];
  selectedNodeKinds: string[];
  setSelectedLinkKinds: React.Dispatch<React.SetStateAction<string[]>>;
  setSelectedNodeKinds: React.Dispatch<React.SetStateAction<string[]>>;
  nodeColorFunction: (kind: string) => string;
  linkColorFunction: (kind: string) => string;
  nodeKindItems: List<Tree<any>>;
}) {
  const [markedSchemaNodeKinds, setMarkedSchemaNodeKinds] = useState<
    ImmutableSet<string>
  >(ImmutableSet([]));
  const [markedSchemaLinkKinds, setMarkedSchemaLinkKinds] = useState<
    ImmutableSet<SimpleLink<string>>
  >(ImmutableSet([]));

  const simpleGraph = useMemo(() => {
    const nodes = schemaGraphData
      .get('nodes')
      .filter((node) => selectedNodeKinds.includes(node.get('id')));
    const selectedNodeForrest = Array.from(
      ImmutableSet(
        flattenForest(
          ({ item, children }) => ({ item, children }),
          removeNodesFromForest(
            (item) => !selectedNodeKinds.includes(item.id),
            nodeKindItems.toJS() as Tree<any>[]
          )
        )
      )
    );
    const flattenSubclassOfLinksAux = selectedNodeForrest.map(
      ({ item, children }) => {
        return children.map((child) => {
          return InmutableMap({
            id: 'subclass',
            source: item.id,
            target: child.item.id,
          });
        });
      }
    );
    const flattenSubclassOfLinks = flattenSubclassOfLinksAux[0]
      ? flattenSubclassOfLinksAux[0].concat(
          ...flattenSubclassOfLinksAux.slice(1)
        )
      : [];
    const subclassOfLinks = ImmutableSet(flattenSubclassOfLinks);

    const nodeMap = InmutableMap(nodes.map((node) => [node.get('id'), node]));
    const filteredLinks = ImmutableSet(schemaGraphData.get('links'))
      .filter((llink) => {
        return selectedLinkKinds.some(
          (selectedLinkKind) => llink.get('id') === selectedLinkKind
        );
      })
      .union(subclassOfLinks)
      .filter((llink) => {
        return (
          nodeMap.has(llink.get('source')) && nodeMap.has(llink.get('target'))
        );
      });
    const links = List(
      filteredLinks
      // .union(
      //   ImmutableSet(
      //     selectedSchemaGraph.links
      //       .map((link) => {
      //         const sourceNode = nodeMap.get(link.item.source);
      //         const targetNode = nodeMap.get(link.item.target);
      //         if (!sourceNode || !targetNode) {
      //           return null;
      //         }
      //         return InmutableMap({
      //           id: link.item.id,
      //           source: link.item.source,
      //           target: link.item.target,
      //         });
      //       })
      //       .filter((ll) => ll !== null)
      //   )
      // )
    );
    return InmutableMap({ nodes, links });
  }, [selectedLinkKinds, selectedNodeKinds, schemaGraphData, nodeKindItems]);

  return (
    <>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          marginTop: '20px',
          marginBottom: '20px',
        }}
      >
        <SchemaGraph
          simpleGraph={simpleGraph}
          selectedNodeIds={ImmutableSet(markedSchemaNodeKinds)}
          selectedLinkIds={ImmutableSet(markedSchemaLinkKinds)}
          onNodeSelectionChange={setMarkedSchemaNodeKinds}
          onLinkSelectionChange={setMarkedSchemaLinkKinds}
          width={1400}
          height={1000}
          nodeColorFunction={nodeColorFunction}
          linkColorFunction={linkColorFunction}
        />
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          marginTop: '20px',
          marginBottom: '20px',
        }}
      >
        <button
          onClick={useCallback(() => {
            if (
              markedSchemaNodeKinds.size > 0 ||
              markedSchemaLinkKinds.size > 0
            ) {
              setSelectedNodeKinds((prev) =>
                prev.filter((elem) => !markedSchemaNodeKinds.includes(elem))
              );
              const markableLinks = Array.from(
                markedSchemaLinkKinds
                  .filter(({ id }) => id !== 'subclass')
                  .map(({ id }) => id)
              );
              setSelectedLinkKinds((prev) =>
                prev.filter((elem) => !markableLinks.includes(elem))
              );
              setMarkedSchemaNodeKinds(ImmutableSet([]));
              setMarkedSchemaLinkKinds(ImmutableSet([]));
            }
          }, [
            markedSchemaNodeKinds,
            markedSchemaLinkKinds,
            setSelectedNodeKinds,
            setSelectedLinkKinds,
            setMarkedSchemaNodeKinds,
            setMarkedSchemaLinkKinds,
          ])}
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
      </div>
    </>
  );
}
