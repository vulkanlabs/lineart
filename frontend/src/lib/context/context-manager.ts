/**
 * Central context management for the agent system
 */

import { PageContext, ContextManager } from "./types";

class ContextManagerImpl implements ContextManager {
    private context: PageContext = {
        page: "other",
        route: "",
        params: {},
        data: {},
    };

    getCurrentContext(): PageContext {
        return { ...this.context };
    }

    setContext(newContext: Partial<PageContext>): void {
        this.context = {
            ...this.context,
            ...newContext,
            data: {
                ...this.context.data,
                ...newContext.data,
            },
        };
    }

    updateContextData(data: Partial<PageContext["data"]>): void {
        this.context.data = {
            ...this.context.data,
            ...data,
        };
    }

    isWorkflowPage(): boolean {
        return this.context.page === "workflow";
    }

    // Helper method to extract context from current URL
    updateFromRoute(route: string, params: Record<string, string>): void {
        const isWorkflow = route.includes("/workflow");
        this.setContext({
            page: isWorkflow ? "workflow" : "other",
            route,
            params,
        });
    }
}

// Singleton instance
export const contextManager = new ContextManagerImpl();

// Helper functions
export function getCurrentContext(): PageContext {
    return contextManager.getCurrentContext();
}

export function isOnWorkflowPage(): boolean {
    return contextManager.isWorkflowPage();
}

export function updatePageContext(context: Partial<PageContext>): void {
    contextManager.setContext(context);
}

export function updateContextData(data: Partial<PageContext["data"]>): void {
    contextManager.updateContextData(data);
}
