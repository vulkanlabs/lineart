import {
    AppWorkflowFrame as SharedAppWorkflowFrame,
    GLOBAL_SCOPE_CONFIG,
    type GlobalScopeWorkflowFrameProps,
} from "@vulkanlabs/base";

// Re-export the props type for backward compatibility
export type AppWorkflowFrameProps = GlobalScopeWorkflowFrameProps;

// Global scope AppWorkflowFrame wrapper with pre-validated configuration
export function AppWorkflowFrame(props: AppWorkflowFrameProps) {
    return <SharedAppWorkflowFrame {...props} config={GLOBAL_SCOPE_CONFIG} />;
}
