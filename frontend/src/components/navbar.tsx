"use client";
import Link from 'next/link';
import Image from 'next/image';
import LogoLight from "/public/vulkan-light.png";
import { usePathname } from 'next/navigation';
import { cn } from "@/lib/utils";

export default function Navbar() {
    const pathname = usePathname();
    const isSubpathActive = (path: string) => pathname.startsWith(path);

    const sidebarSections = [
        // { name: "Dashboard", path: "/dashboard" },
        { name: "Políticas", path: "/policies" },
        { name: "Componentes", path: "/components" },
        // { name: "Integrações", path: "/integrations" },
    ];

    return (
        <nav className="flex-row gap-4 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6 overflow-clip">
            <Link href="/" className="flex items-center gap-2 text-xl font-bold">
                <Image src={LogoLight} alt="Vulkan logo" className="max-h-10 max-w-10" />
                <span>Vulkan Engine</span>
            </Link>
            {sidebarSections.map((section) => (
                <Link key={section.name} href={section.path}
                    className={cn(
                        "flex items-center text-base gap-2 hover:font-bold",
                        isSubpathActive(section.path) ? "font-bold" : "text-muted-foreground"
                    )}>
                    <span>{section.name}</span>
                </Link>
            ))
            }
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