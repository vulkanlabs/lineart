"use client";

import {
    Logs,
    Network,
    FolderCog,
} from "lucide-react";
import { SidebarSectionProps, Sidebar } from "@/components/page-layout";

export function LocalSidebar({ policyData }) {
    const sidebarSections: SidebarSectionProps[] = [
        {
            name: "Workflow",
            icon: Network,
            path: `/policies/${policyData.policy_id}/workflow`,
        },
        {
            name: "Resources",
            icon: FolderCog,
            path: `/policies/${policyData.policy_id}/runs`,
            disabled: true,
        },
        {
            name: "Logs",
            icon: Logs,
            path: "/logs",
            disabled: true,
        },
    ];
    return <Sidebar sections={sidebarSections} />;
}
