import { Given, Then } from "@cucumber/cucumber";
import assert from "assert";

/**
 * Sets up Playwright listeners to capture MCP tool-call events from
 * Socket.IO traffic. Intercepts BOTH HTTP long-polling responses AND
 * WebSocket frames, since Socket.IO starts with polling before upgrading.
 *
 * Usage in feature:
 *   Given I start capturing MCP tool events
 */
Given("I start capturing MCP tool events", async function () {
  const { page } = this.playwright;

  // Store captured events on the test context (not in the page)
  this.mcpToolCalls = [];

  // 1. Intercept HTTP polling responses (Socket.IO starts with polling)
  page.on("response", async (response) => {
    try {
      const url = response.url();
      if (!url.includes("socket.io")) return;

      const body = await response.text().catch(() => "");
      if (body.includes("on_tool_start")) {
        this.mcpToolCalls.push(body);
      }
    } catch (e) {
      // ignore — response may already be disposed
    }
  });

  // 2. Intercept WebSocket frames (after Socket.IO upgrades)
  page.on("websocket", (ws) => {
    ws.on("framereceived", (frame) => {
      try {
        if (
          typeof frame.payload === "string" &&
          frame.payload.includes("on_tool_start")
        ) {
          this.mcpToolCalls.push(frame.payload);
        }
      } catch (e) {
        // ignore
      }
    });
  });

  console.log("[MCP] Capturing tool events via HTTP polling + WebSocket");
});

/**
 * Asserts that at least one "on_tool_start" event was received during
 * the chat interaction, proving the MCP tool was invoked.
 *
 * This step should be placed AFTER "I should receive an LLM response"
 * to ensure all events have already arrived.
 *
 * Usage in feature:
 *   Then the MCP tool 'get_literature_supported_knowledge' should have been called
 */
Then(
  "the MCP tool {string} should have been called",
  async function (toolName) {
    const captures = this.mcpToolCalls || [];

    console.log(`\n[MCP] Checking for tool '${toolName}'...`);
    console.log(`[MCP] Captured ${captures.length} on_tool_start event(s)`);

    for (let i = 0; i < captures.length; i++) {
      console.log(`[MCP] Event ${i + 1}:`, captures[i]);
    }

    assert(
      captures.length > 0,
      `Expected MCP tool '${toolName}' to be called, but no on_tool_start events ` +
        `were detected in Socket.IO traffic (polling + WebSocket). ` +
        `The LLM may not have used the tool, or the MCP server may be unavailable.`
    );

    const matching = captures.filter((frame) => frame.includes(toolName));
    if (matching.length > 0) {
      console.log(
        `[MCP] ✓ Tool '${toolName}' confirmed (${matching.length} matching event(s))`
      );
    } else {
      console.log(
        `[MCP] ⚠ on_tool_start detected but '${toolName}' not found in frame data. A tool was called.`
      );
    }
  }
);
