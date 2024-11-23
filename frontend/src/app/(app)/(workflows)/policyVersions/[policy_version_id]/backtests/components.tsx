"use client";
import React, { useState, useEffect } from "react";
import { useUser } from "@stackframe/stack";
import { useRouter } from "next/navigation";

import { RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormField,
    FormControl,
    FormDescription,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { fetchBacktestWorkspace, getAuthHeaders } from "@/lib/api";
import { ShortenedID } from "@/components/shortened-id";

export function BacktestsTableComponent({ backtests }) {
    const router = useRouter();
    console.log("backtests", backtests);

    function createBacktest() {
        console.log("Creating backtest");
    }

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Backtests</h1>
                <div className="flex gap-4">
                    <Button
                        className="bg-blue-600 hover:bg-blue-500"
                        onClick={() => createBacktest()}
                    >
                        Create Backtest
                    </Button>
                    <Button onClick={() => router.refresh()}>
                        <RotateCw className="mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>
            <BacktestsTable backtests={backtests} />
        </div>
    );
}

function BacktestsTable({ backtests }) {
    // const router = useRouter();

    function parseDate(date: string) {
        return new Date(date).toLocaleString();
    }

    return (
        <Table>
            <TableCaption>Your Backtests.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Input File ID</TableHead>
                    <TableHead>Created At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {backtests.map((backtest) => (
                    <TableRow
                        key={backtest.backtest_id}
                        className="cursor-pointer"
                        // onClick={() => router.push(`/policies/${policy.policy_id}/versions`)}
                    >
                        <TableCell>
                            <ShortenedID id={backtest.backtest_id} />
                        </TableCell>
                        <TableCell>{backtest.input_file_id}</TableCell>
                        <TableCell>{parseDate(backtest.created_at)}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

export function UploadedFilesTableComponent({ uploadedFiles }) {
    const router = useRouter();
    console.log("uploadedFiles", uploadedFiles);

    function uploadFile() {
        console.log("Uploading file");
    }

    return (
        <div>
            <div className="flex justify-between items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Uploaded Files</h1>
                <div className="flex gap-4">
                    <Button
                        className="bg-blue-600 hover:bg-blue-500"
                        onClick={() => uploadFile()}
                    >
                        Upload File
                    </Button>
                    <Button onClick={() => router.refresh()}>
                        <RotateCw className="mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>
            <UploadedFilesTable uploadedFiles={uploadedFiles} />
        </div>
    );
}

function UploadedFilesTable({ uploadedFiles }) {
    // const router = useRouter();

    function parseDate(date: string) {
        return new Date(date).toLocaleString();
    }

    return (
        <Table>
            <TableCaption>Your Uploaded Files.</TableCaption>
            <TableHeader>
                <TableRow>
                    <TableHead>ID</TableHead>
                    {/* <TableHead>File Schema</TableHead> */}
                    <TableHead>Created At</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {uploadedFiles.map((file) => (
                    <TableRow
                        key={file.uploaded_file_id}
                        className="cursor-pointer"
                        // onClick={() => router.push(`/policies/${policy.policy_id}/versions`)}
                    >
                        <TableCell>
                            <ShortenedID id={file.uploaded_file_id} />
                        </TableCell>
                        {/* <TableCell>{file.file_schema}</TableCell> */}
                        <TableCell>{parseDate(file.created_at)}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

export async function PendingWorkspaceCreation({ policyVersionId }) {
    const [ready, setReady] = useState(false);
    const terminalStates = ["OK", "CREATION_FAILED"];

    const user = useUser();

    const refreshStatus = () => {
        fetchBacktestWorkspace(user, policyVersionId)
            .then((data) => {
                setReady(terminalStates.includes(data.status));
            })
            .catch((error) => {
                setReady(true);
                console.error(error);
                return null;
            });
    };

    useEffect(() => {
        if (ready) {
            window.location.reload();
        }
        refreshStatus();
        const comInterval = setInterval(refreshStatus, 20000);
        return () => clearInterval(comInterval);
    }, [ready]);

    return <div className="flex justify-center items-center text-center">PENDING STATE...</div>;
}

export async function CreateWorkspacePage({ policyVersionId, workspaceCreationAction }) {
    const [workspaceStatus, setWorkspaceStatus] = useState(null);
    const [workspaceReady, setWorkspaceReady] = useState(null);

    const user = useUser();

    const refreshStatus = () => {
        console.log("refreshing status");
        fetchBacktestWorkspace(user, policyVersionId)
            .then((data) => {
                setWorkspaceStatus(data.status);
                setWorkspaceReady(data.status === "OK");
                console.log("set status to", data.status);
            })
            .catch((error) => {
                setWorkspaceReady(false);
                console.error(error);
                return null;
            });
    };

    useEffect(() => {
        console.log("calling useEffect");
        if (workspaceStatus === "OK") {
            console.log("workspaceStatus is OK, returning");
            return;
        }
        const refreshTime = 20000;
        refreshStatus();
        console.log("status", workspaceStatus);
        console.log("setting interval");
        const comInterval = setInterval(refreshStatus, refreshTime);
        return () => clearInterval(comInterval);
    }, [workspaceReady]);

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

    const user = useUser();
    const authJson = await user.getAuthJson();
    const headers = {
        "x-stack-access-token": authJson.accessToken,
        "x-stack-refresh-token": authJson.refreshToken,
    };
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url = `${serverUrl}/policy-versions/${policyVersionId}/backtest-workspace`;

    function createWorkspaceFn() {
        setSubmitting(true);
        setError(null);

        workspaceCreationAction({ url, headers })
            .then((data) => {
                console.log("Workspace created", data);
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
    const user = useUser();
    const authJson = await user.getAuthJson();
    const headers = {
        "x-stack-access-token": authJson.accessToken,
        "x-stack-refresh-token": authJson.refreshToken,
    };
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url = `${serverUrl}/policy-versions/${policyVersionId}/backtest-workspace`;

    function sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    async function createWorkspaceFn() {
        workspaceCreationAction({ url, headers });
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
