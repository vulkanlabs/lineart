"use client";

import { ColumnDef } from "@tanstack/react-table";
import { useState, Suspense, useEffect, useCallback } from "react";
import {
    CopyIcon,
    CalendarIcon,
    CheckIcon,
    FileIcon,
    LinkIcon,
    Settings2Icon,
    EditIcon,
    SaveIcon,
    XIcon,
    EyeIcon,
    EyeOffIcon,
} from "lucide-react";

import { DataSource } from "@vulkan-server/DataSource";
import { DataSourceEnvVarBase } from "@vulkan-server/DataSourceEnvVarBase";
import { ConfigurationVariablesBase } from "@vulkan-server/ConfigurationVariablesBase";
import { DataTable } from "@/components/data-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Loader from "@/components/animations/loader";
import DataSourceUsageAnalytics from "./usage-analytics";
import { setDataSourceEnvVars, fetchDataSourceEnvVars } from "@/lib/api";

export default function DataSourcePage({ dataSource }: { dataSource: DataSource }) {
    const [copiedField, setCopiedField] = useState<string | null>(null);

    console.log("Retrieved Data Source Spec: ", dataSource);

    const copyToClipboard = (text: string, field: string) => {
        navigator.clipboard.writeText(text);
        setCopiedField(field);
        setTimeout(() => setCopiedField(null), 2000);
    };

    // Get full data source as formatted JSON
    const getFullDataSourceJson = () => {
        return JSON.stringify(dataSource, null, 2);
    };

    const formatDate = (date: Date) => {
        return new Date(date).toLocaleDateString(undefined, {
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    // Format TTL seconds into days, hours, minutes, seconds
    const formatTimeFromSeconds = (totalSeconds: number) => {
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        const parts = [];
        if (days > 0) parts.push(`${days} day${days !== 1 ? "s" : ""}`);
        if (hours > 0) parts.push(`${hours} hour${hours !== 1 ? "s" : ""}`);
        if (minutes > 0) parts.push(`${minutes} minute${minutes !== 1 ? "s" : ""}`);
        if (seconds > 0 || parts.length === 0)
            parts.push(`${seconds} second${seconds !== 1 ? "s" : ""}`);

        return parts.join(", ");
    };

    // Format JSON data for display
    const formatJson = (json: any) => {
        if (!json) return null;
        return JSON.stringify(json, null, 2);
    };

    // Prepare params for the params table
    const sourcePathParams = dataSource.source.path_params
        ? Object.entries(dataSource.source.path_params).map(([key, value]) => ({
              key,
              value: JSON.stringify(value, null, 2),
          }))
        : [];

    const sourceQueryParams = dataSource.source.query_params
        ? Object.entries(dataSource.source.query_params).map(([key, value]) => ({
              key,
              value: typeof value === "object" ? JSON.stringify(value, null, 2) : String(value),
          }))
        : [];

    const sourceHeaders = dataSource.source.headers
        ? Object.entries(dataSource.source.headers).map(([key, value]) => ({
              key,
              value: typeof value === "object" ? JSON.stringify(value, null, 2) : String(value),
          }))
        : [];

    return (
        <div className="flex flex-col gap-6 p-6">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <div className="flex items-center gap-2">
                        <h1 className="text-3xl font-bold tracking-tight">{dataSource.name}</h1>
                        {dataSource.archived && <Badge variant="destructive">Archived</Badge>}
                    </div>
                    {dataSource.description && (
                        <p className="text-muted-foreground mt-1">{dataSource.description}</p>
                    )}
                </div>
                <div className="flex gap-2">
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => copyToClipboard(dataSource.data_source_id, "id")}
                                >
                                    {copiedField === "id" ? (
                                        <CheckIcon className="h-4 w-4" />
                                    ) : (
                                        <CopyIcon className="h-4 w-4" />
                                    )}
                                    <span className="ml-2">
                                        ID: {dataSource.data_source_id.substring(0, 8)}...
                                    </span>
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>Copy data source ID</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => copyToClipboard(getFullDataSourceJson(), "json")}
                                >
                                    {copiedField === "json" ? (
                                        <CheckIcon className="h-4 w-4" />
                                    ) : (
                                        <CopyIcon className="h-4 w-4" />
                                    )}
                                    <span className="ml-2">Copy as JSON</span>
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>Copy full data source specification</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                </div>
            </div>

            <Separator />

            {/* Main content */}
            <Tabs defaultValue="general" className="w-full">
                <TabsList className="mb-4">
                    <TabsTrigger value="general">General</TabsTrigger>
                    <TabsTrigger value="source">Source</TabsTrigger>
                    <TabsTrigger value="caching">Caching</TabsTrigger>
                </TabsList>

                <TabsContent value="general">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <CalendarIcon className="h-5 w-5" />
                                    Summary
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid gap-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-sm font-medium">Created At</p>
                                            <p className="text-sm text-muted-foreground">
                                                {formatDate(dataSource.created_at)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium">Last Updated</p>
                                            <p className="text-sm text-muted-foreground">
                                                {formatDate(dataSource.last_updated_at)}
                                            </p>
                                        </div>
                                    </div>
                                    {dataSource.metadata && (
                                        <div>
                                            <p className="text-sm font-medium">Metadata</p>
                                            <Card className="bg-muted/50 mt-2">
                                                <CardContent className="p-4">
                                                    <ScrollArea className="h-[150px]">
                                                        <pre className="text-xs">
                                                            {formatJson(dataSource.metadata)}
                                                        </pre>
                                                    </ScrollArea>
                                                </CardContent>
                                            </Card>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        <EditableVariablesCard dataSource={dataSource} />
                    </div>
                </TabsContent>

                <TabsContent value="source">
                    <div className="grid gap-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <LinkIcon className="h-5 w-5" />
                                    Source Configuration
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                                    <div>
                                        <p className="text-sm font-medium">URL</p>
                                        <p className="text-sm text-muted-foreground break-all">
                                            {dataSource.source.url}
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-sm font-medium">Method</p>
                                        <p className="text-sm text-muted-foreground">
                                            {dataSource.source.method || "GET"}
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-sm font-medium">Response Type</p>
                                        <p className="text-sm text-muted-foreground">
                                            {dataSource.source.response_type || "JSON"}
                                        </p>
                                    </div>

                                    {dataSource.source.timeout && (
                                        <div>
                                            <p className="text-sm font-medium">Timeout</p>
                                            <p className="text-sm text-muted-foreground">
                                                {dataSource.source.timeout}s
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {sourcePathParams.length > 0 ? (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Path Parameters</p>
                                        <ParamsTable params={sourcePathParams} />
                                    </div>
                                ) : (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Path Parameters</p>
                                        <p className="text-sm text-muted-foreground">
                                            No path parameters provided.
                                        </p>
                                    </div>
                                )}

                                {sourceQueryParams.length > 0 ? (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Query Parameters</p>
                                        <ParamsTable params={sourceQueryParams} />
                                    </div>
                                ) : (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Query Parameters</p>
                                        <p className="text-sm text-muted-foreground">
                                            No query parameters provided.
                                        </p>
                                    </div>
                                )}

                                {sourceHeaders.length > 0 ? (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Headers</p>
                                        <ParamsTable params={sourceHeaders} />
                                    </div>
                                ) : (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Headers</p>
                                        <p className="text-sm text-muted-foreground">
                                            No headers provided.
                                        </p>
                                    </div>
                                )}

                                {dataSource.source.body ? (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Body</p>
                                        <Card className="bg-muted/50">
                                            <CardContent className="p-4">
                                                <ScrollArea className="h-[200px]">
                                                    <pre className="text-xs">
                                                        {formatJson(dataSource.source.body)}
                                                    </pre>
                                                </ScrollArea>
                                            </CardContent>
                                        </Card>
                                    </div>
                                ) : (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Body Schema</p>
                                        <p className="text-sm text-muted-foreground">
                                            No body schema provided.
                                        </p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {dataSource.source.retry && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className="text-base">Retry Policy</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <p className="text-sm font-medium">Max Retries</p>
                                            <p className="text-sm text-muted-foreground">
                                                {dataSource.source.retry.max_retries}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium">Backoff Factor</p>
                                            <p className="text-sm text-muted-foreground">
                                                {dataSource.source.retry.backoff_factor}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium">Status Force List</p>
                                            <p className="text-sm text-muted-foreground">
                                                {dataSource.source.retry.status_forcelist
                                                    ? dataSource.source.retry.status_forcelist.join(
                                                          ", ",
                                                      )
                                                    : "None"}
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="caching">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Settings2Icon className="h-5 w-5" />
                                Caching Configuration
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4">
                                <div className="flex items-center justify-between">
                                    <p className="text-sm font-medium">Caching Enabled</p>
                                    <Badge
                                        variant={
                                            dataSource.caching?.enabled ? "default" : "outline"
                                        }
                                    >
                                        {dataSource.caching?.enabled ? "Enabled" : "Disabled"}
                                    </Badge>
                                </div>

                                {dataSource.caching?.enabled && dataSource.caching?.ttl && (
                                    <div>
                                        <p className="text-sm font-medium">TTL (Time to Live)</p>
                                        <p className="text-sm text-muted-foreground">
                                            {formatTimeFromSeconds(Number(dataSource.caching.ttl))}{" "}
                                            ({Number(dataSource.caching.ttl)} seconds)
                                        </p>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Usage Analytics Section */}
            <Suspense
                fallback={
                    <div className="flex justify-center p-8">
                        <Loader />
                    </div>
                }
            >
                <DataSourceUsageAnalytics dataSourceId={dataSource.data_source_id} />
            </Suspense>
        </div>
    );
}

function EditableVariablesCard({ dataSource }: { dataSource: DataSource }) {
    const [isEditing, setIsEditing] = useState(false);
    const [editingVariables, setEditingVariables] = useState<DataSourceEnvVarBase[]>([]);
    const [envVars, setEnvVars] = useState<DataSourceEnvVarBase[]>([]);
    const [isSaving, setIsSaving] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [visibleVariables, setVisibleVariables] = useState<Set<number>>(new Set());

    // Load environment variables from API
    const loadEnvVars = useCallback(async () => {
        try {
            setIsLoading(true);
            const variables = await fetchDataSourceEnvVars(dataSource.data_source_id);
            setEnvVars(variables || []);
        } catch (error) {
            console.error("Error loading environment variables:", error);
            setEnvVars([]);
        } finally {
            setIsLoading(false);
        }
    }, [dataSource.data_source_id]);

    // Load env vars on component mount
    useEffect(() => {
        loadEnvVars();
    }, [loadEnvVars]);

    // Initialize editing variables from predefined variables
    const initializeEditingVariables = () => {
        const predefinedVariables = dataSource.variables || [];
        setEditingVariables(
            predefinedVariables.map((varName) => ({
                name: varName,
                value: "", // Values are not returned from API for security
            })),
        );
    };

    const handleEdit = () => {
        initializeEditingVariables();
        setIsEditing(true);
    };

    const handleCancel = () => {
        setIsEditing(false);
        setEditingVariables([]);
    };

    const handleSave = async () => {
        try {
            setIsSaving(true);
            await setDataSourceEnvVars(dataSource.data_source_id, editingVariables);
            setIsEditing(false);
            // Reload environment variables to reflect changes
            await loadEnvVars();
        } catch (error) {
            console.error("Error saving environment variables:", error);
            // Optionally show an error message to the user
        } finally {
            setIsSaving(false);
        }
    };

    const handleVariableChange = (index: number, value: string) => {
        const updatedVariables = [...editingVariables];
        updatedVariables[index] = { ...updatedVariables[index], value };
        setEditingVariables(updatedVariables);
    };

    const toggleVariableVisibility = (index: number) => {
        const newVisible = new Set(visibleVariables);
        if (newVisible.has(index)) {
            newVisible.delete(index);
        } else {
            newVisible.add(index);
        }
        setVisibleVariables(newVisible);
    };

    const runtimeParams = dataSource.runtime_params || [];
    const predefinedVariables = dataSource.variables || [];

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <FileIcon className="h-5 w-5" />
                        Variables
                    </CardTitle>
                    {predefinedVariables.length > 0 && !isEditing ? (
                        <Button variant="outline" size="sm" onClick={handleEdit}>
                            <EditIcon className="h-4 w-4 mr-2" />
                            Edit Environment Variables
                        </Button>
                    ) : isEditing ? (
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={handleCancel}>
                                <XIcon className="h-4 w-4 mr-2" />
                                Cancel
                            </Button>
                            <Button size="sm" onClick={handleSave} disabled={isSaving}>
                                <SaveIcon className="h-4 w-4 mr-2" />
                                {isSaving ? "Saving..." : "Save"}
                            </Button>
                        </div>
                    ) : null}
                </div>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Runtime Parameters Section */}
                <div>
                    <h4 className="text-sm font-medium mb-3">Runtime Parameters</h4>
                    <p className="text-xs text-muted-foreground mb-3">
                        These parameters are configured in the workflows that use the data source.
                    </p>
                    {runtimeParams.length > 0 ? (
                        <div className="space-y-2">
                            {runtimeParams.map((param, index) => (
                                <div
                                    key={index}
                                    className="flex items-center justify-between p-2 bg-muted/30 rounded 
                                        border-l-2 border-blue-500"
                                >
                                    <span className="text-sm font-medium">{param}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-muted-foreground">
                            No runtime parameters configured.
                        </p>
                    )}
                </div>

                <Separator />

                {/* Environment Variables Section */}
                <div>
                    <h4 className="text-sm font-medium mb-3">Environment Variables</h4>
                    <p className="text-xs text-muted-foreground mb-3">
                        These variables are configured at the data source level and available during
                        execution.
                    </p>

                    {predefinedVariables.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                            No environment variables defined for this data source.
                        </p>
                    ) : isLoading ? (
                        <div className="flex justify-center p-4">
                            <Loader />
                        </div>
                    ) : !isEditing ? (
                        <div className="space-y-2">
                            {predefinedVariables.map((variableName, index) => {
                                const envVar = envVars.find((env) => env.name === variableName);
                                const isConfigured =
                                    envVar &&
                                    envVar.value &&
                                    typeof envVar.value === "string" &&
                                    envVar.value.trim() !== "";
                                return (
                                    <div
                                        key={index}
                                        className="flex items-center justify-between p-2 bg-muted/30 rounded 
                                            border-l-2 border-green-500"
                                    >
                                        <span className="text-sm font-medium">{variableName}</span>
                                        <Badge variant={isConfigured ? "outline" : "destructive"}>
                                            {isConfigured ? "Configured" : "Not Set"}
                                        </Badge>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {editingVariables.map((variable, index) => (
                                <div key={index} className="flex items-center gap-4">
                                    <div className="flex-1">
                                        <Label className="text-sm font-medium">
                                            {variable.name}
                                        </Label>
                                    </div>
                                    <div className="flex-1 relative">
                                        <Input
                                            id={`var-value-${index}`}
                                            type={visibleVariables.has(index) ? "text" : "password"}
                                            placeholder="Enter variable value"
                                            value={variable.value ? String(variable.value) : ""}
                                            onChange={(e) =>
                                                handleVariableChange(index, e.target.value)
                                            }
                                            className="pr-10"
                                        />
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                                            onClick={() => toggleVariableVisibility(index)}
                                        >
                                            {visibleVariables.has(index) ? (
                                                <EyeOffIcon className="h-4 w-4" />
                                            ) : (
                                                <EyeIcon className="h-4 w-4" />
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

const paramsTableColumns: ColumnDef<ConfigurationVariablesBase>[] = [
    {
        accessorKey: "key",
        header: "Key",
        cell: ({ row }) => <p>{row.getValue("key") || "-"}</p>,
    },
    {
        accessorKey: "value",
        header: "Value",
        cell: ({ row }) => <p>{row.getValue("value") || "-"}</p>,
    },
];

function ParamsTable({ params }) {
    return <DataTable columns={paramsTableColumns} data={params} />;
}
