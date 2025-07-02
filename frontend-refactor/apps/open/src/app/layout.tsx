import { Inter } from "next/font/google";
import "@/app/globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
    title: "Vulkan Engine",
    description: "Workspace for policies in Vulkan",
    icons: {
        icon: "/favicon.ico",
    },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <Providers>
                    {children}
                </Providers>
            </body>
        </html>
    );
}
