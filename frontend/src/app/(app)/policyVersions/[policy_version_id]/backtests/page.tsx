import { Suspense } from "react";
import { stackServerApp } from "@/stack";

import { fetchBacktestWorkspace, fetchPolicyVersionBacktests, listUploadedFiles } from "@/lib/api";

import { WorkspaceCreation, PendingWorkspaceCreation } from "./_components/workspace";
import { BacktestsTableComponent, UploadedFilesTableComponent } from "./_components/tables";
import { workspaceCreationAction } from "./actions";

export default async function Page(props) {
    const params = await props.params;

    const backtestWorkspace = await fetchBacktestWorkspace(params.policy_version_id).catch(
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
    const backtests = await fetchPolicyVersionBacktests(policyVersionId).catch((error) => {
        console.error(error);
        return [];
    });
    return <BacktestsTableComponent policyVersionId={policyVersionId} backtests={backtests} />;
}

async function UploadedFilesTable({ policyVersionId }) {
    const uploadedFiles = await listUploadedFiles().catch((error) => {
        console.error(error);
        return [];
    });
    return (
        <UploadedFilesTableComponent
            policyVersionId={policyVersionId}
            uploadedFiles={uploadedFiles}
        />
    );
}
