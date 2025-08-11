import { WorkflowFrame as SharedWorkflowFrame, type RunFrameConfig } from "@vulkanlabs/base";
import type { RunNodeLayout } from "./types";
import type { EdgeLayoutConfig } from "@/lib/workflow/types";
import { layoutGraph } from "@/lib/workflow/graph";

// OSS-specific configuration
const ossRunConfig: RunFrameConfig = {
    layoutGraph: layoutGraph,
};

// OSS-specific WorkflowFrame wrapper
export function WorkflowFrame({ 
    nodes, 
    edges, 
    onNodeClick, 
    onPaneClick 
}: {
    nodes: RunNodeLayout[];
    edges: EdgeLayoutConfig[];
    onNodeClick: (e: React.MouseEvent, node: any) => void;
    onPaneClick: (e: React.MouseEvent) => void;
}) {
    return (
        <SharedWorkflowFrame
            nodes={nodes}
            edges={edges}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            config={ossRunConfig}
        />
    );
}
