"use client";

// React and Next.js
import { useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import Link from "next/link";

// External libraries
import { Workflow, Puzzle, ArrowDownUp, Logs, Menu, FolderOpen, LucideIcon } from "lucide-react";

// Vulkan packages
import { Button, Sheet, SheetContent, SheetTrigger } from "@vulkanlabs/base/ui";
import { cn } from "../../lib/utils";

export interface NavigationSection {
    name: string;
    icon?: LucideIcon;
    path: string;
    disabled?: boolean;
    skipProjectParam?: boolean;
}

export interface SharedNavbarConfig {
    sections: NavigationSection[];
    withProject?: (path: string, projectId?: string) => string;
    rightContent?: React.ReactNode;
    projectId?: string;
    logoComponent: React.ReactNode;
}

export function SharedNavbar({ config }: { config: SharedNavbarConfig }) {
    const [open, setOpen] = useState(false);
    const pathname = usePathname();

    const getHref = (section: NavigationSection) => {
        if (section.disabled) return "#";
        if (section.skipProjectParam || !config.withProject) return section.path;
        return config.withProject(section.path, config.projectId);
    };

    return (
        <header className="sticky flex h-16 min-h-16 items-center gap-4 border-b-2 bg-background px-4 md:px-6">
            <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                    <Button variant="ghost" size="icon" className="md:hidden">
                        <Menu className="h-5 w-5" />
                        <span className="sr-only">Toggle menu</span>
                    </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-[250px] sm:w-[300px]">
                    <nav className="flex flex-col space-y-4 mt-8">
                        {config.sections.map((section) => (
                            <Link
                                key={section.path}
                                href={getHref(section)}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                                    pathname.startsWith(section.path)
                                        ? "bg-muted font-medium"
                                        : "hover:bg-muted/50",
                                    section.disabled && "opacity-50 cursor-not-allowed",
                                )}
                                onClick={(e) => {
                                    if (section.disabled) e.preventDefault();
                                    else setOpen(false);
                                }}
                            >
                                {section.icon && <section.icon className="h-5 w-5" />}
                                <span>{section.name}</span>
                            </Link>
                        ))}
                    </nav>
                </SheetContent>
            </Sheet>
            <nav className="flex items-center gap-4 text-lg font-medium md:gap-5 md:text-sm lg:gap-6">
                {config.logoComponent}
                <div className="hidden md:flex items-center gap-1 lg:gap-2">
                    {config.sections.map((section) => (
                        <Button
                            key={section.path}
                            variant={pathname.startsWith(section.path) ? "secondary" : "ghost"}
                            className={cn(
                                "gap-2",
                                section.disabled && "opacity-50 cursor-not-allowed",
                            )}
                            disabled={section.disabled}
                            asChild={!section.disabled}
                        >
                            {!section.disabled ? (
                                <Link href={getHref(section)} className="flex items-center gap-2">
                                    {/* {section.icon && <section.icon className="h-4 w-4" />} */}
                                    <span>{section.name}</span>
                                </Link>
                            ) : (
                                <>
                                    {/* {section.icon && <section.icon className="h-4 w-4" />} */}
                                    <span>{section.name}</span>
                                </>
                            )}
                        </Button>
                    ))}
                </div>
            </nav>
            {config.rightContent && (
                <div className="ml-auto flex items-center gap-4">{config.rightContent}</div>
            )}
        </header>
    );
}
