import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { MessageContent } from "./message-types";
import {
    MarkdownRenderer,
    ListRenderer,
    PreviewRenderer,
    CodeRenderer,
    StatusRenderer,
} from "./message-renderers";

interface MessageFormatterProps {
    content: MessageContent | string;
    className?: string;
}

export function MessageFormatter({ content, className }: MessageFormatterProps) {
    // Handle legacy string content - render as markdown by default
    if (typeof content === "string") {
        return <MarkdownRenderer content={content} className={className} />;
    }

    const renderContent = (): ReactNode => {
        switch (content.type) {
            case "text":
                return (
                    <div className="text-sm whitespace-pre-wrap">{content.content as string}</div>
                );

            case "markdown":
                return <MarkdownRenderer content={content.content as string} />;

            case "list":
                return <ListRenderer content={content.content as string[]} />;

            case "preview":
                return <PreviewRenderer content={content.content as any} />;

            case "code":
                return <CodeRenderer content={content.content as any} />;

            case "success":
                return <StatusRenderer content={content.content as string} type="success" />;

            case "error":
                return <StatusRenderer content={content.content as string} type="error" />;

            case "info":
                return <StatusRenderer content={content.content as string} type="info" />;

            default:
                return <div className="text-sm text-muted-foreground">Unknown message type</div>;
        }
    };

    return <div className={cn("space-y-2", className)}>{renderContent()}</div>;
}

// Re-export types and helpers for convenience
export type { MessageContent, PreviewContent, CodeContent } from "./message-types";
export {
    createTextMessage,
    createMarkdownMessage,
    createListMessage,
    createPreviewMessage,
    createCodeMessage,
    createJsonMessage,
    createSuccessMessage,
    createErrorMessage,
    createInfoMessage,
} from "./message-utils";
