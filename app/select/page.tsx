"use client";

import { useState } from "react";
import BackButton from "@/src/components/shared/backButton";
import NextButton from "@/src/components/shared/nextButton";
import { MetricsSelector } from "@/src/components/select/MetricsSelector";
import { MetricsSkeleton } from "@/src/components/select/MetricsSkeleton";
import { ConfirmBackDialog } from "@/src/components/select/ConfirmBackDialog";
import { SelectedMetricsBySensor } from "@/src/lib/utils/type";
import { useMetricsData } from "@/src/hooks/useMetricsData";
import { useStepNavigation } from "@/src/hooks/useStepNavigation";

export default function Page() {
  const [selectedMetrics, setSelectedMetrics] = useState<SelectedMetricsBySensor | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const { metricsAvailable } = useMetricsData();
  const { prevPath, nextPath, handleNext, handleBack } = useStepNavigation();

  const handleSelectionChange = (selectedMetrics: SelectedMetricsBySensor) => setSelectedMetrics(selectedMetrics);
  const hasSelectedMetrics = selectedMetrics && Object.values(selectedMetrics).some(arr => arr.length > 0);

  const handleBackClick = () => {
    setShowConfirmDialog(true);
  };

  const handleConfirmBack = () => {
    setShowConfirmDialog(false);
    handleBack();
  };

  return (
    <div>
      {metricsAvailable ? (
        <MetricsSelector
          className="pb-28"
          data={metricsAvailable}
          onSelectionChange={handleSelectionChange}
        />
      ) : (
        <MetricsSkeleton />
      )}
      <div className="fixed bottom-0 left-0 right-0  p-4">
        <div className="flex justify-between items-center w-full mx-auto">
          <BackButton onClick={handleBackClick} disable={!prevPath} />
          <NextButton
            onClick={() => handleNext(selectedMetrics)}
            disable={!nextPath || !hasSelectedMetrics}
          />
        </div>
      </div>

      <ConfirmBackDialog
        open={showConfirmDialog}
        onOpenChange={setShowConfirmDialog}
        onConfirm={handleConfirmBack}
      />
    </div>
  );
}