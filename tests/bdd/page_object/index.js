import { locator } from "@qavajs/steps-playwright/po.js";
export default class App {
  Body = locator("body");
  GetStartedButton = locator("a.button[href='/docs/intro']");

  // Authentik login page selectors
  // Authentik uses Shadow DOM (Lit web components), Playwright pierces it automatically
  AuthentikUsernameInput = locator("input[name='uidField']");
  AuthentikPasswordInput = locator("#ak-stage-password-input");
  AuthentikSubmitButton = locator(".pf-c-button.pf-m-primary.pf-m-block");
}
