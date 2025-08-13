import json
from datetime import datetime
from enum import Enum
from typing import Any, cast

import httpx
from jsonschema import Draft7Validator, ValidationError, validate
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from tms_mcp.config import settings

# ============================================================================
# State Management - Breaking down the large state into focused components
# ============================================================================


class NodeName(str, Enum):
    """Enum for node names to avoid string literals."""

    INITIALIZE = "initialize_state"
    GENERATE = "generate_json_example"
    VALIDATE = "validate_json"
    VERIFY_API = "verify_api_call"
    CHECK_RETRY = "check_retry_limit"
    SUCCESS = "return_success"
    ERROR = "return_error"


class GenerationState(TypedDict):
    """State for JSON generation."""

    schema: dict[str, Any]
    generated_json: str | None
    validation_errors: list[str]


class RetryState(TypedDict):
    """State for retry management."""

    attempt_count: int
    max_attempts: int


class ValidationState(TypedDict):
    """State for validation results."""

    is_valid: bool
    error_message: str | None


class APIVerificationState(TypedDict):
    """State for API verification."""

    endpoint: str | None
    skip_api_verification: bool
    api_verification_success: bool
    api_verification_error: str | None
    api_response_status: int | None
    api_response_data: dict[str, Any] | None
    api_duration_ms: float | None


class ResultState(TypedDict):
    """State for final results."""

    success: bool
    message: str | None
    attempts_used: int | None
    last_generated_json: str | None
    last_validation_errors: list[str] | None


class RequestBodyGeneratorState(
    GenerationState,
    RetryState,
    ValidationState,
    APIVerificationState,
    ResultState,
):
    """Complete state for the request body generator graph."""

    pass


# ============================================================================
# Response Models
# ============================================================================


class GeneratedJSON(BaseModel):
    """Schema for the generated JSON response."""

    json_content: str = Field(description="The generated JSON as a string")


# ============================================================================
# Service Classes - Separating concerns into focused classes
# ============================================================================


class LLMService:
    """Service for LLM interactions."""

    def __init__(self):
        self.model_config = {
            "model_id": settings.AWS_BEDROCK_MODEL_ID,
            "temperature": 1,
            "region_name": settings.AWS_DEFAULT_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "disable_streaming": False,
            "additional_model_request_fields": {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 3000,
                }
            },
        }

    def _build_system_prompt(self, validation_errors: list[str], api_error: str | None = None) -> str:
        """Build the system prompt for JSON generation."""
        base_prompt = """You are a JSON generator. Generate a realistic example JSON that STRICTLY conforms to the provided JSON schema.

CRITICAL REQUIREMENTS:
- The JSON must pass JSON schema validation
- Include ALL required fields specified in the schema
- Use correct data types for each field (string, integer, number, boolean, array, object)
- Follow any format constraints (e.g., email format, date format)
- Respect minimum/maximum values and array length constraints
- Use realistic, meaningful data values
- For location fields, use Korean locations (Seoul, Busan, Incheon, etc.)
- Do not include distance and duration matrices
- Try to include optional fields when they add value to the example
- ALWAYS set timelimit to 5

The generated JSON will be validated against the schema, so accuracy is essential."""

        if validation_errors:
            base_prompt += f"\n\nPREVIOUS VALIDATION ERRORS TO FIX:\n{chr(10).join(validation_errors)}"
            base_prompt += "\n\nPlease carefully address each validation error above and ensure the new JSON strictly follows the schema requirements."

        if api_error:
            base_prompt += f"\n\nAPI VERIFICATION ERROR:\n{api_error}"
            base_prompt += "\n\nThe generated JSON failed API verification. Please ensure the JSON contains valid, realistic data that the API can process successfully."

        return base_prompt

    async def generate_json(
        self, schema: dict[str, Any], validation_errors: list[str], api_error: str | None = None
    ) -> str:
        """Generate JSON using the LLM."""
        llm = ChatBedrockConverse(**self.model_config).with_structured_output(GeneratedJSON)

        system_prompt = self._build_system_prompt(validation_errors, api_error)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate a JSON example for this schema:\n{json.dumps(schema, indent=2)}"),
        ]

        response = await llm.ainvoke(messages)
        if hasattr(response, "json_content"):
            return response.json_content
        raise ValueError("Invalid LLM response")


