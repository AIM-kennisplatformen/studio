import { locator } from "@qavajs/steps-playwright/po.js";
export default class App {
  Body = locator("body");
  GetStartedButton = locator("a.button[href='/docs/intro']");

  // Authentik login page selectors
  // Authentik uses Shadow DOM (Lit web components), Playwright pierces it automatically
  AuthentikUsernameInput = locator("input[name='uidField']");
  AuthentikPasswordInput = locator("#ak-stage-password-input");
  AuthentikSubmitButton = locator(".pf-c-button.pf-m-primary.pf-m-block");

  // Chat UI selectors (from frontend/src/chat.jsx + prompt-input.jsx)
  // The textarea has name="message" and placeholder="Type your message..."
  ChatMessageInput = locator("textarea[name='message']");
  // The submit button is a <button type="submit"> inside the prompt input form
  ChatSendButton = locator("button[type='submit']");
  // All chatbot response elements (collection) — each bot response is a Response div
  // Try multiple selectors to be robust:
  // 1. First try the Response component (from shadcn-io/ai)
  ChatResponse = locator.native(({ page }) =>
    // Response containers can have various classes, but usually have bg-gray-50
    page.locator("div[class*='bg-gray-50']").first()
  );
  // The actual LLM reply — waits for a response that contains actual bot message (not "Thinking")
  // Polls until finding a bot response that has actual text content
  ChatLLMResponse = locator.native(async ({ page }) => {
    const responses = page.locator("div[class*='bg-gray-50']");
    const maxWait = 60000; // 60 seconds max wait for LLM response
    const startTime = Date.now();
    
    // Keep polling until we find a real LLM response (not just thinking state)
    while (Date.now() - startTime < maxWait) {
      const count = await responses.count();
      
      for (let i = 0; i < count; i++) {
        const elem = responses.nth(i);
        const text = await elem.innerText();
        
        // Skip welcome message container
        if (text.includes("What would you like to explore today?") && !text.includes("\n")) {
          continue;
        }
        
        // Look for responses that have actual content (message from user/bot)
        // Skip if it only contains thinking state
        if (text.includes("🧠 Thinking") && text.split("\n").length < 3) {
          continue;
        }
        
        // If we found a response with substantial content that's not just welcome, return it
        if (text.length > 50 && !text.startsWith("Welcome to the knowledge platform")) {
          return elem;
        }
      }
      
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    
    // Timeout: return last response
    return responses.last();
  });
}
