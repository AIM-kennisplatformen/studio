import { useRef, useState } from "react";
import { Action } from "@/components/shadcn-io/ai/actions";
import { Copy, Check } from "lucide-react";

export default function CopyButton({ value }) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);

  return (
    <Action
      label="Copy Message"
      tooltip="Copy message"
      className="size-6 rounded-md !bg-white/90 p-1 shadow-xs transition-colors hover:!bg-white"
      onClick={() => {
        navigator.clipboard.writeText(value);
        setCopied(true);
        clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => setCopied(false), 2000);
      }}>
      <div className="relative flex size-3.5 items-center justify-center">
        <Copy
          className={`text-primary absolute size-3.5 transition-all duration-300 ease-in-out ${
            copied
              ? "pointer-events-none scale-75 rotate-45 opacity-0"
              : "scale-100 rotate-0 opacity-100"
          }`}
        />
        <Check
          className={`text-primary absolute size-3.5 transition-all duration-300 ease-in-out ${
            copied
              ? "scale-100 rotate-0 opacity-100"
              : "pointer-events-none scale-75 -rotate-45 opacity-0"
          }`}
        />
      </div>
    </Action>
  );
}
