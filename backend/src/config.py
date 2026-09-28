import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

backend_root = Path(__file__).resolve().parents[1]
load_dotenv(backend_root / ".env")
load_dotenv(backend_root.parent / ".env")


CITATION_INSTRUCTIONS = (
    "Use only the returned passages as evidence.\n"
    "After deciding which documents you actually use, assign them consecutive citation numbers in order of first citation.\n"
    "Cite supported claims in the answer with bracketed numbers such as [1], and reuse the same number whenever you cite the same document.\n"
    "Separate the references from the answer body with a blank line and the exact Markdown heading `## References`.\n"
    "After the heading, add another blank line and format the references as an ordered Markdown list with one reference per line (`1. ...`, `2. ...`).\n"
    "Never place a reference on the same line as the heading, and never combine multiple references on one line.\n"
    "Include only cited documents, exactly once each and in first-citation order.\n"
    "For each list item, copy the document's `ieee_reference` verbatim after the list marker.\n"
    "Never show `pdf_hash` values or relevance scores.\n"
)


def root_question_prompt(question: str, history_text: str = "") -> str:
    history_section = (
        f"Conversation History:\n{history_text}\n\n" if history_text else ""
    )
    return (
        "SYSTEM META-INSTRUCTION:\n"
        "Use the `search_literature` MCP tool before answering.\n"
        "Search for evidence that addresses the full question, with particular attention to best practices, target groups, and strategic considerations.\n"
        "Only apply publication-date, document-type, or organization filters when the user explicitly requests them.\n"
        f"{CITATION_INSTRUCTIONS}"
        "If the search returns no relevant evidence, say so rather than inventing support.\n\n"
        f"{history_section}"
        f'Question:\n"{question}"\n'
    )


def subnode_question_prompt(question: str, subnode: str, history_text: str = "") -> str:
    history_section = (
        f"Conversation History:\n{history_text}\n\n" if history_text else ""
    )
    focus = (
        subnode
        if subnode != "root"
        else "Best practices || Target groups || Strategic overview"
    )
    return (
        "SYSTEM META-INSTRUCTION:\n"
        "Use the `search_literature` MCP tool before answering.\n"
        "Form its natural-language `query` from the full question and the selected focus below, without changing the user's intent.\n"
        "Only apply publication-date, document-type, or organization filters when the user explicitly requests them.\n"
        f"{CITATION_INSTRUCTIONS}"
        "If the search returns no relevant evidence, say so rather than inventing support.\n\n"
        f"{history_section}"
        f'Question:\n"{question}"\n\n'
        f'Selected focus:\n"{focus}"\n'
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
    return f"You've selected subset {subnode}. Please ask me your question?"


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
    "base_url": require_env("BACKEND_BASE_URL", "http://localhost:10090/api").rstrip(
        "/"
    ),
    "frontend_base_url": require_env(
        "FRONTEND_BASE_URL", "http://localhost:10090"
    ).rstrip("/"),
    "discovery_url": require_env(
        "OAUTH_DISCOVERY_URL",
        "http://auth.localhost:10091/application/o/kg/.well-known/openid-configuration",
    ),
    "logout_url": require_env(
        "OAUTH_LOGOUT_URL",
        "https://authscepa.mads-han.src.surf-hosted.nl/application/o/kg-dev/end-session/",
    ),
    "oauth_redirect_uri": require_env(
        "OAUTH_REDIRECT_URI", "http://localhost:10090/api/auth/callback"
    ),
    "client_id": require_env(
        "OAUTH_CLIENT_ID", "rkuclih8uzm44nTUvwasexioUKFk5aG1zhG8jcJX"
    ),
    "client_secret": require_env(
        "OAUTH_CLIENT_SECRET",
        "NEb0sAcMc2kTTdvfJMctLYE35Fp0GqyqFp4oOVrstxsevnVMJutiIhvb6TzwPrkbphAh1EiI74oRRO79xRCoZTh1suFYTV9J0tmRJBIFIF4znDYwNyDp3IzUQlESvaS0",
    ),
    "session_secret": require_env("SESSION_SECRET", secrets.token_urlsafe(32)),
    "mcp_tool_config_path": require_env("MCP_TOOL_CONFIG_PATH"),
    "llm_model": require_env("LLM_MODEL"),
    "openai_host": require_env("OPENAI_HOST"),
    "openai_api_key": require_env("OPENAI_API_KEY"),
    "redis_url": require_env("REDIS_URL", "redis://localhost:6379/0"),
    "redis_expiration_time": int(os.getenv("REDIS_EXPIRATION_TIME", "86400")),
    "chat_history_limit": int(os.getenv("CHAT_HISTORY_LIMIT", "10")),
    "postgres_url": require_env(
        "POSTGRES_URL",
        "postgresql://studio:studio@studio_postgres:5432/studio",
    ),
}


STATIC_TITLE_PROMPT = (
    "Create a concise title for this chat session.\n"
    "Rules: maximum 6 words, no quotation marks, no trailing punctuation, "
    "and no extra text.\n\n"
    "First user message:\n{question}\n\nAI response:\n{answer}"
)

DYNAMIC_TITLE_PROMPT = (
    "Create a concise title for this chat session based on the "
    "latest conversation.\nRules: maximum 6 words, no quotation marks, "
    "no trailing punctuation, and no extra text.\n\n"
    "Recent conversation:\n{conversation_text}"
)
