"use client";

import { useState, useCallback } from "react";
import { Upload, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import type { DataSource } from "@vulkanlabs/client-open";
import {
    Button,
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "../ui";
import { toast } from "sonner";

interface PublishDataSourceDialogProps {
    dataSource: DataSource;
    onPublish: (dataSourceId: string) => Promise<void>;
}

/**
 * Validates if a data source has the minimum required configuration to be published
 */
function validateDataSourceForPublish(dataSource: DataSource): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Check if URL is configured
    if (!dataSource.source?.url || dataSource.source.url.trim() === "") {
        errors.push("URL is required");
    }

    return {
        isValid: errors.length === 0,
        errors,
    };
}

/**
 * Dialog to confirm publishing a data source from draft to published status
 * Once published, data sources become read-only and available in workflows
 */
export function PublishDataSourceDialog({ dataSource, onPublish }: PublishDataSourceDialogProps) {
    const router = useRouter();
    const [open, setOpen] = useState(false);
    const [isPublishing, setIsPublishing] = useState(false);

    const validation = validateDataSourceForPublish(dataSource);
    const isPublishDisabled = !validation.isValid;

    const handleButtonClick = useCallback(() => {
        if (isPublishDisabled) {
            toast.error("Cannot publish data source", {
                description: validation.errors.join(", "),
            });
            return;
        }
        setOpen(true);
    }, [isPublishDisabled, validation.errors]);

    const handlePublish = async () => {
        // Double-check validation before publishing
        const currentValidation = validateDataSourceForPublish(dataSource);
        if (!currentValidation.isValid) {
            toast.error("Cannot publish data source", {
                description: currentValidation.errors.join(", "),
            });
            return;
        }

        setIsPublishing(true);
        try {
            await onPublish(dataSource.data_source_id);
            toast.success("Data source published successfully", {
                description: `${dataSource.name} is now available in workflows`,
            });
            setOpen(false);
            router.refresh();
        } catch (error: any) {
            console.error("Failed to publish data source:", error);
            toast.error("Failed to publish data source", {
                description: error.message || "An unknown error occurred",
            });
        } finally {
            setIsPublishing(false);
        }
    };

    return (
        <>
            <Button variant="default" size="sm" onClick={handleButtonClick}>
                <Upload className="h-4 w-4 mr-2" />
                Publish
            </Button>

            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>Publish Data Source</DialogTitle>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <p className="text-sm">
                            Publishing <strong>{dataSource.name}</strong> will make it available for use in
                            workflows.
                        </p>
                        <div className="space-y-2">
                            <p className="text-sm font-medium">After publishing:</p>
                            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                                <li>URL, headers, parameters and body cannot be changed</li>
                                <li>Retry policy, timeout and cache TTL can still be adjusted</li>
                                <li>Testing remains available for validation</li>
                            </ul>
                        </div>
                        <p className="text-sm text-muted-foreground">This action cannot be undone.</p>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setOpen(false)} disabled={isPublishing}>
                            Cancel
                        </Button>
                        <Button onClick={handlePublish} disabled={isPublishing}>
                            {isPublishing ? "Publishing..." : "Publish"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}
