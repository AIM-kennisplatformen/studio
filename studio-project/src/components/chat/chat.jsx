import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai/conversation";

export function Chat() {

  return (
<Conversation className="relative w-full" style={{ height: "500px" }}>
  <ConversationContent>
    <Message from={"user"}>
      <MessageContent>Hi there!</MessageContent>
    </Message>
  </ConversationContent>
  <ConversationScrollButton />
</Conversation>
);
}
