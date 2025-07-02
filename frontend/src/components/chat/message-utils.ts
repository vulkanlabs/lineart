/**
 * Utility functions for message content processing
 */

import { MessageContent, PreviewContent, CodeContent } from "./message-types";

/**
 * Language aliases for code syntax highlighting
 */
export const LANGUAGE_ALIASES: { [key: string]: string } = {
    js: "javascript",
    ts: "typescript",
    py: "python",
    sh: "bash",
    yml: "yaml",
};

/**
 * Normalizes language identifiers using common aliases
 */
export function normalizeLanguage(language: string): string {
    return LANGUAGE_ALIASES[language] || language;
}

/**
 * Detects if content is valid JSON and returns the language if so
 */
export function detectJsonLanguage(content: string): string | null {
    const trimmed = content.trim();

    if (trimmed.length <= 2) return null;

    if (
        (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
        (trimmed.startsWith("[") && trimmed.endsWith("]"))
    ) {
        try {
            const parsed = JSON.parse(trimmed);
            if (typeof parsed === "object" && parsed !== null) {
                return "json";
            }
        } catch {
            // Not valid JSON
        }
    }

    return null;
}

/**
 * Processes raw content to auto-format JSON
 */
export function processJsonContent(rawContent: string): string {
    const trimmed = rawContent.trim();

    // Only try to parse as JSON if it's reasonably structured
    if (
        (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
        (trimmed.startsWith("[") && trimmed.endsWith("]"))
    ) {
        try {
            const parsed = JSON.parse(trimmed);
            // Only format as JSON if it's a non-trivial object/array
            if (typeof parsed === "object" && parsed !== null) {
                return "```json\n" + JSON.stringify(parsed, null, 2) + "\n```";
            }
        } catch {
            // Not valid JSON, return as-is
        }
    }

    return rawContent;
}

/**
 * Helper functions for creating formatted messages
 */

export const createTextMessage = (text: string): MessageContent => ({
    type: "text",
    content: text,
});

export const createMarkdownMessage = (markdown: string): MessageContent => ({
    type: "markdown",
    content: markdown,
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

export const createJsonMessage = (jsonObject: any, title?: string): MessageContent => ({
    type: "code",
    content: {
        code: JSON.stringify(jsonObject, null, 2),
        language: "json",
        title: title || "JSON Data",
    },
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
