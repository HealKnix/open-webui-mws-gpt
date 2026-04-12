"""External agent backends for Open WebUI.

This package provides an alternative chat-completion path where an actual
agent framework (LangGraph) drives the conversation, reusing Open WebUI's
existing tool registry, RAG pipeline and event transport. Agent events are
streamed to the frontend using the AG UI protocol.

The entry point is :func:`run_agent_backend` — dispatched from
``process_chat_response`` in ``open_webui.utils.middleware`` when a model
has ``params.agent_backend`` set.
"""

from open_webui.utils.agents.dispatcher import run_agent_backend, is_agent_backend_enabled

__all__ = ['run_agent_backend', 'is_agent_backend_enabled']
