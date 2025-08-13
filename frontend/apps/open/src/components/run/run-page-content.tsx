// Use shared run page content with local workflow frame
import { SharedRunPageContent } from "@vulkanlabs/base";
import { WorkflowFrame } from "@/components/run/frame";
import type { RunNodeLayout } from "@/components/run/types";
import { EdgeLayoutConfig } from "@vulkanlabs/base";
import type { RunData, RunLogs } from "@vulkanlabs/client-open";

export default function RunPageContent({
    nodes,
    edges,
    runLogs,
    runData,
}: {
    nodes: RunNodeLayout[];
    edges: EdgeLayoutConfig[];
    runLogs: RunLogs;
    runData: RunData;
}) {
    return (
        <SharedRunPageContent
            nodes={nodes}
            edges={edges}
            runLogs={runLogs}
            runData={runData}
            config={{
                WorkflowFrame,
                RunNodeLayout,
                containerOverflow: "hidden",
                sidebarOverflow: "hidden", 
                tableClass: "w-full",
                useResponsiveColumns: true,
            }}
        />
    );
}
