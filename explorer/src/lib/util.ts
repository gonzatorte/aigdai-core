import {
  SemanticGraphLink,
  SemanticGraphLinkBase,
  SemanticGraphNode,
  SemanticGraphSingleLink,
  Tree,
  TreeItem,
} from '../types';
import * as lodash from 'lodash';

function findAllIndexes<T>(
  arr: T[],
  predicate: (item: T) => boolean
): number[] {
  return arr.reduce((acc, item, index) => {
    if (predicate(item)) {
      acc.push(index);
    }
    return acc;
  }, [] as number[]);
}

export function removeNodesFromTree<T>(
  removeCondition: (node: TreeItem<T>) => boolean,
  tree: Tree<T>
): Tree<T>[] {
  if (removeCondition(tree.item)) {
    const forest = tree.children.map((child) =>
      removeNodesFromTree(removeCondition, child)
    );
    return forest[0] ? forest[0].concat(...forest.slice(1)) : [];
  }
  const withChildrenIndexes = findAllIndexes(tree.children, (child) =>
    removeCondition(child.item)
  );
  for (const index of withChildrenIndexes) {
    tree.children.splice(
      index,
      1,
      ...([] as Tree<T>[]).concat(
        ...tree.children.map((child) =>
          removeNodesFromTree(removeCondition, child)
        )
      )
    );
  }
  return [tree];
}

export function removeNodesFromForest<T>(
  removeCondition: (node: TreeItem<T>) => boolean,
  forest: Tree<T>[]
): Tree<T>[] {
  const forestAux = forest.map((tree) =>
    removeNodesFromTree(removeCondition, tree)
  );
  return forestAux[0] ? forestAux[0].concat(...forestAux.slice(1)) : [];
}

export function flattenTree<T>(applyFn: (tree: Tree) => T, tree: Tree): T[] {
  return [applyFn(tree)].concat(
    ...tree.children.map((child) => flattenTree(applyFn, child))
  );
}

export function flattenForest<T>(
  applyFn: (tree: Tree) => T,
  trees: Tree[]
): T[] {
  return ([] as T[]).concat(
    ...trees.map((tree) => flattenTree<T>(applyFn, tree))
  );
}

export function getLeafs<T>(applyFn: (tree: Tree) => T, trees: Tree<T>[]): T[] {
  return ([] as T[]).concat(
    ...trees.map((tree) => flattenTree<T>(applyFn, tree))
  );
}

export function dfsApplyForrest<T, P>(
  applyFn: (tree: TreeItem<T>) => TreeItem<P>,
  trees: Tree<T>[]
): Tree<P>[] {
  return trees.map((tree) => dfsApply(applyFn, tree));
}

export function dfsApply<T, P>(
  applyFn: (tree: TreeItem<T>) => TreeItem<P>,
  tree: Tree<T>
): Tree<P> {
  return {
    item: applyFn(tree.item),
    children: tree.children.map((child) => dfsApply(applyFn, child)),
  };
}

export function createTree<T>(
  getId: (node: T) => string,
  getParentId: (node: TreeItem<T>) => string | null,
  getItemData: (node: T) => TreeItem<T>,
  nodes: T[]
): Tree<T>[] {
  const tt = new Map<string, Tree<T>>(
    nodes.map((node) => [
      getId(node),
      {
        item: {
          ...getItemData(node),
          id: getId(node),
        },
        children: [] as Tree<T>[],
      },
    ])
  );
  const trees = Array.from(tt.values());
  const parentedGroups = Object.entries(
    lodash.groupBy(trees, ({ item }) => getParentId(item))
  );
  const roots =
    parentedGroups.find(([parentId, _items]) => parentId === 'null')?.[1] || [];
  parentedGroups.forEach(([parentId, items]) => {
    tt.get(parentId)?.children.push(...items);
  });
  return roots;
}

export function someDescendantsSelected(
  tree: Tree,
  selectedItems: string[]
): boolean {
  return (
    tree.children.some((child) => selectedItems.includes(child.item.id)) ||
    tree.children.some((child) => someDescendantsSelected(child, selectedItems))
  );
}

export function normalizeKinds(kinds: string[]) {
  return [...new Set([...kinds].sort())];
}

export function serializeKinds(kinds: string[]) {
  return normalizeKinds(kinds).join(',');
}

export function getLinkId(
  link:
    | SemanticGraphLink<string | SemanticGraphNode>
    | SemanticGraphSingleLink<string | SemanticGraphNode>,
  reverse: boolean = false
) {
  return `${getLinkShortId(link, reverse)}-${serializeKinds('kind' in link ? link.kind : [link.singleKind])}`;
}

export function normalizeLink(
  d: SemanticGraphLink<string | SemanticGraphNode>
): SemanticGraphLink<string> {
  return {
    kind: d.kind,
    source: typeof d.source === 'string' ? d.source : d.source.id,
    target: typeof d.target === 'string' ? d.target : d.target.id,
  };
}

export function getLinkShortId(
  link: SemanticGraphLinkBase<string | SemanticGraphNode>,
  reverse: boolean = false
) {
  const first = reverse ? link.target : link.source;
  const last = reverse ? link.source : link.target;
  return `${typeof first === 'string' ? first : first.id}-${
    typeof last === 'string' ? last : last.id
  }`;
}

export function getNodeId(node: SemanticGraphNode) {
  return `${getNodeShortId(node)}-${serializeKinds(node.kind)}`;
}

export function getNodeShortId(node: SemanticGraphNode) {
  return node.id;
}

export function getLinkShortUriId(
  link: SemanticGraphLink<string | SemanticGraphNode>
) {
  const validId = /[^a-zA-Z0-9]/g;
  return `arrow-${(typeof link.source === 'string'
    ? link.source
    : link.source.id
  ).replace(validId, '')}-${(typeof link.target === 'string'
    ? link.target
    : link.target.id
  ).replace(validId, '')}`;
}

// const SURROGATE_PAIR_REGEXP = /[\uD800-\uDBFF][\uDC00-\uDFFF]/gs;
// const NON_ALPHANUMERIC_REGEXP = /([^\#-~| |!])/gs;
// export function encodeEntities(value: string) {
//   return value.
//     replace(/&/g, '&amp;').
//     replace(SURROGATE_PAIR_REGEXP, function(value: string) {
//       const hi = value.charCodeAt(0);
//       const low = value.charCodeAt(1);
//       return '&#' + (((hi - 0xD800) * 0x400) + (low - 0xDC00) + 0x10000) + ';';
//     }).
//     replace(NON_ALPHANUMERIC_REGEXP, function(value: string) {
//       return '&#' + value.charCodeAt(0) + ';';
//     }).
//     replace(/</g, '&lt;').
//     replace(/>/g, '&gt;');
// }
export function encodeEntities(value: string) {
  return new Option(value).innerHTML;
}
