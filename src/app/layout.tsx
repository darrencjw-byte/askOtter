import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import { SgdsProvider } from "@/components/sgds-provider";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";
import "./sgds.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Government of Singapore",
  description: "A Singapore Government digital service built with VIBER Studio.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-screen flex-col bg-background text-foreground font-sans">
        <SgdsProvider>
          <sgds-masthead fluid></sgds-masthead>
          <main className="flex-1">{children}</main>
          <sgds-footer
            contactHref="#"
            feedbackHref="#"
            privacyHref="/privacy"
            termsOfUseHref="/terms"
          ></sgds-footer>
          <Toaster richColors position="top-right" />
        </SgdsProvider>
      </body>
    </html>
  );
}
