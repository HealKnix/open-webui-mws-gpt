"""
Tool Digest Builder Module

Extracts and summarizes tool calls from chat messages for context compression.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class ToolCallDigest:
    """Digest of a single tool call."""
    tool_name: str
    arguments_summary: str
    result_summary: str
    status: str  # success | error | pending
    artifacts: List[str]
    timestamp: Optional[int] = None


class ToolDigestBuilder:
    """Builds digests of tool calls from chat messages."""

    # Maximum length for summaries
    MAX_ARGS_LENGTH = 500
    MAX_RESULT_LENGTH = 1000
    MAX_ARTIFACTS = 5

    def __init__(self):
        self.tool_calls: List[ToolCallDigest] = []

    def extract_tool_calls(self, messages: List[Dict[str, Any]]) -> List[ToolCallDigest]:
        """
        Extract tool calls from a list of messages.

        Args:
            messages: List of message dicts with role, content, etc.

        Returns:
            List of ToolCallDigest objects
        """
        digests = []

        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            output = msg.get('output', [])

            # Extract tool calls from assistant messages with tool calls
            if role == 'assistant' and output:
                for item in output:
                    if isinstance(item, dict) and item.get('type') == 'tool_call':
                        digest = self._parse_tool_call(item, msg)
                        if digest:
                            digests.append(digest)

            # Also check for tool results in messages
            if role == 'tool':
                digest = self._parse_tool_result(msg)
                if digest:
                    digests.append(digest)

        return digests

    def _parse_tool_call(
        self,
        tool_call: Dict[str, Any],
        message: Dict[str, Any]
    ) -> Optional[ToolCallDigest]:
        """Parse a tool call from assistant output."""
        try:
            call_data = tool_call.get('data', {})
            tool_name = call_data.get('name', 'unknown_tool')
            arguments = call_data.get('arguments', {})

            # Summarize arguments
            args_summary = self._summarize_arguments(arguments)

            # Try to find result in subsequent messages or in the same message
            result_summary = "Pending execution"
            status = "pending"
            artifacts = []

            # Check if result is in the tool call itself
            if 'result' in call_data:
                result = call_data['result']
                result_summary, status, artifacts = self._summarize_result(result)

            return ToolCallDigest(
                tool_name=tool_name,
                arguments_summary=args_summary,
                result_summary=result_summary,
                status=status,
                artifacts=artifacts,
                timestamp=message.get('timestamp'),
            )

        except Exception as e:
            log.warning(f"Failed to parse tool call: {e}")
            return None

    def _parse_tool_result(self, message: Dict[str, Any]) -> Optional[ToolCallDigest]:
        """Parse a tool result message."""
        try:
            content = message.get('content', '')
            if not content:
                return None

            # Try to parse as JSON
            if isinstance(content, str):
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {'result': content}
            else:
                data = content

            tool_name = data.get('tool_name', 'unknown_tool')
            result = data.get('result', data)

            result_summary, status, artifacts = self._summarize_result(result)

            return ToolCallDigest(
                tool_name=tool_name,
                arguments_summary="See previous call",
                result_summary=result_summary,
                status=status,
                artifacts=artifacts,
                timestamp=message.get('timestamp'),
            )

        except Exception as e:
            log.warning(f"Failed to parse tool result: {e}")
            return None

    def _summarize_arguments(self, arguments: Dict[str, Any]) -> str:
        """Create a concise summary of tool arguments."""
        if not arguments:
            return "No arguments"

        # Handle different argument formats
        if isinstance(arguments, str):
            return self._truncate(arguments, self.MAX_ARGS_LENGTH)

        # Build summary from key arguments
        parts = []
        for key, value in arguments.items():
            # Skip internal/verbose fields
            if key.startswith('_') or key in ('verbose', 'debug'):
                continue

            value_str = self._value_to_string(value)
            if value_str:
                parts.append(f"{key}={value_str}")

        summary = ", ".join(parts)
        return self._truncate(summary, self.MAX_ARGS_LENGTH)

    def _summarize_result(self, result: Any) -> tuple[str, str, List[str]]:
        """
        Summarize tool result.

        Returns:
            Tuple of (summary, status, artifacts)
        """
        status = "success"
        artifacts = []

        # Handle error results
        if isinstance(result, dict):
            if 'error' in result or 'Error' in str(result):
                status = "error"
                error_msg = result.get('error', result.get('message', str(result)))
                return self._truncate(str(error_msg), self.MAX_RESULT_LENGTH), status, artifacts

            # Extract artifacts if present
            if 'artifacts' in result:
                artifacts = self._extract_artifacts(result['artifacts'])

            # Check for success/failure indicators
            if result.get('success') is False:
                status = "error"

        # Convert result to string summary
        if isinstance(result, dict):
            # Try to extract key information
            summary_parts = []

            # Common result fields
            for key in ('result', 'output', 'data', 'content', 'message', 'summary'):
                if key in result:
                    value = result[key]
                    if isinstance(value, (list, dict)):
                        summary_parts.append(f"{key}: {self._summarize_collection(value)}")
                    else:
                        summary_parts.append(f"{key}: {self._truncate(str(value), 200)}")
                    break

            if not summary_parts:
                # Use all top-level keys
                for key, value in list(result.items())[:5]:  # Limit to 5 keys
                    if key not in ('artifacts', 'metadata'):
                        value_str = self._value_to_string(value)
                        if value_str:
                            summary_parts.append(f"{key}={value_str}")

            summary = "; ".join(summary_parts) if summary_parts else self._truncate(str(result), self.MAX_RESULT_LENGTH)
        else:
            summary = self._truncate(str(result), self.MAX_RESULT_LENGTH)

        return summary, status, artifacts

    def _extract_artifacts(self, artifacts_data: Any) -> List[str]:
        """Extract artifact references from result."""
        artifacts = []

        if isinstance(artifacts_data, list):
            for item in artifacts_data[:self.MAX_ARTIFACTS]:
                if isinstance(item, dict):
                    # Extract name or id
                    name = item.get('name', item.get('id', item.get('filename', str(item))))
                    artifacts.append(name)
                elif isinstance(item, str):
                    artifacts.append(item)
        elif isinstance(artifacts_data, dict):
            # Single artifact
            name = artifacts_data.get('name', artifacts_data.get('id', str(artifacts_data)))
            artifacts.append(name)

        return artifacts

    def _summarize_collection(self, collection: Any) -> str:
        """Summarize a list or dict."""
        if isinstance(collection, list):
            if len(collection) == 0:
                return "empty list"
            elif len(collection) == 1:
                return f"1 item: {self._truncate(str(collection[0]), 100)}"
            else:
                return f"{len(collection)} items"
        elif isinstance(collection, dict):
            return f"{len(collection)} fields"
        else:
            return self._truncate(str(collection), 100)

    def _value_to_string(self, value: Any) -> str:
        """Convert a value to a concise string representation."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return self._truncate(value, 100)
        if isinstance(value, list):
            if len(value) == 0:
                return "[]"
            elif len(value) == 1:
                return f"[{self._value_to_string(value[0])}]"
            else:
                return f"[{len(value)} items]"
        if isinstance(value, dict):
            return f"{{{len(value)} fields}}"
        return self._truncate(str(value), 100)

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def build_digest_summary(self, digests: List[ToolCallDigest]) -> List[Dict[str, Any]]:
        """
        Build a JSON-serializable summary of tool digests.

        Args:
            digests: List of ToolCallDigest objects

        Returns:
            List of dicts suitable for storage in database
        """
        result = []
        for digest in digests:
            result.append({
                'tool_name': digest.tool_name,
                'arguments_summary': digest.arguments_summary,
                'result_summary': digest.result_summary,
                'status': digest.status,
                'artifacts': digest.artifacts,
                'timestamp': digest.timestamp,
            })
        return result

    def merge_digests(
        self,
        existing_digests: List[Dict[str, Any]],
        new_digests: List[ToolCallDigest]
    ) -> List[Dict[str, Any]]:
        """
        Merge new digests with existing ones, avoiding duplicates.

        Args:
            existing_digests: Existing digests from database
            new_digests: Newly extracted digests

        Returns:
            Merged list of digests
        """
        merged = list(existing_digests)
        existing_timestamps = {d.get('timestamp') for d in existing_digests if d.get('timestamp')}

        for digest in new_digests:
            # Skip if we already have this timestamp
            if digest.timestamp and digest.timestamp in existing_timestamps:
                continue

            merged.append({
                'tool_name': digest.tool_name,
                'arguments_summary': digest.arguments_summary,
                'result_summary': digest.result_summary,
                'status': digest.status,
                'artifacts': digest.artifacts,
                'timestamp': digest.timestamp,
            })

        return merged


def extract_tool_digest_from_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to extract tool digest from messages.

    Args:
        messages: List of chat messages

    Returns:
        List of tool digest dicts
    """
    builder = ToolDigestBuilder()
    digests = builder.extract_tool_calls(messages)
    return builder.build_digest_summary(digests)
