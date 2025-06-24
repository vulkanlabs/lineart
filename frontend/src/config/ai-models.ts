/**
 * AI Model configurations for different providers
 * This file contains the available models for each AI provider
 */

export type AIProvider = "openai" | "anthropic" | "google";

export interface ModelOption {
    value: string;
    label: string;
    description?: string;
    status?: "stable" | "preview" | "experimental";
}

export const AI_PROVIDERS: Array<{ value: AIProvider; label: string }> = [
    { value: "openai", label: "OpenAI" },
    { value: "anthropic", label: "Anthropic" },
    { value: "google", label: "Google" },
] as const;

export const AI_MODELS: Record<AIProvider, ModelOption[]> = {
    openai: [
        // Latest GPT-4.1 models (2025)
        {
            value: "gpt-4.1",
            label: "GPT-4.1",
            description: "Latest flagship model with enhanced capabilities",
            status: "preview",
        },
        {
            value: "gpt-4.1-mini",
            label: "GPT-4.1 Mini",
            description: "Affordable balance of speed and intelligence",
            status: "preview",
        },
        {
            value: "gpt-4.1-nano",
            label: "GPT-4.1 Nano",
            description: "Fastest, most cost-effective model",
            status: "preview",
        },
        // Reasoning models
        {
            value: "o3",
            label: "OpenAI o3",
            description: "Most powerful reasoning model for complex problems",
            status: "preview",
        },
        {
            value: "o4-mini",
            label: "OpenAI o4-mini",
            description: "Faster, cost-efficient reasoning model",
            status: "preview",
        },
        // Current GPT-4 models (stable)
        {
            value: "gpt-4o",
            label: "GPT-4o",
            description: "Current flagship model",
            status: "stable",
        },
        {
            value: "gpt-4o-mini",
            label: "GPT-4o Mini",
            description: "Cost-effective with strong performance",
            status: "stable",
        },
        {
            value: "gpt-4-turbo",
            label: "GPT-4 Turbo",
            description: "Enhanced GPT-4 with improved speed",
            status: "stable",
        },
        {
            value: "gpt-4",
            label: "GPT-4",
            description: "Standard GPT-4 model",
            status: "stable",
        },
        // GPT-3.5 (stable but older)
        {
            value: "gpt-3.5-turbo",
            label: "GPT-3.5 Turbo",
            description: "Legacy but reliable model",
            status: "stable",
        },
    ],
    anthropic: [
        // Latest Claude 4 models (2025)
        {
            value: "claude-opus-4-20250514",
            label: "Claude Opus 4",
            description: "Most capable and intelligent model",
            status: "preview",
        },
        {
            value: "claude-sonnet-4-20250514",
            label: "Claude Sonnet 4",
            description: "High-performance with exceptional reasoning",
            status: "preview",
        },
        // Claude 3.7 models
        {
            value: "claude-3-7-sonnet-20250219",
            label: "Claude 3.7 Sonnet",
            description: "Extended thinking capabilities",
            status: "preview",
        },
        // Current Claude 3.5 models (stable)
        {
            value: "claude-3-5-sonnet-20241022",
            label: "Claude 3.5 Sonnet",
            description: "Latest stable Sonnet with improved capabilities",
            status: "stable",
        },
        {
            value: "claude-3-5-haiku-20241022",
            label: "Claude 3.5 Haiku",
            description: "Fast and accurate responses",
            status: "stable",
        },
        // Claude 3 models (stable)
        {
            value: "claude-3-opus-20240229",
            label: "Claude 3 Opus",
            description: "Most capable Claude 3 model",
            status: "stable",
        },
        {
            value: "claude-3-sonnet-20240229",
            label: "Claude 3 Sonnet",
            description: "Balanced performance and cost",
            status: "stable",
        },
        {
            value: "claude-3-haiku-20240307",
            label: "Claude 3 Haiku",
            description: "Fastest Claude 3 model",
            status: "stable",
        },
    ],
    google: [
        // Latest Gemini 2.5 models (2025)
        {
            value: "gemini-2.5-pro",
            label: "Gemini 2.5 Pro",
            description: "Most powerful thinking model",
            status: "preview",
        },
        {
            value: "gemini-2.5-flash",
            label: "Gemini 2.5 Flash",
            description: "Best price-performance with adaptive thinking",
            status: "preview",
        },
        {
            value: "gemini-2.5-flash-lite-preview-06-17",
            label: "Gemini 2.5 Flash-Lite",
            description: "Most cost-efficient model",
            status: "experimental",
        },
        // Gemini 2.0 models
        {
            value: "gemini-2.0-flash",
            label: "Gemini 2.0 Flash",
            description: "Next generation features and speed",
            status: "preview",
        },
        {
            value: "gemini-2.0-flash-lite",
            label: "Gemini 2.0 Flash-Lite",
            description: "Cost efficiency and low latency",
            status: "preview",
        },
        // Current Gemini 1.5 models (stable)
        {
            value: "gemini-1.5-pro",
            label: "Gemini 1.5 Pro",
            description: "Complex reasoning tasks",
            status: "stable",
        },
        {
            value: "gemini-1.5-flash",
            label: "Gemini 1.5 Flash",
            description: "Fast and versatile",
            status: "stable",
        },
        {
            value: "gemini-1.5-flash-8b",
            label: "Gemini 1.5 Flash-8B",
            description: "High volume, lightweight tasks",
            status: "stable",
        },
        // Legacy (still supported)
        {
            value: "gemini-pro",
            label: "Gemini Pro",
            description: "Legacy model, still supported",
            status: "stable",
        },
    ],
};

// Default models for each provider
export const DEFAULT_MODELS: Record<AIProvider, string> = {
    openai: "gpt-4o",
    anthropic: "claude-3-5-sonnet-20241022",
    google: "gemini-1.5-pro",
};

// Helper function to get models for a provider
export const getModelsForProvider = (provider: AIProvider): ModelOption[] => {
    return AI_MODELS[provider] || [];
};

// Helper function to get default model for a provider
export const getDefaultModelForProvider = (provider: AIProvider): string => {
    return DEFAULT_MODELS[provider] || AI_MODELS[provider]?.[0]?.value || "";
};
