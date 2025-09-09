"use client";
import React from "react";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { MyStepper } from "@/src/components/shared/stepper";
import { getIndexByPathname } from "@/src/lib/pathNavigation";
import "./globals.css";

export default function RootLayout({ children }: React.PropsWithChildren) {
  const pathname = usePathname();
  const step = getIndexByPathname(pathname);

  return (
    <html lang="en" className="h-screen">
      <body className="flex flex-col h-screen relative overflow-hidden">
        <header className="flex items-center justify-end p-5">
          <Image src="/logo-bobine.svg" alt="logo" width={100} height={100} />
        </header>

        <main className="flex-grow flex h-full">
          <div className="flex justify-center items-center p-6">
            <MyStepper activeStep={step + 1} />
          </div>
          <div className="flex-grow pt-4 pr-4 overflow-auto">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}