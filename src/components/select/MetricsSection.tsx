"use client";

import React from "react";
import { CardContent, CardHeader, CardTitle } from "@/src/components/ui/card";

interface MetricsSectionProps {
  title: string;
  children: React.ReactNode;
}

export const MetricsSection: React.FC<MetricsSectionProps> = ({ title, children }) => {
  return (
    <>
      <CardHeader>
        <CardTitle className="text-lg font-medium text-gray-900">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {children}
      </CardContent>
    </>
  );
};