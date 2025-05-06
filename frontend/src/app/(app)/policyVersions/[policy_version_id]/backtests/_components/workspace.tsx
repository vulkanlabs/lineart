"use client";
import React, { useState, useEffect } from "react";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { fetchBacktestWorkspace } from "@/lib/api";

export async function PendingWorkspaceCreation({ policyVersionId }) {
    const [ready, setReady] = useState(false);

    useEffect(() => {
        const terminalStates = ["OK", "CREATION_FAILED"];
        const refreshStatus = () => {
            fetchBacktestWorkspace(policyVersionId)
                .then((data) => {
                    setReady(terminalStates.includes(data.status));
                })
                .catch((error) => {
                    setReady(true);
                    console.error(error);
                    return null;
                });
        };

        if (ready) {
            window.location.reload();
        }
        refreshStatus();
        const comInterval = setInterval(refreshStatus, 20000);
        return () => clearInterval(comInterval);
    }, [ready, policyVersionId]);

    return (
        <div className="flex justify-center items-center h-full">
            <div className="flex flex-col gap-8">
                <div className="text-lg font-medium text-center">
                    Creating backtest workspace. This may take a few minutes.
                </div>
                <div className="flex justify-center">
                    <Box sx={{ display: "flex" }}>
                        <CircularProgress size={100} thickness={2} color="inherit" />
                    </Box>
                </div>
            </div>
        </div>
    );
}

export async function CreateWorkspacePage({ policyVersionId, workspaceCreationAction }) {
    const [workspaceStatus, setWorkspaceStatus] = useState(null);
    const [workspaceReady, setWorkspaceReady] = useState(null);

    useEffect(() => {
        const refreshStatus = () => {
            fetchBacktestWorkspace(policyVersionId)
                .then((data) => {
                    setWorkspaceStatus(data.status);
                    setWorkspaceReady(data.status === "OK");
                })
                .catch((error) => {
                    setWorkspaceReady(false);
                    console.error(error);
                    return null;
                });
        };

        if (workspaceStatus === "OK") {
            return;
        }
        const refreshTime = 20000;
        refreshStatus();
        const comInterval = setInterval(refreshStatus, refreshTime);
        return () => clearInterval(comInterval);
    }, [workspaceReady, policyVersionId, workspaceStatus]);

    if (workspaceReady === null && workspaceStatus === null) {
        return <div>Loading...</div>;
    }

    if (workspaceReady) {
        return <div>Backtests Page</div>;
    }

    return (
        <WorkspaceCreationPage
            policyVersionId={policyVersionId}
            workspaceStatus={workspaceStatus}
            workspaceCreationAction={workspaceCreationAction}
        />
    );
}

async function WorkspaceCreationPage({
    policyVersionId,
    workspaceStatus,
    workspaceCreationAction,
}) {
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<Error>(null);

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url = `${serverUrl}/policy-versions/${policyVersionId}/backtest-workspace`;

    function createWorkspaceFn() {
        setSubmitting(true);
        setError(null);

        workspaceCreationAction({ url })
            .then((data) => {
                window.location.reload();
            })
            .catch((error) => {
                setError(error);
            });
    }

    if (submitting || workspaceStatus === "CREATION_PENDING") {
        return <div>Creating workspace...</div>;
    }
    if (error || workspaceStatus === "CREATION_FAILED") {
        return <div>Error creating workspace: {error?.message ?? "UNKNOWN"}</div>;
    }

    return (
        <div className="flex justify-center items-center mt-10">
            <WorkspaceCreationCard createWorkspaceFn={createWorkspaceFn} submitting={false} />
        </div>
    );
}

export async function WorkspaceCreation({
    policyVersionId,
    workspaceStatus,
    workspaceCreationAction,
}) {
    const [submitting, setSubmitting] = useState(false);
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url = `${serverUrl}/policy-versions/${policyVersionId}/backtest-workspace`;

    function sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    async function createWorkspaceFn() {
        workspaceCreationAction({ url });
        setSubmitting(true);
        await sleep(5000);
        window.location.reload();
    }

    if (workspaceStatus === "CREATION_PENDING") {
        return <div>Creating workspace...</div>;
    }
    if (workspaceStatus === "CREATION_FAILED") {
        return <div>Error creating workspace</div>;
    }

    return (
        <div className="flex justify-center items-center mt-10">
            <WorkspaceCreationCard createWorkspaceFn={createWorkspaceFn} submitting={submitting} />
        </div>
    );
}

function WorkspaceCreationCard({ createWorkspaceFn, submitting }) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Create Backtest Workspace</CardTitle>
                <CardDescription>
                    Create a workspace to run backtests for this policy version.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="flex flex-row gap-4">
                    <Button
                        className="bg-green-600 hover:bg-green-500"
                        onClick={createWorkspaceFn}
                        disabled={submitting}
                    >
                        Create Workspace
                    </Button>
                    {submitting && <p>Submitting...</p>}
                </div>
            </CardContent>
        </Card>
    );
}

function WorkspaceCreationErrorCard({ createWorkspaceFn }) {
    return (
        <div className="flex justify-center items-center mt-10">
            <Card>
                <CardHeader>
                    <CardTitle>Create Backtest Workspace</CardTitle>
                    <CardDescription>
                        Create a workspace to run backtests for this policy version.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div>Error creating workspace</div>
                    <Button>Retry</Button>
                </CardContent>
            </Card>
        </div>
    );
}
