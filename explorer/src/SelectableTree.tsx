import React, { useState, useCallback, useMemo } from 'react';
import { Tree } from './types';
import { flattenForest, someDescendantsSelected } from './lib/util';

function TreeNode({
  tree,
  level,
  selectedItems,
  collapsedItems,
  onItemSelect,
  onItemToggle,
  indentSize,
}: {
  tree: Tree;
  level: number;
  selectedItems: string[];
  collapsedItems: Set<string>;
  onItemSelect: (itemId: string) => void;
  onItemToggle: (itemId: string) => void;
  indentSize: number;
}) {
  const isSelected = selectedItems.includes(tree.item.id);
  const isCollapsed = collapsedItems.has(tree.item.id);
  const hasChildren = tree.children.length > 0;

  const someChildrenSelected = someDescendantsSelected(tree, selectedItems);

  return (
    <div>
      <div
        onClick={() => onItemSelect(tree.item.id)}
        style={{
          padding: '12px 16px',
          paddingLeft: `${16 + level * indentSize}px`,
          borderBottom: '1px solid #2c3e50',
          backgroundColor: isSelected ? '#3498db' : 'transparent',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          transition: 'background-color 0.2s ease',
        }}
        onMouseEnter={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = '#2c3e50';
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = 'transparent';
          }
        }}
      >
        {/* Selection Checkbox */}
        <input
          type="checkbox"
          checked={isSelected}
          ref={(input) => {
            if (input) {
              input.indeterminate = !isSelected && someChildrenSelected;
            }
          }}
          onChange={() => onItemSelect(tree.item.id)}
          onClick={(e) => e.stopPropagation()}
          style={{
            margin: 0,
            cursor: 'pointer',
          }}
        />

        {/* Expand/Collapse Icon */}
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onItemToggle(tree.item.id);
            }}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              color: '#bdc3c7',
              fontSize: '12px',
              width: '16px',
              height: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'transform 0.2s ease',
              transform: isCollapsed ? 'rotate(0deg)' : 'rotate(90deg)',
            }}
            title={isCollapsed ? 'Expand children' : 'Collapse children'}
          >
            ▶
          </button>
        )}

        {/* Item Content */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: isSelected ? '#fff' : '#ecf0f1',
              marginBottom: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            {/* Color Indicator */}
            {tree.item.color && (
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: tree.item.color,
                  flexShrink: 0,
                }}
              />
            )}
            {tree.item.title || tree.item.id}
          </div>
          {tree.item.description && (
            <div
              style={{
                fontSize: '12px',
                color: isSelected ? '#bdc3c7' : '#95a5a6',
                marginLeft: '20px', // Align with title text (after color indicator)
              }}
            >
              {tree.item.description}
            </div>
          )}
        </div>
      </div>

      {/* Render children if not collapsed */}
      {hasChildren &&
        !isCollapsed &&
        tree.children.map((child) => (
          <TreeNode
            key={child.item.id}
            tree={child}
            level={level + 1}
            selectedItems={selectedItems}
            collapsedItems={collapsedItems}
            onItemSelect={onItemSelect}
            onItemToggle={onItemToggle}
            indentSize={indentSize}
          />
        ))}
    </div>
  );
}

export default function SelectableTree({
  trees,
  selectedItems,
  onSelectionChange,
  onSelectionSet,
  maxHeight = 400,
  indentSize = 20,
}: {
  trees: Tree[];
  selectedItems: string[];
  onSelectionChange: (selectedId: string) => void;
  onSelectionSet: (selectedIds: string[]) => void;
  maxHeight?: number;
  indentSize?: number;
}) {
  const [collapsedItems, setCollapsedItems] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState('');

  const qq = query.trim().toLowerCase();
  const visibleTrees = useMemo(() => {
    if (!qq) return trees;
    const filterNode = (
      node: Tree
    ): { tree: Tree; isSelected: boolean } | null => {
      const title = (node.item.title || node.item.id).toLowerCase();
      const matchingChildren = node.children
        .map(filterNode)
        .filter((t): t is { tree: Tree; isSelected: boolean } => Boolean(t));
      const isSelected = selectedItems.includes(node.item.id);
      if (title.includes(qq) || isSelected || matchingChildren.length > 0) {
        return {
          tree: {
            item: node.item,
            children: matchingChildren.map((t) => t.tree),
          },
          isSelected,
        };
      }
      return null;
    };
    return trees
      .map(filterNode)
      .filter((t): t is { tree: Tree; isSelected: boolean } => Boolean(t))
      .map((t) => t.tree);
  }, [trees, qq, selectedItems]);

  // Handle item selection (including children)
  const handleItemSelect = useCallback(
    (itemId: string) => {
      const findItem = (inTrees: Tree[]): Tree | null => {
        for (const node of inTrees) {
          if (node.item.id === itemId) return node;
          const found = findItem(node.children);
          if (found) return found;
        }
        return null;
      };
      const item = findItem(trees);
      if (!item) return;
      onSelectionChange(itemId);
    },
    [onSelectionChange, trees]
  );

  // Handle item collapse/expand
  const handleItemToggle = useCallback(
    (itemId: string) => {
      const newCollapsed = new Set(collapsedItems);
      if (newCollapsed.has(itemId)) {
        newCollapsed.delete(itemId);
      } else {
        newCollapsed.add(itemId);
      }
      setCollapsedItems(newCollapsed);
    },
    [collapsedItems]
  );

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#34495e',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      {/* Search Bar */}
      <div
        style={{
          padding: '8px',
          borderBottom: '1px solid #2c3e50',
          backgroundColor: '#2f4154',
        }}
      >
        <button
          type="button"
          onClick={() => {
            const allVisibles = flattenForest(
              (tree) => tree.item.id,
              visibleTrees
            );
            onSelectionSet(allVisibles);
          }}
        >
          select all
        </button>
        <button
          type="button"
          onClick={() => {
            onSelectionSet([]);
          }}
        >
          deselect all
        </button>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search..."
          style={{
            width: '100%',
            padding: '6px 8px',
            borderRadius: 4,
            border: '1px solid #2c3e50',
            backgroundColor: '#223042',
            color: '#ecf0f1',
          }}
        />
      </div>
      {/* Tree Container */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          maxHeight: maxHeight,
        }}
      >
        {visibleTrees.map((node: Tree) => (
          <TreeNode
            key={node.item.id}
            tree={node}
            level={0}
            selectedItems={selectedItems}
            collapsedItems={collapsedItems}
            onItemSelect={handleItemSelect}
            onItemToggle={handleItemToggle}
            indentSize={indentSize}
          />
        ))}
      </div>
    </div>
  );
}
