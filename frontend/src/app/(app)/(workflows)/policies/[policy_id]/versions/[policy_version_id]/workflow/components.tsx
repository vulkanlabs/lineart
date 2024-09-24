"use client";

import { Logs, Network, FolderCog } from "lucide-react";
import { SidebarSectionProps, Sidebar } from "@/components/page-layout";

export function LocalSidebar({ policyVersion }) {
    const baseUrl = `/policies/${policyVersion.policy_id}/versions/${policyVersion.policy_version_id}`;
    const sidebarSections: SidebarSectionProps[] = [
        {
            name: "Workflow",
            icon: Network,
            path: `${baseUrl}/workflow`,
        },
        {
            name: "Resources",
            icon: FolderCog,
            path: `${baseUrl}/resources`,
            disabled: true,
        },
        {
            name: "Logs",
            icon: Logs,
            path: `${baseUrl}/logs`,
            disabled: true,
        },
    ];
    return <Sidebar sections={sidebarSections} />;
}
