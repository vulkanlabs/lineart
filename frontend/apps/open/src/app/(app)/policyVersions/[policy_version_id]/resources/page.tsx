import { Suspense } from "react";

import {
    fetchPolicyVersionVariables,
    fetchPolicyVersionDataSources,
    fetchPolicyVersion,
} from "@/lib/api";

import { Loader } from "@vulkan/base";
import { EnvironmentVariables } from "./components";
import { DataSourcesTable, RequirementsEditor } from "./components";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const params = await props.params;

    return (
        <div className="flex flex-col p-8 gap-8">
            <div>
                <h1 className="mb-5 text-2xl font-bold tracking-tight">Environment Variables</h1>
                <Suspense fallback={<Loader />}>
                    <EnvironmentVariablesSection policy_version_id={params.policy_version_id} />
                </Suspense>
            </div>

            <div>
                <h1 className="mb-5 text-2xl font-bold tracking-tight">Data Sources</h1>
                <Suspense fallback={<Loader />}>
                    <DataSourcesSection policy_version_id={params.policy_version_id} />
                </Suspense>
            </div>

            <div>
                <h1 className="mb-5 text-2xl font-bold tracking-tight">Python Requirements</h1>
                <Suspense fallback={<Loader />}>
                    <RequirementsSection policy_version_id={params.policy_version_id} />
                </Suspense>
            </div>
        </div>
    );
}

async function EnvironmentVariablesSection({ policy_version_id }: { policy_version_id: string }) {
    const policyVersion = await fetchPolicyVersion(policy_version_id).catch((error) => {
        console.error(error);
        return null;
    });

    if (!policyVersion) {
        return <div>Policy version not found</div>;
    }

    const variables = await fetchPolicyVersionVariables(policy_version_id).catch((error) => {
        console.error(error);
        return [];
    });

    return <EnvironmentVariables policyVersion={policyVersion} variables={variables} />;
}

async function DataSourcesSection({ policy_version_id }: { policy_version_id: string }) {
    const dataSources = await fetchPolicyVersionDataSources(policy_version_id).catch((error) => {
        console.error(error);
        return [];
    });

    return <DataSourcesTable sources={dataSources} />;
}

async function RequirementsSection({ policy_version_id }: { policy_version_id: string }) {
    const policyVersion = await fetchPolicyVersion(policy_version_id).catch((error) => {
        console.error(error);
        return null;
    });

    if (!policyVersion) {
        return <div>Policy version not found</div>;
    }

    return <RequirementsEditor policyVersion={policyVersion} />;
}
