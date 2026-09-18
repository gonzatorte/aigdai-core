export type DataProp = { key: string; value: string | number | boolean };

export type SemanticGraphNode = {
  id: string;
  kind: string[];
  dataProps: Array<DataProp>;
};

export type SemanticGraphLinkBase<T = SemanticGraphNode> = {
  source: T;
  target: T;
};

export type SemanticGraphLink<T = SemanticGraphNode> =
  SemanticGraphLinkBase<T> & {
    kind: string[];
  };

export type SemanticGraphSingleLink<T = SemanticGraphNode> =
  SemanticGraphLinkBase<T> & {
    singleKind: string;
  };

export type Neighborhood = {
  target: SemanticGraphNode;
  kind: string[];
};

export type SemanticGraphData = Map<
  string,
  SemanticGraphNode & { links: Neighborhood[] }
>;

export type TreeItem<T> = Omit<T, 'id' | 'title' | 'description' | 'color'> & {
  id: string;
  title?: string;
  description?: string;
  color?: string;
};

export type Tree<T = any> = {
  item: TreeItem<T>;
  children: Tree[];
};
