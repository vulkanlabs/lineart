"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { CopyIcon, CheckIcon, Pencil, Save, X } from "lucide-react";
import type { DataSource } from "@vulkanlabs/client-open";
import { toast } from "sonner";

import {
    Badge,
    Button,
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
    Input,
} from "../ui";
import { PublishDataSourceDialog } from "./PublishDataSourceDialog";

interface DataSourceHeaderProps {
    dataSource: DataSource;
    copiedField: string | null;
    onCopyToClipboard: (text: string, field: string) => void;
    onGetFullDataSourceJson: (dataSource: DataSource) => string;
    onPublish?: (dataSourceId: string, projectId?: string) => Promise<DataSource>;
    onUpdateDataSource?: (
        dataSourceId: string,
        updates: Partial<DataSource>,
        projectId?: string,
    ) => Promise<DataSource>;
    projectId?: string;
}

export function DataSourceHeader({
    dataSource,
    copiedField,
    onCopyToClipboard,
    onGetFullDataSourceJson,
    onPublish,
    onUpdateDataSource,
    projectId,
}: DataSourceHeaderProps) {
    const router = useRouter();

    const status = dataSource.status ?? "DRAFT";
    const isDraft = status === "DRAFT";
    const isPublished = status === "PUBLISHED";

    const [isEditingDescription, setIsEditingDescription] = useState(false);
    const [descriptionValue, setDescriptionValue] = useState(dataSource.description || "");
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        setDescriptionValue(dataSource.description || "");
    }, [dataSource.description]);

    const handleSaveDescription = async () => {
        if (!onUpdateDataSource) return;

        setIsSaving(true);
        try {
            await onUpdateDataSource(
                dataSource.data_source_id,
                { description: descriptionValue || null },
                projectId,
            );
            setIsEditingDescription(false);
            toast.success("Description updated successfully");
            router.refresh();
        } catch (error) {
            console.error("Failed to update description:", error);
            toast.error("Failed to update description");
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancelDescription = () => {
        setDescriptionValue(dataSource.description || "");
        setIsEditingDescription(false);
    };

    return (
        <div className="flex justify-between items-start">
            <div className="flex-1 mr-4">
                <div className="flex items-center gap-2">
                    <h1 className="text-3xl font-bold tracking-tight">{dataSource.name}</h1>
                    {dataSource.status === "ARCHIVED" && (
                        <Badge variant="destructive">Archived</Badge>
                    )}
                    {isDraft && <Badge variant="secondary">Draft</Badge>}
                </div>

                {!isEditingDescription ? (
                    <div className="mt-2 flex items-center gap-2 group">
                        <p className="text-muted-foreground text-sm">
                            {dataSource.description || "Add a description..."}
                        </p>
                        {onUpdateDataSource && (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 px-2 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={() => setIsEditingDescription(true)}
                            >
                                <Pencil className="h-3 w-3 mr-1.5" />
                                <span className="text-xs">Edit</span>
                            </Button>
                        )}
                    </div>
                ) : (
                    <div className="mt-2 flex items-center gap-2 max-w-2xl">
                        <Input
                            value={descriptionValue}
                            onChange={(e) => setDescriptionValue(e.target.value)}
                            placeholder="Add a description..."
                            className="h-8 text-sm"
                            disabled={isSaving}
                            autoFocus
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    handleSaveDescription();
                                } else if (e.key === "Escape") {
                                    handleCancelDescription();
                                }
                            }}
                        />
                        <Button
                            variant="outline"
                            size="sm"
                            className="h-8"
                            onClick={handleCancelDescription}
                            disabled={isSaving}
                        >
                            <X className="h-3.5 w-3.5 mr-1.5" />
                            Cancel
                        </Button>
                        <Button
                            size="sm"
                            className="h-8"
                            onClick={handleSaveDescription}
                            disabled={isSaving}
                        >
                            <Save className="h-3.5 w-3.5 mr-1.5" />
                            {isSaving ? "Saving..." : "Save"}
                        </Button>
                    </div>
                )}
            </div>
            <div className="flex gap-2">
                {onPublish && (
                    <PublishDataSourceDialog
                        dataSource={dataSource}
                        onPublish={onPublish}
                        isPublished={isPublished}
                        projectId={projectId}
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
