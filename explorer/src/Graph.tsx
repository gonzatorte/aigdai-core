import React, {
  useRef,
  useEffect,
  useState,
  useMemo,
  useCallback,
} from 'react';
import * as d3 from 'd3';
import {
  SemanticGraphNode,
  SemanticGraphLink,
  Neighborhood,
  DataProp,
  SemanticGraphData,
  SemanticGraphSingleLink,
} from './types';
import {
  normalizeKinds,
  getLinkId,
  getLinkShortId,
  getNodeId,
  getNodeShortId,
  serializeKinds,
  normalizeLink,
} from './lib/util';
import { useTraceUpdate } from './hooks/useTraceUpdate';
import { List as ImmutableList, Set as ImmutableSet } from 'immutable';

export type PositionedGraphNode = SemanticGraphNode & {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
};

export type PositionedGraphLink<T = PositionedGraphNode> =
  SemanticGraphLink<T> & {
    source: T;
    target: T;
  };

// Selection box type
type SelectionBox = {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
};

// Drag function for node interaction
const drag = (
  simulation: d3.Simulation<PositionedGraphNode, PositionedGraphLink>,
  width: number,
  height: number
) => {
  function dragstarted(
    event: d3.D3DragEvent<SVGGElement, PositionedGraphNode, PositionedGraphNode>
  ) {
    if (!event.active) simulation.alpha(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }
  function dragged(
    event: d3.D3DragEvent<SVGGElement, PositionedGraphNode, PositionedGraphNode>
  ) {
    const nodeRadius = 10;
    const padding = 20;
    const minX = padding + nodeRadius;
    const maxX = width - padding - nodeRadius;
    const minY = padding + nodeRadius;
    const maxY = height - padding - nodeRadius;

    // Constrain drag position to bounds
    const constrainedX = Math.max(minX, Math.min(maxX, event.x));
    const constrainedY = Math.max(minY, Math.min(maxY, event.y));

    event.subject.fx = constrainedX;
    event.subject.fy = constrainedY;
  }
  function dragended(
    event: d3.D3DragEvent<SVGGElement, PositionedGraphNode, PositionedGraphNode>
  ) {
    if (!event.active) simulation.alpha(0.3).restart();
    event.subject.fx = null;
    event.subject.fy = null;
  }
  return d3
    .drag<SVGGElement, PositionedGraphNode>()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended);
};

