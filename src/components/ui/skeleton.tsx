import { cn } from "@/src/lib/utils"

const skeletonKeyframes = `
@keyframes skeleton-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
`;

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: skeletonKeyframes }} />
      <div
        className={cn("rounded-md bg-muted", className)}
        style={{
          animation: "skeleton-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
          ...props.style
        }}
        {...props}
      />
    </>
  )
}

export { Skeleton }
