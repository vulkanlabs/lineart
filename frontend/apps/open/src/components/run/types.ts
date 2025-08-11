import { NodeLayoutConfig, NodeDependency } from "@/lib/workflow/types";
import { StepDetails } from "@vulkanlabs/client-open";

// Re-export shared base types
export * from "@vulkanlabs/base";

// OSS-specific typed version that extends base types
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
