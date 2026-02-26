import { locator } from "@qavajs/steps-playwright/po.js";
export default class App {
  Body = locator("body");
  GetStartedButton = locator("a.button[href='/docs/intro']");

  // Authentik login page selectors
  AuthentikUsernameInput = locator("input[name='uidField']");
  AuthentikPasswordInput = locator("#ak-stage-password-input");
  AuthentikSubmitButton = locator(".pf-c-button.pf-m-primary.pf-m-block");

  // Chat UI selectors
  ChatMessageInput = locator("textarea[name='message']");
  ChatSendButton = locator("button[type='submit']");
  // The first bot response container (welcome message)
  ChatResponse = locator.native(({ page }) =>
    page.locator("div[class*='bg-gray-50']").first()
  );
}
