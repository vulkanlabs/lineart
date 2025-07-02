import { ReactNode } from "react";
import { CheckCircle, AlertCircle, Info, List, FileText, Code } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { PreviewContent, CodeContent } from "./message-types";
import { normalizeLanguage, detectJsonLanguage, processJsonContent } from "./message-utils";

/**
 * Custom code component for markdown rendering with syntax highlighting
 */
function CodeComponent({ className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || "");
    let language = match ? match[1] : "";

    // Normalize language using aliases
    if (language) {
        language = normalizeLanguage(language);
    }

    // Auto-detect JSON if no language specified
    const content = String(children).trim();
    if (!language) {
        const detectedLanguage = detectJsonLanguage(content);
        if (detectedLanguage) {
            language = detectedLanguage;
        }
    }

    const inline = !match && !language;

    return !inline && language ? (
        <SyntaxHighlighter
            style={oneDark as any}
            language={language}
            PreTag="div"
            className="rounded-md !mt-2 !mb-2"
            showLineNumbers={content.split("\n").length > 3}
            {...props}
        >
            {content}
        </SyntaxHighlighter>
    ) : (
        <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
            {children}
        </code>
    );
}

/**
 * Markdown component overrides for consistent styling
 */
const markdownComponents = {
    code: CodeComponent,

    // Style blockquotes
    blockquote({ children }: { children: ReactNode }) {
        return (
            <blockquote className="border-l-4 border-l-primary pl-4 my-4 italic">
                {children}
            </blockquote>
        );
    },

    // Style tables
    table({ children }: { children: ReactNode }) {
        return (
            <div className="overflow-x-auto my-4">
                <table className="min-w-full border border-border rounded-md">{children}</table>
            </div>
        );
    },

    th({ children }: { children: ReactNode }) {
        return (
            <th className="border border-border px-3 py-2 bg-muted font-medium text-left">
                {children}
            </th>
        );
    },

    td({ children }: { children: ReactNode }) {
        return <td className="border border-border px-3 py-2">{children}</td>;
    },

    // Style headings
    h1({ children }: { children: ReactNode }) {
        return <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>;
    },

    h2({ children }: { children: ReactNode }) {
        return <h2 className="text-lg font-semibold mt-3 mb-2">{children}</h2>;
    },

    h3({ children }: { children: ReactNode }) {
        return <h3 className="text-base font-medium mt-2 mb-1">{children}</h3>;
    },

    // Style lists
    ul({ children }: { children: ReactNode }) {
        return <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>;
    },

    ol({ children }: { children: ReactNode }) {
        return <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>;
    },

    li({ children }: { children: ReactNode }) {
        return <li className="text-sm">{children}</li>;
    },

    // Style links
    a({ href, children }: { href?: string; children: ReactNode }) {
        return (
            <a
                href={href}
                className="text-primary hover:underline"
                target="_blank"
                rel="noopener noreferrer"
            >
                {children}
            </a>
        );
    },
};

/**
 * Renders markdown content with syntax highlighting and custom components
 */
export function MarkdownRenderer({
    content,
    className = "",
}: {
    content: string;
    className?: string;
}) {
    const processedContent = processJsonContent(content);

    return (
        <div className={`text-sm prose prose-sm max-w-none ${className}`}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={markdownComponents}
            >
                {processedContent}
            </ReactMarkdown>
        </div>
    );
}

/**
 * Renders list type messages
 */
export function ListRenderer({ content }: { content: string[] }) {
    return (
        <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
                <List className="h-4 w-4" />
                <span>Items</span>
            </div>
            <ul className="space-y-1 text-sm">
                {content.map((item, index) => (
                    <li key={index} className="flex items-start gap-2">
                        <span className="text-muted-foreground">•</span>
                        <span>{item}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}

/**
 * Renders preview type messages
 */
export function PreviewRenderer({ content }: { content: PreviewContent }) {
    return (
        <Card className="border-l-4 border-l-primary">
            <CardContent className="pt-4">
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        <h4 className="font-medium">{content.title}</h4>
                    </div>
                    {content.description && (
                        <p className="text-sm text-muted-foreground">{content.description}</p>
                    )}
                    {content.items && (
                        <div className="space-y-2">
                            {content.items.map((item, index) => (
                                <div key={index} className="flex items-center justify-between py-1">
                                    <span className="text-sm font-medium">{item.label}:</span>
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
                    {content.actions && (
                        <div className="flex gap-2 pt-2 border-t">
                            {content.actions.map((action, index) => (
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
}

/**
 * Renders code type messages
 */
export function CodeRenderer({ content }: { content: CodeContent }) {
    return (
        <div className="space-y-2">
            {content.title && (
                <div className="flex items-center gap-2 text-sm font-medium">
                    <Code className="h-4 w-4" />
                    <span>{content.title}</span>
                </div>
            )}
            <div className="bg-muted rounded-md p-3 overflow-x-auto">
                <div className="text-xs text-muted-foreground mb-2">{content.language}</div>
                <pre className="text-sm">
                    <code>{content.code}</code>
                </pre>
            </div>
        </div>
    );
}

/**
 * Renders status messages (success, error, info)
 */
export function StatusRenderer({
    content,
    type,
}: {
    content: string;
    type: "success" | "error" | "info";
}) {
    const configs = {
        success: {
            Icon: CheckCircle,
            containerClass: "bg-green-50 border-green-200",
            iconClass: "text-green-600",
            textClass: "text-green-800",
        },
        error: {
            Icon: AlertCircle,
            containerClass: "bg-red-50 border-red-200",
            iconClass: "text-red-600",
            textClass: "text-red-800",
        },
        info: {
            Icon: Info,
            containerClass: "bg-blue-50 border-blue-200",
            iconClass: "text-blue-600",
            textClass: "text-blue-800",
        },
    };

    const config = configs[type];
    const { Icon } = config;

    return (
        <div className={`flex items-start gap-2 p-3 border rounded-md ${config.containerClass}`}>
            <Icon className={`h-4 w-4 mt-0.5 flex-shrink-0 ${config.iconClass}`} />
            <div className={`text-sm ${config.textClass}`}>{content}</div>
        </div>
    );
}
