import { Then } from "@cucumber/cucumber";
import assert from "assert";


/**
 * Custom step that waits for an actual LLM response in the chat.
 * FAILS the test if no real response appears within the timeout.
 *
 * It distinguishes real LLM responses from:
 *  - The welcome message ("Welcome to the knowledge platform")
 *  - The thinking indicator ("🧠 Thinking...")
 *
 * Usage in feature:
 *   Then I should receive an LLM response within 90 seconds
 */
Then(
  "I should receive an LLM response within {int} seconds",
  async function (timeoutSeconds) {
    const { page } = this.playwright;
    const maxWait = timeoutSeconds * 1000;
    const pollInterval = 2000;
    const startTime = Date.now();

    // Patterns that indicate a non-real response
    const SKIP_PATTERNS = [
      "Welcome to the knowledge platform",
      "What would you like to explore today?",
      "🧠 Thinking",
    ];

    console.log(`\nWaiting up to ${timeoutSeconds}s for LLM response...`);

    let lastResponseCount = 0;

    while (Date.now() - startTime < maxWait) {
      // Look for bot response containers (bg-gray-50 is the Response component)
      const responses = await page.locator("div[class*='bg-gray-50']").all();
      lastResponseCount = responses.length;

      for (const elem of responses) {
        const text = (await elem.innerText()).trim();

        // Skip known non-response elements
        if (SKIP_PATTERNS.some((p) => text.startsWith(p) || text === p)) {
          continue;
        }

        // Skip very short text (likely empty or partial render)
        if (text.length < 5) {
          continue;
        }

          // We found a real LLM response!
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        console.log(`\nReceived LLM response after ${elapsed}s:`);
        console.log(text.substring(0, 300));
        return; // Test passes
      }

      // Check if the thinking indicator is still visible
      const thinkingVisible = await page
        .locator("text=🧠 Thinking")
        .isVisible()
        .catch(() => false);

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
      console.log(
        `  ... ${elapsed}s elapsed | ${responses.length} response containers | thinking: ${thinkingVisible}`
      );

      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }

    // Timeout — FAIL the test
    console.log(
      `\nTimed out after ${timeoutSeconds}s waiting for LLM response.`
    );
    console.log(`   Found ${lastResponseCount} response containers, but none contained a valid LLM reply.`);
    assert.fail(
      `No LLM response received within ${timeoutSeconds} seconds. ` +
        `The LLM worker may be down, the API key invalid, or the model unavailable.`
    );
  }
);
