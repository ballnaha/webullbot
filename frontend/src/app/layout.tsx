import type { Metadata } from "next";
// ใช้ @fontsource แทน next/font/google เพื่อไม่ต้องออก internet (ไม่ trigger Windows Firewall)
import "@fontsource/sarabun/300.css";
import "@fontsource/sarabun/400.css";
import "@fontsource/sarabun/500.css";
import "@fontsource/sarabun/600.css";
import "@fontsource/sarabun/700.css";
import "@fontsource/sarabun/800.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "./globals.css";
import ClientLayout from "frontend/components/ClientLayout";

export const metadata: Metadata = {
  title: "Webull Trading Bot Dashboard",
  description: "Web GUI dashboard for Python Webull Trading Bot and Simulator",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
