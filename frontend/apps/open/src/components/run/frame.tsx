import { WorkflowFrame as SharedWorkflowFrame, type RunFrameConfig } from "@vulkanlabs/base";
import type { RunNodeLayout } from "./types";
import type { EdgeLayoutConfig } from "@vulkanlabs/base";
import { getLayoutedNodes } from "@vulkanlabs/base";

// Global scope run frame configuration
const globalScopeRunConfig: RunFrameConfig = {
    layoutGraph: getLayoutedNodes,
};

// Global scope WorkflowFrame wrapper
export function WorkflowFrame({
    nodes,
    edges,
    onNodeClick,
    onPaneClick,
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
            config={globalScopeRunConfig}
        />
    );
}
