import { MessageContent } from "@/components/chat/message-formatter";

export interface ChatRequest {
    message: string;
    session_id?: string;
}

export interface ChatResponse {
    response: string;
    session_id?: string;
    tools_used?: boolean;
}

// Configuration interfaces for vulkan-agent
export interface AgentConfigRequest {
    provider: "openai" | "anthropic" | "google";
    api_key: string;
    model: string;
    max_tokens?: number;
    temperature?: number;
}

export interface AgentConfigResponse {
    provider: "openai" | "anthropic" | "google";
    model: string;
    max_tokens: number;
    temperature: number;
    api_key_configured: boolean;
}

export interface AgentConfigValidationRequest {
    provider: "openai" | "anthropic" | "google";
    api_key: string;
    model?: string;
}

export interface AgentConfigValidationResponse {
    valid: boolean;
    message: string;
    provider: "openai" | "anthropic" | "google";
}

export interface AgentConfigStatus {
    configured: boolean;
    message: string;
}

// Legacy interfaces - keeping for backward compatibility
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

// Session management interfaces
export interface CreateSessionRequest {
    name?: string;
}

export interface SessionResponse {
    id: string;
    name: string;
    created_at: string;
    message_count: number;
}

export interface CreateSessionResponse {
    id: string;
    name: string;
    message: string;
}

export interface MessageResponse {
    id: number;
    role: string;
    content: string;
    created_at: string;
}

export interface SessionMessagesResponse {
    session_id: string;
    messages: MessageResponse[];
}

class AgentApiClient {
    private baseUrl: string;

    constructor(baseUrl?: string) {
        this.baseUrl =
            baseUrl || process.env.NEXT_PUBLIC_VULKAN_AGENT_URL || "http://localhost:8001";
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
        return this.request<ChatResponse>("/api/chat/message", {
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
     * Get agent health status
     */
    async getHealth(): Promise<{ status: string; timestamp: string; version?: string }> {
        return this.request<{ status: string; timestamp: string; version?: string }>(
            "/api/chat/status",
        );
    }

    // Configuration API methods
    /**
     * Get current agent configuration
     */
    async getConfig(): Promise<AgentConfigResponse> {
        return this.request<AgentConfigResponse>("/api/config");
    }

    /**
     * Update agent configuration
     */
    async updateConfig(config: AgentConfigRequest): Promise<AgentConfigResponse> {
        return this.request<AgentConfigResponse>("/api/config", {
            method: "PUT",
            body: JSON.stringify(config),
        });
    }

    /**
     * Validate API key and configuration without saving
     */
    async validateConfig(
        validation: AgentConfigValidationRequest,
    ): Promise<AgentConfigValidationResponse> {
        return this.request<AgentConfigValidationResponse>("/api/config/validate", {
            method: "POST",
            body: JSON.stringify(validation),
        });
    }

    /**
     * Get agent configuration status
     */
    async getConfigStatus(): Promise<AgentConfigStatus> {
        return this.request<AgentConfigStatus>("/api/config/status");
    }

    // Session management methods
    /**
     * Create a new conversation session
     */
    async createSession(request: CreateSessionRequest = {}): Promise<CreateSessionResponse> {
        return this.request<CreateSessionResponse>("/api/sessions", {
            method: "POST",
            body: JSON.stringify(request),
        });
    }

    /**
     * List all conversation sessions
     */
    async listSessions(): Promise<SessionResponse[]> {
        return this.request<SessionResponse[]>("/api/sessions");
    }

    /**
     * Get information about a specific session
     */
    async getSession(sessionId: string): Promise<SessionResponse> {
        return this.request<SessionResponse>(`/api/sessions/${sessionId}`);
    }

    /**
     * Get messages for a specific session
     */
    async getSessionMessages(sessionId: string, limit?: number): Promise<SessionMessagesResponse> {
        const params = new URLSearchParams();
        if (limit) params.append("limit", limit.toString());

        const queryString = params.toString();
        const endpoint = `/api/sessions/${sessionId}/messages${queryString ? `?${queryString}` : ""}`;

        return this.request<SessionMessagesResponse>(endpoint);
    }

    /**
     * Delete a conversation session and all its messages
     */
    async deleteSession(sessionId: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/api/sessions/${sessionId}`, {
            method: "DELETE",
        });
    }
}

// Export a default instance
export const agentApi = new AgentApiClient();

// Export the class for custom instances
export { AgentApiClient };

// Helper functions for common operations
export const createChatRequest = (message: string, session_id?: string): ChatRequest => ({
    message,
    session_id,
});

export const isMessageContent = (content: unknown): content is MessageContent => {
    return (
        typeof content === "object" && content !== null && "type" in content && "content" in content
    );
};
