import type { Metadata } from "next";
import Sidebar from "@/components/layout/Sidebar";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "CryptoPulse AI — Decision Platform",
  description: "Real-time algorithmic trading decisions and machine learning analytics.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto h-screen p-8 bg-slate-950">
          <div className="max-w-7xl mx-auto space-y-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
