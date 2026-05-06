import { When } from "@cucumber/cucumber";

/**
 * Custom step to extract all cookies from the current Playwright browser context
 * and add them as a Cookie header to an API request object.
 *
 * Usage in feature:
 *   When I add browser cookies to '$meRequest'
 */
When(
  "I add browser cookies to {value}",
  async function (requestKey) {
    const request = await requestKey.value();

    // Get all cookies from the current Playwright browser context
    const cookies = await this.playwright.context.cookies();

    if (cookies.length === 0) {
      throw new Error(
        "No cookies found in browser context. Make sure you are logged in first."
      );
    }

    // Format cookies as a Cookie header string
    const cookieHeader = cookies
      .map((c) => `${c.name}=${c.value}`)
      .join("; ");

    // Add the Cookie header to the API request
    if (!request.headers) {
      request.headers = {};
    }
    request.headers["Cookie"] = cookieHeader;
  }
);
