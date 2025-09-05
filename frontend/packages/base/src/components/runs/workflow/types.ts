import type { Node, Position } from "@xyflow/react";

import { StepDetails, DependencyDict } from "@vulkanlabs/client-open";

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

export interface NodeData extends Record<string, unknown> {
    label: string;
    type: string;
    description?: string | null;
    dependencies?: { [key: string]: DependencyDict } | null;
    metadata?: { [key: string]: any } | null;
    run?: StepDetails;
    clicked?: boolean;
}
export interface ReactflowEdge {
    id: string;
    source: string;
    target: string;
}

export type ReactflowNode = Node<NodeData>;

export type ELKLayoutedNode = ReactflowNode & {
    x?: number;
    y?: number;
    layoutOptions?: Record<string, string>;
    children?: ELKLayoutedNode[];
};
