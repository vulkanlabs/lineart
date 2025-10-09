"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import {
    Button,
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "../ui";
import { toast } from "sonner";

interface PublishDataSourceDialogProps {
    dataSourceId: string;
    dataSourceName: string;
    onPublish: (dataSourceId: string) => Promise<void>;
    trigger?: React.ReactNode;
}

/**
 * Dialog to confirm publishing a data source from draft to published status
 * Once published, data sources become read-only and available in workflows
 */
export function PublishDataSourceDialog({
    dataSourceId,
    dataSourceName,
    onPublish,
    trigger,
}: PublishDataSourceDialogProps) {
    const router = useRouter();
    const [open, setOpen] = useState(false);
    const [isPublishing, setIsPublishing] = useState(false);

    const handlePublish = async () => {
        setIsPublishing(true);
        try {
            await onPublish(dataSourceId);
            toast.success("Data source published successfully", {
                description: `${dataSourceName} is now available in workflows`,
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
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                {trigger || (
                    <Button variant="default" size="sm">
                        <Upload className="h-4 w-4 mr-2" />
                        Publish
                    </Button>
                )}
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Publish Data Source</DialogTitle>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <p className="text-sm">
                        Publishing <strong>{dataSourceName}</strong> will make it available for use in workflows.
                    </p>
                    <div className="space-y-2">
                        <p className="text-sm font-medium">After publishing:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                            <li>URL, headers, parameters and body cannot be changed</li>
                            <li>Retry policy, timeout and cache TTL can still be adjusted</li>
                            <li>Testing remains available for validation</li>
                        </ul>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        This action cannot be undone.
                    </p>
                </div>

                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={() => setOpen(false)}
                        disabled={isPublishing}
                    >
                        Cancel
                    </Button>
                    <Button onClick={handlePublish} disabled={isPublishing}>
                        {isPublishing ? "Publishing..." : "Publish"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
