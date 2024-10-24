"use client";
import { Logs, Network, FolderCog, Play } from "lucide-react";

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
            name: "Launcher",
            icon: Play,
            path: `${baseUrl}/launcher`,
        },
        {
            name: "Runs",
            icon: Logs,
            path: `${baseUrl}/runs`,
        },
    ];
    const innerNavbarSections: InnerNavbarSectionProps[] = [
        { key: "Policy:", value: policy.name },
        { key: "Version:", value: policyVersion.alias },
    ];
    return (
        <div className="flex flex-col w-full h-full">
            <InnerNavbar backRoute={`/policies/${policy.policy_id}/versions`} sections={innerNavbarSections} />
            <PageLayout sidebar={{ sections, retractable: true }} content={{ scrollable: true }}>
                {children}
            </PageLayout>
        </div>
    );
}
