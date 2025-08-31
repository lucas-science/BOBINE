import React from "react";
import { Alert, AlertDescription, AlertTitle } from "@/src/components/ui/alert";
import { AlertCircle, X } from "lucide-react";
import { cn } from "@/src/lib/utils";

interface ErrorAlertProps {
    error: string | null;
    onDismiss: () => void;
    title?: string;
    className?: string;
    hideDismissButton?: boolean;
}

export default function ErrorAlert({
    error,
    onDismiss,
    title = "Erreur lors du traitement",
    className,
    hideDismissButton = false,
}: ErrorAlertProps) {
    if (!error) return null;

    return (
        <Alert className={cn("mb-6 bg-red-50 border-red-200 text-red-800", className)}>
            <div className="flex items-center space-x-2 mb-1">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <p className="text-red-500">{title}</p>
            </div>
            <AlertDescription className="flex items-start justify-between">
                <div className="text-sm text-red-700">{error}</div>
                {!hideDismissButton && (
                    <button
                        type="button"
                        className="ml-4 flex-shrink-0 rounded-md p-1 text-red-400"
                        onClick={onDismiss}
                        aria-label="Fermer l'alerte"
                    >
                        <X className="h-4 w-4 hover:cursor-pointer" />
                    </button>
                )}
            </AlertDescription>
        </Alert>
    );
}