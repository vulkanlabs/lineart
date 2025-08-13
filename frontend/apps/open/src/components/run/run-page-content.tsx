// OSS App - Use shared run page content
import { SharedRunPageContent } from "@vulkanlabs/base";
import { WorkflowFrame } from "@/components/run/frame";
import type { RunNodeLayout } from "@/components/run/types";
import { EdgeLayoutConfig } from "@/lib/workflow/types";
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
