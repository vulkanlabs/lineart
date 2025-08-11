// Base types that can be used by both apps
// Apps should extend these types with their specific imports

export interface BaseRunNodeData {
    label: string;
    description: string;
    type: string;
    dependencies?: any[]; // Apps should provide their NodeDependency type
    run?: any; // Apps should provide their StepDetails type
}

export interface BaseRunNodeLayout {
    draggable?: boolean;
    data: BaseRunNodeData;
    id: string;
    position?: { x: number; y: number };
    type?: string;
}

export interface RunLogEvent {
    log_type?: string;
    message: string;
    level: string;
}

export interface RunLog {
    timestamp: string;
    step_key?: string;
    source: string;
    event: RunLogEvent;
}

export interface RunLogs {
    run_id: string;
    status: string;
    last_updated_at: string;
    logs: RunLog[];
}