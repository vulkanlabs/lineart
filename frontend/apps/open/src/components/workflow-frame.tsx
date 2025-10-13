import {
    AppWorkflowFrame as SharedAppWorkflowFrame,
    type AppWorkflowFrameProps,
} from "@vulkanlabs/base";

// Global scope AppWorkflowFrame wrapper with pre-validated configuration
export function AppWorkflowFrame(props: AppWorkflowFrameProps) {
    return <SharedAppWorkflowFrame {...props} />;
}
