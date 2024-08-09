"use client";
import Link from 'next/link';
import { Pi } from "lucide-react";
import { usePathname } from 'next/navigation';
import { cn } from "@/lib/utils";

export default function Navbar() {
    const pathname = usePathname();
    const isSubpathActive = (path) => pathname.startsWith(path);

    return (
        <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
            <Link href="/" className="flex items-center gap-2 text-lg font-bold md:text-base">
                <Pi />
                <span>Vulkan Engine</span>
            </Link>
            <></>

            <Link href="/dashboard" className={cn(
                "flex items-center gap-2 text md:text-base",
                isSubpathActive("/dashboard") ? "font-semibold" : "text-muted-foreground"
            )}>
                <span>Dashboard</span>
            </Link>
            <Link href="/policies" className={cn(
                "flex items-center gap-2 text md:text-base",
                isSubpathActive("/policies") ? "font-semibold" : "text-muted-foreground"
            )}>
                <span>Políticas</span>
            </Link>
            <Link href="/components" className={cn(
                "flex items-center gap-2 text md:text-base",
                isSubpathActive("/components") ? "font-semibold" : "text-muted-foreground"
            )}>
                <span>Componentes</span>
            </Link>
            <Link href="/integrations" className={cn(
                "flex items-center gap-2 text md:text-base",
                isSubpathActive("/integrations") ? "font-semibold" : "text-muted-foreground"
            )}>
                <span>Integrações</span>
            </Link>
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