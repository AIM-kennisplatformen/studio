import CopyButton from "@/components/CopyButton";
import { Message, MessageContent } from "@/components/shadcn-io/ai/message";
import { User } from "lucide-react";

export default function UserMessage({ value }) {
  return (
    <div className="group flex w-full flex-col items-end">
      <span className="text-muted-foreground mb-1 flex items-center gap-1 text-[10px] font-semibold tracking-wider uppercase">
        You <User className="h-3 w-3" />
      </span>
      <Message from="user" className="flex w-full justify-end !pt-0 pl-[5%]">
        <MessageContent className="bg-primary selection:!text-primary max-w-prose wrap-break-word text-white selection:!bg-white">
          <span>{value}</span>
        </MessageContent>
      </Message>
      <div className="pointer-events-none mr-1 translate-y-1 opacity-0 transition-all duration-200 ease-out group-hover:pointer-events-auto group-hover:translate-y-0 group-hover:opacity-100">
        <CopyButton value={value} />
      </div>
    </div>
  );
}
