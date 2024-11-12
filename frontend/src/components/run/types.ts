import { NodeLayoutConfig, NodeDependency } from "@/lib/workflow/types";

export type RunNodeLayout = NodeLayoutConfig & {
    draggable?: boolean;
    data: {
        label: string;
        description: string;
        type: string;
        dependencies?: NodeDependency[];
        run?: RunStep | null;
    };
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

type RunSteps = {
    [key: string]: RunStep;
};

export type RunData = {
    run_id: string;
    last_updated_at: string;
    steps: RunSteps;
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
