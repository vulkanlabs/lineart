"use client";
import { Layers, Network, FolderCog, Play, GitCompare } from "lucide-react";

import { SidebarSectionProps, PageLayout } from "@/components/page-layout";
import { InnerNavbarSectionProps, InnerNavbar } from "@/components/inner-navbar";

export function RouteLayout({ policy, policyVersion, children }) {
    const baseUrl = `/policyVersions/${policyVersion.policy_version_id}`;
    const sections: SidebarSectionProps[] = [
        {
            name: "Workflow",
            icon: Network,
            path: `${baseUrl}/workflow`,
        },
        {
            name: "Resources",
            icon: FolderCog,
            path: `${baseUrl}/resources`,
        },
        {
            name: "Runs",
            icon: Layers,
            path: `${baseUrl}/runs`,
        },
        {
            name: "Launcher",
            icon: Play,
            path: `${baseUrl}/launcher`,
        },
        {
            name: "Backtests",
            icon: GitCompare,
            path: `${baseUrl}/backtests`,
        },
    ];

    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Policy:", value: policy.name },
        { key: "Version:", value: policyVersion.alias },
    ];

    return (
        <div className="flex flex-col w-full h-full">
            <InnerNavbar
                backRoute={`/policies/${policy.policy_id}/overview`}
                sections={innerNavbarSections}
            />
            <PageLayout sidebar={{ sections, retractable: true }} content={{ scrollable: true }}>
                {children}
            </PageLayout>
        </div>
    );
}
