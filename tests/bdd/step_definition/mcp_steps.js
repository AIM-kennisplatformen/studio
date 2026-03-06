import { Given } from "@cucumber/cucumber";

/**
 * Records the current timestamp so we can later query Langfuse
 * for MCP tool observations that occurred after this point.
 * This is a convenience alias — sets the same langfuseStartTime
 * used by langfuse_steps.js.
 *
 * Usage in feature:
 *   Given I start capturing MCP tool events
 */
Given("I start capturing MCP tool events", async function () {
  this.langfuseStartTime = new Date().toISOString();
  console.log(`[MCP] Recording start time: ${this.langfuseStartTime}`);
});
