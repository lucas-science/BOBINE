"use client";
import { usePathname, useRouter } from "next/navigation";
import BackButton from "../components/backButton";
import NextButton from "../components/nextButton";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { useEffect } from "react";
import { Button } from "@/src/ui/button";
import { generateExcelFile } from "@/src/lib/utils/invoke.utils";

export default function Page() {
    const router = useRouter();
    const pathname = usePathname();
    const step = getIndexByPathname(pathname);
    const [prevPath, nextPath] = getNavigationByIndex(step);

    useEffect(() => {
        // get local storage item
        const selectedMetrics = localStorage.getItem('selectedMetrics');
        if (selectedMetrics) {  
            try {
                const parsedMetrics = JSON.parse(selectedMetrics);
                console.log("Selected metrics from localStorage:", parsedMetrics);
            } catch (error) {
                console.error("Error parsing selected metrics from localStorage:", error);
            }
        }
    }, []);

    const handleNext = async () => {
        if (!nextPath) return;
        router.push(nextPath);
    };

    const handleBack = async () => {
        if (!prevPath) return;
        router.push(prevPath);
    }
    const handleGenerateExcel = async () => {
        const selectedMetrics = localStorage.getItem('selectedMetrics');
        if (!selectedMetrics) {
            console.error("No selected metrics found in localStorage");
            return;
        }
        try {
            const parsedMetrics = JSON.parse(selectedMetrics);
            await generateExcelFile("/home/lucaslhm/Documents", parsedMetrics);
            console.log("Generating Excel file with metrics:", parsedMetrics);
        } catch (error) {
            console.error("Error generating Excel file:", error);
        }
    }
    return (
        <div>
            <p>Export</p>
            <Button onClick={handleGenerateExcel}></Button>
            <div className="fixed bottom-0 left-0 right-0 bg-amber-300 p-4">
                <div className="flex justify-between items-center w-full mx-auto">
                    <BackButton onClick={handleBack} disable={!prevPath} />
                    <NextButton
                        onClick={handleNext}
                        disable={!nextPath}
                    />
                </div>
            </div>
        </div>
    );
}