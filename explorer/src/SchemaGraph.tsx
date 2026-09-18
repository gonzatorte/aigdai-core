import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import type Immutable from 'immutable';
import { List, Set as ImmutableSet } from 'immutable';

export type SimpleNode = {
  id: string;
  dataProps: string[];
};

export type SimpleLink<T = string> = {
  id: string;
  source: T;
  target: T;
};

export type PositionedSimpleNode = SimpleNode & {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
};

// Selection box type
type SelectionBox = {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
};

// Helper function to get link short ID for grouping
export const getLinkFullId = (
  link: SimpleLink<PositionedSimpleNode | string>
) => {
  return `${link.id}-${getLinkShortId(link)}`;
};

const getLinkShortId = (
  link: SimpleLink<PositionedSimpleNode | string>,
  reverse: boolean = false
) => {
  const first = reverse ? link.target : link.source;
  const last = reverse ? link.source : link.target;
  return `${typeof first === 'string' ? first : first.id}-${
    typeof last === 'string' ? last : last.id
  }`;
};

function calculateLinkPosition(
  linkId: string,
  target: PositionedSimpleNode,
  source: PositionedSimpleNode,
  tolerance: number,
  linkGroup: SimpleLink[]
) {
  const sourceX = source.x || 0;
  const sourceY = source.y || 0;
  const targetX = target.x || 0;
  const targetY = target.y || 0;

  // Calculate the base direction from source to target
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const distance = Math.sqrt(dx * dx + dy * dy);

  if (distance === 0) {
    return {
      distance,
      sourceX,
      sourceY,
      endX: targetX,
      endY: targetY,
      controlX: 0,
      controlY: 0,
    };
  }

  // Find how many links exist between these two nodes
  const linkCount = linkGroup.length;

  // Calculate the angle for this specific link
  let angleOffset = 0;
  if (linkCount > 1) {
    const linkIndex = linkGroup.findIndex((l: SimpleLink) => l.id === linkId);

    if (linkIndex !== -1) {
      const sectionAngle = Math.PI / linkCount;
      angleOffset = (linkIndex - (linkCount - 1) / 2) * sectionAngle;
    }
  }

  // Calculate perpendicular direction for the curve
  const baseAngle = Math.atan2(dy, dx);
  const curveAngle = baseAngle + angleOffset;

  // Calculate control points for the curve
  const curveDistance = Math.min(distance * 0.3, 50);
  const controlX = sourceX + Math.cos(curveAngle) * curveDistance;
  const controlY = sourceY + Math.sin(curveAngle) * curveDistance;

  let endX, endY;
  if (distance <= tolerance * 2) {
    // Nodes are too close, use straight line
    const ratio = tolerance / distance;
    endX = sourceX + dx * ratio;
    endY = sourceY + dy * ratio;
  } else {
    // Use curved path
    const ratio = (distance - tolerance) / distance;
    endX = sourceX + dx * ratio;
    endY = sourceY + dy * ratio;
  }
  return {
    distance,
    sourceX,
    sourceY,
    endX,
    endY,
    controlX,
    controlY,
  };
}

function calculateLinkMidpoint(
  target: PositionedSimpleNode,
  source: PositionedSimpleNode,
  control: { x: number; y: number },
  tolerance: number
) {
  const sourceX = source.x || 0;
  const sourceY = source.y || 0;
  const targetX = target.x || 0;
  const targetY = target.y || 0;
  const distance = Math.sqrt(
    (targetX - sourceX) * (targetX - sourceX) +
      (targetY - sourceY) * (targetY - sourceY)
  );
  if (distance <= tolerance * 2) {
    // For straight lines, use simple midpoint
    const midX = (sourceX + targetX) / 2;
    const midY = (sourceY + targetY) / 2;
    return { midX, midY };
  }
  // For curved paths, calculate midpoint along the curve
  // Use quadratic Bezier formula for midpoint
  const controlX = control.x || 0;
  const controlY = control.y || 0;
  const midX = (sourceX + 2 * controlX + targetX) / 4;
  const midY = (sourceY + 2 * controlY + targetY) / 4;
  return { midX, midY };
}

