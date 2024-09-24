"use client";
import { SidebarSectionProps, PageLayout } from "@/components/page-layout";
import { Network, Workflow, Puzzle, ArrowDownUp, Logs } from "lucide-react";

export default function Layout({ children }) {
    const sections: SidebarSectionProps[] = [
        {
            name: "Policies",
            icon: Workflow,
            path: "/policies",
        },
        {
            name: "Components",
            icon: Puzzle,
            path: "/components",
        },
        {
            name: "Integrations",
            icon: ArrowDownUp,
            path: "/integrations",
            disabled: true,
        },
        {
            name: "Logs",
            icon: Logs,
            path: "/logs",
            disabled: true,
        },
    ];
    const title = { name: "Workflows", icon: Network, path: "/policies" };

    return (
        <PageLayout title={title} sidebarSections={sections} retractable>
            {children}
        </PageLayout>
    );
}