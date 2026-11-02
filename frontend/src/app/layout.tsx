import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AgentOps AI — Autonomous Production Incident Investigator",
  description: "Enterprise autonomous incident investigation, multi-agent root cause analysis, and sandboxed patch validation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background text-foreground flex antialiased`}>
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <Header />
          <main className="flex-1 p-8 max-w-7xl w-full mx-auto space-y-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
