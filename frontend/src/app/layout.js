import { Inter } from "next/font/google";
import Navbar from "@/components/navbar";
import Sidebar from "@/components/sidebar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Vulkan Engine",
  description: "Workspace for policies in Vulkan",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex flex-col h-screen w-screen max-h-screen">
          <header className="flex h-16 min-h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
            <Navbar />
          </header>
          <div className="grid h-full w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
            <Sidebar />
            <div className="flex flex-col max-h-full">
              {children}
            </div>
          </div>
        </div>

      </body>
    </html>
  );
}
