"use client";

import { LinkIcon } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table";
import { Card, CardContent, CardHeader, CardTitle, ScrollArea } from "@vulkanlabs/base/ui";
import { DataTable } from "../..";
import type { ConfigurationVariablesBase, DataSource } from "@vulkanlabs/client-open";

const paramsTableColumns: ColumnDef<ConfigurationVariablesBase>[] = [
    {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => <p>{row.getValue("name") || "-"}</p>,
    },
    {
        accessorKey: "value",
        header: "Value",
        cell: ({ row }) => <p>{row.getValue("value") || "-"}</p>,
    },
];

function ParamsTable({ params }: { params: ConfigurationVariablesBase[] }) {
    return (
        <DataTable
            columns={paramsTableColumns}
            data={params}
            emptyMessage="No parameters found"
            className=""
        />
    );
}

interface SourceConfigurationCardProps {
    dataSource: DataSource;
    formatJson: (json: any) => string | null;
}

export function SourceConfigurationCard({ dataSource, formatJson }: SourceConfigurationCardProps) {
    const sourceQueryParams = dataSource.source.params
        ? Object.entries(dataSource.source.params).map(([key, value]) => ({
              name: key,
              value: typeof value === "object" ? JSON.stringify(value, null, 2) : String(value),
          }))
        : [];

    const sourceHeaders = dataSource.source.headers
        ? Object.entries(dataSource.source.headers).map(([key, value]) => ({
              name: key,
              value: typeof value === "object" ? JSON.stringify(value, null, 2) : String(value),
          }))
        : [];

    return (
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
                        <p className="text-sm text-muted-foreground">No headers provided.</p>
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
                        <p className="text-sm text-muted-foreground">No body schema provided.</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
