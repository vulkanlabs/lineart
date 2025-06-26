/**
 * Workflow-specific actions that can be triggered by the agent
 */

import { PolicyDefinitionDictInput } from "@vulkan-server/PolicyDefinitionDictInput";
import { AgentAction, ActionResult, UpdateWorkflowSpecAction } from "./types";
import { ActionHandler, registerAction } from "./action-registry";

// Import workflow store functions (we'll need to add these)
// For now we'll use a placeholder approach

class WorkflowActionsImpl {
    private workflowStore: any = null;

    // This will be called to inject the workflow store
    setWorkflowStore(store: any): void {
        this.workflowStore = store;
    }

    async updateWorkflowSpec(action: UpdateWorkflowSpecAction): Promise<ActionResult> {
        try {
            if (!this.workflowStore) {
                throw new Error("Workflow store not available");
            }

            const { workflowSpec, reason } = action.payload;

            // Update the workflow specification
            await this.workflowStore.updateFromSpec(workflowSpec);

            return {
                success: true,
                data: {
                    reason,
                    nodesCount: workflowSpec.nodes.length,
                },
            };
        } catch (error) {
            console.error("Error updating workflow spec:", error);
            return {
                success: false,
                error: error instanceof Error ? error.message : "Failed to update workflow",
            };
        }
    }
}

// Singleton instance
export const workflowActions = new WorkflowActionsImpl();

// Action handlers
export const updateWorkflowSpecHandler: ActionHandler = async (action: AgentAction) => {
    if (action.type !== "UPDATE_WORKFLOW_SPEC") {
        throw new Error(`Invalid action type: ${action.type}`);
    }
    return workflowActions.updateWorkflowSpec(action as UpdateWorkflowSpecAction);
};

// Helper to create UPDATE_WORKFLOW_SPEC action
export function createUpdateWorkflowSpecAction(
    workflowSpec: PolicyDefinitionDictInput,
    description: string,
    reason?: string,
): UpdateWorkflowSpecAction {
    return {
        type: "UPDATE_WORKFLOW_SPEC",
        payload: {
            workflowSpec,
            reason,
        },
        requiresConfirmation: true,
        description,
    };
}

// Register the workflow action handlers
registerAction("UPDATE_WORKFLOW_SPEC", updateWorkflowSpecHandler);
