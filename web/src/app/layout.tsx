import type { Metadata } from "next";
import "./globals.css";
import { Navigation } from "@/components/Navigation";

export const metadata: Metadata = {
  title: "Recruiter Copilot & Job-Ad Compliance Checker",
  description: "AI assistant for recruiter workflows, salary transparency checks, and inclusive job ad authoring",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased min-h-screen flex flex-col">
        <Navigation />
        <main className="flex-1 flex flex-col">{children}</main>
      </body>
    </html>
  );
}