// Function to initialize node groups with event listeners, visual elements, and labels
const initializeNodeGroups = (
  nodeGroup: d3.Selection<SVGGElement, PositionedGraphNode, any, any>,
  simulation: d3.Simulation<PositionedGraphNode, PositionedGraphLink>,
  nodeSize: number,
  width: number,
  height: number,
  setTooltip: React.Dispatch<React.SetStateAction<null | TooltipPayload>>,
  setLoadingNodes: React.Dispatch<React.SetStateAction<Set<string>>>,
  nodeColorFunction: (kind: string) => string,
  onNodeLoading: (
    node: SemanticGraphNode,
    internalNodes: Map<string, SemanticGraphNode>
  ) => Promise<{
    dataProps: DataProp[];
    kind: string[];
    neighborhood: Neighborhood[];
  } | void>,
  internalNodes: Map<string, SemanticGraphNode>,
  selectedNodeIds: ImmutableSet<string>,
  onSelectionChange?: React.Dispatch<
    React.SetStateAction<ImmutableSet<string>>
  >,
  onNewLink?: (sourceId: string, targetId: string) => void,
  svgElement?: SVGSVGElement,
  isUpdate: boolean = false
) => {
  // Add concentric circles for each kind and label for each node
  nodeGroup.each(function (d) {
    const singleNodeGroup = d3.select(this).classed('node', true);
    if (!isUpdate) {
      // Add label first (so it appears behind the node)
      singleNodeGroup
        .append('text')
        .text(d.id)
        .attr('font-size', nodeSize + 2)
        .attr('font-weight', 'bold')
        .attr('text-anchor', 'middle')
        .attr('fill', '#333')
        .attr('stroke', 'none') // Ensure no stroke on text
        .attr('y', -(nodeSize + 5)) // Position label above the node
        .style('pointer-events', 'none'); // Prevent labels from handling events
    }

    const kinds = d.kind;
    const isSelected = selectedNodeIds.includes(d.id);
    const oldNodes = singleNodeGroup.selectAll('circle.kind-circle');
    oldNodes.remove();
    if (kinds.length === 0) {
      // Fallback for nodes without kinds
      singleNodeGroup
        .append('circle')
        .attr('r', nodeSize)
        .attr('fill', '#ccc')
        .attr('stroke', isSelected ? '#007bff' : '#fff')
        .attr('stroke-width', isSelected ? 3 : 1)
        .classed('kind-circle main-kind-circle', true);
    } else {
      // Multiple kinds - concentric circles
      const circleSpacing = nodeSize / kinds.length;
      kinds.forEach((kind, index) => {
        const radius = nodeSize - index * circleSpacing;
        singleNodeGroup
          .append('circle')
          .attr('r', radius)
          .attr('fill', nodeColorFunction(kind))
          .attr('stroke', index === 0 && isSelected ? '#007bff' : '#fff')
          .attr('stroke-width', index === 0 && isSelected ? 3 : 1)
          .classed('kind-circle', true)
          .classed('main-kind-circle', index === 0);
      });
    }

    if (isUpdate) {
      return;
    }
    // Add plus icon for creating new links
    const plusIcon = singleNodeGroup
      .append('g')
      .classed('plus-icon', true)
      .attr('transform', `translate(${nodeSize + 8}, 0)`)
      .style('cursor', 'pointer')
      .style('pointer-events', 'all');

    // Create plus icon using SVG elements
    plusIcon
      .append('circle')
      .attr('r', nodeSize * (6 / 10))
      .attr('fill', '#4ade80')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    plusIcon
      .append('text')
      .text('+')
      .attr('font-size', nodeSize.toString(10))
      .attr('font-weight', 'bold')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', '#fff')
      .style('pointer-events', 'none');

    // Add drag behavior for creating new links
    if (onNewLink) {
      let dragLine: d3.Selection<SVGLineElement, unknown, any, any> | null =
        null;
      let sourceNode: PositionedGraphNode | null = null;

      const plusDrag = d3
        .drag<SVGGElement, PositionedGraphNode>()
        .on('start', function (event, d) {
          event.sourceEvent.stopPropagation();
          sourceNode = d;

          // Create drag line
          if (svgElement) {
            const svg = d3.select(svgElement);
            dragLine = svg
              .append('line')
              .classed('drag-line', true)
              .attr('stroke', '#4ade80')
              .attr('stroke-width', 2)
              .attr('stroke-dasharray', '5,5')
              .attr('marker-end', 'url(#arrow-marker)')
              .style('pointer-events', 'none');
          }
        })
        .on('drag', function (event, _d) {
          if (dragLine && sourceNode) {
            const sourceX = sourceNode.x || 0;
            const sourceY = sourceNode.y || 0;
            dragLine
              .attr('x1', sourceX)
              .attr('y1', sourceY)
              .attr('x2', event.x)
              .attr('y2', event.y);
          }
        })
        .on('end', function (event, _d) {
          if (dragLine) {
            dragLine.remove();
            dragLine = null;
          }

          if (sourceNode) {
            // Find the target node at the drop position
            const nodes = simulation.nodes();
            const targetNode = nodes.find((node) => {
              if (node.id === sourceNode!.id) return false;
              const nodeX = node.x || 0;
              const nodeY = node.y || 0;
              const distance = Math.sqrt(
                Math.pow(event.x - nodeX, 2) + Math.pow(event.y - nodeY, 2)
              );
              return distance <= nodeSize + 10; // Allow some tolerance
            });

            if (targetNode && onNewLink) {
              onNewLink(sourceNode.id, targetNode.id);
            }
          }
          sourceNode = null;
        });

      plusIcon.call(plusDrag as any);
    }
  });

  if (isUpdate) {
    return;
  }
  // Add event listeners to the node group (will be applied to circles, not labels)
  const selectHandler = (event: MouseEvent, d: PositionedGraphNode) => {
    event.stopPropagation();
    if (onSelectionChange) {
      if (event.shiftKey) {
        // Multi-select with Ctrl/Cmd key
        onSelectionChange((prev) =>
          prev.includes(d.id)
            ? prev.filter((id) => id !== d.id)
            : prev.add(d.id)
        );
      } else {
        // Single select
        onSelectionChange(ImmutableSet([d.id]));
      }
    }
  };
  const expandHandler = async (event: MouseEvent, d: PositionedGraphNode) => {
    // Stop event propagation to prevent clearing selection when double-clicking on nodes
    event.stopPropagation();

    // Set loading state for this node
    setLoadingNodes((prev) => new Set(prev).add(d.id));

    try {
      await onNodeLoading(d, internalNodes);
      // ToDo: Put a ticker border for loaded items
      // d.attr('stroke-width', 3);
      // You can handle the returned neighborhood data here
    } catch (error) {
      console.error('Error loading neighborhoods:', error);
    } finally {
      // Clear loading state for this node
      setLoadingNodes((prev) => {
        const newSet = new Set(prev);
        newSet.delete(d.id);
        return newSet;
      });
    }
  };
  nodeGroup
    .style('cursor', 'pointer')
    .on('mouseover', function (event, d) {
      setTooltip({
        x: event.pageX + nodeSize,
        y: event.pageY - nodeSize,
        nodeId: d.id,
      });
    })
    .on('mouseout', function () {
      setTooltip(null);
    })
    .on('click', selectHandler)
    .on('dblclick', expandHandler)
    .on('auxclick', expandHandler)
    .call(drag(simulation, width, height));
};

