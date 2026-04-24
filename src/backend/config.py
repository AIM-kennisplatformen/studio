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
        "Provide an evidence-informed explanation when possible.\n"
    )


def subnode_question_prompt(question: str, subnode: str) -> str:
    keyword = subnode if subnode != "root" else "Best practices || Target groups || Strategic overview"
    return (
        "SYSTEM META-INSTRUCTION:\n"
        "If relevant, use the `paper_search` MCP tool to identify scientific "
        "literature or studies relevant to the question.\n\n"
        "Don't alter question and keywords below — insert them straight into the tool.\n"
        f"full_question:\n\"{question}\"\n\n"
        f"keywords_related_to_question=\"{keyword}\" "
        "Provide an evidence-informed explanation when possible.\n"
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
    "chat_history_limit": int(os.getenv("CHAT_HISTORY_LIMIT", "10")),
    "chat_history_ttl": int(os.getenv("CHAT_HISTORY_TTL", "86400")),
}