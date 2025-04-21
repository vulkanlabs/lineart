import { Inter } from "next/font/google";
import "@/app/globals.css";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
    title: "Vulkan Engine",
    description: "Workspace for policies in Vulkan",
};

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body className={inter.className}>
                {children}
                <Toaster />
            </body>
        </html>
    );
}
