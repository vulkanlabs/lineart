import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Menu,
  Package,
  Pencil
} from "lucide-react";
import { Button } from "@/components/ui/button";


const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Vulkan Engine",
  description: "Workspace for policies in Vulkan",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">

          {/* Side + Nav Bar */}
          <div className="hidden border-r bg-muted/40 md:block">
            <div className="flex h-full max-h-screen flex-col gap-2">
              {/* TOP LEFT: identificação + home button + notific */}
              <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
                <Link href="/" className="flex items-center gap-2 font-semibold">
                  <Package className="h-6 w-6" />
                  <span className="">Vulkan Engine</span>
                </Link>
              </div>
              {/* END TOP LEFT */}

              <div className="flex-1">
                <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
                  <Link
                    href="/policies"
                    className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
                  >
                    <Pencil className="h-4 w-4" />
                    Políticas
                  </Link>
                </nav>
              </div>
            </div>
          </div>
          {/* END Side + Nav Bar */}

          <div className="flex flex-col">
            {/* Collapsible Side Bar */}
            <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6">
              <Sheet key="left">
                <SheetTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="shrink-0 md:hidden"
                  >
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Toggle navigation menu</span>
                  </Button>
                </SheetTrigger>
                <SheetContent side="left">
                  <SheetHeader>
                    <SheetTitle>Sheet Title</SheetTitle>
                    <SheetDescription>Sheet Description</SheetDescription>
                  </SheetHeader>
                  <div className="p-4">
                    <p>Sheet Content</p>
                  </div>
                </SheetContent>
              </Sheet>
            </header>
            {/* END Collapsible Side Bar */}

            {children}
          </div>

        </div>

      </body>
    </html>
  );
}
