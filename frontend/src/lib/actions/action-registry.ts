/**
 * Registry of available frontend actions
 */

import { AgentAction, ActionResult } from "./types";

export type ActionHandler = (action: AgentAction) => Promise<ActionResult>;

class ActionRegistryImpl {
    private handlers = new Map<string, ActionHandler>();

    register(actionType: string, handler: ActionHandler): void {
        this.handlers.set(actionType, handler);
    }

    unregister(actionType: string): void {
        this.handlers.delete(actionType);
    }

    getHandler(actionType: string): ActionHandler | undefined {
        return this.handlers.get(actionType);
    }

    isActionSupported(actionType: string): boolean {
        return this.handlers.has(actionType);
    }

    getSupportedActions(): string[] {
        return Array.from(this.handlers.keys());
    }
}

// Singleton instance
export const actionRegistry = new ActionRegistryImpl();

// Helper functions
export function registerAction(actionType: string, handler: ActionHandler): void {
    actionRegistry.register(actionType, handler);
}

export function isActionSupported(actionType: string): boolean {
    return actionRegistry.isActionSupported(actionType);
}

export function getSupportedActions(): string[] {
    return actionRegistry.getSupportedActions();
}
