import React from "react";
import { CardHeader, CardTitle, CardContent } from "@/src/components/ui/card";

export const MetricsSection: React.FC<{ title: string; children: React.ReactNode; }> = ({ title, children }) => {
  return (
    <>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold text-gray-900">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">{children}</CardContent>
    </>
  );
};
