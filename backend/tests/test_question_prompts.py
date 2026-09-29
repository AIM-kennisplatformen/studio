from src.config import root_question_prompt, subnode_question_prompt


def test_question_prompts_require_citations_for_only_used_sources():
    prompts = [
        root_question_prompt("What does the evidence show?"),
        subnode_question_prompt("What does the evidence show?", "Target groups"),
    ]

    for prompt in prompts:
        assert "assign them consecutive citation numbers in order of first citation" in prompt
        assert "Include only cited documents, exactly once each" in prompt
        assert "exact Markdown heading `## References`" in prompt
        assert "one reference per line (`1. ...`, `2. ...`)" in prompt
        assert "Never place a reference on the same line as the heading" in prompt
        assert "copy the document's `ieee_reference` verbatim" in prompt
        assert "Never show `pdf_hash` values or relevance scores" in prompt


def test_root_question_prompt_uses_all_classification_filters():
    prompt = root_question_prompt("What does the evidence show?")

    assert (
        "user_personas=['best_practices', 'target_groups', 'strategic_overview']"
        in prompt
    )
    assert (
        "literature_kinds=['grey_literature', 'scientific_literature', "
        "'project_report']" in prompt
    )


def test_subnode_question_prompt_maps_focus_to_user_persona():
    prompt = subnode_question_prompt(
        "What does the evidence show?", "Target groups"
    )

    assert "user_personas=['target_groups']" in prompt
    assert (
        "literature_kinds=['grey_literature', 'scientific_literature', "
        "'project_report']" in prompt
    )
