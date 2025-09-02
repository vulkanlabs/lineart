import { StepDetails } from "@vulkanlabs/client-open";

export type RunNodeLayout = NodeLayoutConfig & {
    draggable?: boolean;
    data: {
        label: string;
        description: string;
        type: string;
        dependencies?: NodeDependency[];
        run?: StepDetails;
    };
};

type RunLogEvent = {
    log_type?: string;
    message: string;
    level: string;
};

type RunLog = {
    timestamp: string;
    step_key?: string;
    source: string;
    event: RunLogEvent;
};

export type RunLogs = {
    run_id: string;
    status: string;
    last_updated_at: string;
    logs: RunLog[];
};

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
        metadata?: Record<string, any>;
    };
    width: number;
    height: number;
    type: string;
    draggable?: boolean;
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
}

export type LayoutedNode = NodeLayoutConfig & { position: { x: number; y: number } };
