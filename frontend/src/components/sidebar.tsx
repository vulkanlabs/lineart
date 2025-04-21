"use client";

import Link from "next/link";
import { ChartSpline, Users2, Code2, ListTree, Section } from "lucide-react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useUser } from "@stackframe/stack";

import { fetchComponents, fetchPolicy, fetchPolicyVersionComponents } from "@/lib/api";

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="flex flex-col border-r-2 gap-4 w-64 max-w-64 h-full overflow-auto">
            <div className="mt-4">{chooseSideBar(pathname)}</div>
        </div>
    );
}

function chooseSideBar(pathname: string) {
    if (pathname.startsWith("/policies")) {
        const policyId = extractPolicyId(pathname);
        if (policyId === null) {
            return <PoliciesSidebarNav />;
        }
        return <PolicyDetailsSidebar policyId={policyId} />;
    }

    // default
    return <SidebarNav />;
}

type SidebarSectionProps = {
    name: string;
    path: string;
    icon?: any;
    children?: SidebarSectionItemProps[];
    emptySectionMsg?: string;
};

function withPath(props: SidebarSectionProps, path: string): SidebarSectionProps {
    return {
        ...props,
        path: path,
    };
}

function withChildren(
    props: SidebarSectionProps,
    children: SidebarSectionItemProps[],
): SidebarSectionProps {
    return {
        ...props,
        children: children,
    };
}

type SidebarSectionItemProps = {
    name: string;
    path: string;
};

const SectionDefinitions: Map<string, SidebarSectionProps> = new Map([
    [
        "teams",
        {
            name: "Teams",
            icon: Users2,
            path: "/teams",
            emptySectionMsg: "There is nothing here yet.",
        },
    ],
    [
        "components",
        {
            name: "Components",
            icon: Code2,
            path: "/components",
            emptySectionMsg: "Your components will be shown here.",
        },
    ],
    [
        "policies",
        {
            name: "Policies",
            icon: Code2,
            path: "/policies",
            emptySectionMsg: "Your policies will be shown here.",
        },
    ],
    [
        "monitoring",
        {
            name: "Monitoring",
            icon: ChartSpline,
            path: ``,
            emptySectionMsg: "There is nothing here yet.",
        },
    ],
]);

function SidebarNav() {
    // TODO: Get Teams + Components + Policies
    const sections = [
        SectionDefinitions.get("teams"),
        SectionDefinitions.get("components"),
        SectionDefinitions.get("policies"),
    ];

    return <SidebarMenu title="Navigation" sections={sections} />;
}

function PoliciesSidebarNav() {
    const [components, setComponents] = useState([]);
    const user = useUser();

    useEffect(() => {
        fetchComponents(user).then((data) => {
            const componentData = data.map((component: { component_id: number; name: string }) => ({
                name: component.name,
                path: `/components/${component.component_id}`,
            }));
            setComponents(componentData);
        });
    }, []);

    const sections: Array<SidebarSectionProps> = [
        SectionDefinitions.get("teams"),
        withChildren(SectionDefinitions.get("components"), components),
    ];

    return <SidebarMenu title="Policies" sections={sections} />;
}

function PolicyDetailsSidebar({ policyId }: { policyId: string }) {
    const [currentPolicy, setCurrentPolicy] = useState(null);
    const [components, setComponents] = useState([]);
    const user = useUser();

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const pathname = usePathname();

    useEffect(() => {
        fetchPolicy(user, policyId)
            .then((policy) => setCurrentPolicy(policy))
            .catch((error) => {
                console.error(error);
            });

        return;
    }, [policyId, pathname, serverUrl]);

    // Handle component dependencies
    useEffect(() => {
        if (!currentPolicy || !currentPolicy.active_policy_version_id) {
            return;
        }
        fetchPolicyVersionComponents(user, currentPolicy.active_policy_version_id)
            .then((dependencies) => {
                const componentData = dependencies.map((dep) => ({
                    name: dep.component_name,
                    path: `/components/${dep.component_id}`,
                }));
                setComponents(componentData);
            })
            .catch((error) => {
                throw Error(`Error fetching components for policy ${currentPolicy.id}`, {
                    cause: error,
                });
            });
    }, [serverUrl, currentPolicy]);

    const sections = [
        withPath(SectionDefinitions.get("monitoring"), `/policies/${policyId}/monitoring`),
        withChildren(SectionDefinitions.get("components"), components),
    ];

    return (
        <SidebarMenu title={currentPolicy ? currentPolicy.name : "Policy"} sections={sections} />
    );
}

function SidebarMenu({ title, sections }: { title: string; sections: SidebarSectionProps[] }) {
    return (
        <div className="flex flex-col gap-4 mt-1">
            <div className="pb-4 border-b-2 ">
                <h1 className="text-xl text-wrap font-semibold ml-4">{title}</h1>
            </div>
            {sections.map((section) => (
                <div key={section.name}>
                    <Link href={section.path}>
                        <div className="flex ml-4 gap-2">
                            {section?.icon && <section.icon />}
                            <h2 className="text-base font-semibold text-clip">{section.name}</h2>
                        </div>
                    </Link>
                    <div className="flex flex-col gap-2 ml-4">
                        {!section.children || section.children.length == 0 ? (
                            <EmptySidebarSection text={section.emptySectionMsg} />
                        ) : (
                            section.children.map((child) => (
                                <Link
                                    key={child.name}
                                    href={child.path}
                                    className="flex text-sm gap-2 justify-end mr-8 hover:font-semibold"
                                >
                                    <span>{child.name}</span>
                                </Link>
                            ))
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}

function EmptySidebarSection({ text }: { text: string }) {
    return <span className="text-sm text-clip justify-end">{text}</span>;
}

function extractPolicyId(path: string): string | null {
    if (!path.startsWith("/policies/")) {
        return null;
    }
    const parts = path.split("/");
    if (parts.length < 3) {
        return null;
    }
    return parts[2];
}
