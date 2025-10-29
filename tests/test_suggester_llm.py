import pytest
import logging
from edam_mcp.tools.suggestion_llm import suggest_new_concept, suggest_concepts_for_description
from edam_mcp.models.requests import SuggestionRequest

class TestSuggestionLLM:

    # test that the suggester returns a list of suggestions
    # that each suggestion has the expected attributes
    # that the first suggestion contains expected words from the description
    @pytest.mark.asyncio
    async def test_get_suggestions_returns_list(self):

        description = "single-cell spatial transcriptomics"

        response = await suggest_concepts_for_description(
            description=description,
            concept_type="Operation",  # or None for auto-detection
            max_suggestions=3,
        )
        
        assert isinstance(response.suggestions, list)
        assert len(response.suggestions) > 0
        for suggestion in response.suggestions:
            assert hasattr(suggestion, 'suggested_label')
            assert hasattr(suggestion, 'suggested_uri')
            assert hasattr(suggestion, 'concept_type')
            assert hasattr(suggestion, 'confidence')
        # print out the suggestions for visual inspection
        if response.suggestions:
                        print(f"  Generated {response.total_suggestions} suggestions:")
                        for suggestion in response.suggestions:
                            print(f"    - {suggestion.suggested_label}")
                            print(f"      URI: {suggestion.suggested_uri}")
                            print(f"      Type: {suggestion.concept_type}")
                            print(f"      Confidence: {suggestion.confidence:.2f}")
                            if suggestion.parent_concept:
                                print(f"      Parent: {suggestion.parent_concept}")
        # check that the first suggestion contains expected words, like "transcriptomics" and single and cell 
        first_suggestion = response.suggestions[0]
        assert "single" in first_suggestion.suggested_label.lower()
        assert "cell" in first_suggestion.suggested_label.lower()
        assert "spatial" in first_suggestion.suggested_label.lower()
        assert "transcriptomics" in first_suggestion.suggested_label.lower()
    

    # test that an empty description raises an exception
    @pytest.mark.asyncio
    async def test_empty_description_raises_exception(self):

        description = ""
        with pytest.raises(Exception):
            await suggest_concepts_for_description(
                description=description,
                concept_type="Operation",  # or None for auto-detection
                max_suggestions=3,
            )

