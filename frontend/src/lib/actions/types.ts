/**
 * Action type definitions for frontend actions triggered by the agent
 */

import { PolicyDefinitionDictInput } from "@vulkan-server/PolicyDefinitionDictInput";

// Base action interface
export interface FrontendAction {
    type: string;
    payload: any;
    requiresConfirmation: boolean;
    description: string;
}

// Workflow-specific actions
export interface UpdateWorkflowSpecAction extends FrontendAction {
    type: "UPDATE_WORKFLOW_SPEC";
    payload: {
        workflowSpec: PolicyDefinitionDictInput;
        reason?: string;
    };
    requiresConfirmation: true;
    description: string;
}

// Union type of all possible actions
export type AgentAction = UpdateWorkflowSpecAction;

// Action execution result
export interface ActionResult {
    success: boolean;
    error?: string;
    data?: any;
}

// Action confirmation dialog props
export interface ActionConfirmationProps {
    action: AgentAction;
    onConfirm: () => Promise<void>;
    onCancel: () => void;
    isExecuting: boolean;
}
