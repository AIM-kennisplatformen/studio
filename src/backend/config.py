import os
import secrets
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def root_question_prompt(question: str, history_text: str = "") -> str:
    history_section = f"Conversation History:\n{history_text}\n\n" if history_text else ""
    return (
        "SYSTEM META-INSTRUCTION:\n"
        "Use the `get_literature_supported_knowledge` MCP tool to identify sources relevant to the question.\n\n"
        f"{history_section}"
        f"full_question:\n\"{question}\"\n\n"
        "keywords_related_to_question=\"Best practices || Target groups || Strategic overview\"\n"
        "The tool can only be called with an English question, if there is a case where there is another language? Translate it before calling tool\n\n"
        "RESPONSE INSTRUCTIONS:\n"
        "- Answer in the same language as the question.\n"
        "- The answer must be evidence-informed and cite sources using IEEE numeric style [1], [2], etc.\n"
        "- At the end, add a references section using the markdown heading: ## References\n"
        "- Use `## References` (markdown h2 with ##), NOT bold text like **References**.\n"
        "- There must be a blank line before and after the ## References heading.\n"
        "- Each reference must be a markdown hyperlink: the full IEEE-formatted citation text is the link label, and the pdf_url from the tool result is the href.\n"
        "- Format: [1] [A. Author et al., \"Title,\" Journal, year.](pdf_url)\n"
        "- If the BibTeX entry contains a DOI, append it as: https://doi.org/<DOI>\n"
        "- Every reference MUST be clickable — never output a bare URL or plain text reference.\n"
        "- Example: [1] [B. Frantál and P. Dvořák, \"Reducing energy poverty...,\" Energy Policy, 2022.](http://localhost:10090/api/pdf/zotero/ABCD1234)\n"
    )


def subnode_question_prompt(question: str, subnode: str, history_text: str = "") -> str:
    history_section = f"Conversation History:\n{history_text}\n\n" if history_text else ""
    keyword = subnode if subnode != "root" else "Best practices || Target groups || Strategic overview"
    return (
        "SYSTEM META-INSTRUCTION:\n"
        "If relevant, use the `paper_search` MCP tool to identify scientific "
        "literature or studies relevant to the question.\n\n"
        "Don't alter question and keywords below — insert them straight into the tool.\n"
        f"{history_section}"
        f"full_question:\n\"{question}\"\n\n"
        f"keywords_related_to_question=\"{keyword}\"\n"
        "The tool can only be called with an English question, if there is a case where there is another language? Translate it before calling tool\n"
        "The answer you will give the user needs to be evidence-informed in the same language as the question.\n"
        "At the end, add a references section using the markdown heading: ## References\n"
        "- Use `## References` (markdown h2 with ##), NOT bold text like **References**.\n"
        "- There must be a blank line before and after the ## References heading.\n"
        "Each reference must be a markdown hyperlink: IEEE citation text as label, pdf_url as href.\n"
        "Format: [1] [A. Author, \"Title,\" Journal, year.](pdf_url)\n"
    )

def node_no_question_prompt() -> str:
    return (
        "Do you want to ask a question, answered by the full body of literature? "
        "Please proceed, by asking me your question?"
    )


def node_repeat_question_prompt(question: str) -> str:
    return (
        "Answer a question by using the full body of literature. "
        f"Would you like to ask a different question than: '{question}'? "
        "**Respond with another question** or type **yes** to repeat the previous question."
    )


def subnode_no_question_prompt(subnode: str) -> str:
    return (
        f"You've selected subset {subnode}. "
        "Please ask me your question?"
    )


def subnode_repeat_question_prompt(subnode: str, question: str) -> str:
    return (
        f"You've selected subset {subnode}. "
        "Please ask me your question using this subset. "
        f"If you want to repeat your previous question: `{question}` "
        "type **yes**, otherwise **Respond with another question**."
    )


def require_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    elif value == "":
        logger.warning(f"Environment variable {name} is empty")
    return value

config: dict = {
    "base_url": require_env("BACKEND_BASE_URL", "http://localhost:10090"),
    "discovery_url": require_env(
        "OAUTH_DISCOVERY_URL",
        "http://auth.localhost:9000/application/o/kg/.well-known/openid-configuration"
    ),
    "logout_url": require_env(
        "OAUTH_LOGOUT_URL",
        "https://authscepa.mads-han.src.surf-hosted.nl/application/o/kg-dev/end-session/"
    ),
    "client_id": require_env("OAUTH_CLIENT_ID", "rkuclih8uzm44nTUvwasexioUKFk5aG1zhG8jcJX"),
    "client_secret": require_env(
        "OAUTH_CLIENT_SECRET",
        "NEb0sAcMc2kTTdvfJMctLYE35Fp0GqyqFp4oOVrstxsevnVMJutiIhvb6TzwPrkbphAh1EiI74oRRO79xRCoZTh1suFYTV9J0tmRJBIFIF4znDYwNyDp3IzUQlESvaS0"
    ),
    "session_secret": require_env("SESSION_SECRET", secrets.token_urlsafe(32)),
    "mcp_tool_config_path": require_env("MCP_TOOL_CONFIG_PATH"),
    "llm_model": require_env("LLM_MODEL"),
    "openai_host": require_env("OPENAI_HOST"),
    "openai_api_key": require_env("OPENAI_API_KEY"),
    "redis_url": require_env("REDIS_URL", "redis://localhost:6379/0"),
    "redis_expiration_time": int(os.getenv("REDIS_EXPIRATION_TIME", "86400")),
    "chat_history_limit": int(os.getenv("CHAT_HISTORY_LIMIT", "10")),
    "vite_dev_server_url": require_env("VITE_DEV_SERVER_URL", "http://localhost:5173"),
}
