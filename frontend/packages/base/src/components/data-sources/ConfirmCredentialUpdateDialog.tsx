"use client";

import { AlertTriangle } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "../ui/dialog";
import { Button } from "../ui";

interface ConfirmCredentialUpdateDialogProps {
    open: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    isLoading?: boolean;
}

export function ConfirmCredentialUpdateDialog({
    open,
    onConfirm,
    onCancel,
    isLoading = false,
}: ConfirmCredentialUpdateDialogProps) {
    return (
        <Dialog open={open} onOpenChange={(open) => !open && !isLoading && onCancel()}>
            <DialogContent>
                <DialogHeader>
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-100">
                            <AlertTriangle className="h-5 w-5 text-yellow-600" />
                        </div>
                        <DialogTitle>Update Credentials for Published Data Source?</DialogTitle>
                    </div>
                    <DialogDescription className="pt-4 space-y-3">
                        <p>
                            You are about to update credentials for a published data source. This
                            action will:
                        </p>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                            <li>
                                Affect all users and applications currently using this data source
                            </li>
                            <li>Apply immediately to all future requests using this data source</li>
                            <li>
                                Potentially cause authentication issues if credentials are invalid
                            </li>
                        </ul>
                        <p className="font-medium pt-2">
                            Please ensure the new credentials are correct before proceeding.
                        </p>
                    </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <Button variant="outline" onClick={onCancel} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={onConfirm} disabled={isLoading}>
                        {isLoading ? "Updating..." : "Update Credentials"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
