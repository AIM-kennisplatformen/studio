import { Button } from "@/components/ui/button"
import { Message, MessageContent } from "@/components/ui/shadcn-io/ai/Message";
import { Response } from "@/components/ui/shadcn-io/ai/Response";

export function ChatAI() {
  const messages = [
    { id: 1, role: "user", content: "Hello!" },
    { id: 2, role: "assistant", content: "Hi! How can I help?" },
  ];

  return (
    <div>
        <Button>Button</Button>
      {messages.map(msg => (
        <Message from={msg.role} key={msg.id}>
          <MessageContent>
            <Response>{msg.content}</Response>
          </MessageContent>
        </Message>
      ))}
    </div>
  );
}