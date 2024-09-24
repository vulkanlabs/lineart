"use client";

import {
    GitCompare,
    FlaskConical,
    GitBranch,
    ChartColumnStacked,
    Layers,
} from "lucide-react";
import { SidebarSectionProps, Sidebar } from "@/components/page-layout";

export function LocalSidebar({ policyId }) {
    const sidebarSections: SidebarSectionProps[] = [
        {
            name: "Versions",
            icon: GitBranch,
            path: `/policies/${policyId}/versions`,
        },
        {
            name: "Runs",
            icon: Layers,
            path: `/policies/${policyId}/runs`,
        },
        {
            name: "Experiments",
            icon: FlaskConical,
            path: `/policies/${policyId}/experiments`,
            disabled: true,
        },
        {
            name: "Backtests",
            icon: GitCompare,
            path: `/policies/${policyId}/backtests`,
            disabled: true,
        },
        {
            name: "Metrics",
            icon: ChartColumnStacked,
            path: `/policies/${policyId}/metrics`,
            disabled: true,
        },
    ];
    return <Sidebar sections={sidebarSections} />;
}
