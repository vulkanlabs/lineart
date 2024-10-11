import { stackServerApp } from "@/stack";
import { Suspense } from "react";

import { InnerNavbarSectionProps, InnerNavbar } from "@/components/inner-navbar";
import { fetchPolicyVersion, fetchRun, fetchRunsData, fetchRunLogs } from "@/lib/api";
import Loader from "@/components/loader";

import RunPageContent from "./components/content";
import type { NodeDefinition, GraphDefinition, RunData, RunNode, RunLogs } from "./types";

export default async function Page({ params }) {
    const innerNavbarSections: InnerNavbarSectionProps[] = [{ key: "Run:", value: params.run_id }];

    return (
        <div className="flex flex-col w-full h-full overflow-scroll">
            <InnerNavbar sections={innerNavbarSections} />
            <Suspense fallback={<Loader />}>
                <RunPage runId={params.run_id} />
            </Suspense>
        </div>
    );
}

async function RunPage({ runId }) {
    const user = await stackServerApp.getUser();
    const runLogs: RunLogs = await fetchRunLogs(user, runId).catch((error) => {
        console.error(error);
        return {};
    });
    const runData: RunData = await fetchRunsData(user, runId).catch((error) => {
        console.error(error);
        return {};
    });
    const run = await fetchRun(user, runId).catch((error) => {
        console.error(error);
        return {};
    });
    const policyVersion = await fetchPolicyVersion(user, run.policy_version_id).catch((error) => {
        console.error(error);
    });
    const graphData: GraphDefinition = JSON.parse(policyVersion.graph_definition);

    const flatNodes = Object.values(graphData).flatMap((nodeDefinition) => {
        if (nodeDefinition.node_type === "COMPONENT") {
            return Object.values(nodeDefinition.metadata.nodes);
        }
        return [nodeDefinition];
    });

    const runGraph: RunNode[] = flatNodes.map((node: NodeDefinition) => {
        const runStep = runData.steps[node.name];
        return {
            ...node,
            run: runStep,
        };
    });

    return <RunPageContent runGraph={runGraph} runLogs={runLogs} />;
}
