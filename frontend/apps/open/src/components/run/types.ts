import { NodeLayoutConfig, NodeDependency } from "@/lib/workflow/types";
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