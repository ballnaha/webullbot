import type { Metadata } from "next";
// ใช้ @fontsource แทน next/font/google เพื่อไม่ต้องออก internet (ไม่ trigger Windows Firewall)
import "@fontsource/sarabun";
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