class JSONValidator:
    """Service for JSON validation."""

    @staticmethod
    def validate_json_string(json_string: str) -> dict[str, Any]:
        """Parse and return JSON from string."""
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    @staticmethod
    def validate_against_schema(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        """Validate data against schema and return errors."""
        errors: list[str] = []
        try:
            validate(instance=data, schema=schema)
            return errors
        except ValidationError as e:
            # Format the main error
            error_msg = f"Schema validation failed: {e.message}"
            if e.path:
                error_msg += f" at path: {' -> '.join(str(p) for p in e.path)}"
            errors.append(error_msg)

            # Get additional errors for context
            validator = Draft7Validator(schema)
            all_errors = list(validator.iter_errors(data))

            # Add up to 3 additional errors
            for idx, error in enumerate(all_errors[1:4], 1):
                path_str = " -> ".join(str(p) for p in error.path) if error.path else "root"
                errors.append(f"Error {idx + 1}: {error.message} at path: {path_str}")

            if len(all_errors) > 4:
                errors.append(f"... and {len(all_errors) - 4} more validation errors")

            return errors


class APIClient:
    """Service for API verification."""

    def __init__(self):
        self.api_key = settings.ROUTING_API_KEY
        self.base_url = settings.ROUTING_API_BASE_URL.rstrip("/")
        if self.base_url.endswith("/api"):
            self.base_url = self.base_url[:-4]
        self.timeout = 60

    def _build_headers(self) -> dict[str, str]:
        """Build API request headers."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/vnd.omelet.v2+json",
            "X-API-KEY": self.api_key,
        }

    async def verify_json(self, endpoint: str, data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Verify JSON by calling the API endpoint.

        Returns:
            Tuple of (success, result_dict)
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._build_headers()

        start_time = datetime.now()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url=url, json=data, headers=headers)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {"response_text": response.text}

                return True, {
                    "api_verification_success": True,
                    "api_verification_error": None,
                    "api_response_status": response.status_code,
                    "api_response_data": response_data,
                    "api_duration_ms": round(duration_ms, 2),
                }
            else:
                try:
                    error_data = response.json()
                    error_message = f"API call failed ({response.status_code}): {error_data}"
                except json.JSONDecodeError:
                    error_message = f"API call failed ({response.status_code}): {response.text}"

                return False, {
                    "api_verification_success": False,
                    "api_verification_error": error_message,
                    "api_response_status": response.status_code,
                    "api_response_data": None,
                    "api_duration_ms": round(duration_ms, 2),
                }

        except Exception as e:
            return False, {
                "api_verification_success": False,
                "api_verification_error": f"API verification exception: {str(e)}",
                "api_response_status": None,
                "api_response_data": None,
                "api_duration_ms": None,
            }


# ============================================================================
# Node Functions - Simplified and focused
# ============================================================================

# Initialize services as module-level singletons
llm_service = LLMService()
json_validator = JSONValidator()
api_client = APIClient()


def initialize_state(state: RequestBodyGeneratorState) -> RequestBodyGeneratorState:
    """Initialize the state with default values."""
    defaults: RequestBodyGeneratorState = {
        # Generation state
        "schema": state["schema"],
        "generated_json": None,
        "validation_errors": [],
        # Retry state
        "attempt_count": 0,
        "max_attempts": 3,
        # Validation state
        "is_valid": False,
        "error_message": None,
        # API verification state
        "endpoint": state.get("endpoint"),
        "skip_api_verification": state.get("skip_api_verification", True),
        "api_verification_success": False,
        "api_verification_error": None,
        "api_response_status": None,
        "api_response_data": None,
        "api_duration_ms": None,
        # Result state
        "success": False,
        "message": None,
        "attempts_used": None,
        "last_generated_json": None,
        "last_validation_errors": None,
    }
    return defaults


async def generate_json_example(state: RequestBodyGeneratorState) -> Command:
    """Generate a JSON example based on the provided schema using LLM."""
    try:
        generated_json = await llm_service.generate_json(
            schema=state["schema"],
            validation_errors=state["validation_errors"],
            api_error=state.get("api_verification_error"),
        )

        return Command(
            update={
                "generated_json": generated_json,
                "attempt_count": state["attempt_count"] + 1,
            },
            goto=NodeName.VALIDATE.value,
        )
    except Exception as e:
        return Command(
            update={
                "error_message": f"LLM generation failed: {str(e)}",
                "attempt_count": state["attempt_count"] + 1,
            },
            goto=NodeName.CHECK_RETRY.value,
        )


def validate_json(state: RequestBodyGeneratorState) -> Command:
    """Validate the generated JSON against the schema."""
    if not isinstance(state["generated_json"], str):
        return Command(
            update={
                "is_valid": False,
                "validation_errors": ["Generated JSON is not a string"],
            },
            goto=NodeName.CHECK_RETRY.value,
        )

    try:
        # Parse JSON
        parsed_json = json_validator.validate_json_string(state["generated_json"])

        # Validate against schema
        validation_errors = json_validator.validate_against_schema(parsed_json, state["schema"])

        if validation_errors:
            return Command(
                update={
                    "is_valid": False,
                    "validation_errors": validation_errors,
                },
                goto=NodeName.CHECK_RETRY.value,
            )

        # Determine next step based on API verification settings
        should_verify_api = not state.get("skip_api_verification", True) and state.get("endpoint") is not None

        next_node = NodeName.VERIFY_API.value if should_verify_api else NodeName.SUCCESS.value

        return Command(
            update={
                "is_valid": True,
                "validation_errors": [],
            },
            goto=next_node,
        )

    except ValueError as e:
        return Command(
            update={
                "is_valid": False,
                "validation_errors": [str(e)],
            },
            goto=NodeName.CHECK_RETRY.value,
        )


async def verify_api_call(state: RequestBodyGeneratorState) -> Command:
    """Verify the generated JSON by calling the actual API endpoint."""
    if not state["generated_json"]:
        return Command(
            update={
                "api_verification_success": False,
                "api_verification_error": "No generated JSON to verify",
            },
            goto=NodeName.CHECK_RETRY.value,
        )

    endpoint = state.get("endpoint")
    if not endpoint:
        return Command(
            update={
                "api_verification_success": False,
                "api_verification_error": "No endpoint specified for API verification",
            },
            goto=NodeName.CHECK_RETRY.value,
        )

    try:
        request_data = json.loads(state["generated_json"])
        success, result = await api_client.verify_json(endpoint, request_data)

        if success:
            return Command(
                update=result,
                goto=NodeName.SUCCESS.value,
            )
        else:
            # Add validation error for retry
            result["validation_errors"] = [f"API verification failed: {result['api_verification_error']}"]
            return Command(
                update=result,
                goto=NodeName.CHECK_RETRY.value,
            )

    except Exception as e:
        return Command(
            update={
                "api_verification_success": False,
                "api_verification_error": f"API verification exception: {str(e)}",
                "api_response_status": None,
                "api_response_data": None,
                "api_duration_ms": None,
                "validation_errors": [f"API verification exception: {str(e)}"],
            },
            goto=NodeName.CHECK_RETRY.value,
        )


def check_retry_limit(state: RequestBodyGeneratorState) -> Command:
    """Check if we've exceeded the retry limit."""
    if state["attempt_count"] >= state["max_attempts"]:
        return Command(
            update={"error_message": f"Failed to generate valid JSON after {state['max_attempts']} attempts"},
            goto=NodeName.ERROR.value,
        )
    return Command(goto=NodeName.GENERATE.value)


def return_success(state: RequestBodyGeneratorState) -> RequestBodyGeneratorState:
    """Return success message with generated JSON."""
    # Build appropriate success message
    if state.get("api_verification_success"):
        message = (
            f"Successfully generated and verified JSON example "
            f"(API call: {state['api_response_status']}, {state['api_duration_ms']:.0f}ms)"
        )
    elif not state.get("skip_api_verification", True):
        message = "Successfully generated valid JSON example (API verification was attempted)"
    else:
        message = "Successfully generated valid JSON example"

    return {
        **state,
        "success": True,
        "attempts_used": state["attempt_count"],
        "message": message,
    }


def return_error(state: RequestBodyGeneratorState) -> RequestBodyGeneratorState:
    """Return error message after max attempts."""
    return {
        **state,
        "success": False,
        "attempts_used": state["attempt_count"],
        "last_generated_json": state.get("generated_json"),
        "last_validation_errors": state.get("validation_errors", []),
        "message": state["error_message"],
    }


# ============================================================================
# Graph Construction
# ============================================================================


def create_request_body_generator_graph() -> StateGraph[RequestBodyGeneratorState]:
    """Create and return the request body generator graph."""
    graph = StateGraph(RequestBodyGeneratorState)

    # Add nodes using enum values
    graph.add_node(NodeName.INITIALIZE.value, initialize_state)
    graph.add_node(NodeName.GENERATE.value, generate_json_example)
    graph.add_node(NodeName.VALIDATE.value, validate_json)
    graph.add_node(NodeName.VERIFY_API.value, verify_api_call)
    graph.add_node(NodeName.CHECK_RETRY.value, check_retry_limit)
    graph.add_node(NodeName.SUCCESS.value, return_success)
    graph.add_node(NodeName.ERROR.value, return_error)

    # Add edges
    graph.add_edge(START, NodeName.INITIALIZE.value)
    graph.add_edge(NodeName.INITIALIZE.value, NodeName.GENERATE.value)
    graph.add_edge(NodeName.SUCCESS.value, END)
    graph.add_edge(NodeName.ERROR.value, END)

    return graph


# Compile the graph
request_body_generator = create_request_body_generator_graph().compile()


# ============================================================================
# Public API
# ============================================================================


async def generate_example_json(
    schema: dict[str, Any], endpoint: str | None = None, skip_api_verification: bool = True
) -> RequestBodyGeneratorState:
    """
    Generate an example JSON based on the provided schema.

    Args:
        schema: The JSON schema to generate an example for
        endpoint: API endpoint to verify the generated JSON against (e.g., "/api/vrp")
        skip_api_verification: Whether to skip API verification (default: True)

    Returns:
        RequestBodyGeneratorState containing success status, generated JSON, and metadata
    """
    initial_state: RequestBodyGeneratorState = {
        # Generation state
        "schema": schema,
        "generated_json": None,
        "validation_errors": [],
        # Retry state
        "attempt_count": 0,
        "max_attempts": 3,
        # Validation state
        "is_valid": False,
        "error_message": None,
        # API verification state
        "endpoint": endpoint,
        "skip_api_verification": skip_api_verification,
        "api_verification_success": False,
        "api_verification_error": None,
        "api_response_status": None,
        "api_response_data": None,
        "api_duration_ms": None,
        # Result state
        "success": False,
        "message": None,
        "attempts_used": None,
        "last_generated_json": None,
        "last_validation_errors": None,
    }

    result = await request_body_generator.ainvoke(cast(Any, initial_state))
    return cast(RequestBodyGeneratorState, result)


# ============================================================================
# Example Usage
# ============================================================================


if __name__ == "__main__":
    import asyncio
    from pathlib import Path

    async def main():
        # Load the cost-matrix schema from the docs
        schema_path = Path(__file__).parent.parent / "docs" / "schemas" / "request_body" / "cost-matrix.json"
        with open(schema_path, "r") as f:
            schema_data = json.load(f)

        example_schema = schema_data["schema"]

        # Generate with API verification
        print("=== Generating with API verification ===")
        result = await generate_example_json(example_schema, endpoint="/api/cost-matrix", skip_api_verification=False)

        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")

        if result.get("api_verification_success"):
            print(f"API Status: {result['api_response_status']}")
            print(f"API Duration: {result['api_duration_ms']}ms")
        elif result.get("api_verification_error"):
            print(f"API Error: {result['api_verification_error']}")

        print("\n=== Full Result Details ===")
        print(json.dumps(result, indent=2, default=str))

    asyncio.run(main())
