import Memory from "./memory/index.js";
import App from "./page_object/index.js";

export default {
    paths: ["tests/bdd/features/*.feature"],
    require: [
        "node_modules/@qavajs/steps-memory/index.js",
        "node_modules/@qavajs/steps-playwright/index.js",
        "node_modules/@qavajs/steps-api/index.js",
        "tests/bdd/step_definition/*.js" 
    ],  
    format: [
        "@qavajs/console-formatter",
        ["@qavajs/html-formatter", "report/report.html"]
    ],
    memory: new Memory(),
    pageObject: new App(),
    browser: {
        capabilities: {
            browserName: "chromium",
            // Map host.docker.internal to localhost so OAuth redirects work
            // (Authentik returns URLs with host.docker.internal when accessed from Docker)
            args: ["--host-resolver-rules=MAP host.docker.internal 127.0.0.1"]
        }
    }
}
