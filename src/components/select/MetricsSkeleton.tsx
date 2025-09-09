import React from "react";
import { Skeleton } from "@/src/components/ui/skeleton";

export const MetricsSkeleton: React.FC = () => {
  return (
    <div className="w-full max-w-2xl mx-auto space-y-6 pb-28">
      {[...Array(4)].map((_, index) => (
        <div key={index} className="space-y-3">
          <Skeleton className="h-8 w-64" />
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-3/4" />
          </div>
        </div>
      ))}
    </div>
  );
};