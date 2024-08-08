'use client';
import Link from "next/link";
import { ChevronRightIcon, ChevronLeftIcon, Users2, Code2, ListTree } from "lucide-react";

import { createContext, useContext, useState } from 'react';
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";

const SidebarContext = createContext();

export default function Sidebar() {
    const [isOpen, setIsOpen] = useState(false);
    const pathname = usePathname();

    return (
        <SidebarContext.Provider value={{ isOpen }}>
            <div className="flex flex-col border-r gap-4 w-fit h-full transition-[width] duration-1000">
                <Button
                    onClick={() => setIsOpen(!isOpen)}
                    className="justify-start w-fit rounded-full"
                >
                    {isOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                </Button>
                {chooseNavBar(pathname)}
            </div>
        </SidebarContext.Provider>
    );
}

function chooseNavBar(pathname) {
    if (pathname.startsWith("/policies")) {
        return <PoliciesSidebarNav />;
    }
    return <SidebarNav />;
}

function SidebarNav() {
    let { isOpen } = useContext(SidebarContext);

    return (
        <div className="flex flex-col gap-4 mt-1 ">
            <Link href="/teams" className="flex mx-2 gap-2 hover:font-bold">
                <Users2 />
                <span className={isOpen ? "ease-in" : "hidden"}>Times</span>
            </Link>

            <Link href="/components" className="flex mx-2 gap-2 hover:font-bold">
                <Code2 />
                <span className={isOpen ? "ease-in" : "hidden"}>Componentes</span>
            </Link>

            <Link href="/policies" className="flex mx-2 gap-2 hover:font-bold">
                <ListTree />
                <span className={isOpen ? "ease-in" : "hidden"}>Políticas</span>
            </Link>
        </div>
    );
}

function PoliciesSidebarNav() {
    let { isOpen } = useContext(SidebarContext);

    return (
        <div className="flex flex-col gap-4 mt-1">
            <h1 className="text-lg font-semibold">Policy</h1>
        </div>
    );
};
