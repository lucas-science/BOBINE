"use client";
import React, { useTransition } from "react";
import Image from "next/image";
import { useRouter, usePathname } from "next/navigation";
import "./globals.css";

import { MyStepper } from "./components/stepper";
import BackButton from "./components/backButton";
import NextButton from "./components/nextButton";
import {
  getNavigationByIndex,
  getIndexByPathname
} from "@/src/lib/pathNavigation";

export default function RootLayout({
  children,
}: React.PropsWithChildren<object>) {
  const router   = useRouter();
  const pathname = usePathname();
  const step     = getIndexByPathname(pathname);

  const [prevPath, nextPath] = getNavigationByIndex(step);
  const [isPending, startTransition] = useTransition(); //true tant que la navigation est en cours

  const handleNext = () => {
    if (!nextPath) return;
    startTransition(() => {
      router.push(nextPath);
    });
  };

  const handleBack = () => {
    if (!prevPath) return;
    startTransition(() => {
      router.push(prevPath);
    });
  };

  return (
    <html lang="en" className="h-screen">
      <body className="flex flex-col h-screen relative overflow-hidden">
        {isPending && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/50">
            <div className="animate-spin rounded-full border-4 border-gray-300 border-t-blue-500 w-12 h-12" />
          </div>
        )}

        <header className="flex items-center justify-end p-5">
          <Image src="/logo-bobine.svg" alt="logo" width={100} height={100} />
        </header>

        <main className="flex-grow flex h-full pb-16">
          <div className="flex justify-center items-center p-6">
            <MyStepper activeStep={step + 1} />
          </div>
          <div className="flex-grow pt-4 pr-4 overflow-auto">
            {children}
          </div>
        </main>

        <footer className="flex items-center justify-between p-7 fixed bottom-0 w-full">
          <BackButton onClick={handleBack} disable={!prevPath} />
          <NextButton onClick={handleNext} disable={!nextPath} />
        </footer>
      </body>
    </html>
  );
}
