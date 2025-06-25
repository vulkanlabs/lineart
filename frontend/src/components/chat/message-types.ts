/**
 * Type definitions for message content
 */

export interface MessageContent {
    type: "text" | "markdown" | "list" | "preview" | "error" | "success" | "info" | "code";
    content: string | string[] | PreviewContent | CodeContent;
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
