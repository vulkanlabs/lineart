import {
    AppWorkflowFrame as SharedAppWorkflowFrame,
    type OSSWorkflowFrameProps,
    type AppWorkflowFrameConfig,
} from "@vulkanlabs/base";

// OSS-specific configuration
const ossWorkflowConfig: AppWorkflowFrameConfig = {
    requirePolicyId: false,
    passProjectIdToFrame: true,
};

// Re-export the props type for backward compatibility
export type AppWorkflowFrameProps = OSSWorkflowFrameProps;

// OSS-specific AppWorkflowFrame wrapper
export function AppWorkflowFrame(props: AppWorkflowFrameProps) {
    return <SharedAppWorkflowFrame {...props} config={ossWorkflowConfig} />;
}
