/**
 * Type definitions for the agent context system
 */

import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { PolicyDefinitionDictInput } from "@vulkan-server/PolicyDefinitionDictInput";
import { WorkflowState } from "@/workflow/types";

export interface PageContext {
    page: "workflow" | "other";
    route: string;
    params: Record<string, string>;
    data: {
        policyVersion?: PolicyVersion;
        workflowState?: WorkflowState;
        currentWorkflowSpec?: PolicyDefinitionDictInput;
    };
}

export interface FrontendAction {
    type: string;
    payload: any;
    requiresConfirmation: boolean; // Always true for first draft
}

export interface ActionMessage {
    type: "action";
    content: {
        action: FrontendAction;
        preview?: any;
        description: string;
    };
}

export interface ContextManager {
    getCurrentContext(): PageContext;
    setContext(context: Partial<PageContext>): void;
    updateContextData(data: Partial<PageContext["data"]>): void;
    isWorkflowPage(): boolean;
}
