import {
    AppWorkflowFrame as SharedAppWorkflowFrame,
    type BasicWorkflowFrameProps,
    type AppWorkflowFrameConfig,
} from "@vulkanlabs/base";

// Local workflow configuration
const workflowConfig: AppWorkflowFrameConfig = {
    requirePolicyId: false,
    passProjectIdToFrame: true,
};

// Re-export the props type for backward compatibility
export type AppWorkflowFrameProps = BasicWorkflowFrameProps;

// Local AppWorkflowFrame wrapper
export function AppWorkflowFrame(props: AppWorkflowFrameProps) {
    return <SharedAppWorkflowFrame {...props} config={workflowConfig} />;
}
