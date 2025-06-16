import { MessageContent } from "@/components/chat/message-formatter";

export interface ChatRequest {
    message: string;
    context?: {
        userId?: string;
        sessionId?: string;
        previousMessages?: number;
    };
}

export interface ChatResponse {
    response: string | MessageContent;
    sessionId?: string;
    suggestions?: string[];
    metadata?: {
        processingTime?: number;
        model?: string;
        tokens?: number;
    };
}

export interface AgentSettings {
    id?: string;
    userId: string;
    provider: "openai" | "anthropic";
    model: string;
    apiKey: string;
    maxTokens?: number;
    temperature?: number;
    systemPrompt?: string;
    createdAt?: string;
    updatedAt?: string;
}

export interface AgentSettingsResponse {
    settings: AgentSettings;
}

export interface AgentCapabilities {
    availableProviders: Array<{
        id: string;
        name: string;
        models: Array<{
            id: string;
            name: string;
            description?: string;
        }>;
    }>;
    features: string[];
    version: string;
}

export interface ChatHistoryResponse {
    messages: Array<{
        role: string;
        content: string;
        timestamp: string;
    }>;
}

class AgentApiClient {
    private baseUrl: string;

    constructor(baseUrl?: string) {
        this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_VULKAN_SERVER_URL || "";
    }

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultHeaders = {
            "Content-Type": "application/json",
        };

        const config: RequestInit = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.detail || errorJson.message || errorMessage;
                } catch {
                    // If not JSON, use the text as error message
                    errorMessage = errorText || errorMessage;
                }

                throw new Error(errorMessage);
            }

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                return await response.json();
            }

            // For non-JSON responses, return the text as a generic object
            const text = await response.text();
            return { response: text } as T;
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(
                "An unexpected error occurred while communicating with the agent service",
            );
        }
    }

    /**
     * Send a chat message to the AI agent
     */
    async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        return this.request<ChatResponse>("/ai-agent/chat", {
            method: "POST",
            body: JSON.stringify(request),
        });
    }

    /**
     * Get current agent settings for the user
     */
    async getSettings(): Promise<AgentSettingsResponse> {
        return this.request<AgentSettingsResponse>("/ai-agent/settings");
    }

    /**
     * Update agent settings
     */
    async updateSettings(settings: Partial<AgentSettings>): Promise<AgentSettingsResponse> {
        return this.request<AgentSettingsResponse>("/ai-agent/settings", {
            method: "PUT",
            body: JSON.stringify(settings),
        });
    }

    /**
     * Test API key validity for a provider
     */
    async testApiKey(
        provider: string,
        apiKey: string,
        model?: string,
    ): Promise<{ valid: boolean; error?: string }> {
        return this.request<{ valid: boolean; error?: string }>("/ai-agent/test-api-key", {
            method: "POST",
            body: JSON.stringify({ provider, apiKey, model }),
        });
    }

    /**
     * Get available capabilities and models
     */
    async getCapabilities(): Promise<AgentCapabilities> {
        return this.request<AgentCapabilities>("/ai-agent/capabilities");
    }

    /**
     * Get chat history for the current session
     */
    async getChatHistory(sessionId?: string, limit?: number): Promise<ChatHistoryResponse> {
        const params = new URLSearchParams();
        if (sessionId) params.append("sessionId", sessionId);
        if (limit) params.append("limit", limit.toString());

        const queryString = params.toString();
        const endpoint = `/ai-agent/history${queryString ? `?${queryString}` : ""}`;

        return this.request<ChatHistoryResponse>(endpoint);
    }

    /**
     * Clear chat history for the current session
     */
    async clearChatHistory(sessionId?: string): Promise<{ success: boolean }> {
        return this.request<{ success: boolean }>("/ai-agent/history", {
            method: "DELETE",
            body: JSON.stringify({ sessionId }),
        });
    }

    /**
     * Get agent health status
     */
    async getHealth(): Promise<{ status: string; timestamp: string; version?: string }> {
        return this.request<{ status: string; timestamp: string; version?: string }>(
            "/ai-agent/health",
        );
    }
}

// Export a default instance
export const agentApi = new AgentApiClient();

// Export the class for custom instances
export { AgentApiClient };

// Helper functions for common operations
export const createChatRequest = (
    message: string,
    context?: ChatRequest["context"],
): ChatRequest => ({
    message,
    context,
});

export const isMessageContent = (content: unknown): content is MessageContent => {
    return (
        typeof content === "object" && content !== null && "type" in content && "content" in content
    );
};
