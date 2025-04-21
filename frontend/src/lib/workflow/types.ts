export type NodeDependency = {
    node: string;
    output?: string | null;
    key?: string | null;
};

export type NodeDefinition = {
    name: string;
    node_type: string;
    description: string;
    hidden: boolean;
    metadata: any;
    dependencies?: NodeDependency[];
};

export type GraphDefinition = {
    [key: string]: NodeDefinition;
};

export type Dict = {
    [key: string]: string | number | boolean;
};

export interface NodeLayoutConfig {
    id: string;
    data: {
        label: string;
        description: string;
        type: string;
        dependencies?: NodeDependency[];
    };
    width: number;
    height: number;
    type: string;
    parentId?: string;
    parentReference?: string;
    children?: NodeLayoutConfig[];
    layoutOptions?: Dict;
    targetPosition?: string;
    sourcePosition?: string;
    x?: number;
    y?: number;
}

export interface EdgeLayoutConfig {
    id: string;
    source: string;
    target: string;
    isComponentIO: boolean;
    fromComponentChild?: boolean;
    fromComponent?: string;
    toComponentChild?: boolean;
    toComponent?: string;
}