export default function SchemaGraph({
  simpleGraph,
  width,
  height,
  selectedNodeIds,
  selectedLinkIds,
  onNodeSelectionChange,
  onLinkSelectionChange,
  nodeColorFunction,
  linkColorFunction,
}: {
  simpleGraph: Immutable.MapOf<{
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
  width: number;
  height: number;
  selectedNodeIds: ImmutableSet<string>;
  selectedLinkIds: ImmutableSet<SimpleLink<string>>;
  nodeColorFunction: (kind: string) => string;
  linkColorFunction: (kind: string) => string;
  onNodeSelectionChange: React.Dispatch<
    React.SetStateAction<ImmutableSet<string>>
  >;
  onLinkSelectionChange: React.Dispatch<
    React.SetStateAction<ImmutableSet<SimpleLink<string>>>
  >;
}) {
  // useTraceUpdate({
  //   simpleGraph,
  //   width,
  //   height,
  //   selectedNodeIds,
  //   selectedLinkIds,
  //   onNodeSelectionChange,
  //   onLinkSelectionChange,
  //   nodeColorFunction,
  //   linkColorFunction,
  // });
  const svgMainGroupRef = useRef<SVGGElement>(null);
  const simulationRef = useRef<d3.Simulation<
    PositionedSimpleNode,
    SimpleLink
  > | null>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    content: React.ReactNode;
  } | null>(null);

  useEffect(() => {
    if (
      !svgMainGroupRef.current ||
      !svgMainGroupRef.current.parentElement ||
      !(svgMainGroupRef.current.parentElement instanceof SVGSVGElement)
    )
      return;
    const svgMainGroup = d3.select(svgMainGroupRef.current);
    svgMainGroup
      .selectAll<SVGGElement, SimpleLink<PositionedSimpleNode>>('.link')
      .attr('stroke', (d) => {
        const isSelected = selectedLinkIds.some(
          (selectedLink) => getLinkFullId(selectedLink) === getLinkFullId(d)
        );
        return isSelected ? '#007bff' : linkColorFunction(d.id);
      })
      .attr('stroke-width', (d) => {
        const isSelected = selectedLinkIds.some(
          (selectedLink) => getLinkFullId(selectedLink) === getLinkFullId(d)
        );
        return isSelected ? 5 : 2;
      });
  }, [selectedLinkIds, linkColorFunction]);

  useEffect(() => {
    if (
      !svgMainGroupRef.current ||
      !svgMainGroupRef.current.parentElement ||
      !(svgMainGroupRef.current.parentElement instanceof SVGSVGElement)
    )
      return;
    const svgMainGroup = d3.select(svgMainGroupRef.current);
    svgMainGroup
      .selectAll<SVGGElement, SimpleNode>('.node')
      .attr('stroke', (d) =>
        selectedNodeIds.includes(d.id) ? '#007bff' : '#000'
      )
      .attr('stroke-width', (d) => (selectedNodeIds.includes(d.id) ? 3 : 2));
  }, [selectedNodeIds]);

  // Function to check if a node is within the selection box
  const isPointInSelectionBox = (
    point: { x?: number; y?: number },
    box: SelectionBox
  ): boolean => {
    if (!point.x || !point.y) return false;

    // Get the current transform of the graph group
    if (!svgMainGroupRef.current) return false;
    const graphGroup = d3.select(svgMainGroupRef.current).select('g');
    const transform = d3.zoomTransform(graphGroup.node() as any);

    // Transform the node coordinates to screen coordinates
    const nodeScreenX = point.x + transform.x;
    const nodeScreenY = point.y + transform.y;

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

  const handleSelectionBoxComplete = useCallback(
    (box: SelectionBox, isMultiSelect: boolean) => {
      if (
        !svgMainGroupRef.current ||
        !svgMainGroupRef.current.parentElement ||
        !(svgMainGroupRef.current.parentElement instanceof SVGSVGElement)
      )
        return;
      const svgMainGroup = d3.select(svgMainGroupRef.current);

      const nodes = svgMainGroup
        .selectAll<SVGGElement, PositionedSimpleNode>('.node')
        .data();
      const nodesInBox = nodes.filter((node) =>
        isPointInSelectionBox(node, box)
      );
      const nodeIdsInBox = nodesInBox.map((node) => node.id);
      if (isMultiSelect) {
        onNodeSelectionChange((prev) => prev.concat(nodeIdsInBox));
      } else {
        onNodeSelectionChange(ImmutableSet(nodeIdsInBox));
      }

      const linksSelector = svgMainGroup.selectAll<
        SVGRectElement,
        SimpleLink<PositionedSimpleNode>
      >('.link-square');
      const linkDatas = linksSelector.data();
      const linkPositions = linksSelector.nodes().map(function (
        link: SVGRectElement
      ) {
        return {
          x: link.x.baseVal.value,
          y: link.y.baseVal.value,
        };
      });
      if (linkPositions.length !== linkDatas.length) {
        throw new Error('Links X and Y lengths do not match');
      }
      const links = linkDatas.map((link, index) => ({
        ...link,
        ...linkPositions[index],
      }));
      const linksInBox = links.filter((link) =>
        isPointInSelectionBox(link, box)
      );
      const linkObjectsInBox = linksInBox.map((link) => ({
        id: link.id,
        source: link.source.id,
        target: link.target.id,
      }));
      if (isMultiSelect) {
        onLinkSelectionChange((prev) => prev.concat(linkObjectsInBox));
      } else {
        onLinkSelectionChange(ImmutableSet(linkObjectsInBox));
      }
    },
    [onNodeSelectionChange, onLinkSelectionChange]
  );

  useEffect(() => {
    if (
      !svgMainGroupRef.current ||
      !svgMainGroupRef.current.parentElement ||
      !(svgMainGroupRef.current.parentElement instanceof SVGSVGElement)
    )
      return;

    // Convert immutable data to plain objects for D3
    const plainNodes = simpleGraph
      .get('nodes')
      .map((node) => ({
        id: node.get('id'),
        dataProps: node.get('dataProps').toArray(),
      }))
      .toArray();

    const plainLinks = simpleGraph.get('links').toJS();
    // Clear previous content
    d3.select(svgMainGroupRef.current).selectAll('*').remove();

    // Create SVG
    const svgMainGroup = d3.select(svgMainGroupRef.current);
    const svg = svgMainGroupRef.current.parentElement as SVGSVGElement;

    const padding = 20;
    // Create force simulation
    const internalLinks = simpleGraph.get('links').toJS();
    const simulation = d3
      .forceSimulation<PositionedSimpleNode, SimpleLink>(plainNodes)
      .force(
        'link',
        d3
          .forceLink<PositionedSimpleNode, SimpleLink>(internalLinks)
          .id((d) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody<PositionedSimpleNode>().strength(-300))
      .force(
        'center',
        d3.forceCenter<PositionedSimpleNode>(width / 2, height / 2)
      )
      .force('collision', d3.forceCollide<PositionedSimpleNode>().radius(30))
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

    // Store simulation reference
    simulationRef.current = simulation;

    // Create a group for all graph elements to enable panning
    const graphGroup = svgMainGroup.append('g');

    // Add bounds rectangle to visualize the containment area
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

    // Add selection box visual element
    graphGroup
      .append('rect')
      .attr('class', 'selection-box')
      .attr('fill', 'rgba(0, 123, 255, 0.1)')
      .attr('stroke', '#007bff')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3')
      .style('pointer-events', 'none')
      .style('display', 'none');

    // Group links by source-target pairs to handle multiple links between same nodes
    const linkCategories = new Map<string, SimpleLink[]>();
    plainLinks.forEach((link) => {
      const key = getLinkShortId(link);
      const linkCategory = linkCategories.get(key);
      if (linkCategory) {
        linkCategory.push(link);
      } else {
        linkCategories.set(key, [link]);
      }
    });

    // Create link groups (each containing a path and a square)
    const linkGroups = svgMainGroup
      .append('g')
      .selectAll<SVGGElement, SimpleLink>('g.link-group')
      .data(internalLinks, (d) => `${d.id}-${d.source}-${d.target}`)
      .join('g')
      .attr('class', 'link-group');

    // Add paths to link groups
    linkGroups
      .append('path')
      .attr('marker-end', 'url(#schema-arrow-marker)')
      .attr('stroke-dasharray', (d) => (d.id === 'subclass' ? '5,5' : 'none'))
      .attr('stroke-opacity', 0.6)
      .attr('fill', 'none')
      .attr('class', 'link')
      .style('cursor', 'pointer')
      .attr('stroke', (d) => linkColorFunction(d.id))
      .attr('stroke-width', 2)
      .on('click', function (event, d) {
        event.stopPropagation();
        const linkObject: SimpleLink<string> = {
          id: d.id,
          source: typeof d.source === 'string' ? d.source : d.source,
          target: typeof d.target === 'string' ? d.target : d.target,
        };

        if (event.shiftKey) {
          // Multi-select with Ctrl/Cmd key
          onLinkSelectionChange((prev) =>
            prev.some((link) => getLinkFullId(link) === getLinkFullId(d))
              ? prev.filterNot(
                  (link) => getLinkFullId(link) === getLinkFullId(d)
                )
              : prev.add(linkObject)
          );
        } else {
          // Single select
          onLinkSelectionChange(ImmutableSet<SimpleLink<string>>([linkObject]));
        }
      });

    // Add squares to link groups
    linkGroups
      .append('rect')
      .attr('width', 8)
      .attr('height', 8)
      .attr('fill', (d) => linkColorFunction(d.id))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .attr('class', 'link-square')
      .on('mouseover', (event, d) => {
        setTooltip({
          x: event.pageX,
          y: event.pageY,
          content: d.id,
        });
      })
      .on('mouseout', () => {
        setTooltip(null);
      });

    // Create node groups (each containing a circle and label)
    const nodeGroups = svgMainGroup
      .append('g')
      .selectAll<SVGGElement, SimpleNode>('g.node-group')
      .data(plainNodes, (d) => d.id)
      .join('g')
      .attr('class', 'node-group')
      .style('cursor', 'pointer')
      .on('click', function (event, d) {
        // Stop event propagation to prevent clearing selection when clicking on nodes
        event.stopPropagation();

        if (event.shiftKey) {
          // Multi-select with Ctrl/Cmd key
          onNodeSelectionChange((prev) =>
            prev.includes(d.id) ? prev.delete(d.id) : prev.add(d.id)
          );
        } else {
          // Single select
          onNodeSelectionChange(ImmutableSet([d.id]));
        }
      });

    // Add circles to node groups
    nodeGroups
      .append('circle')
      .attr('r', 15)
      .attr('fill', (d) => nodeColorFunction(d.id))
      .attr('class', 'node')
      .attr('stroke', '#000')
      .attr('stroke-width', 2)
      .on('mouseover', (event, d) => {
        setTooltip({
          x: event.pageX,
          y: event.pageY,
          content: (
            <>
              {d.dataProps.map((prop) => (
                <div key={prop}>{prop}</div>
              ))}
            </>
          ),
        });
      })
      .on('mouseout', () => {
        setTooltip(null);
      });

    // Add labels to node groups
    nodeGroups
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .text((d) => d.id);

    // Add drag behavior
    const drag = d3
      .drag<SVGGElement, SimpleNode>()
      .on('start', (event) => {
        if (!event.active) simulation.alpha(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on('drag', (event) => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on('end', (event) => {
        if (!event.active) simulation.alpha(0.3).restart();
        event.subject.fx = null;
        event.subject.fy = null;
      });

    nodeGroups.call(drag);

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
        if (event.sourceEvent.target === svg) {
          const [x, y] = d3.pointer(event, svg);

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
        if (event.sourceEvent.target === svg) {
          const [x, y] = d3.pointer(event, svg);

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
        if (event.sourceEvent.target === svg) {
          if (isSelecting && selectionBox) {
            const [x, y] = d3.pointer(event, svg);
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

    const svgSelector = d3.select(svg);
    svgSelector.call(combinedDrag);

    // Add click handler to clear selection when clicking on empty space
    svgSelector.on('click', function (event) {
      // Only clear selection if clicking on the SVG background (not on nodes or other elements)
      if (event.target === svg) {
        onNodeSelectionChange(ImmutableSet([]));
        onLinkSelectionChange(ImmutableSet([]));
        setSelectionBox(null);
      }
    });

    // Update positions on simulation tick
    simulation.on('tick', () => {
      // Update link paths
      const nodeRadius = 15;
      const arrowOffset = 10;
      const totalOffset = nodeRadius + arrowOffset;

      linkGroups.select('path.link').attr('d', (d) => {
        const source = d.source as unknown as PositionedSimpleNode;
        const target = d.target as unknown as PositionedSimpleNode;

        const key = getLinkShortId(d);
        const linkGroup = linkCategories.get(key) || [];

        const { distance, sourceX, sourceY, endX, endY, controlX, controlY } =
          calculateLinkPosition(d.id, source, target, totalOffset, linkGroup);
        if (distance === 0) return '';
        return `M ${sourceX} ${sourceY} Q ${controlX} ${controlY} ${endX} ${endY}`;
      });

      linkGroups.select('rect.link-square').attr('x', (d) => {
        const source = d.source as unknown as PositionedSimpleNode;
        const target = d.target as unknown as PositionedSimpleNode;

        const key = getLinkShortId(d);
        const linkGroup = linkCategories.get(key) || [];

        const { distance, sourceX, controlX, controlY } = calculateLinkPosition(
          d.id,
          source,
          target,
          totalOffset,
          linkGroup
        );
        if (distance === 0) {
          return sourceX - 4;
        }
        return (
          calculateLinkMidpoint(
            source,
            target,
            { x: controlX, y: controlY },
            totalOffset
          ).midX - 4
        );
      });
      linkGroups.select('rect.link-square').attr('y', (d) => {
        const source = d.source as unknown as PositionedSimpleNode;
        const target = d.target as unknown as PositionedSimpleNode;

        const key = getLinkShortId(d);
        const linkGroup = linkCategories.get(key) || [];

        const { distance, sourceY, controlX, controlY } = calculateLinkPosition(
          d.id,
          source,
          target,
          totalOffset,
          linkGroup
        );
        if (distance === 0) {
          return sourceY - 4;
        }
        return (
          calculateLinkMidpoint(
            source,
            target,
            { x: controlX, y: controlY },
            totalOffset
          ).midY - 4
        );
      });
      nodeGroups.attr(
        'transform',
        (d: PositionedSimpleNode) => `translate(${d.x},${d.y})`
      );
    });

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [
    simpleGraph,
    width,
    height,
    onLinkSelectionChange,
    onNodeSelectionChange,
    handleSelectionBoxComplete,
    linkColorFunction,
    nodeColorFunction,
  ]);

  return (
    <div
      style={{
        width: width,
        height: height,
        border: '1px solid #ccc',
        overflow: 'hidden',
        marginLeft: '40px', // Space for the menu toggle button
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <svg
        style={{
          border: '1px solid #ccc',
          position: 'relative',
          top: 0,
          left: 0,
        }}
        width={width}
        height={height}
      >
        <defs>
          <marker
            id="schema-arrow-marker"
            viewBox="0 -5 10 10"
            refX={10}
            refY={0}
            markerWidth={8}
            markerHeight={8}
            orient="auto"
          >
            <path d="M0,-5L10,0L0,5" fill="#ccc" />
          </marker>
        </defs>
        <g ref={svgMainGroupRef} />
      </svg>
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            left: tooltip.x + 10,
            top: tooltip.y - 10,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '14px',
            pointerEvents: 'none',
            zIndex: 1000,
          }}
        >
          {tooltip.content}
        </div>
      )}
    </div>
  );
}
