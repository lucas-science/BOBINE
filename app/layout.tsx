"use client";
import React, { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import "./globals.css";

import { MyStepper } from "./components/stepper";
import BackButton from "./components/backButton";
import NextButton from "./components/nextButton";
import { getNavigationByIndex } from "@/src/lib/pathNavigation";

export default function RootLayout({ children }: React.PropsWithChildren<object>) {
  const [step, setStep] = useState<number>(0);
  const router = useRouter();

  const handleNext = () => {
    const paths = getNavigationByIndex(step);
    setStep((prevStep) => prevStep + 1);

    if (paths[1]) {
      router.push(paths[1]);
    }
  };

  const handleBack = () => {
    const paths = getNavigationByIndex(step);
    setStep((prevStep) => prevStep - 1);

    if (paths[0]) {
      router.push(paths[0]);
    }
  };
  useEffect(() => console.log("Current st ep:", step), [step]);

  return (
    <html lang="en">
      <body className="flex flex-col min-h-screen">
        <header className="flex items-center justify-end p-4">
          <Image src="/logo-bobine.svg" alt="logo" width={100} height={100} />
        </header>
        <main className="flex-grow flex h-full">
          <div className="flex justify-center items-center p-6">
            <MyStepper activeStep={step+1} />
          </div>
          <div className="flex-grow">{children}</div>
        </main>
        <footer className="flex items-center justify-between p-7">
          <BackButton onClick={handleBack} disable={step===0}/>
          <NextButton onClick={handleNext} disable={step===2}/>
        </footer>
      </body>
    </html>
  );
}
