'use client';
import Link from "next/link";
import { ChevronRightIcon, ChevronLeftIcon, Users2, Code2, ListTree } from "lucide-react";

import { createContext, useContext, useEffect, useState } from 'react';
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";
import { fetchComponents, fetchPolicy, fetchPolicyVersionComponents } from "@/lib/api";
import { string } from "zod";


const SidebarContext = createContext({ isOpen: true });

export default function Sidebar() {
    const [isOpen, setIsOpen] = useState(true);
    const pathname = usePathname();

    return (
        <SidebarContext.Provider value={{ isOpen }}>
            <div className="flex flex-col border-r-2 gap-4 w-64 max-w-64 h-full overflow-auto">
                {/* <Button
                    onClick={() => setIsOpen(!isOpen)}
                    className="justify-start w-12 rounded-full"
                >
                    {isOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                </Button> */}
                <div className="mt-4">
                    {chooseNavBar(pathname)}
                </div>
            </div>
        </SidebarContext.Provider>
    );
}

function chooseNavBar(pathname: string) {
    if (pathname.startsWith("/policies")) {
        return <PoliciesSidebarNav />;
    }
    return <SidebarNav />;
}

function SidebarNav() {
    const { isOpen } = useContext(SidebarContext);
    const sections = [
        // { name: "Times", path: "/teams", icon: Users2 },
        { name: "Políticas", path: "/policies", icon: ListTree },
        { name: "Componentes", path: "/components", icon: Code2 },
    ];

    return (
        <div className="flex flex-col gap-4 mt-1">
            {sections.map((section) => (
                <Link
                    key={section.name}
                    href={section.path}
                    className="flex ml-4 gap-2 hover:font-semibold"
                >
                    <section.icon />
                    <span className={isOpen ? "ease-in" : "hidden"}>{section.name}</span>
                </Link>
            ))}
        </div>
    );
}

// TODO: This code has two different behaviors depending on whether or 
// not the user is in a specific policy.
// We should try splitting this up into two different components.
function PoliciesSidebarNav() {
    const { isOpen } = useContext(SidebarContext);
    const [currentPolicy, setCurrentPolicy] = useState(null);
    const [components, setComponents] = useState([]);

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const pathname = usePathname();

    useEffect(() => {
        const policyId = extractPolicyId(pathname);
        if (policyId === null) {
            setCurrentPolicy(null);
            fetchComponents(serverUrl)
                .then((data) => {
                    const componentData = data.map(
                        (component: { component_id: number, name: string }) => ({
                            "name": component.name,
                            "path": `/components/${component.component_id}`,
                        }));
                    setComponents(componentData);
                })
            return;
        }

        fetchPolicy(serverUrl, policyId)
            .then((policy) => setCurrentPolicy(policy))
            .catch((error) => {
                console.error(error);
                setCurrentPolicy(null);
                setComponents([]);
            })

        return;
    }, [pathname, serverUrl]);

    // Handle component & policy dependencies
    useEffect(() => {
        if (currentPolicy == null) {
            return;
        }

        fetchPolicyVersionComponents(serverUrl, currentPolicy?.active_policy_version_id)
            .then((dependencies) => {
                const componentData = dependencies.map(
                    (dep) => ({
                        "name": dep.component_name,
                        "path": `/components/${dep.component_id}`,
                    }));
                setComponents(componentData);
            })
            .catch((error) => {
                throw Error(`Error fetching components for policy ${currentPolicy.id}`, { cause: error })
            });
    }, [currentPolicy]);

    const sections = [
        {
            name: "Monitoramento",
            children: [],
            emptySectionMsg: "Ainda não tem nada aqui."
        },
        {
            name: "Componentes",
            children: components,
            emptySectionMsg: "Seus componentes ficam aqui. Crie um novo para começar."
        },
    ];

    return (
        <div className="flex flex-col gap-4 mt-1">
            <div className="pb-4 border-b-2 ">
                <h1 className="text-xl text-wrap font-semibold ml-4">
                    {currentPolicy == null ? "Políticas" : currentPolicy.name}
                </h1>
            </div>
            {sections.map((section) => (
                <div key={section.name}>
                    <h2 className="text-base font-semibold text-clip ml-4">{section.name}</h2>
                    <div className="flex flex-col gap-2 ml-4">
                        {
                            section.children.length == 0
                                ? <EmptySidebarSection text={section.emptySectionMsg} />
                                : section.children.map((child) => (
                                    <Link key={child.name}
                                        href={child.path}
                                        className="flex text-sm gap-2 justify-end mr-8 hover:font-semibold"
                                    >
                                        <span>{child.name}</span>
                                    </Link>
                                ))}
                    </div>
                </div>
            ))}
        </div>
    );
};

function EmptySidebarSection({ text }: { text: string }) {
    return (
        <span className="text-sm text-clip justify-end">{text}</span>
    );
}


function extractPolicyId(path: string): number | null {
    if (!path.startsWith("/policies/")) {
        return null;
    }
    const parts = path.split("/");
    if (parts.length < 3) {
        return null;
    }
    return parseInt(parts[2]);
}