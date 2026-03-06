import { Then } from "@cucumber/cucumber";
import assert from "assert";
import Memory from "../memory/index.js";

const LANGFUSE_HOST = process.env.LANGFUSE_HOST;
const LANGFUSE_PUBLIC_KEY = process.env.LANGFUSE_PUBLIC_KEY;
const LANGFUSE_SECRET_KEY = process.env.LANGFUSE_SECRET_KEY;

function getLangfuseAuth() {
  assert(LANGFUSE_HOST, "LANGFUSE_HOST is not set in environment");
  assert(LANGFUSE_PUBLIC_KEY, "LANGFUSE_PUBLIC_KEY is not set in environment");
  assert(LANGFUSE_SECRET_KEY, "LANGFUSE_SECRET_KEY is not set in environment");
  return Buffer.from(`${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}`).toString("base64");
}

async function queryLangfuseObservations({ name, type, fromStartTime, auth }) {
  const url = new URL("/api/public/observations", LANGFUSE_HOST);
  url.searchParams.set("name", name);
  url.searchParams.set("fromStartTime", fromStartTime);
  url.searchParams.set("type", type);

  const maxAttempts = 5;
  const pollInterval = 5000;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const response = await fetch(url.toString(), {
      headers: { Authorization: `Basic ${auth}` },
    });

    const responseText = await response.text();
    assert(response.ok, `Langfuse API returned ${response.status}: ${responseText}`);

    const body = JSON.parse(responseText);
    const observations = body.data || [];

    console.log(`[Langfuse] Attempt ${attempt}/${maxAttempts}: found ${observations.length} ${type} observation(s) for '${name}'`);

    if (observations.length > 0) {
      return observations;
    }

    if (attempt < maxAttempts) {
      console.log(`[Langfuse] Waiting ${pollInterval / 1000}s before retrying...`);
      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }
  }

  return [];
}

/**
 * Verifies that the LLM response was logged in Langfuse as a GENERATION.
 *
 * Usage in feature:
 *   Then the LLM response should be logged in Langfuse
 */
Then("the LLM response should be logged in Langfuse", async function () {
  const auth = getLangfuseAuth();
  const startTime = this.langfuseStartTime;
  assert(startTime, "Langfuse start time not set — did you forget 'Given I record the Langfuse start time'?");

  const memory = new Memory();
  const generationName = memory.langfuseGenerationName;
  console.log(`\n[Langfuse] Querying for LLM generation '${generationName}' since ${startTime}...`);

  const observations = await queryLangfuseObservations({
    name: generationName,
    type: "GENERATION",
    fromStartTime: startTime,
    auth,
  });

  assert(
    observations.length > 0,
    `Expected an LLM generation to be logged in Langfuse, but none were found. ` +
      `The LLM worker may not be reporting to Langfuse.`
  );

  console.log(`[Langfuse] ✓ LLM generation confirmed (${observations.length} observation(s))`);
});

/**
 * Verifies that a specific MCP tool was called by checking Langfuse for
 * a TOOL observation with the given name.
 *
 * Usage in feature:
 *   Then the MCP tool 'get_literature_supported_knowledge' should have been called
 */
Then(
  "the MCP tool {string} should have been called",
  async function (toolName) {
    const auth = getLangfuseAuth();
    const startTime = this.langfuseStartTime;
    assert(startTime, "Langfuse start time not set — did you forget 'Given I record the Langfuse start time'?");

    console.log(`\n[Langfuse] Querying for tool '${toolName}' since ${startTime}...`);

    const observations = await queryLangfuseObservations({
      name: toolName,
      type: "TOOL",
      fromStartTime: startTime,
      auth,
    });

    assert(
      observations.length > 0,
      `Expected MCP tool '${toolName}' to be called, but no matching observations ` +
        `were found in Langfuse. The LLM may not have used the tool, or the MCP server may be unavailable.`
    );

    console.log(`[Langfuse] ✓ Tool '${toolName}' confirmed (${observations.length} observation(s))`);
  }
);
