"use client";

import { cn } from "../../lib/utils";

interface JSONViewerProps {
    data: any;
    className?: string;
}

/**
 * JSON viewer component with syntax highlighting
 * Displays JSON data in a formatted, readable way
 */
export function JSONViewer({ data, className }: JSONViewerProps) {
    const jsonString = typeof data === "string" ? data : JSON.stringify(data, null, 2);

    return (
        <pre
            className={cn(
                "p-4 bg-muted rounded-md overflow-auto text-sm font-mono",
                "border border-border",
                className,
            )}
        >
            <code className="text-foreground">{jsonString}</code>
        </pre>
    );
}
