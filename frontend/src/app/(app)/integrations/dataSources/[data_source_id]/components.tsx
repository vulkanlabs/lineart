"use client";

import { ColumnDef } from "@tanstack/react-table";
import { useState } from "react";
import {
    CopyIcon,
    CalendarIcon,
    CheckIcon,
    FileIcon,
    LinkIcon,
    Settings2Icon,
    X,
} from "lucide-react";

import { DataSource } from "@vulkan-server/DataSource";
import { ConfigurationVariablesBase } from "@vulkan-server/ConfigurationVariablesBase";
import { DataTable } from "@/components/data-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export default function DataSourcePage({ dataSource }: { dataSource: DataSource }) {
    const [copiedField, setCopiedField] = useState<string | null>(null);

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
    const sourceParams = dataSource.source.params
        ? Object.entries(dataSource.source.params).map(([key, value]) => ({
              key,
              value: value.toString(),
          }))
        : [];

    const sourceHeaders = dataSource.source.headers
        ? Object.entries(dataSource.source.headers).map(([key, value]) => ({
              key,
              value: value.toString(),
          }))
        : [];

    const variablesData = dataSource.variables
        ? dataSource.variables.map((variable) => ({
              key: variable,
              value: "-",
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
                    <TabsTrigger value="caching">Caching & Performance</TabsTrigger>
                    {dataSource.metadata && <TabsTrigger value="metadata">Metadata</TabsTrigger>}
                </TabsList>

                <TabsContent value="general">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <CalendarIcon className="h-5 w-5" />
                                    Timestamps
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-1 gap-4">
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
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <FileIcon className="h-5 w-5" />
                                    Keys & Variables
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {dataSource.keys.length > 0 && (
                                        <div>
                                            <p className="text-sm font-medium mb-2">Keys</p>
                                            <div className="flex flex-wrap gap-2">
                                                {dataSource.keys.map((key) => (
                                                    <Badge key={key} variant="outline">
                                                        {key}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {variablesData.length > 0 && (
                                        <div>
                                            <p className="text-sm font-medium mb-2">Variables</p>
                                            <ParamsTable params={variablesData} />
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
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

                                    {dataSource.source.timeout && (
                                        <div>
                                            <p className="text-sm font-medium">Timeout</p>
                                            <p className="text-sm text-muted-foreground">
                                                {dataSource.source.timeout}s
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {sourceParams.length > 0 ? (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Query Parameters</p>
                                        <ParamsTable params={sourceParams} />
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

                                {dataSource.source.body_schema ? (
                                    <div className="mt-6">
                                        <p className="text-sm font-medium mb-2">Body Schema</p>
                                        <Card className="bg-muted/50">
                                            <CardContent className="p-4">
                                                <ScrollArea className="h-[200px]">
                                                    <pre className="text-xs">
                                                        {formatJson(dataSource.source.body_schema)}
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
                                            {formatTimeFromSeconds(dataSource.caching.ttl)} (
                                            {dataSource.caching.ttl} seconds)
                                        </p>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {dataSource.metadata && (
                    <TabsContent value="metadata">
                        <Card>
                            <CardHeader>
                                <CardTitle>Metadata</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <Card className="bg-muted/50">
                                    <CardContent className="p-4">
                                        <ScrollArea className="h-[300px]">
                                            <pre className="text-xs">
                                                {formatJson(dataSource.metadata)}
                                            </pre>
                                        </ScrollArea>
                                    </CardContent>
                                </Card>
                            </CardContent>
                        </Card>
                    </TabsContent>
                )}
            </Tabs>
        </div>
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
