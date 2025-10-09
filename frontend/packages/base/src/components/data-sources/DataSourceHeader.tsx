"use client";

import { CopyIcon, CheckIcon } from "lucide-react";
import type { DataSource } from "@vulkanlabs/client-open";
import { Badge, Button, Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui";
import { PublishDataSourceDialog } from "./PublishDataSourceDialog";

interface DataSourceHeaderProps {
    dataSource: DataSource;
    copiedField: string | null;
    onCopyToClipboard: (text: string, field: string) => void;
    onGetFullDataSourceJson: (dataSource: DataSource) => string;
    onPublish?: (dataSourceId: string) => Promise<void>;
}

export function DataSourceHeader({
    dataSource,
    copiedField,
    onCopyToClipboard,
    onGetFullDataSourceJson,
    onPublish,
}: DataSourceHeaderProps) {
    // Mock status until backend is ready - TODO: remove when backend implements status field
    const status = (dataSource as any).status || "draft";
    const isDraft = status === "draft";
    const isPublished = status === "published";

    return (
        <div className="flex justify-between items-start">
            <div>
                <div className="flex items-center gap-2">
                    <h1 className="text-3xl font-bold tracking-tight">{dataSource.name}</h1>
                    {dataSource.archived && <Badge variant="destructive">Archived</Badge>}
                    {isPublished && (
                        <Badge variant="default" className="bg-green-600">
                            Published
                        </Badge>
                    )}
                    {isDraft && <Badge variant="secondary">Draft</Badge>}
                </div>
                {dataSource.description && (
                    <p className="text-muted-foreground mt-1">{dataSource.description}</p>
                )}
            </div>
            <div className="flex gap-2">
                {isDraft && onPublish && (
                    <PublishDataSourceDialog
                        dataSource={dataSource}
                        onPublish={onPublish}
                    />
                )}

                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => onCopyToClipboard(dataSource.data_source_id, "id")}
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
                                onClick={() =>
                                    onCopyToClipboard(onGetFullDataSourceJson(dataSource), "json")
                                }
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
    );
}
