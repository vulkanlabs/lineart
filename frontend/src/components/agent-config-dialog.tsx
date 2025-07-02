"use client";

import { useState, useEffect } from "react";
import { Settings, Eye, EyeOff, Check, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

import { agentApi, type AgentConfigRequest, type AgentConfigResponse } from "@/lib/agent-api";
import {
    AI_PROVIDERS,
    AI_MODELS,
    getDefaultModelForProvider,
    getModelsForProvider,
    type AIProvider,
} from "@/config/ai-models";

const STATUS_BADGE_CLASSES = "text-xs bg-orange-100 text-orange-700 px-1 py-0.5 rounded";

interface ConfigFormData {
    provider: AIProvider;
    api_key: string;
    model: string;
    max_tokens: number;
    temperature: number;
}

export function AgentConfigDialog() {
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isValidating, setIsValidating] = useState(false);
    const [showApiKey, setShowApiKey] = useState(false);
    const [isConfigured, setIsConfigured] = useState(false);

    const [formData, setFormData] = useState<ConfigFormData>({
        provider: "openai",
        api_key: "",
        model: getDefaultModelForProvider("openai"),
        max_tokens: 500,
        temperature: 0.7,
    });

    const [isApiKeyConfigured, setIsApiKeyConfigured] = useState<Record<AIProvider, boolean>>({
        openai: false,
        anthropic: false,
        google: false,
    });

    const [validationStatus, setValidationStatus] = useState<{
        isValid: boolean | null;
        message: string;
    }>({ isValid: null, message: "" });

    // Load current configuration when dialog opens
    useEffect(() => {
        if (isOpen) {
            loadCurrentConfig();
        }
    }, [isOpen]);

    // Check configuration status on component mount
    useEffect(() => {
        checkConfigStatus();
    }, []);

    const checkConfigStatus = async () => {
        try {
            const status = await agentApi.getConfigStatus();
            setIsConfigured(status.configured);
        } catch (error) {
            console.error("Failed to check config status:", error);
            setIsConfigured(false);
        }
    };

    const loadCurrentConfig = async () => {
        try {
            setIsLoading(true);
            const config = await agentApi.getConfig();
            if (process.env.NODE_ENV === "development") {
                console.log("Loaded config from server:", config);
            }

            // Ensure the model is valid for the provider before setting form data
            const availableModels = getModelsForProvider(config.provider as AIProvider);
            const modelExists = availableModels.some((m) => m.value === config.model);
            const finalModel = modelExists
                ? config.model
                : getDefaultModelForProvider(config.provider as AIProvider);

            setFormData({
                provider: config.provider as AIProvider,
                api_key: "", // Don't populate API key for security
                model: finalModel,
                max_tokens: config.max_tokens,
                temperature: config.temperature,
            });
            setIsApiKeyConfigured((prev) => ({
                ...prev,
                [config.provider as AIProvider]: config.api_key_configured || false,
            }));
            setValidationStatus({ isValid: null, message: "" });

            // If API key is configured, automatically set validation status without message
            if (config.api_key_configured) {
                setValidationStatus({ isValid: true, message: "" });
            }
        } catch (error) {
            console.error("Failed to load config:", error);
            // If config doesn't exist or fails to load, keep default values
            // But still reset validation status
            setValidationStatus({ isValid: null, message: "" });
        } finally {
            setIsLoading(false);
        }
    };

    const handleProviderChange = (provider: AIProvider) => {
        const defaultModel = getDefaultModelForProvider(provider);
        setFormData((prev) => ({
            ...prev,
            provider,
            model: defaultModel,
            api_key: "", // Clear API key when switching providers
        }));
        // Don't reset API key configured status - keep track per provider
        // Set validation status based on whether this provider has an API key configured
        if (isApiKeyConfigured[provider]) {
            setValidationStatus({ isValid: true, message: "" });
        } else {
            setValidationStatus({ isValid: null, message: "" });
        }
    };

    const handleApiKeyChange = (api_key: string) => {
        setFormData((prev) => ({ ...prev, api_key }));
        setValidationStatus({ isValid: null, message: "" });
        // Reset configured status for current provider when user starts typing
        if (api_key.length > 0) {
            setIsApiKeyConfigured((prev) => ({
                ...prev,
                [formData.provider]: false,
            }));
        }
    };

    const validateApiKey = async () => {
        // If API key is already configured and user hasn't entered a new one, skip validation
        if (!formData.api_key.trim() && isApiKeyConfigured[formData.provider]) {
            setValidationStatus({ isValid: true, message: "" });
            return;
        }

        if (!formData.api_key.trim()) {
            setValidationStatus({ isValid: false, message: "API key is required" });
            return;
        }

        try {
            setIsValidating(true);
            const result = await agentApi.validateConfig({
                provider: formData.provider,
                api_key: formData.api_key,
                model: formData.model,
            });

            setValidationStatus({
                isValid: result.valid,
                message: result.message,
            });
        } catch (error) {
            setValidationStatus({
                isValid: false,
                message: error instanceof Error ? error.message : "Validation failed",
            });
        } finally {
            setIsValidating(false);
        }
    };

    const handleSave = async () => {
        // Check if API key is required
        const needsApiKey = !isApiKeyConfigured[formData.provider] || formData.api_key.trim();

        if (needsApiKey && !formData.api_key.trim()) {
            toast.error("Please enter an API key");
            return;
        }

        // Only require validation if we're setting a new API key
        if (formData.api_key.trim() && validationStatus.isValid !== true) {
            toast.error("Please validate your API key first");
            return;
        }

        try {
            setIsLoading(true);
            const config: AgentConfigRequest = {
                provider: formData.provider,
                api_key: formData.api_key || "", // Send empty string if keeping existing key
                model: formData.model,
                max_tokens: formData.max_tokens,
                temperature: formData.temperature,
            };

            await agentApi.updateConfig(config);

            // If we saved a new API key, mark this provider as configured
            if (formData.api_key.trim()) {
                setIsApiKeyConfigured((prev) => ({
                    ...prev,
                    [formData.provider]: true,
                }));
            }

            setIsConfigured(true);
            setIsOpen(false);
            toast.success("Agent configuration saved successfully!");
        } catch (error) {
            toast.error(error instanceof Error ? error.message : "Failed to save configuration");
        } finally {
            setIsLoading(false);
        }
    };

    // Helper function to determine if save button should be enabled
    const canSave = () => {
        if (isLoading) return false;

        // If we have a new API key, it must be validated
        if (formData.api_key.trim()) {
            return validationStatus.isValid === true;
        }

        // If no API key entered, we can save if one is already configured
        return isApiKeyConfigured[formData.provider];
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button variant="ghost" size="icon" className="relative" title="Configure AI Agent">
                    <Settings className="h-5 w-5" />
                    {!isConfigured && (
                        <div className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full" />
                    )}
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Configure AI Agent</DialogTitle>
                    <DialogDescription>
                        Set up your AI agent with your preferred provider and settings.
                    </DialogDescription>
                </DialogHeader>

                {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin" />
                        <span className="ml-2">Loading configuration...</span>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Provider Selection */}
                        <div className="space-y-2">
                            <Label htmlFor="provider">AI Provider</Label>
                            <Select value={formData.provider} onValueChange={handleProviderChange}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {AI_PROVIDERS.map((provider) => (
                                        <SelectItem key={provider.value} value={provider.value}>
                                            {provider.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Model Selection */}
                        <div className="space-y-2">
                            <Label htmlFor="model">Model</Label>
                            <Select
                                value={formData.model}
                                onValueChange={(model) =>
                                    setFormData((prev) => ({ ...prev, model }))
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue>
                                        {(() => {
                                            const selectedModel = getModelsForProvider(
                                                formData.provider,
                                            ).find((m) => m.value === formData.model);
                                            return selectedModel ? (
                                                <div className="flex items-center gap-2">
                                                    <span>{selectedModel.label}</span>
                                                    {selectedModel.status &&
                                                        selectedModel.status !== "stable" && (
                                                            <span className={STATUS_BADGE_CLASSES}>
                                                                {selectedModel.status}
                                                            </span>
                                                        )}
                                                </div>
                                            ) : (
                                                formData.model
                                            );
                                        })()}
                                    </SelectValue>
                                </SelectTrigger>
                                <SelectContent>
                                    {getModelsForProvider(formData.provider).map((model) => (
                                        <SelectItem key={model.value} value={model.value}>
                                            <div className="flex flex-col py-1">
                                                <div className="flex items-center gap-2">
                                                    <span>{model.label}</span>
                                                    {model.status && model.status !== "stable" && (
                                                        <span className={STATUS_BADGE_CLASSES}>
                                                            {model.status}
                                                        </span>
                                                    )}
                                                </div>
                                                {model.description && (
                                                    <span className="text-xs text-muted-foreground mt-0.5">
                                                        {model.description}
                                                    </span>
                                                )}
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* API Key */}
                        <div className="space-y-2">
                            <Label htmlFor="api_key">API Key</Label>
                            <div className="space-y-2">
                                <div className="relative">
                                    <Input
                                        id="api_key"
                                        type={showApiKey ? "text" : "password"}
                                        value={formData.api_key}
                                        onChange={(e) => handleApiKeyChange(e.target.value)}
                                        placeholder={
                                            isApiKeyConfigured[formData.provider] &&
                                            !formData.api_key
                                                ? "Leave empty to keep current key"
                                                : "Enter your API key"
                                        }
                                        className="pr-20"
                                    />
                                    <div className="absolute right-1 top-1 flex gap-1">
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            className="h-8 w-8 p-0"
                                            onClick={() => setShowApiKey(!showApiKey)}
                                        >
                                            {showApiKey ? (
                                                <EyeOff className="h-4 w-4" />
                                            ) : (
                                                <Eye className="h-4 w-4" />
                                            )}
                                        </Button>
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            className="h-8 px-2"
                                            onClick={validateApiKey}
                                            disabled={
                                                isValidating ||
                                                (!formData.api_key.trim() &&
                                                    !isApiKeyConfigured[formData.provider])
                                            }
                                        >
                                            {isValidating ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                "Test"
                                            )}
                                        </Button>
                                    </div>
                                </div>

                                {/* API Key Status Info */}
                                {isApiKeyConfigured[formData.provider] && !formData.api_key && (
                                    <div className="text-sm text-green-600 flex items-center gap-1">
                                        <Check className="h-3 w-3" />
                                        API key configured for{" "}
                                        {AI_PROVIDERS.find((p) => p.value === formData.provider)
                                            ?.label || formData.provider}
                                    </div>
                                )}

                                {/* Validation Status */}
                                {validationStatus.message && (
                                    <Card
                                        className={`border ${
                                            validationStatus.isValid
                                                ? "border-green-200 bg-green-50"
                                                : "border-red-200 bg-red-50"
                                        }`}
                                    >
                                        <CardContent className="p-3">
                                            <div className="flex items-center gap-2">
                                                {validationStatus.isValid ? (
                                                    <Check className="h-4 w-4 text-green-600" />
                                                ) : (
                                                    <AlertCircle className="h-4 w-4 text-red-600" />
                                                )}
                                                <span
                                                    className={`text-sm ${
                                                        validationStatus.isValid
                                                            ? "text-green-800"
                                                            : "text-red-800"
                                                    }`}
                                                >
                                                    {validationStatus.message}
                                                </span>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )}
                            </div>
                        </div>

                        <Separator />

                        {/* Advanced Settings */}
                        <div className="space-y-4">
                            <h4 className="text-sm font-medium">Advanced Settings</h4>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="max_tokens">Max Tokens</Label>
                                    <Input
                                        id="max_tokens"
                                        type="number"
                                        min="1"
                                        max="100000"
                                        value={formData.max_tokens}
                                        onChange={(e) =>
                                            setFormData((prev) => ({
                                                ...prev,
                                                max_tokens: parseInt(e.target.value) || 500,
                                            }))
                                        }
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="temperature">Temperature</Label>
                                    <Input
                                        id="temperature"
                                        type="number"
                                        min="0"
                                        max="2"
                                        step="0.1"
                                        value={formData.temperature}
                                        onChange={(e) =>
                                            setFormData((prev) => ({
                                                ...prev,
                                                temperature: parseFloat(e.target.value) || 0.7,
                                            }))
                                        }
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <DialogFooter>
                    <Button variant="outline" onClick={() => setIsOpen(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={!canSave()}>
                        {isLoading ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                Saving...
                            </>
                        ) : (
                            "Save Configuration"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
