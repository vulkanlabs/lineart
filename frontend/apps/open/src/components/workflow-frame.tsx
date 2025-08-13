import {
    AppWorkflowFrame as SharedAppWorkflowFrame,
    type GlobalScopeWorkflowFrameProps,
    type AppWorkflowFrameConfig,
} from "@vulkanlabs/base";

// Global scope configuration (no policy isolation)
const globalScopeConfig: AppWorkflowFrameConfig = {
    requirePolicyId: false,
    passProjectIdToFrame: true,
};

// Re-export the props type for backward compatibility
export type AppWorkflowFrameProps = GlobalScopeWorkflowFrameProps;

// Global scope AppWorkflowFrame wrapper
export function AppWorkflowFrame(props: AppWorkflowFrameProps) {
    return <SharedAppWorkflowFrame {...props} config={globalScopeConfig} />;
}
