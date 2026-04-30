import Memory from "./memory/index.js";
import App from "./page_object/index.js";

const isCI = !!process.env.CI;

export default {
    paths: ["features/*.feature"],
    require: [
        "node_modules/@qavajs/steps-memory/index.js",
        "node_modules/@qavajs/steps-playwright/index.js",
        "node_modules/@qavajs/steps-api/index.js",
        "step_definition/*.js"
    ],
    format: [
        "@qavajs/console-formatter",
        ["@qavajs/html-formatter", "report/report.html"]
    ],
    // Increase Cucumber step timeout to 120s (default is 10s)
    // Needed for steps that wait for LLM responses
    defaultTimeout: 120000,
    memory: new Memory(),
    pageObject: new App(),
    browser: {
        capabilities: {
            browserName: "chromium",
            // In CI, use 'chrome' channel to avoid headless shell networking issues
            // The headless shell binary has broken network access in GitHub Actions
            ...(isCI && { channel: "chrome" }),
            // CI-specific args: --no-sandbox and --disable-dev-shm-usage are required for GitHub Actions
            // Local: --host-resolver-rules maps host.docker.internal so OAuth redirects work
            args: isCI
                ? ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                : ["--host-resolver-rules=MAP host.docker.internal 127.0.0.1"]
        },
        timeout: {
            // Playwright context default timeout for actions (type, click, fill)
            // Default is 10s — increased to 30s for slow Authentik page loads
            action: 30000,
            // Page-level timeout for element condition waits (e.g. to be visible)
            // Set to 30s to allow time for LLM chatbot responses
            page: 30000,
            // Timeout for value/text validation polling
            value: 30000,
            // Polling interval for value validations
            valueInterval: 500
        }
    }
}
