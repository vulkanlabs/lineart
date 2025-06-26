/**
 * Type definitions for message content
 */

import { AgentAction } from "@/lib/actions/types";

export interface MessageContent {
    type:
        | "text"
        | "markdown"
        | "list"
        | "preview"
        | "error"
        | "success"
        | "info"
        | "code"
        | "action"
        | "workflow-update";
    content:
        | string
        | string[]
        | PreviewContent
        | CodeContent
        | ActionContent
        | WorkflowUpdateContent;
}

export interface ActionContent {
    action: AgentAction;
    preview?: any;
    description: string;
}

export interface WorkflowUpdateContent {
    title: string;
    description: string;
    nodesAdded?: number;
    nodesModified?: number;
    nodesRemoved?: number;
}

export interface PreviewContent {
    title: string;
    description?: string;
    items?: Array<{
        label: string;
        value: string;
        type?: "text" | "code" | "badge";
    }>;
    actions?: Array<{
        label: string;
        action: string;
        variant?: "default" | "outline" | "destructive";
    }>;
}

export interface CodeContent {
    language: string;
    code: string;
    title?: string;
}

/**
 * Helper function to create an action message
 */
export function createActionMessage(
    action: AgentAction,
    description: string,
    preview?: any,
): MessageContent {
    return {
        type: "action",
        content: {
            action,
            description,
            preview,
        } as ActionContent,
    };
}
