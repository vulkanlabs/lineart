/**
 * Action confirmation dialog component
 */

"use client";

import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { AgentAction } from "@/lib/actions/types";

interface ActionConfirmationDialogProps {
    action: AgentAction | null;
    isOpen: boolean;
    onConfirm: () => Promise<void>;
    onCancel: () => void;
}

export function ActionConfirmationDialog({
    action,
    isOpen,
    onConfirm,
    onCancel,
}: ActionConfirmationDialogProps) {
    const [isExecuting, setIsExecuting] = useState(false);
    const [result, setResult] = useState<{ success: boolean; error?: string } | null>(null);

    const handleConfirm = async () => {
        setIsExecuting(true);
        setResult(null);

        try {
            await onConfirm();
            setResult({ success: true });
            // Auto-close after success
            setTimeout(() => {
                handleClose();
            }, 2000);
        } catch (error) {
            setResult({
                success: false,
                error: error instanceof Error ? error.message : "An error occurred",
            });
        } finally {
            setIsExecuting(false);
        }
    };

    const handleClose = () => {
        setResult(null);
        setIsExecuting(false);
        onCancel();
    };

    if (!action) return null;

    const getActionIcon = () => {
        if (result?.success) return <CheckCircle className="h-6 w-6 text-green-500" />;
        if (result?.error) return <XCircle className="h-6 w-6 text-red-500" />;
        return <AlertTriangle className="h-6 w-6 text-yellow-500" />;
    };

    const getActionDetails = () => {
        switch (action.type) {
            case "UPDATE_WORKFLOW_SPEC":
                return {
                    title: "Update Workflow",
                    details: [
                        `Nodes to be updated: ${action.payload.workflowSpec.nodes.length}`,
                        action.payload.reason && `Reason: ${action.payload.reason}`,
                    ].filter(Boolean),
                };
            default:
                return {
                    title: "Execute Action",
                    details: [`Action type: ${action.type}`],
                };
        }
    };

    const actionDetails = getActionDetails();

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <div className="flex items-center gap-3">
                        {getActionIcon()}
                        <DialogTitle>
                            {result?.success
                                ? "Action Completed"
                                : result?.error
                                  ? "Action Failed"
                                  : actionDetails.title}
                        </DialogTitle>
                    </div>
                    <DialogDescription>
                        {result?.success && "The action was executed successfully."}
                        {result?.error && `Error: ${result.error}`}
                        {!result && action.description}
                    </DialogDescription>
                </DialogHeader>

                {!result && (
                    <div className="py-4">
                        <div className="space-y-2">
                            {actionDetails.details.map((detail, index) => (
                                <div key={index} className="text-sm text-muted-foreground">
                                    • {detail}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <DialogFooter>
                    {result?.success ? (
                        <Button onClick={handleClose}>Close</Button>
                    ) : result?.error ? (
                        <Button onClick={handleClose}>Close</Button>
                    ) : (
                        <>
                            <Button variant="outline" onClick={handleClose} disabled={isExecuting}>
                                Cancel
                            </Button>
                            <Button onClick={handleConfirm} disabled={isExecuting}>
                                {isExecuting ? "Executing..." : "Confirm"}
                            </Button>
                        </>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
