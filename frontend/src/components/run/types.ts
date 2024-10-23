export type NodeDependency = {
    node: string;
    output?: string | null;
    key?: string | null;
};

export type NodeDefinition = {
    name: string;
    node_type: string;
    description: string;
    dependencies: NodeDependency[] | null;
    hidden: boolean;
    metadata: any;
};

export type GraphDefinition = {
    [key: string]: NodeDefinition;
};

export type RunStepMetadata = {
    step_name: string;
    node_type: string;
    start_time: number;
    end_time: number;
    error?: string | null;
    extra?: any | null;
};

export type RunStep = {
    output: any;
    metadata: RunStepMetadata | null;
};

export type RunSteps = {
    [key: string]: RunStep;
};

export type RunData = {
    run_id: string;
    last_updated_at: string;
    steps: RunSteps;
};

export type RunNode = NodeDefinition & {
    run: RunStep | null;
}

export type RunLogEvent = {
    log_type?: string;
    message: string;
    level: string;
};

export type RunLog = {
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
