"use client";

// External libraries
import { Workflow, Puzzle, ArrowDownUp, Logs } from "lucide-react";

// Vulkan packages
import { SharedNavbar, type NavigationSection } from "@vulkanlabs/base";

// Local imports
import { VulkanLogo } from "@/components/logo";
import "@/app/globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
    const sections: NavigationSection[] = [
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
            path: "/integrations/dataSources",
        },
        {
            name: "Logs",
            icon: Logs,
            path: "/logs",
            disabled: true,
        },
    ];

    return (
        <div className="flex flex-col w-full h-screen max-h-screen overflow-hidden-safe">
            <SharedNavbar
                config={{
                    sections,
                    logoComponent: <VulkanLogo />,
                }}
            />
            <div className="w-full h-full overflow-hidden-safe">{children}</div>
        </div>
    );
}
