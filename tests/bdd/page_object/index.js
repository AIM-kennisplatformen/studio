import { locator } from "@qavajs/steps-playwright/po.js";
export default class App {
  Body = locator("body");
  GetStartedButton = locator("a.button[href='/docs/intro']");
}
