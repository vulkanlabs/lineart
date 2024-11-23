import { Suspense } from "react";
import { stackServerApp } from "@/stack";

import {
    fetchBacktestWorkspace,
    fetchPolicyVersionBacktests,
    fetchBacktestFiles,
    getAuthHeaders,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import {
    CreateWorkspacePage,
    BacktestsTableComponent,
    UploadedFilesTableComponent,
    WorkspaceCreation,
    PendingWorkspaceCreation,
} from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();

    const backtestWorkspace = await fetchBacktestWorkspace(user, params.policy_version_id).catch(
        (error) => {
            console.error(error);
            return null;
        },
    );

    if (backtestWorkspace?.status === "CREATION_PENDING") {
        return <PendingWorkspaceCreation policyVersionId={params.policy_version_id} />;
    }

    if (backtestWorkspace?.status === "OK") {
        return (
            <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
                <Suspense
                    fallback={
                        <div className="flex flex-col gap-2">
                            <h1 className="text-lg font-semibold md:text-2xl">Backtests</h1>
                            <div>Loading Backtests...</div>
                        </div>
                    }
                >
                    <BacktestsTable policyVersionId={params.policy_version_id} />
                </Suspense>
                <Suspense
                    fallback={
                        <div className="flex flex-col gap-2">
                            <h1 className="text-lg font-semibold md:text-2xl">Uploaded Files</h1>
                            <div>Loading Files...</div>
                        </div>
                    }
                >
                    <UploadedFilesTable policyVersionId={params.policy_version_id} />
                </Suspense>
            </div>
        );
    }

    return (
        <WorkspaceCreation
            workspaceStatus={backtestWorkspace?.status}
            workspaceCreationAction={workspaceCreationAction}
            policyVersionId={params.policy_version_id}
        />
    );
}

async function BacktestsTable({ policyVersionId }) {
    const user = await stackServerApp.getUser();
    const backtests = await fetchPolicyVersionBacktests(user, policyVersionId).catch((error) => {
        console.error(error);
        return [];
    });
    return <BacktestsTableComponent backtests={backtests} />;
}

async function UploadedFilesTable({ policyVersionId }) {
    const user = await stackServerApp.getUser();
    const uploadedFiles = await fetchBacktestFiles(user, policyVersionId).catch((error) => {
        console.error(error);
        return [];
    });
    return <UploadedFilesTableComponent uploadedFiles={uploadedFiles} />;
}

async function getWorkspaceStatusAction({ user, policyVersionId }) {
    "use server";
    const workspaceStatus = await fetchBacktestWorkspace(user, policyVersionId).catch((error) => {
        console.error(error);
        return null;
    });
    return workspaceStatus;
}

async function workspaceCreationAction({ url, headers }: { url: string; headers: any }) {
    "use server";
    const request = new Request(url, {
        method: "POST",
        headers: {
            ...headers,
        },
        mode: "cors",
    });

    return fetch(request)
        .then(async (response) => {
            if (!response.ok) {
                throw new Error("Failed to create workspace: " + response, { cause: response });
            }
            const data = await response.json();
            return data;
        })
        .catch((error) => {
            const errorMsg = "Error creating workspace";
            throw new Error(errorMsg, {
                cause: error,
            });
        });
}
