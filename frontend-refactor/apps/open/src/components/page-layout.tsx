"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { cn } from "../../lib/utils";
import { SquareChevronLeft, SquareChevronRight } from "lucide-react";

export type SidebarTitleProps = {
    name: string;
    icon?: any;
};

export type SidebarSectionProps = {
    name: string;
    path: string;
    icon?: any;
    disabled?: boolean;
    info?: string;
};

export type SidebarProps = {
    title?: SidebarTitleProps;
    sections: SidebarSectionProps[];
    retractable?: boolean;
};

export type PageContentProps = {
    scrollable?: boolean;
};

export function PageLayout({
    sidebar,
    content,
    children,
}: {
    sidebar: SidebarProps;
    content?: PageContentProps;
    children: React.ReactNode;
}) {
    return (
        <div className="flex flex-row w-full h-full overflow-scroll">
            <Sidebar
                title={sidebar.title}
                sections={sidebar.sections}
                retractable={sidebar.retractable}
            />
            <div
                className={cn(
                    "flex flex-col w-full h-full",
                    content?.scrollable ? "overflow-scroll" : "overflow-clip",
                )}
            >
                {children}
            </div>
        </div>
    );
}

export function Sidebar({ title, sections, retractable }: SidebarProps) {
    const [expandOnHover, setExpandOnHover] = useState(false);
    const [isMouseOver, setIsMouseOver] = useState(true);
    const [isExpanded, setIsExpanded] = useState(true);
    const pathname = usePathname();
    const isSubpathActive = (path: string) => pathname.startsWith(path);

    function mouseEnterEvent() {
        if (!retractable) return;
        if (isMouseOver) return;
        if (!expandOnHover) return;
        setIsExpanded(true);
        setIsMouseOver(true);
    }

    function mouseLeaveEvent() {
        if (!retractable) return;
        if (!expandOnHover) return;
        if (expandOnHover) setIsExpanded(false);
        setIsMouseOver(false);
    }

    function toggleExpansion() {
        if (!retractable) return;
        setIsMouseOver(true);
        if (isExpanded && !expandOnHover) {
            setIsExpanded(false);
            setExpandOnHover(true);
            return;
        }
        if (isExpanded && expandOnHover) {
            setExpandOnHover(false);
            return;
        }
        if (!isExpanded && expandOnHover) {
            setIsExpanded(true);
            setExpandOnHover(false);
            return;
        }
    }

    return (
        <div
            className={cn(
                "flex flex-col border-r-2 gap-4 h-full overflow-clip",
                isExpanded ? "w-64 max-w-64" : "w-16 max-w-16",
            )}
            onMouseEnter={mouseEnterEvent}
            onMouseLeave={mouseLeaveEvent}
        >
            <div className="flex flex-col">
                {title && (
                    <div className="py-4 border-b-2 ">
                        <div className="ml-6 flex gap-4 h-7">
                            {title?.icon && <title.icon />}
                            {isExpanded && (
                                <h1 className="text-xl text-wrap font-semibold">{title.name}</h1>
                            )}
                        </div>
                    </div>
                )}
                {sections.map((sectionProps) => (
                    <div
                        key={sectionProps.name}
                        className={cn(
                            "py-4",
                            isSubpathActive(sectionProps.path)
                                ? "bg-slate-100 hover:bg-slate-200"
                                : "hover:bg-gray-100",
                        )}
                    >
                        <div className="ml-6">
                            {sectionProps.disabled ? (
                                <SidebarSection
                                    sectionProps={sectionProps}
                                    isSelected={isSubpathActive(sectionProps.path)}
                                    isExpanded={isExpanded}
                                />
                            ) : (
                                <Link href={sectionProps.path}>
                                    <SidebarSection
                                        sectionProps={sectionProps}
                                        isSelected={isSubpathActive(sectionProps.path)}
                                        isExpanded={isExpanded}
                                    />
                                </Link>
                            )}
                        </div>
                    </div>
                ))}
            </div>
            {retractable && (
                <div className="relative w-full h-full">
                    <div
                        className="absolute bottom-4 cursor-pointer ml-4"
                        onClick={() => toggleExpansion()}
                    >
                        {expandOnHover ? (
                            <SquareChevronRight strokeWidth={0.5} className="h-8 w-8" />
                        ) : (
                            <SquareChevronLeft strokeWidth={0.5} className="h-8 w-8" />
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export function SidebarSection({
    sectionProps,
    isSelected,
    isExpanded,
}: {
    sectionProps: SidebarSectionProps;
    isSelected: boolean;
    isExpanded?: boolean;
}) {
    const iconColor = isSelected ? "#065985" : "#646870";

    return (
        <div className="flex gap-4 items-center h-6">
            {sectionProps?.icon && <sectionProps.icon color={iconColor} className="h-4" />}
            {isExpanded && (
                <h2
                    className={cn(
                        "text-base text-clip font-semibold",
                        sectionProps.disabled ? "text-muted-foreground" : "text-primary",
                        isSelected ? "text-sky-800" : "",
                    )}
                >
                    {sectionProps.name}
                </h2>
            )}
        </div>
    );
}
