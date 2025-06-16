import { ReactNode } from "react";
import { CheckCircle, AlertCircle, Info, List, FileText, Code } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface MessageContent {
    type: "text" | "list" | "preview" | "error" | "success" | "info" | "code";
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

interface MessageFormatterProps {
    content: MessageContent | string;
    className?: string;
}

export function MessageFormatter({ content, className }: MessageFormatterProps) {
    // Handle legacy string content
    if (typeof content === "string") {
        return <div className={cn("text-sm", className)}>{content}</div>;
    }

    const renderContent = (): ReactNode => {
        switch (content.type) {
            case "text":
                return (
                    <div className="text-sm whitespace-pre-wrap">{content.content as string}</div>
                );

            case "list":
                const items = content.content as string[];
                return (
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm font-medium">
                            <List className="h-4 w-4" />
                            <span>Items</span>
                        </div>
                        <ul className="space-y-1 text-sm">
                            {items.map((item, index) => (
                                <li key={index} className="flex items-start gap-2">
                                    <span className="text-muted-foreground">•</span>
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                );

            case "preview":
                const preview = content.content as PreviewContent;
                return (
                    <Card className="border-l-4 border-l-primary">
                        <CardContent className="pt-4">
                            <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                    <FileText className="h-4 w-4" />
                                    <h4 className="font-medium">{preview.title}</h4>
                                </div>
                                {preview.description && (
                                    <p className="text-sm text-muted-foreground">
                                        {preview.description}
                                    </p>
                                )}
                                {preview.items && (
                                    <div className="space-y-2">
                                        {preview.items.map((item, index) => (
                                            <div
                                                key={index}
                                                className="flex items-center justify-between py-1"
                                            >
                                                <span className="text-sm font-medium">
                                                    {item.label}:
                                                </span>
                                                {item.type === "badge" ? (
                                                    <Badge variant="secondary">{item.value}</Badge>
                                                ) : item.type === "code" ? (
                                                    <code className="bg-muted px-2 py-1 rounded text-xs">
                                                        {item.value}
                                                    </code>
                                                ) : (
                                                    <span className="text-sm text-muted-foreground">
                                                        {item.value}
                                                    </span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {preview.actions && (
                                    <div className="flex gap-2 pt-2 border-t">
                                        {preview.actions.map((action, index) => (
                                            <Badge
                                                key={index}
                                                variant={action.variant || "outline"}
                                                className="cursor-pointer hover:opacity-80"
                                            >
                                                {action.label}
                                            </Badge>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                );

            case "code":
                const codeContent = content.content as CodeContent;
                return (
                    <div className="space-y-2">
                        {codeContent.title && (
                            <div className="flex items-center gap-2 text-sm font-medium">
                                <Code className="h-4 w-4" />
                                <span>{codeContent.title}</span>
                            </div>
                        )}
                        <div className="bg-muted rounded-md p-3 overflow-x-auto">
                            <div className="text-xs text-muted-foreground mb-2">
                                {codeContent.language}
                            </div>
                            <pre className="text-sm">
                                <code>{codeContent.code}</code>
                            </pre>
                        </div>
                    </div>
                );

            case "success":
                return (
                    <div className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded-md">
                        <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <div className="text-sm text-green-800">{content.content as string}</div>
                    </div>
                );

            case "error":
                return (
                    <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
                        <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                        <div className="text-sm text-red-800">{content.content as string}</div>
                    </div>
                );

            case "info":
                return (
                    <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                        <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div className="text-sm text-blue-800">{content.content as string}</div>
                    </div>
                );

            default:
                return <div className="text-sm text-muted-foreground">Unknown message type</div>;
        }
    };

    return <div className={cn("space-y-2", className)}>{renderContent()}</div>;
}

// Helper functions for creating formatted messages
export const createTextMessage = (text: string): MessageContent => ({
    type: "text",
    content: text,
});

export const createListMessage = (items: string[]): MessageContent => ({
    type: "list",
    content: items,
});

export const createPreviewMessage = (preview: PreviewContent): MessageContent => ({
    type: "preview",
    content: preview,
});

export const createCodeMessage = (
    code: string,
    language: string,
    title?: string,
): MessageContent => ({
    type: "code",
    content: { code, language, title },
});

export const createSuccessMessage = (text: string): MessageContent => ({
    type: "success",
    content: text,
});

export const createErrorMessage = (text: string): MessageContent => ({
    type: "error",
    content: text,
});

export const createInfoMessage = (text: string): MessageContent => ({
    type: "info",
    content: text,
});
