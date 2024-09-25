"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from "@/lib/utils";
import { VulkanLogo } from "@/components/logo";
import { UserButton } from '@stackframe/stack';

export default function Navbar() {
    const pathname = usePathname();
    const isSubpathActive = (path: string) => pathname.startsWith(path);

    const sections = [
        // { name: "Dashboard", path: "/dashboard" },
        { name: "Políticas", path: "/policies" },
        { name: "Componentes", path: "/components" },
        // { name: "Integrações", path: "/integrations" },
    ];

    return (
        <nav className="flex gap-4 text-lg font-medium md:items-center md:gap-5 md:text-sm lg:gap-6 overflow-clip">
            <VulkanLogo />
            {/* {sections.map((section) => (
                <Link key={section.name} href={section.path}
                    className={cn(
                        "flex items-center text-base gap-2 hover:font-bold",
                        isSubpathActive(section.path) ? "font-bold" : "text-muted-foreground"
                    )}>
                    <span>{section.name}</span>
                </Link>
            ))
            } */}
            <div className="absolute right-0 m-8">
                <UserButton />
            </div>
        </nav>
    );
}


// {/* Collapsible Side Bar */}
// <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6">
//   <Sheet key="left">
//     <SheetTrigger asChild>
//       <Button
//         variant="outline"
//         size="icon"
//         className="shrink-0 md:hidden"
//       >
//         <Menu className="h-5 w-5" />
//         <span className="sr-only">Toggle navigation menu</span>
//       </Button>
//     </SheetTrigger>
//     <SheetContent side="left">
//       <SheetHeader>
//         <SheetTitle>Sheet Title</SheetTitle>
//         <SheetDescription>Sheet Description</SheetDescription>
//       </SheetHeader>
//       <div className="p-4">
//         <p>Sheet Content</p>
//       </div>
//     </SheetContent>
//   </Sheet>
// </header>
// {/* END Collapsible Side Bar */}