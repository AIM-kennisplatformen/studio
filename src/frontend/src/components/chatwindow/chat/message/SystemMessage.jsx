import { CircleCheck, MonitorCog, PenLine } from "lucide-react";
import { Response } from "@/components/shadcn-io/ai/response";
import { cn } from "@/lib/utils";

export default function SystemMessage({
  value,
  reverted = false,
  previousName,
  onButtonClick,
  type,
}) {
  switch (type) {
    case "adaptiveTitleMessage":
      return (
        <div className="flex w-full flex-col items-start gap-1 pr-[5%]">
          <span className="text-muted-foreground flex items-center gap-1.5 text-[10px] font-semibold tracking-wider uppercase">
            <MonitorCog className="h-3 w-3" /> System Message
          </span>
          <div
            className={cn(
              "flex w-full items-center gap-2.5 rounded-xl border px-3.5 py-2.5",
              reverted
                ? "border-emerald-700 bg-emerald-600"
                : "border-emerald-600/20 bg-emerald-500/10"
            )}>
            <div
              className={cn(
                "flex h-6.5 w-6.5 flex-none items-center justify-center rounded-full transition-colors",
                reverted ? "bg-white/20" : "bg-emerald-600/10"
              )}>
              {reverted ? (
                <CircleCheck
                  className="h-3.5 w-3.5 text-white"
                  strokeWidth={2.5}
                />
              ) : (
                <PenLine
                  className="h-3.5 w-3.5 text-emerald-700"
                  strokeWidth={2.2}
                />
              )}
            </div>

            <Response
              className={cn(
                "min-w-0 flex-1 text-[13.5px] leading-snug wrap-break-word",
                reverted ? "text-white" : "text-emerald-950"
              )}>
              {reverted
                ? `Reverted to: ***${previousName}***`
                : `Chat renamed ${previousName ? `from ***${previousName}***` : ""} to: ***${value}***`}
            </Response>

            {!reverted && onUndo && (
              <button
                type="button"
                onClick={onButtonClick}
                className="flex-none rounded px-1 py-0.5 text-[10px] leading-none font-medium text-emerald-700/60 transition-colors hover:text-emerald-700">
                Undo
              </button>
            )}
          </div>
        </div>
      );
    case "candidateTitleMessage":
      return <></>;

    default:
      return null;
  }
}
