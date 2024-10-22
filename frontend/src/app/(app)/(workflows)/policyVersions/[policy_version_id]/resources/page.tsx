import { Suspense } from "react";
import { stackServerApp } from "@/stack";
import { CurrentUser } from "@stackframe/stack";

import { fetchPolicyVersionVariables, fetchPolicyVersionComponents } from "@/lib/api";
import Loader from "@/components/loader";
import { PolicyVersionComponentDependenciesTable } from "@/components/component/dependencies-table";

import { ConfigVariablesTable, EmptyVariablesTable } from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();

    return (
        <div className="flex flex-col p-8 gap-8">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Configuration Variables</h1>
                <Suspense fallback={<Loader />}>
                    <ConfigVariablesSection
                        user={user}
                        policy_version_id={params.policy_version_id}
                    />
                </Suspense>
            </div>

            <div>
                <h1 className="text-2xl font-bold tracking-tight">Components</h1>
                <Suspense fallback={<Loader />}>
                    <ComponentsSection user={user} policy_version_id={params.policy_version_id} />
                </Suspense>
            </div>
        </div>
    );
}

async function ConfigVariablesSection({
    user,
    policy_version_id,
}: {
    user: CurrentUser;
    policy_version_id: string;
}) {
    const variables = await fetchPolicyVersionVariables(user, policy_version_id).catch((error) => {
        console.error(error);
    });

    return variables.length > 0 ? (
        <ConfigVariablesTable variables={variables} />
    ) : (
        <EmptyVariablesTable />
    );
}

async function ComponentsSection({
    user,
    policy_version_id,
}: {
    user: CurrentUser;
    policy_version_id: string;
}) {
    const components = await fetchPolicyVersionComponents(user, policy_version_id).catch(
        (error) => {
            console.error(error);
        },
    );

    return components?.length > 0 ? (
        <PolicyVersionComponentDependenciesTable entries={components} />
    ) : (
        <EmptyVariablesTable />
    );
}
