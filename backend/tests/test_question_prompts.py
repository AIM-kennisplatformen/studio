from src.config import root_question_prompt, subnode_question_prompt


def test_question_prompts_require_citations_for_only_used_sources():
    prompts = [
        root_question_prompt("What does the evidence show?"),
        subnode_question_prompt("What does the evidence show?", "Target groups"),
    ]

    for prompt in prompts:
        assert (
            "assign them consecutive citation numbers in order of first citation"
            in prompt
        )
        assert "Include only cited documents, exactly once each" in prompt
        assert "exact Markdown heading `## References`" in prompt
        assert "one reference per line (`1. ...`, `2. ...`)" in prompt
        assert "Never place a reference on the same line as the heading" in prompt
        assert "copy the document's `ieee_reference` verbatim" in prompt
        assert "Never show `pdf_hash` values or relevance scores" in prompt


def test_root_question_prompt_does_not_exclude_unclassified_documents():
    prompt = root_question_prompt("What does the evidence show?")

    assert "omit `user_personas`" in prompt
    assert "omit `literature_kinds`" in prompt
    assert "literature_kinds=[" not in prompt


def test_subnode_question_prompt_maps_focus_to_user_persona():
    prompt = subnode_question_prompt("What does the evidence show?", "Target groups")

    assert "user_personas=['target_groups']" in prompt
    assert "omit `literature_kinds`" in prompt
    assert "literature_kinds=[" not in prompt


def test_question_text_adds_literature_kind_to_required_selected_persona():
    prompt = subnode_question_prompt(
        "What does scientific literature say about energy poverty?",
        "Strategic overview",
    )

    assert "user_personas=['strategic_overview']" in prompt
    assert "literature_kinds=['scientific_literature']" in prompt


def test_child_node_requires_parent_persona_and_literature_kind():
    prompt = subnode_question_prompt(
        "What does the evidence say?",
        "Strategic overview / Scientific literature",
        required_user_personas=["strategic_overview"],
        required_literature_kinds=["scientific_literature"],
    )

    assert "user_personas=['strategic_overview']" in prompt
    assert "literature_kinds=['scientific_literature']" in prompt
