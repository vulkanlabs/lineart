"use client";

import { useState } from "react";
import { Save, X, Settings2 } from "lucide-react";
import { useRouter } from "next/navigation";
import type { DataSource } from "@vulkanlabs/client-open";
import { Button, Input, Label, Separator, Switch } from "../ui";
import { toast } from "sonner";

interface EditDataSourcePanelProps {
    dataSource: DataSource;
    updateDataSource: (
        dataSourceId: string,
        updates: Partial<DataSource>,
        projectId?: string,
    ) => Promise<DataSource>;
    projectId?: string;
    disabled?: boolean;
}

export function EditDataSourcePanel({
    dataSource,
    updateDataSource,
    projectId,
    disabled = false,
}: EditDataSourcePanelProps) {
    const router = useRouter();
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const formatJsonForDisplay = (obj: any): string => {
        if (!obj || Object.keys(obj).length === 0) return "";
        return JSON.stringify(obj, null, 2);
    };

    const isEmptyOrPlaceholderUrl = (url: string | undefined): boolean => {
        if (!url) return true;
        return url.includes("placeholder") || url.includes("example.com");
    };

    // Source configuration
    const [url, setUrl] = useState(
        isEmptyOrPlaceholderUrl(dataSource.source.url) ? "" : dataSource.source.url
    );
    const [method, setMethod] = useState<"GET" | "POST" | "PUT" | "DELETE" | "PATCH">(
        dataSource.source.method || "GET",
    );
    const [headers, setHeaders] = useState(formatJsonForDisplay(dataSource.source.headers));
    const [params, setParams] = useState(formatJsonForDisplay(dataSource.source.params));

    // Retry configuration
    const [maxRetries, setMaxRetries] = useState(
        dataSource.source.retry?.max_retries !== undefined &&
        dataSource.source.retry?.max_retries !== null &&
        dataSource.source.retry?.max_retries !== 3
            ? dataSource.source.retry.max_retries.toString()
            : "",
    );
    const [backoffFactor, setBackoffFactor] = useState(
        dataSource.source.retry?.backoff_factor !== undefined &&
        dataSource.source.retry?.backoff_factor !== null &&
        dataSource.source.retry?.backoff_factor !== 2
            ? dataSource.source.retry.backoff_factor.toString()
            : "",
    );

    // Caching configuration
    const [cachingEnabled, setCachingEnabled] = useState(dataSource.caching?.enabled || false);
    const [ttlSeconds, setTtlSeconds] = useState(
        dataSource.caching?.ttl?.seconds !== undefined &&
        dataSource.caching?.ttl?.seconds !== null &&
        dataSource.caching?.ttl?.seconds !== 300
            ? dataSource.caching.ttl.seconds.toString()
            : "",
    );

    const handleSave = async () => {
        setIsSaving(true);
        try {
            let parsedHeaders = {};
            let parsedParams = {};

            // Parse headers
            if (headers.trim()) {
                try {
                    parsedHeaders = JSON.parse(headers);
                } catch (e) {
                    toast.error("Invalid JSON format in headers");
                    setIsSaving(false);
                    return;
                }
            }

            // Parse params
            if (params.trim()) {
                try {
                    parsedParams = JSON.parse(params);
                } catch (e) {
                    toast.error("Invalid JSON format in params");
                    setIsSaving(false);
                    return;
                }
            }

            const updates: Partial<DataSource> = {
                source: {
                    ...dataSource.source,
                    url,
                    method: method as "GET" | "POST" | "PUT" | "DELETE",
                    headers: parsedHeaders,
                    params: parsedParams,
                    retry: {
                        max_retries: maxRetries ? parseInt(maxRetries, 10) : 3,
                        backoff_factor: backoffFactor ? parseFloat(backoffFactor) : 2,
                        status_forcelist: dataSource.source.retry?.status_forcelist || [],
                    },
                },
                caching: {
                    enabled: cachingEnabled,
                    ttl: {
                        seconds: ttlSeconds ? parseInt(ttlSeconds, 10) : 300,
                    },
                },
            };

            await updateDataSource(dataSource.data_source_id, updates, projectId);

            toast.success("Data source updated successfully");
            setIsEditing(false);
            router.refresh();
        } catch (error: any) {
            console.error("Failed to update data source:", error);
            toast.error(error.message || "Failed to update data source");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setUrl(dataSource.source.url || "");
        setMethod(dataSource.source.method || "GET");
        setHeaders(formatJsonForDisplay(dataSource.source.headers));
        setParams(formatJsonForDisplay(dataSource.source.params));
        setMaxRetries(
            dataSource.source.retry?.max_retries !== undefined &&
            dataSource.source.retry?.max_retries !== null &&
            dataSource.source.retry?.max_retries !== 3
                ? dataSource.source.retry.max_retries.toString()
                : "",
        );
        setBackoffFactor(
            dataSource.source.retry?.backoff_factor !== undefined &&
            dataSource.source.retry?.backoff_factor !== null &&
            dataSource.source.retry?.backoff_factor !== 2
                ? dataSource.source.retry.backoff_factor.toString()
                : "",
        );
        setCachingEnabled(dataSource.caching?.enabled || false);
        setTtlSeconds(
            dataSource.caching?.ttl?.seconds !== undefined &&
            dataSource.caching?.ttl?.seconds !== null &&
            dataSource.caching?.ttl?.seconds !== 300
                ? dataSource.caching.ttl.seconds.toString()
                : "",
        );
        setIsEditing(false);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold md:text-2xl">Configuration</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Configure HTTP endpoint, retry policy, and caching
                        {disabled && " (Read-only)"}
                    </p>
                </div>
                {!isEditing ? (
                    <Button onClick={() => setIsEditing(true)} disabled={disabled}>
                        <Settings2 className="h-4 w-4 mr-2" />
                        Edit
                    </Button>
                ) : (
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
                            <X className="h-4 w-4 mr-2" />
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={isSaving}>
                            <Save className="h-4 w-4 mr-2" />
                            {isSaving ? "Saving..." : "Save"}
                        </Button>
                    </div>
                )}
            </div>

            <Separator />

            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="md:col-span-1">
                        <Label htmlFor="method">Method</Label>
                        <select
                            id="method"
                            value={method}
                            onChange={(e) =>
                                setMethod(
                                    e.target.value as "GET" | "POST" | "PUT" | "DELETE" | "PATCH",
                                )
                            }
                            disabled={!isEditing}
                            className="mt-1.5 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                            <option value="PUT">PUT</option>
                            <option value="PATCH">PATCH</option>
                            <option value="DELETE">DELETE</option>
                        </select>
                    </div>

                    <div className="md:col-span-3">
                        <Label htmlFor="url">URL</Label>
                        <Input
                            id="url"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            disabled={!isEditing}
                            placeholder="https://api.example.com/endpoint"
                            className="mt-1.5 font-mono text-sm"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <Label htmlFor="headers">Headers (JSON)</Label>
                        <textarea
                            id="headers"
                            value={headers}
                            onChange={(e) => setHeaders(e.target.value)}
                            disabled={!isEditing}
                            rows={6}
                            className="mt-1.5 flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono resize-none"
                            placeholder={'{\n  "Content-Type": "application/json",\n  "Authorization": "Bearer token"\n}'}
                        />
                    </div>

                    <div>
                        <Label htmlFor="params">Query Parameters (JSON)</Label>
                        <textarea
                            id="params"
                            value={params}
                            onChange={(e) => setParams(e.target.value)}
                            disabled={!isEditing}
                            rows={6}
                            className="mt-1.5 flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono resize-none"
                            placeholder={'{\n  "page": "1",\n  "limit": "10"\n}'}
                        />
                    </div>
                </div>

                <Separator />

                <div>
                    <h3 className="text-base font-semibold mb-4">Retry Policy</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-md">
                        <div>
                            <Label htmlFor="maxRetries">Max Retries</Label>
                            <Input
                                id="maxRetries"
                                type="number"
                                min="0"
                                value={maxRetries}
                                onChange={(e) => setMaxRetries(e.target.value)}
                                disabled={!isEditing}
                                placeholder="3"
                                className="mt-1.5"
                            />
                            <p className="text-xs text-muted-foreground mt-1">
                                Number of retry attempts
                            </p>
                        </div>

                        <div>
                            <Label htmlFor="backoffFactor">Backoff Factor</Label>
                            <Input
                                id="backoffFactor"
                                type="number"
                                min="0"
                                step="0.1"
                                value={backoffFactor}
                                onChange={(e) => setBackoffFactor(e.target.value)}
                                disabled={!isEditing}
                                placeholder="2"
                                className="mt-1.5"
                            />
                            <p className="text-xs text-muted-foreground mt-1">
                                Exponential backoff multiplier
                            </p>
                        </div>
                    </div>
                </div>

                <Separator />

                <div>
                    <h3 className="text-base font-semibold mb-4">Caching</h3>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <Switch
                                id="cachingEnabled"
                                checked={cachingEnabled}
                                onCheckedChange={setCachingEnabled}
                                disabled={!isEditing}
                            />
                            <div className="flex-1">
                                <Label htmlFor="cachingEnabled" className="text-sm font-medium cursor-pointer">
                                    Enable response caching
                                </Label>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Cache responses to improve performance
                                </p>
                            </div>
                        </div>

                        {cachingEnabled && (
                            <div className="max-w-xs">
                                <Label htmlFor="ttl">TTL (seconds)</Label>
                                <Input
                                    id="ttl"
                                    type="number"
                                    min="0"
                                    value={ttlSeconds}
                                    onChange={(e) => setTtlSeconds(e.target.value)}
                                    disabled={!isEditing}
                                    placeholder="300"
                                    className="mt-1.5"
                                />
                                <p className="text-xs text-muted-foreground mt-1">
                                    How long to cache responses
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
