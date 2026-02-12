import Memory from "./memory/index.js";
import App from "./page_object/index.js";

export default {
    paths: ["tests/bdd/features/*.feature"],
    import: [
        "./node_modules/@qavajs/steps-memory/index.js",
        "./node_modules/@qavajs/steps-playwright/index.js",
        "./node_modules/@qavajs/steps-api/index.js",
        "./tests/bdd/step_definition/*.js" 
    ],
    format: [
        "@qavajs/console-formatter",
        ["@qavajs/html-formatter", "report/report.html"]
    ],
    memory: new Memory(),
    pageObject: new App(),
    browser: {
        capabilities: {
            browserName: "chromium"
        }
    }
}