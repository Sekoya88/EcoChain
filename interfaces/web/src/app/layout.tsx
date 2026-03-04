import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { ThemeInit } from "@/components/theme-init";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "EcoChain AI",
  description: "Supply Chain Carbon Footprint Optimizer — Scope 3 Multi-Agent Analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){
  var t=localStorage.getItem('ecochain-theme')||'dark';
  var e=t==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;
  document.documentElement.classList.remove('light','dark');document.documentElement.classList.add(e);
})();`,
          }}
        />
      </head>
      <body className={`${dmSans.variable} font-sans antialiased`}>
        <ThemeInit />
        {children}
      </body>
    </html>
  );
}
