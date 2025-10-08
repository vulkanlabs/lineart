"use client";

import { useState, useMemo } from "react";
import { Info, Plus, X } from "lucide-react";
import { Button, Label, Input, Separator } from "../ui";
import type { DataSource } from "@vulkanlabs/client-open";

interface CustomParam {
    key: string;
    value: string;
}

interface TestConfigPanelProps {
    dataSource: DataSource;
    onTest: (config: { configured_params: any; override_env_vars?: any }) => Promise<void>;
    isLoading?: boolean;
    initialConfig?: {
        configuredParams: Record<string, string>;
        overrideEnvVars: Record<string, string>;
        customParams: CustomParam[];
        customEnvVars: CustomParam[];
    };
    onConfigChange?: (config: {
        configuredParams: Record<string, string>;
        overrideEnvVars: Record<string, string>;
        customParams: CustomParam[];
        customEnvVars: CustomParam[];
    }) => void;
}

/**
 * Panel for configuring test parameters
 * Allows users to provide runtime params and override environment variables
 */
export function TestConfigPanel({
    dataSource,
    onTest,
    isLoading,
    initialConfig,
    onConfigChange,
}: TestConfigPanelProps) {
    const [testError, setTestError] = useState<string | null>(null);

    const runtimeParams = dataSource.runtime_params || [];
    const requiredVariables = dataSource.variables || [];

    // Create default values from runtime params
    const defaultParams = useMemo(() => {
        const params: Record<string, string> = {};
        runtimeParams.forEach((param) => {
            params[param] = "";
        });
        return params;
    }, [runtimeParams]);

    // Use initialConfig as the source of truth
    const configuredParams = initialConfig?.configuredParams || defaultParams;
    const overrideEnvVars = initialConfig?.overrideEnvVars || {};
    const customParams = initialConfig?.customParams || [];
    const customEnvVars = initialConfig?.customEnvVars || [];

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setTestError(null);
        try {
            // Merge configured params with custom params
            const allParams = { ...configuredParams };
            customParams.forEach(({ key, value }) => {
                if (key.trim() && value.trim()) {
                    allParams[key.trim()] = value;
                }
            });

            // Filter out empty values
            const filteredParams = Object.fromEntries(
                Object.entries(allParams).filter(([_, value]) => value.trim() !== "")
            );

            // Merge required env vars with custom env vars
            const allEnvVars = { ...overrideEnvVars };
            customEnvVars.forEach(({ key, value }) => {
                if (key.trim() && value.trim()) allEnvVars[key.trim()] = value;
            });

            const filteredEnvVars = Object.fromEntries(
                Object.entries(allEnvVars).filter(([_, value]) => value.trim() !== "")
            );

            await onTest({
                configured_params: filteredParams,
                override_env_vars: Object.keys(filteredEnvVars).length > 0 ? filteredEnvVars : undefined,
            });
        } catch (error: any) {
            setTestError(error.message || "Failed to run test");
        }
    };

    const handleParamChange = (paramName: string, value: string) => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams: { ...configuredParams, [paramName]: value },
                overrideEnvVars,
                customParams,
                customEnvVars,
            });
        }
    };

    const handleEnvVarChange = (varName: string, value: string) => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams,
                overrideEnvVars: { ...overrideEnvVars, [varName]: value },
                customParams,
                customEnvVars,
            });
        }
    };

    const addCustomParam = () => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams,
                overrideEnvVars,
                customParams: [...customParams, { key: "", value: "" }],
                customEnvVars,
            });
        }
    };

    const removeCustomParam = (index: number) => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams,
                overrideEnvVars,
                customParams: customParams.filter((_, i) => i !== index),
                customEnvVars,
            });
        }
    };

    const updateCustomParam = (index: number, field: "key" | "value", value: string) => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams,
                overrideEnvVars,
                customParams: customParams.map((param, i) =>
                    i === index ? { ...param, [field]: value } : param
                ),
                customEnvVars,
            });
        }
    };

    const addCustomEnvVar = () => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams,
                overrideEnvVars,
                customParams,
                customEnvVars: [...customEnvVars, { key: "", value: "" }],
            });
        }
    };

    const removeCustomEnvVar = (index: number) => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams,
                overrideEnvVars,
                customParams,
                customEnvVars: customEnvVars.filter((_, i) => i !== index),
            });
        }
    };

    const updateCustomEnvVar = (index: number, field: "key" | "value", value: string) => {
        if (onConfigChange) {
            onConfigChange({
                configuredParams,
                overrideEnvVars,
                customParams,
                customEnvVars: customEnvVars.map((envVar, i) =>
                    i === index ? { ...envVar, [field]: value } : envVar
                ),
            });
        }
    };

    return (
        <div className="space-y-6">
            <h3 className="text-base font-semibold">Test Configuration</h3>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <Label className="text-sm font-medium">Runtime Parameters</Label>
                            {runtimeParams.length === 0 && (
                                <span className="text-xs text-muted-foreground italic">
                                    (No parameters configured)
                                </span>
                            )}
                        </div>
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={addCustomParam}
                            className="h-8"
                        >
                            <Plus className="h-3 w-3 mr-1" />
                            Add Custom
                        </Button>
                    </div>

                    <div className="space-y-3">
                        {runtimeParams.map((param) => (
                            <div key={param}>
                                <Label htmlFor={`param-${param}`} className="text-sm">
                                    {param}
                                </Label>
                                <Input
                                    id={`param-${param}`}
                                    value={configuredParams[param] || ""}
                                    onChange={(e) => handleParamChange(param, e.target.value)}
                                    placeholder={`Enter value for ${param}`}
                                    className="mt-1.5"
                                />
                            </div>
                        ))}

                        {customParams.length > 0 && (
                            <div className="space-y-2">
                                {customParams.map((param, index) => (
                                    <div
                                        key={index}
                                        className="flex items-center space-x-2 p-2 border rounded-md"
                                    >
                                        <Input
                                            id={`custom-param-key-${index}`}
                                            value={param.key}
                                            onChange={(e) => updateCustomParam(index, "key", e.target.value)}
                                            placeholder="Parameter Name (e.g., user_id)"
                                            className="flex-1 font-mono"
                                        />
                                        <Input
                                            id={`custom-param-value-${index}`}
                                            value={param.value}
                                            onChange={(e) => updateCustomParam(index, "value", e.target.value)}
                                            placeholder="Parameter Value"
                                            className="flex-1 font-mono"
                                        />
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => removeCustomParam(index)}
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {runtimeParams.length === 0 && customParams.length === 0 && (
                            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-md border border-dashed">
                                <Info className="h-4 w-4 text-muted-foreground" />
                                <p className="text-sm text-muted-foreground">
                                    No runtime parameters configured. Click "Add Custom" to add test parameters.
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                <Separator />

                <div>
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <Label className="text-sm font-medium">Override Environment Variables</Label>
                            <span className="text-xs text-muted-foreground italic">(Optional)</span>
                        </div>
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={addCustomEnvVar}
                            className="h-8"
                        >
                            <Plus className="h-3 w-3 mr-1" />
                            Add Custom
                        </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">
                        Override environment variables for testing purposes only.
                    </p>

                    <div className="space-y-3">
                        {requiredVariables.map((varName) => (
                            <div key={varName}>
                                <Label htmlFor={`var-${varName}`} className="text-sm">
                                    {varName}
                                </Label>
                                <Input
                                    id={`var-${varName}`}
                                    value={overrideEnvVars[varName] || ""}
                                    onChange={(e) => handleEnvVarChange(varName, e.target.value)}
                                    placeholder={`Override ${varName}`}
                                    className="mt-1.5 font-mono"
                                />
                            </div>
                        ))}

                        {customEnvVars.length > 0 && (
                            <div className="space-y-2">
                                {customEnvVars.map((envVar, index) => (
                                    <div
                                        key={index}
                                        className="flex items-center space-x-2 p-2 border rounded-md"
                                    >
                                        <Input
                                            id={`custom-env-key-${index}`}
                                            value={envVar.key}
                                            onChange={(e) => updateCustomEnvVar(index, "key", e.target.value)}
                                            placeholder="Variable Name (e.g., API_KEY)"
                                            className="flex-1 font-mono"
                                        />
                                        <Input
                                            id={`custom-env-value-${index}`}
                                            value={envVar.value}
                                            onChange={(e) => updateCustomEnvVar(index, "value", e.target.value)}
                                            placeholder="Variable Value"
                                            className="flex-1 font-mono"
                                        />
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => removeCustomEnvVar(index)}
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {requiredVariables.length === 0 && customEnvVars.length === 0 && (
                            <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-md border border-dashed">
                                <Info className="h-4 w-4 text-muted-foreground" />
                                <p className="text-sm text-muted-foreground">
                                    No environment variables required. Click "Add Custom" to add test variables.
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {testError && (
                    <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                        <div className="text-sm text-destructive">{testError}</div>
                    </div>
                )}

                <button type="submit" id="test-submit-btn" className="hidden" />
            </form>
        </div>
    );
}