// Function to create and animate loading spinners
const createLoadingSpinners = (
  nodeGroups: d3.Selection<SVGGElement, PositionedGraphNode, any, any>,
  loadingNodes: Set<string>,
  nodeSize: number
) => {
  // Remove existing spinners
  nodeGroups.selectAll('circle.loading-spinner').remove();

  // Add spinners for loading nodes
  const spinner = nodeGroups
    .filter((d) => loadingNodes.has(d.id))
    .append('circle')
    .classed('loading-spinner', true)
    .attr('r', nodeSize + 5)
    .attr('fill', 'none')
    .attr('stroke', '#666')
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '4,4')
    .style('opacity', 0.7);

  // Animate the spinner
  const animateSpinner = () => {
    spinner
      .transition()
      .duration(1000)
      .ease(d3.easeLinear)
      .styleTween('stroke-dashoffset', () => {
        return (t: number) => `${t * 8}`;
      })
      .on('end', animateSpinner);
  };
  animateSpinner();
};

type TooltipPayload = {
  x: number;
  y: number;
} & (
  | {
      nodeId: string;
    }
  | {
      link: SemanticGraphLink<string>;
    }
);

export default function Graph({
  width,
  height,
  graphData,
  selectedNodeKinds,
  selectedLinkKinds,
  selectedNodeIds = ImmutableSet(),
  selectedLinkIds = [],
  hiddenNodeIds = [],
  hiddenLinkIds = [],
  onSelectionChange,
  onLinkSelectionChange,
  onNodeLoading,
  nodeColorFunction,
  linkColorFunction,
  onNewLink,
}: {
  width: number;
  height: number;
  graphData: SemanticGraphData;
  nodeColorFunction: (kind: string) => string;
  linkColorFunction: (kind: string) => string;
  selectedNodeKinds: string[];
  selectedLinkKinds: string[];
  selectedNodeIds: ImmutableSet<string>;
  selectedLinkIds: SemanticGraphLink<string>[];
  hiddenNodeIds: string[];
  hiddenLinkIds: SemanticGraphLink<string>[];
  onSelectionChange?: React.Dispatch<
    React.SetStateAction<ImmutableSet<string>>
  >;
  onLinkSelectionChange?: React.Dispatch<
    React.SetStateAction<SemanticGraphLink<string>[]>
  >;
  onNodeLoading: (
    node: SemanticGraphNode,
    internalNodes: Map<string, SemanticGraphNode>
  ) => Promise<{
    dataProps: DataProp[];
    kind: string[];
    neighborhood: Neighborhood[];
  } | void>;
  onNewLink?: (sourceId: string, targetId: string) => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<
    PositionedGraphNode,
    PositionedGraphLink<string | SemanticGraphNode>
  > | null>(null);
  const tickFunctionsNodesRef = useRef<() => void>(() => {});
  const [tooltip, setTooltip] = useState<null | TooltipPayload>(null);
  const [loadingNodes, setLoadingNodes] = useState<Set<string>>(new Set());
  const internalNodesRef = useRef<Map<string, SemanticGraphNode>>(new Map());

  // Function to check if a node is within the selection box
  const isNodeInSelectionBox = (
    node: PositionedGraphNode,
    box: SelectionBox
  ): boolean => {
    if (node.x === undefined || node.y === undefined) return false;

    // Get the current transform of the graph group
    if (!svgRef.current) return false;
    const graphGroup = d3.select(svgRef.current).select('g');
    const transform = d3.zoomTransform(graphGroup.node() as any);

    // Transform the node coordinates to screen coordinates
    const nodeScreenX = node.x + transform.x;
    const nodeScreenY = node.y + transform.y;

    const minX = Math.min(box.startX, box.endX);
    const maxX = Math.max(box.startX, box.endX);
    const minY = Math.min(box.startY, box.endY);
    const maxY = Math.max(box.startY, box.endY);

    return (
      nodeScreenX >= minX &&
      nodeScreenX <= maxX &&
      nodeScreenY >= minY &&
      nodeScreenY <= maxY
    );
  };

  // Function to handle selection box completion
  const handleSelectionBoxComplete = useCallback(
    (box: SelectionBox, isMultiSelect: boolean) => {
      if (!onSelectionChange || !simulationRef.current) return;

      const nodes = simulationRef.current.nodes();
      const nodesInBox = nodes.filter((node) =>
        isNodeInSelectionBox(node, box)
      );
      const nodeIdsInBox = nodesInBox.map((node) => node.id);
      if (isMultiSelect) {
        onSelectionChange((prev) => {
          return prev.concat(nodeIdsInBox);
        });
      } else {
        onSelectionChange(ImmutableSet(nodeIdsInBox));
      }
    },
    [onSelectionChange]
  );

  const data = useMemo(() => {
    const nodesAndLinks = Array.from(graphData.values());
    const nodes = nodesAndLinks.map(({ links: _links, ...node }) => {
      const internalNode = internalNodesRef.current.get(node.id);
      if (!internalNode) {
        // ToDo: Crear una instancia separada aca
        const nnode = {
          ...node,
          kind: normalizeKinds(node.kind),
        };
        internalNodesRef.current.set(node.id, nnode);
        return nnode;
      }
      Object.assign(internalNode, {
        kind: normalizeKinds(node.kind),
        dataProps: node.dataProps,
      });
      return internalNode;
    });
    const linksAux = nodesAndLinks.map(({ links, ...node }) =>
      links.map((link) => {
        return {
          target: internalNodesRef.current.get(link.target.id)!,
          kind: normalizeKinds(link.kind),
          source: internalNodesRef.current.get(node.id)!,
        };
      })
    );
    const links = linksAux[0] ? linksAux[0].concat(...linksAux.slice(1)) : [];
    return {
      nodes,
      links,
    };
  }, [graphData]);

  const dataNodesFingerprint = data.nodes.map(getNodeId).sort().join('|');
  // Filter data based on selections
  const filteredNodes = useMemo(() => {
    const newNodes = data.nodes.filter(
      (node) =>
        node.kind.some((kind) => selectedNodeKinds.includes(kind)) &&
        !hiddenNodeIds.includes(node.id)
    );
    return newNodes;
  }, [dataNodesFingerprint, selectedNodeKinds, hiddenNodeIds]);

  const dataLinksFingerprint = data.links
    .map((link) => getLinkId(link))
    .sort()
    .join('|');
  const filteredNodesFingerprint = filteredNodes
    .map((node) => node.id)
    .sort()
    .join('|');
  const filteredLinks = useMemo(() => {
    const netLinks = data.links
      .map((link) => {
        if (hiddenLinkIds.some((l) => getLinkId(l) === getLinkId(link))) {
          return null;
        }
        const sourceNode = filteredNodes.find((n) => n.id === link.source.id);
        const targetNode = filteredNodes.find((n) => n.id === link.target.id);

        if (!sourceNode || !targetNode) {
          return null;
        }

        const linkKindSelected = link.kind.some((kind) =>
          selectedLinkKinds.includes(kind)
        );

        if (!linkKindSelected) {
          return null;
        }

        return link;
      })
      .filter((link) => link !== null);
    return netLinks;
  }, [
    dataLinksFingerprint,
    filteredNodesFingerprint,
    selectedLinkKinds,
    hiddenLinkIds,
  ]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);

    // Create a group for all graph elements to enable panning
    const graphGroup = svg.append('g');

    // Add bounds rectangle to visualize the containment area
    const padding = 20;
    graphGroup
      .append('rect')
      .attr('x', padding)
      .attr('y', padding)
      .attr('width', width - 2 * padding)
      .attr('height', height - 2 * padding)
      .attr('fill', 'none')
      .attr('stroke', '#ff6b6b')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '5,5')
      .attr('opacity', 0.7);

    // Initialize with empty data
    const simulation = d3
      .forceSimulation<PositionedGraphNode>([])
      .force(
        'link',
        d3
          .forceLink<PositionedGraphNode, PositionedGraphLink>([])
          .id((d) => getNodeShortId(d))
          .distance(100)
      )
      .force('colide', d3.forceCollide().radius(2))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      // Add bounding force to keep nodes within the container
      .force('bounds', () => {
        const simulationNodes = simulation.nodes();
        simulationNodes.forEach((node) => {
          if (node.x !== undefined && node.y !== undefined) {
            const nodeRadius = 10; // Node size
            const minX = padding + nodeRadius;
            const maxX = width - padding - nodeRadius;
            const minY = padding + nodeRadius;
            const maxY = height - padding - nodeRadius;

            // Clamp coordinates to keep nodes within bounds
            node.x = Math.max(minX, Math.min(maxX, node.x));
            node.y = Math.max(minY, Math.min(maxY, node.y));

            // Add stronger repulsive force from boundaries
            const boundaryForce = 4.0;
            const boundaryBuffer = 20;

            if (node.x <= minX + boundaryBuffer) {
              node.vx =
                (node.vx || 0) +
                boundaryForce * (1 - (node.x - minX) / boundaryBuffer);
            } else if (node.x >= maxX - boundaryBuffer) {
              node.vx =
                (node.vx || 0) -
                boundaryForce * (1 - (maxX - node.x) / boundaryBuffer);
            }
            if (node.y <= minY + boundaryBuffer) {
              node.vy =
                (node.vy || 0) +
                boundaryForce * (1 - (node.y - minY) / boundaryBuffer);
            } else if (node.y >= maxY - boundaryBuffer) {
              node.vy =
                (node.vy || 0) -
                boundaryForce * (1 - (maxY - node.y) / boundaryBuffer);
            }
          }
        });
      })
      .alphaDecay(0.0428)
      .alphaMin(0.001);

    // Store simulation reference and initialize internal tracking
    simulationRef.current = simulation;

    // Create empty link group (will be populated by link effect) - rendered first so links appear behind nodes
    graphGroup
      .append('g')
      .classed('link-group', true)
      .attr('stroke-opacity', 0.8);

    // Create empty node group (will be populated by node effect) - rendered second so nodes appear on top
    graphGroup
      .append('g')
      .classed('node-group', true)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add selection box visual element
    graphGroup
      .append('rect')
      .classed('selection-box', true)
      .attr('fill', 'rgba(0, 123, 255, 0.1)')
      .attr('stroke', '#007bff')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3')
      .style('pointer-events', 'none')
      .style('display', 'none');

    // Combined tick function that calls all registered tick functions
    simulation.on('tick', () => {
      tickFunctionsNodesRef.current?.();
    });

    // Add pan and selection box behavior
    let isPanning = false;
    let isSelecting = false;
    const selectionBoxElement = graphGroup.select('.selection-box');
    let selectionBox: SelectionBox | null = null;
    const setSelectionBox = (box: SelectionBox | null) => {
      selectionBox = box;
      if (selectionBox) {
        // Get the current transform of the graph group
        const transform = d3.zoomTransform(graphGroup.node() as any);

        // Adjust selection box coordinates to account for the transform
        const adjustedStartX = selectionBox.startX - transform.x;
        const adjustedStartY = selectionBox.startY - transform.y;
        const adjustedEndX = selectionBox.endX - transform.x;
        const adjustedEndY = selectionBox.endY - transform.y;

        const x = Math.min(adjustedStartX, adjustedEndX);
        const y = Math.min(adjustedStartY, adjustedEndY);
        const width = Math.abs(adjustedEndX - adjustedStartX);
        const height = Math.abs(adjustedEndY - adjustedStartY);

        selectionBoxElement
          .style('display', 'block')
          .attr('x', x)
          .attr('y', y)
          .attr('width', width)
          .attr('height', height);
      } else {
        selectionBoxElement.style('display', 'none');
      }
    };

    const combinedDrag = d3
      .drag<SVGSVGElement, unknown>()
      .on('start', function (event) {
        // Only start if clicking on the background (not on nodes)
        if (event.sourceEvent.target === svgRef.current) {
          const [x, y] = d3.pointer(event, svgRef.current);

          // Check if Ctrl key is pressed for panning
          if (event.sourceEvent.ctrlKey) {
            isPanning = true;
            d3.select(this).style('cursor', 'grabbing');
          } else {
            isSelecting = true;
            setSelectionBox({
              startX: x,
              startY: y,
              endX: x,
              endY: y,
            });
            d3.select(this).style('cursor', 'crosshair');
          }
        }
      })
      .on('drag', function (event) {
        // Only handle if clicking on the background (not on nodes)
        if (event.sourceEvent.target === svgRef.current) {
          const [x, y] = d3.pointer(event, svgRef.current);

          if (isSelecting && selectionBox) {
            // Update selection box
            setSelectionBox({ ...selectionBox, endX: x, endY: y });
          } else if (isPanning) {
            // Handle panning
            const currentTransform = d3.zoomTransform(graphGroup.node() as any);
            const newTransform = currentTransform.translate(event.dx, event.dy);
            graphGroup.attr(
              'transform',
              `translate(${newTransform.x}, ${newTransform.y})`
            );
          }
        }
      })
      .on('end', function (event) {
        // Only complete if clicking on the background (not on nodes)
        if (event.sourceEvent.target === svgRef.current) {
          if (isSelecting && selectionBox) {
            const [x, y] = d3.pointer(event, svgRef.current);
            const finalBox = { ...selectionBox, endX: x, endY: y };

            // Only process if the box has some minimum size
            const minSize = 5;
            const width = Math.abs(finalBox.endX - finalBox.startX);
            const height = Math.abs(finalBox.endY - finalBox.startY);

            const isMultiSelect = event.sourceEvent.shiftKey;
            if (width > minSize || height > minSize) {
              handleSelectionBoxComplete(finalBox, isMultiSelect);
            }

            setSelectionBox(null);
          }

          isPanning = false;
          isSelecting = false;
          d3.select(this).style('cursor', 'grab');
        }
      });

    svg.call(combinedDrag);

    // Add click handler to clear selection when clicking on empty space
    svg.on('click', function (event) {
      // Only clear selection if clicking on the SVG background (not on nodes or other elements)
      if (event.target === svgRef.current) {
        if (onSelectionChange) {
          onSelectionChange(ImmutableSet());
        }
        if (onLinkSelectionChange) {
          onLinkSelectionChange([]);
        }
        setSelectionBox(null);
      }
    });

    return () => {
      simulation.stop();
    };
  }, [
    width,
    height,
    onSelectionChange,
    onLinkSelectionChange,
    handleSelectionBoxComplete,
  ]);

  useTraceUpdate({
    loadingNodes,
    filteredNodes,
    filteredLinks,
    linkColorFunction,
    width,
    height,
    nodeColorFunction,
    onNodeLoading,
    selectedNodeIds,
    onSelectionChange,
    onLinkSelectionChange,
    onNewLink,
    handleSelectionBoxComplete,
  });

  // Effect to handle adding new nodes to existing simulation
  useEffect(() => {
    if (!simulationRef.current) return;

    const simulation = simulationRef.current;
    let internalNodes = simulation.nodes();
    const currentNodes: PositionedGraphNode[] = filteredNodes.map((node) => {
      const oldNode = internalNodes.find((n) => n.id === node.id);
      if (oldNode) {
        // Preserve the existing node object and update only changed properties
        Object.assign(oldNode, {
          kind: node.kind,
          dataProps: node.dataProps,
          // Preserve position properties
          x: oldNode.x,
          y: oldNode.y,
          fx: oldNode.fx,
          fy: oldNode.fy,
        });
        return oldNode; // Return the same object reference
      }
      const newNode = {
        ...node,
        x: width / 2, // Start at center
        y: height / 2,
        fx: undefined,
        fy: undefined,
      };
      return newNode;
    });
    simulation.nodes(currentNodes);
    internalNodes = simulation.nodes();

    const linkForce = simulation.force('link') as
      | d3.ForceLink<
          PositionedGraphNode,
          PositionedGraphLink<string | SemanticGraphNode>
        >
      | undefined;
    if (!linkForce) {
      throw new Error('Link force not found');
    }
    let internalLinks = linkForce ? linkForce.links() : [];

    // Find new links that aren't in the internal set
    const newLinks = filteredLinks
      .map((currentLink) => {
        const currentLinkId = getLinkId(currentLink);
        const oldLink = internalLinks.find(
          (l) => getLinkId(l) === currentLinkId
        );
        if (!oldLink) {
          const sourceNode = internalNodes.find(
            (n) => n.id === currentLink.source.id
          );
          const targetNode = internalNodes.find(
            (n) => n.id === currentLink.target.id
          );
          if (!sourceNode || !targetNode) {
            throw new Error('Source or target node not found');
          }
          const newLink = {
            ...currentLink,
            source: sourceNode.id,
            target: targetNode.id,
          };
          return newLink;
        }
        return null;
      })
      .filter((link) => link !== null);
    const changedLinks = internalLinks
      .map((currentLink) => {
        const currentLinkId = getLinkId(currentLink);
        const oldLink = filteredLinks.find(
          (l) => getLinkId(l) === currentLinkId
        );
        if (!oldLink) {
          return null;
        }
        if (
          typeof oldLink.target === 'string' ||
          typeof oldLink.source === 'string'
        ) {
          throw new Error('Link source or target is a string');
        }
        return currentLink;
      })
      .filter((link) => link !== null);

    // Add new links to simulation
    const newInternalLinks = [...changedLinks, ...newLinks];
    linkForce.links(newInternalLinks);
    internalLinks = linkForce.links();

    simulation.alpha(0.3).restart();

    // Update visual elements for new nodes
    if (!svgRef.current) {
      return;
    }
    const svg = d3.select(svgRef.current);
    const graphGroup = svg.select('g');
    const nodeSize = 10;

    // Update node groups
    const nodeGroup = graphGroup.select('g.node-group');

    const allNodes = nodeGroup
      .selectAll<SVGGElement, PositionedGraphNode>('g.node')
      .data(internalNodes, function (d) {
        return d.id;
      })
      .join(
        (enter) => {
          const nodesEnter = enter.append('g');
          initializeNodeGroups(
            nodesEnter,
            simulation,
            nodeSize,
            width,
            height,
            setTooltip,
            setLoadingNodes,
            nodeColorFunction,
            onNodeLoading,
            internalNodesRef.current,
            selectedNodeIds,
            onSelectionChange,
            onNewLink,
            svgRef.current || undefined
          );
          return nodesEnter;
        },
        (update) => {
          initializeNodeGroups(
            update,
            simulation,
            nodeSize,
            width,
            height,
            setTooltip,
            setLoadingNodes,
            nodeColorFunction,
            onNodeLoading,
            internalNodesRef.current,
            selectedNodeIds,
            onSelectionChange,
            onNewLink,
            svgRef.current || undefined,
            true
          );
          return update;
        },
        (exit) => {
          return exit.remove();
        }
      );

    // Group links by source-target pairs to handle multiple links between same nodes
    const linkCategories = new Map<string, SemanticGraphSingleLink[]>();
    (internalLinks as PositionedGraphLink<SemanticGraphNode>[]).forEach(
      (link) => {
        const key = getLinkShortId(link);
        const reverseKey = getLinkShortId(link, true);
        for (const kind of link.kind) {
          if (linkCategories.has(key)) {
            linkCategories.get(key)!.push({
              singleKind: kind,
              source: link.source,
              target: link.target,
            });
          } else if (linkCategories.has(reverseKey)) {
            linkCategories.get(reverseKey)!.push({
              singleKind: kind,
              source: link.source,
              target: link.target,
            });
          } else {
            linkCategories.set(key, [
              { singleKind: kind, source: link.source, target: link.target },
            ]);
          }
        }
      }
    );

    // Update link paths
    const linkGroup = graphGroup.select('g.link-group');
    const linksSelector = linkGroup
      .selectAll<SVGPathElement, SemanticGraphLink>('path.link')
      .data(internalLinks, (d) => getLinkId(d));

    linksSelector.exit().remove();

    const linksEnter = linksSelector
      .enter()
      .append('path')
      .classed('link', true)
      .attr('stroke', (d) => {
        return linkColorFunction(d.kind[0] || '');
      })
      .attr('stroke-width', 3)
      .attr('fill', 'none')
      .attr('marker-end', () => `url(#arrow-marker)`)
      .style('cursor', 'pointer')
      .on('mouseover', function (event, d) {
        setTooltip({
          x: event.pageX + nodeSize,
          y: event.pageY - nodeSize,
          link: normalizeLink(d),
        });
      })
      .on('mouseout', function () {
        setTooltip(null);
      })
      .on('click', function (event, d) {
        event.stopPropagation();
        if (onLinkSelectionChange) {
          const linkId = getLinkId(d);
          const linkObject: SemanticGraphLink<string> = {
            source: typeof d.source === 'string' ? d.source : d.source.id,
            target: typeof d.target === 'string' ? d.target : d.target.id,
            kind: d.kind,
          };

          if (event.shiftKey) {
            // Multi-select with Ctrl/Cmd key
            onLinkSelectionChange((prev) =>
              prev.some((link) => getLinkId(link) === linkId)
                ? prev.filter((link) => getLinkId(link) !== linkId)
                : [...prev, linkObject]
            );
          } else {
            // Single select
            onLinkSelectionChange([linkObject]);
          }
        }
      });

    // Merge enter and update selections
    const allLinks = linksEnter.merge(linksSelector);

    createLoadingSpinners(
      allNodes,
      loadingNodes,
      10 // nodeSize
    );

    // Create tick function for node updates
    const nodeTickFunction = () => {
      // Update node positions (this will move both the node and its label together)
      allNodes.attr('transform', (d) => `translate(${d.x || 0}, ${d.y || 0})`);

      allLinks.attr('d', (d) => {
        const source = d.source as PositionedGraphNode;
        const target = d.target as PositionedGraphNode;

        const sourceX = source.x || 0;
        const sourceY = source.y || 0;

        // Calculate the base direction from source to target
        const dx = (target.x || 0) - sourceX;
        const dy = (target.y || 0) - sourceY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance === 0) return '';

        // Find how many links exist between these two nodes
        const key = getLinkShortId(d);
        const reverseKey = getLinkShortId(d, true);
        const linkGroup =
          linkCategories.get(key) || linkCategories.get(reverseKey) || [];
        const linkCount = linkGroup.length;

        // Calculate the angle for this specific link
        let angleOffset = 0;
        if (linkCount > 1) {
          // Find the index of this link in the group
          const linkIndex = linkGroup.findIndex(
            (l) =>
              getLinkId(l) === getLinkId(d) ||
              getLinkId(l, true) === getLinkId(d, true)
          );

          if (linkIndex !== -1) {
            // Divide the semicircle into linkCount sections
            const sectionAngle = Math.PI / linkCount;
            // Start from -π/2 (left side) and go to π/2 (right side)
            angleOffset = (linkIndex - (linkCount - 1) / 2) * sectionAngle;
          }
        }

        // Calculate perpendicular direction for the curve
        const baseAngle = Math.atan2(dy, dx);
        const curveAngle = baseAngle + angleOffset;

        // Calculate control points for the curve
        const curveDistance = Math.min(distance * 0.3, 50); // Limit curve distance
        const controlX = sourceX + Math.cos(curveAngle) * curveDistance;
        const controlY = sourceY + Math.sin(curveAngle) * curveDistance;

        // Calculate end points (avoiding node overlap)
        const nodeRadius = nodeSize;
        const arrowOffset = nodeSize + 5;
        const totalOffset = nodeRadius + arrowOffset;

        if (distance <= totalOffset * 2) {
          // Nodes are too close, draw a straight line
          const ratio = totalOffset / distance;
          const endX = sourceX + dx * ratio;
          const endY = sourceY + dy * ratio;
          return `M ${sourceX} ${sourceY} L ${endX} ${endY}`;
        } else {
          // Draw curved path
          const ratio = (distance - totalOffset) / distance;
          const endX = sourceX + dx * ratio;
          const endY = sourceY + dy * ratio;
          return `M ${sourceX} ${sourceY} Q ${controlX} ${controlY} ${endX} ${endY}`;
        }
      });
    };

    // Update selection styling for existing nodes
    allNodes.each(function (d) {
      const nodeGroup = d3.select(this);
      const isSelected = selectedNodeIds.includes(d.id);
      nodeGroup
        .selectAll('circle.main-kind-circle')
        .attr('stroke', isSelected ? '#007bff' : '#fff')
        .attr('stroke-width', isSelected ? 3 : 1);
    });

    // Register the tick function
    tickFunctionsNodesRef.current = nodeTickFunction;
  }, [
    loadingNodes,
    filteredNodes,
    filteredLinks,
    linkColorFunction,
    width,
    height,
    nodeColorFunction,
    onNodeLoading,
    selectedNodeIds,
    onSelectionChange,
    onLinkSelectionChange,
    onNewLink,
    handleSelectionBoxComplete,
  ]);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const graphGroup = svg.select('g');
    const linkGroup = graphGroup.select('g.link-group');

    const linksSelector = linkGroup.selectAll<
      SVGPathElement,
      SemanticGraphLink
    >('path.link');

    // Update selection styling for existing links
    linksSelector
      .attr('stroke', (d) => {
        const linkId = getLinkId(d);
        const isSelected = selectedLinkIds.some(
          (selectedLink) => getLinkId(selectedLink) === linkId
        );
        return isSelected ? '#007bff' : linkColorFunction(d.kind[0] || '');
      })
      .attr('stroke-width', (d) => {
        const linkId = getLinkId(d);
        const isSelected = selectedLinkIds.some(
          (selectedLink) => getLinkId(selectedLink) === linkId
        );
        return isSelected ? 5 : 3;
      });
  }, [selectedLinkIds]);

  const tooltipData = useMemo(() => {
    if (!tooltip) {
      return null;
    }
    if ('nodeId' in tooltip) {
      const node = graphData.get(tooltip.nodeId);
      if (!node) {
        return null;
      }
      return {
        ...tooltip,
        kind: node.kind,
        dataProps: node.dataProps,
      };
    }
    return {
      ...tooltip,
      kind: tooltip.link.kind,
    };
  }, [tooltip, graphData]);
  return (
    <>
      <div
        style={{
          marginLeft: '40px', // Space for the menu toggle button
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          // minHeight: '100vh',
        }}
      >
        <div
          style={{
            width: width,
            height: height,
            border: '1px solid #ccc',
            cursor: 'grab',
            overflow: 'hidden',
          }}
        >
          <svg
            ref={svgRef}
            width={width}
            height={height}
            style={{
              position: 'relative',
              top: 0,
              left: 0,
            }}
          >
            <defs>
              <marker
                id="arrow-marker"
                viewBox="0 -5 10 10"
                refX={10}
                refY={0}
                markerWidth={6}
                markerHeight={6}
                orient="auto"
              >
                <path d="M0,-5L10,0L0,5" fill="#ccc" />
              </marker>
            </defs>
          </svg>
        </div>
      </div>

      {tooltipData && (
        <div
          style={{
            position: 'absolute',
            left: tooltipData.x,
            top: tooltipData.y,
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            color: 'white',
            padding: '12px',
            borderRadius: '6px',
            fontSize: '12px',
            zIndex: 1000,
            pointerEvents: 'none',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
            maxWidth: '250px',
          }}
        >
          <div
            style={{
              fontWeight: 'bold',
              marginBottom: '8px',
              borderBottom: '1px solid #555',
              paddingBottom: '4px',
            }}
          >
            {'id' in tooltipData &&
              typeof tooltipData.id === 'string' &&
              tooltipData.id}{' '}
            {
              normalizeKinds(tooltipData.kind).map((kind) => (
                <div key={kind}>{kind}</div>
              ))
            }
          </div>
          {'dataProps' in tooltipData &&
            tooltipData.dataProps.map((prop, index) => (
              <div key={index} style={{ marginBottom: '4px' }}>
                <span style={{ color: '#ccc' }}>{prop.key}:</span>{' '}
                <span
                  style={{
                    color:
                      typeof prop.value === 'boolean'
                        ? prop.value
                          ? '#4ade80'
                          : '#f87171'
                        : '#fff',
                  }}
                >
                  {typeof prop.value === 'boolean'
                    ? prop.value
                      ? 'Yes'
                      : 'No'
                    : String(prop.value)}
                </span>
              </div>
            ))}
        </div>
      )}
    </>
  );
}
