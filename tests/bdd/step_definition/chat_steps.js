import { Then, Given } from "@cucumber/cucumber";


/**
 * Custom step to wait for services to be ready before starting the test
 * This ensures Ollama has time to initialize its model
 *
 * Usage in feature:
 *   Given I wait for backend services to be ready
 */
Given(
  "I wait for backend services to be ready",
  async function () {
    const { page } = this.playwright;
    const ollamaUrl = "http://localhost:11434";
    const maxRetries = 60;  // 60 seconds - should be enough if model is cached
    const retryInterval = 1000; // 1 second

    let ollamaReady = false;
    for (let i = 0; i < maxRetries; i++) {
      try {
        console.log(`⏳ Waiting for Ollama (attempt ${i + 1}/${maxRetries})...`);
        const response = await page.evaluate((url) => {
          return fetch(url + "/api/tags", { method: "GET", timeout: 5000 }).then(
            (r) => r.ok,
            () => false
          );
        }, ollamaUrl);

        if (response) {
          console.log("✅ Ollama is ready!");
          ollamaReady = true;
          break;
        }
      } catch (e) {
        // Retry
      }

      if (i < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, retryInterval));
      }
    }

    if (!ollamaReady) {
      console.warn(
        "⚠️  Ollama readiness check timed out after 60s, but continuing with test..."
      );
    }
  }
);

/**
 * Custom step to debug the chat responses by logging all visible response divs
 *
 * Usage in feature:
 *   Then I debug chat responses
 */
Then(
  "I debug chat responses",
  async function () {
    const { page } = this.playwright;
    
    // Find all response containers
    const allResponses = await page.locator("div[class*='bg-gray-50']").all();
    console.log(`\n🔍 Found ${allResponses.length} response containers`);
    
    for (let i = 0; i < allResponses.length; i++) {
      const text = await allResponses[i].innerText();
      const visible = await allResponses[i].isVisible();
      const isWelcome = text.includes("Welcome to the knowledge platform");
      console.log(`\n  Response ${i} (visible: ${visible}, welcome: ${isWelcome}):\n${text.substring(0, 500)}`);
    }
    
    // Also check for any divs with max-w-prose
    const maxWProseResponses = await page.locator("div.max-w-prose").all();
    console.log(`\n  Found ${maxWProseResponses.length} divs with max-w-prose`);
    
    // Check what ChatLLMResponse actually selected
    console.log("\n💬 Checking what ChatLLMResponse would select...");
    const welcomeText = "Welcome to the knowledge platform";
    for (let i = 0; i < allResponses.length; i++) {
      const text = await allResponses[i].innerText();
      if (!text.startsWith(welcomeText)) {
        console.log(`\n📌 ChatLLMResponse should select Response ${i}:`);
        console.log(text);
        break;
      }
    }
  }
);
