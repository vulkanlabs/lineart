import { Suspense } from "react";

import {
    fetchPolicyVersionVariables,
    fetchPolicyVersionDataSources,
    fetchPolicyVersion,
} from "@/lib/api";

import Loader from "@/components/animations/loader";

import { ConfigVariablesTable, DataSourcesTable, RequirementsEditor } from "./components";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const params = await props.params;

    return (
        <div className="flex flex-col p-8 gap-8">
            <div>
                <h1 className="mb-5 text-2xl font-bold tracking-tight">Configuration Variables</h1>
                <Suspense fallback={<Loader />}>
                    <ConfigVariablesSection policy_version_id={params.policy_version_id} />
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

async function ConfigVariablesSection({ policy_version_id }: { policy_version_id: string }) {
    const variables = await fetchPolicyVersionVariables(policy_version_id).catch((error) => {
        console.error(error);
        return [];
    });

    return <ConfigVariablesTable variables={variables} />;
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

    return <RequirementsEditor policyVersion={policyVersion} />;
}
