"use client";
import { SidebarSectionProps, SidebarProps, PageLayout } from "@/components/page-layout";
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
    const sidebar: SidebarProps = { title, sections, retractable: true };

    return (
        <PageLayout sidebar={sidebar} content={{ scrollable: true }}>
            {children}
        </PageLayout>
    );
}
