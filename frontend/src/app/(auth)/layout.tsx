import { Inter } from "next/font/google";
import { VulkanLogo } from "@/components/logo";
import "@/app/globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
    title: "Vulkan Engine",
    description: "Workspace for policies in Vulkan",
};

export default function LoginLayout({ children }) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <div className="flex flex-col w-screen h-screen max-h-screen">
                    <div className="flex h-full w-full">
                        {children}
                    </div>
                </div>
            </body>
        </html>
    );
}
