import { NodeLayoutConfig, NodeDependency } from "@vulkanlabs/base";
import { StepDetails } from "@vulkanlabs/client-open";

// Re-export specific base types needed in run components
export type {
    NodeLayoutConfig,
    NodeDependency,
    VulkanNode,
    EdgeLayoutConfig,
} from "@vulkanlabs/base";

export {
    createWorkflowState,
    getLayoutedNodes,
    defaultElkOptions,
    runNodeTypes,
    SharedRunPageContent,
    ShortenedID,
    DetailsButton,
    DatePickerWithRange,
    ResourceTable,
    parseDate,
} from "@vulkanlabs/base";

export { Badge, Button } from "@vulkanlabs/base/ui";

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
