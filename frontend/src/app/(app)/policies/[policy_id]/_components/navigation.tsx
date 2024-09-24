"use client";

import { useRouter } from "next/navigation";
import {
    GitCompare,
    Undo2,
    FlaskConical,
    GitBranch,
    ChartColumnStacked,
    Layers,
} from "lucide-react";
import { SidebarSectionProps, Sidebar } from "@/components/page-layout";

export function LocalNavbar({ policyData }) {
    const router = useRouter();

    function handleBackClick() {
        router.back();
    }

    return (
        <div className="border-b-2">
            <div className="flex flex-row gap-4">
                <div
                    onClick={handleBackClick}
                    className="flex flex-row px-6 border-r-2 items-center cursor-pointer"
                >
                    <Undo2 />
                </div>
                <div className="flex py-4 gap-2 items-center">
                    <h1 className="text-xl text-wrap font-semibold">Policy:</h1>
                    <h1 className="text-base text-wrap font-normal">{policyData.name}</h1>
                </div>
            </div>
        </div>
    );
}

export function LocalSidebar({ policyData }) {
    const sidebarSections: SidebarSectionProps[] = [
        {
            name: "Versions",
            icon: GitBranch,
            path: `/policies/${policyData.policy_id}`,
        },
        {
            name: "Runs",
            icon: Layers,
            path: `/policies/${policyData.policy_id}/runs`,
            disabled: true,
        },
        {
            name: "Experiments",
            icon: FlaskConical,
            path: `/policies/${policyData.policy_id}/experiments`,
            disabled: true,
        },
        {
            name: "Backtests",
            icon: GitCompare,
            path: `/policies/${policyData.policy_id}/backtests`,
            disabled: true,
        },
        {
            name: "Metrics",
            icon: ChartColumnStacked,
            path: `/policies/${policyData.policy_id}/metrics`,
            disabled: true,
        },
    ];
    const title = { name: policyData.name, path: "/policies" };
    return <Sidebar sections={sidebarSections} />;
}
