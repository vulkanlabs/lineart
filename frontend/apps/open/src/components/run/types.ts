import { NodeLayoutConfig, NodeDependency } from "@vulkanlabs/base";
import { StepDetails } from "@vulkanlabs/client-open";

// Re-export shared base types
export * from "@vulkanlabs/base";

// Local typed version that extends base types
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
