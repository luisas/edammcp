import requests
from ..models.responses import SuggestedConcept
import json
class LLMSuggester:
    """Alternative suggester that uses prompts for large language models (LLMs) via Ollama."""

    def __init__(self, model: str = "tinyllama"):
        """Initialize the LLM suggester with the Ollama model.

        Args:
            model: The name of the Ollama model to use (e.g., "llama2", "gpt-4").
        """
        self.model = model
        self.ollama_url = "http://localhost:11434/api/chat"

    def suggest_concepts(
        self,
        description: str,
        concept_type: str | None = None,
        rationale: str | None = None,
        parent_concept: str | None = None,
        max_suggestions: int = 5,
    ) -> list[SuggestedConcept]:
        """Generate suggestions for new EDAM concepts using an LLM via Ollama.

        Args:
            description: Description of the concept to suggest.
            concept_type: Type of concept (Operation, Data, Format, Topic, Identifier).
            parent_concept: Suggested parent concept.
            max_suggestions: Maximum number of suggestions.

        Returns:
            List of suggested concepts.
        """
        # Construct the prompt for the LLM
        prompt = self._construct_prompt(description, concept_type, parent_concept, max_suggestions)

        # print the prompt for debugging
        # print in magenta
        print("\033[95mLLM Prompt:\033[0m")
        print("\033[95m" + prompt + "\033[0m")
 
        # Call the Ollama API
        response = self._query_ollama(prompt)

        # print response 
        print("\033[96mLLM Response:\033[0m")
        print("\033[96m" + response + "\033[0m")

        # Parse the response into SuggestedConcept objects
        suggestions = self._parse_response(response, description, concept_type, parent_concept)

        return suggestions

    def _construct_prompt(self, description: str, concept_type: str | None, parent_concept: str | None, max_suggestions: int) -> str:
        """Construct a prompt for the LLM to generate concept suggestions.

        Args:
            description: Description text.
            concept_type: Type of concept.
            parent_concept: Suggested parent concept.
            max_suggestions: Maximum number of suggestions.

        Returns:
            A string prompt for the LLM.
        """
        prompt = f"""
        You are an expert in bioinformatics ontologies. Based on the following description, suggest up to {max_suggestions} new concepts for the EDAM ontology. 
        Include the concept label, a short definition, and a confidence score (0.0 to 1.0). 

        Description: {description}
        Concept Type: {concept_type or "Unknown"}
        Parent Concept: {parent_concept or "None"}

        Respond in the following JSON format:
        [
            {{
                "label": "Concept Label",
                "definition": "Short definition of the concept.",
                "confidence": 0.85
            }},
            ...
        ]
        """
        return prompt

    def _query_ollama(self, prompt: str) -> str:
        """Send the prompt to the Ollama API and retrieve the response.

        Args:
            prompt: The prompt string to send to the LLM.

        Returns:
            The raw response from the Ollama API.
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }


        try:
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            complete_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        complete_response += chunk["message"]["content"]
                    if chunk.get("done", False):
                        break

            print("Received complete response from Ollama")
            print(f"Complete Response: {complete_response}")
            return complete_response
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to query Ollama: {e}")

    def _parse_response(self, response: str, description: str, concept_type: str | None, parent_concept: str | None) -> list[SuggestedConcept]:
        """Parse the LLM response into SuggestedConcept objects.

        Args:
            response: The raw response from the LLM.
            description: Original description.
            concept_type: Type of concept.
            parent_concept: Suggested parent concept.

        Returns:
            A list of SuggestedConcept objects.
        """
        import json

        suggestions = []
        try:
            concepts = json.loads(response)
            for concept in concepts:
                suggestions.append(SuggestedConcept(
                    suggested_label=concept["label"],
                    suggested_uri=self._generate_uri(concept["label"], concept_type),
                    concept_type=concept_type,
                    definition=concept["definition"],
                    parent_concept=parent_concept,
                    rationale=f"Generated by LLM from description: '{description}'",
                    confidence=concept["confidence"],
                ))
        except json.JSONDecodeError:
            raise ValueError("Failed to parse LLM response. Ensure the response is in the expected JSON format.")

        return suggestions

    def _generate_uri(self, label: str, concept_type: str | None) -> str:
        """Generate a URI for a concept.

        Args:
            label: Concept label.
            concept_type: Type of concept.

        Returns:
            Generated URI.
        """
        import re

        uri_part = re.sub(r"[^a-zA-Z0-9\s]", "", label)
        uri_part = re.sub(r"\s+", "_", uri_part).lower()
        type_prefix = concept_type.lower() if concept_type else "unknown"

        return f"http://edamontology.org/{type_prefix}_{uri_part}"