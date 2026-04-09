import os
import secrets
from dotenv import load_dotenv

load_dotenv()

def root_question_prompt(question: str) -> str:
    return (
        "SYSTEM META-INSTRUCTION:\n"
        "Use the `get_literature_supported_knowledge` MCP tool to identify sources relevant to the question.\n\n"
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


BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:10090")
DISCOVERY_URL = os.getenv(
    "OAUTH_DISCOVERY_URL",
    "http://auth.localhost:9000/application/o/kg/.well-known/openid-configuration"
)
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "rkuclih8uzm44nTUvwasexioUKFk5aG1zhG8jcJX")
CLIENT_SECRET = os.getenv(
    "OAUTH_CLIENT_SECRET",
    "NEb0sAcMc2kTTdvfJMctLYE35Fp0GqyqFp4oOVrstxsevnVMJutiIhvb6TzwPrkbphAh1EiI74oRRO79xRCoZTh1suFYTV9J0tmRJBIFIF4znDYwNyDp3IzUQlESvaS0"
)
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))