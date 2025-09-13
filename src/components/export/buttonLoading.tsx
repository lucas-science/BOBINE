import { Loader2Icon } from "lucide-react";
import { Button } from "@/src/ui/button";
import { cn } from "@/src/lib/utils"; // utilitaire classique pour merger les classes

interface ButtonLoadingProps {
  className?: string;
}

export function ButtonLoading({ className }: ButtonLoadingProps) {
  return (
    <Button
      disabled
      className={cn(
        "w-full justify-center space-x-2 rounded-lg",
        className
      )}
    >
      <Loader2Icon className="animate-spin h-4 w-4" />
      <span>La génération est en cours ...</span>
    </Button>
  );
}
export default ButtonLoading;