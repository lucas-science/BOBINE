import {
  Stepper,
  StepperIndicator,
  StepperItem,
  StepperSeparator,
  StepperTitle,
  StepperTrigger,
} from "@/src/components/ui/stepper";
import { STEPS_LABELS } from "@/src/lib/utils/navigation.utils";

// Définir les étapes du stepper

interface MyStepperProps {
  activeStep: number; // Le paramètre pour définir l'étape active
}

function MyStepper({ activeStep }: MyStepperProps) {
  return (
    <div className="text-center">
      <Stepper value={activeStep} orientation="vertical" onValueChange={() => {}}>
        {STEPS_LABELS.map(({ step, title }) => (
          <StepperItem
            key={step}
            step={step}
            className="relative items-start [&:not(:last-child)]:flex-1"
          >
            <StepperTrigger className="items-start pb-12 last:pb-0">
              <StepperIndicator />
              <div className="mt-0.5 px-2 text-left">
                <StepperTitle>{title}</StepperTitle>
              </div>
            </StepperTrigger>
            {step < STEPS_LABELS.length && (
              <StepperSeparator className="absolute inset-y-0 left-3 top-[calc(1.5rem+0.125rem)] -order-1 m-0 -translate-x-1/2 group-data-[orientation=vertical]/stepper:h-[calc(100%-1.5rem-0.25rem)] group-data-[orientation=horizontal]/stepper:w-[calc(100%-1.5rem-0.25rem)] group-data-[orientation=horizontal]/stepper:flex-none" />
            )}
          </StepperItem>
        ))}
      </Stepper>
    </div>
  );
}

export { MyStepper };
