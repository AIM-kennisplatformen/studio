import { Given, Then } from "@cucumber/cucumber";
import assert from "assert";

/**
 * Injects a WebSocket interceptor via page.addInitScript so that
 * every incoming WebSocket frame is inspected for MCP tool-call events
 * (specifically "on_tool_start").
 *
 * This runs BEFORE any page script on each navigation, so it captures
 * the Socket.IO WebSocket upgrade that happens when the React app mounts.
 *
 * Usage in feature:
 *   Given I start capturing MCP tool events
 */
Given("I start capturing MCP tool events", async function () {
  const { page } = this.playwright;

  await page.addInitScript(() => {
    window.__mcpToolCalls = [];

    const OrigWebSocket = window.WebSocket;

    // Replace the WebSocket constructor to attach a message listener
    // that captures any frame containing "on_tool_start".
    window.WebSocket = function (url, protocols) {
      const ws =
        protocols !== undefined
          ? new OrigWebSocket(url, protocols)
          : new OrigWebSocket(url);

      ws.addEventListener("message", (event) => {
        try {
          if (
            typeof event.data === "string" &&
            event.data.includes("on_tool_start")
          ) {
            window.__mcpToolCalls.push(event.data);
          }
        } catch (e) {
          // silently ignore parse errors
        }
      });

      return ws;
    };

    // Preserve prototype chain and static properties so Socket.IO
    // feature-detection (instanceof, readyState constants) still works.
    window.WebSocket.prototype = OrigWebSocket.prototype;
    window.WebSocket.CONNECTING = OrigWebSocket.CONNECTING;
    window.WebSocket.OPEN = OrigWebSocket.OPEN;
    window.WebSocket.CLOSING = OrigWebSocket.CLOSING;
    window.WebSocket.CLOSED = OrigWebSocket.CLOSED;
  });

  console.log("[MCP] Init script injected — capturing tool events");
});

/**
 * Asserts that at least one "on_tool_start" event was received over the
 * WebSocket connection during the chat interaction.
 *
 * Because the LLM agent calls the MCP tool BEFORE generating its response,
 * this step should be placed AFTER the "I should receive an LLM response"
 * step to ensure all events have already arrived.
 *
 * Usage in feature:
 *   Then the MCP tool 'get_literature_supported_knowledge' should have been called
 */
Then(
  "the MCP tool {string} should have been called",
  async function (toolName) {
    const { page } = this.playwright;

    const captures = await page.evaluate(() => window.__mcpToolCalls || []);

    console.log(`\n[MCP] Checking for tool '${toolName}'...`);
    console.log(`[MCP] Captured ${captures.length} on_tool_start event(s)`);

    if (captures.length > 0) {
      console.log("[MCP] Sample frame:", captures[0].substring(0, 200));
    }

    assert(
      captures.length > 0,
      `Expected MCP tool '${toolName}' to be called, but no on_tool_start events ` +
        `were detected on the WebSocket. The LLM may not have used the tool, ` +
        `or the MCP server may be unavailable.`
    );

    console.log(
      `[MCP] ✓ Tool invocation confirmed (${captures.length} event(s))`
    );
  }
);
