/**
 * Action executor - handles execution of actions with confirmation
 */

import { actionRegistry } from "./action-registry";
import { AgentAction, ActionResult } from "./types";

export class ActionExecutor {
    async executeAction(action: AgentAction): Promise<ActionResult> {
        const handler = actionRegistry.getHandler(action.type);

        if (!handler) {
            return {
                success: false,
                error: `Unsupported action type: ${action.type}`,
            };
        }

        try {
            return await handler(action);
        } catch (error) {
            console.error(`Error executing action ${action.type}:`, error);
            return {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error occurred",
            };
        }
    }

    isActionSupported(actionType: string): boolean {
        return actionRegistry.isActionSupported(actionType);
    }
}

// Singleton instance
export const actionExecutor = new ActionExecutor();

// Helper function
export async function executeAction(action: AgentAction): Promise<ActionResult> {
    return actionExecutor.executeAction(action);
}
