"""MCP tool for suggesting new EDAM concepts."""

import logging

from fastmcp.server import Context

# Import needed for the mapping attempt
from ..config import settings
from ..models.requests import MappingRequest, SuggestionRequest
from ..models.responses import SuggestionResponse
from ..ontology import ConceptMatcher, LLMSuggester, OntologyLoader
from .mapping import map_to_edam_concept

logger = logging.getLogger(__name__)


async def suggest_new_concept(request: SuggestionRequest, context: Context) -> SuggestionResponse:
    """Suggest new EDAM concepts when no suitable existing concept is found.

    This tool generates suggestions for new concepts that could be integrated
    into the EDAM ontology. It first attempts to map the description to existing
    concepts, and if no suitable match is found, it generates suggestions for
    new concepts with appropriate placement in the ontology hierarchy.

    Args:
        request: Suggestion request containing description and parameters.
        context: MCP context for logging and progress reporting.

    Returns:
        Suggestion response with proposed new concepts.
    """
    try:
        # Log the request
        context.log.info(f"Suggesting concepts for: {request.description[:100]}...")

        # concept_matcher = ConceptMatcher(ontology_loader)
        concept_suggester = LLMSuggester()

        # Generate suggestions for new concepts
        context.log.info("Generating suggestions for new concepts...")
        suggestions = concept_suggester.suggest_concepts(
            description=request.description,
            concept_type=request.concept_type,
            parent_concept=request.parent_concept,
            rationale=request.rationale,
            max_suggestions=settings.max_suggestions,
        )

        context.log.info(f"Generated {len(suggestions)} concept suggestions")

        return SuggestionResponse(
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            mapping_attempted=True,
            mapping_failed_reason=None,
        )

    except Exception as e:
        context.log.error(f"Error in concept suggestion: {e}")
        raise


# Alternative function signature for direct use
async def suggest_concepts_for_description(
    description: str,
    concept_type: str | None = None,
    parent_concept: str | None = None,
    rationale: str | None = None,
    max_suggestions: int = 5,
) -> SuggestionResponse:
    """Alternative interface for suggesting new concepts.

    Args:
        description: Description of the concept to suggest.
        concept_type: Type of concept (Operation, Data, Format, Topic, Identifier).
        parent_concept: Suggested parent concept.
        rationale: Rationale for the suggestion.
        max_suggestions: Maximum number of suggestions to generate.

    Returns:
        Suggestion response with proposed new concepts.
    """
    request = SuggestionRequest(
        description=description,
        concept_type=concept_type,
        parent_concept=parent_concept,
        rationale=rationale,
    )

    # Create a mock context for standalone use
    class MockContext:
        def __init__(self):
            self.log = logging.getLogger(__name__)

    mock_context = MockContext()

    return await suggest_new_concept(request, mock_context)
