import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel

from open_webui.utils.agents.langgraph_adapter import (
    TOOL_APPROVAL_REJECTED_MESSAGE,
    TOOL_APPROVAL_TIMED_OUT_MESSAGE,
    _route_after_llm,
    _tools_node,
)


class EchoArgs(BaseModel):
    value: int


def test_route_after_llm_without_tool_calls_returns_end():
    state = {'messages': [AIMessage(content='done')]}

    assert _route_after_llm(state) == END


def test_route_after_llm_with_tool_calls_routes_to_tools():
    state = {
        'messages': [
            AIMessage(
                content='',
                tool_calls=[{'name': 'echo', 'args': {'value': 1}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    assert _route_after_llm(state) == 'tools'


@pytest.mark.asyncio
async def test_tools_node_returns_tool_message_for_successful_tool_call():
    async def echo_tool(**kwargs):
        return {'value': kwargs['value']}

    tool = StructuredTool.from_function(
        coroutine=echo_tool,
        name='echo',
        description='Echo back the provided value.',
        args_schema=EchoArgs,
    )

    state = {
        'messages': [
            AIMessage(
                content='',
                tool_calls=[{'name': 'echo', 'args': {'value': 7}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    result = await _tools_node(state, {'echo': tool})

    assert len(result['messages']) == 1
    message = result['messages'][0]
    assert isinstance(message, ToolMessage)
    assert message.tool_call_id == 'call1'
    assert message.status == 'success'
    assert '"value": 7' in message.content


@pytest.mark.asyncio
async def test_tools_node_skips_approval_when_tool_is_not_configured_for_it():
    async def echo_tool(**kwargs):
        return {'value': kwargs['value']}

    async def unexpected_event_caller(event_data, timeout=None):
        raise AssertionError('approval should not be requested')

    tool = StructuredTool.from_function(
        coroutine=echo_tool,
        name='echo',
        description='Echo back the provided value.',
        args_schema=EchoArgs,
    )

    state = {
        'messages': [
            AIMessage(
                content='',
                tool_calls=[{'name': 'echo', 'args': {'value': 7}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    result = await _tools_node(
        state,
        {'echo': {'structured_tool': tool, 'tool_id': 'tool:echo'}},
        tool_approval_ids=set(),
        event_caller=unexpected_event_caller,
        run_id='run-123',
    )

    assert len(result['messages']) == 1
    message = result['messages'][0]
    assert isinstance(message, ToolMessage)
    assert message.status == 'success'
    assert '"value": 7' in message.content


@pytest.mark.asyncio
async def test_tools_node_requests_approval_before_running_selected_tool():
    async def echo_tool(**kwargs):
        return {'value': kwargs['value']}

    approval_requests = []

    async def approval_event_caller(event_data, timeout=None):
        approval_requests.append((event_data, timeout))
        return True

    tool = StructuredTool.from_function(
        coroutine=echo_tool,
        name='echo',
        description='Echo back the provided value.',
        args_schema=EchoArgs,
    )

    state = {
        'messages': [
            AIMessage(
                id='msg-1',
                content='',
                tool_calls=[{'name': 'echo', 'args': {'value': 7}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    result = await _tools_node(
        state,
        {'echo': {'structured_tool': tool, 'tool_id': 'tool:echo'}},
        tool_approval_ids={'tool:echo'},
        event_caller=approval_event_caller,
        run_id='run-123',
    )

    assert len(approval_requests) == 1
    event_data, timeout = approval_requests[0]
    assert event_data['type'] == 'confirmation'
    assert event_data['data']['title'] == 'Approve Tool Execution'
    assert event_data['data']['confirmLabel'] == 'Approve'
    assert event_data['data']['cancelLabel'] == 'Reject'
    assert 'Approve running `echo`?' in event_data['data']['message']
    assert '"value": 7' in event_data['data']['message']
    assert timeout is not None

    assert len(result['messages']) == 1
    message = result['messages'][0]
    assert isinstance(message, ToolMessage)
    assert message.status == 'success'
    assert '"value": 7' in message.content


@pytest.mark.asyncio
async def test_tools_node_turns_rejected_approval_into_tool_error():
    tool_called = False

    async def echo_tool(**kwargs):
        nonlocal tool_called
        tool_called = True
        return {'value': kwargs['value']}

    async def approval_event_caller(event_data, timeout=None):
        return {'approved': False}

    tool = StructuredTool.from_function(
        coroutine=echo_tool,
        name='echo',
        description='Echo back the provided value.',
        args_schema=EchoArgs,
    )

    state = {
        'messages': [
            AIMessage(
                content='',
                tool_calls=[{'name': 'echo', 'args': {'value': 7}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    result = await _tools_node(
        state,
        {'echo': {'structured_tool': tool, 'tool_id': 'tool:echo'}},
        tool_approval_ids={'tool:echo'},
        event_caller=approval_event_caller,
        run_id='run-123',
    )

    assert tool_called is False
    assert len(result['messages']) == 1
    message = result['messages'][0]
    assert isinstance(message, ToolMessage)
    assert message.status == 'error'
    assert TOOL_APPROVAL_REJECTED_MESSAGE in message.content


@pytest.mark.asyncio
async def test_tools_node_turns_approval_timeout_into_tool_error():
    tool_called = False

    async def echo_tool(**kwargs):
        nonlocal tool_called
        tool_called = True
        return {'value': kwargs['value']}

    async def approval_event_caller(event_data, timeout=None):
        raise TimeoutError('no response')

    tool = StructuredTool.from_function(
        coroutine=echo_tool,
        name='echo',
        description='Echo back the provided value.',
        args_schema=EchoArgs,
    )

    state = {
        'messages': [
            AIMessage(
                content='',
                tool_calls=[{'name': 'echo', 'args': {'value': 7}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    result = await _tools_node(
        state,
        {'echo': {'structured_tool': tool, 'tool_id': 'tool:echo'}},
        tool_approval_ids={'tool:echo'},
        event_caller=approval_event_caller,
        run_id='run-123',
    )

    assert tool_called is False
    assert len(result['messages']) == 1
    message = result['messages'][0]
    assert isinstance(message, ToolMessage)
    assert message.status == 'error'
    assert TOOL_APPROVAL_TIMED_OUT_MESSAGE in message.content


@pytest.mark.asyncio
async def test_tools_node_returns_error_message_for_unknown_tool():
    state = {
        'messages': [
            AIMessage(
                content='',
                tool_calls=[{'name': 'missing', 'args': {'value': 7}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    result = await _tools_node(state, {})

    assert len(result['messages']) == 1
    message = result['messages'][0]
    assert isinstance(message, ToolMessage)
    assert message.tool_call_id == 'call1'
    assert message.status == 'error'
    assert 'not a valid tool' in message.content


@pytest.mark.asyncio
async def test_tools_node_converts_tool_exception_to_error_message():
    async def failing_tool(**kwargs):
        raise RuntimeError(f"boom:{kwargs['value']}")

    tool = StructuredTool.from_function(
        coroutine=failing_tool,
        name='explode',
        description='Raise an exception.',
        args_schema=EchoArgs,
    )

    state = {
        'messages': [
            AIMessage(
                content='',
                tool_calls=[{'name': 'explode', 'args': {'value': 9}, 'id': 'call1', 'type': 'tool_call'}],
            )
        ]
    }

    result = await _tools_node(state, {'explode': tool})

    assert len(result['messages']) == 1
    message = result['messages'][0]
    assert isinstance(message, ToolMessage)
    assert message.tool_call_id == 'call1'
    assert message.status == 'error'
    assert 'boom:9' in message.content


@pytest.mark.asyncio
async def test_local_tool_executor_emits_tool_start_and_end_events():
    async def echo_tool(**kwargs):
        return {'value': kwargs['value']}

    tool = StructuredTool.from_function(
        coroutine=echo_tool,
        name='echo',
        description='Echo back the provided value.',
        args_schema=EchoArgs,
    )

    async def llm_node(state: MessagesState) -> dict:
        return {
            'messages': [
                AIMessage(
                    content='',
                    tool_calls=[{'name': 'echo', 'args': {'value': 5}, 'id': 'call1', 'type': 'tool_call'}],
                )
            ]
        }

    async def tools_node(state: MessagesState) -> dict:
        return await _tools_node(state, {'echo': tool})

    graph = StateGraph(MessagesState)
    graph.add_node('llm', llm_node)
    graph.add_node('tools', tools_node)
    graph.add_edge(START, 'llm')
    graph.add_conditional_edges('llm', _route_after_llm)
    graph.add_edge('tools', END)
    app = graph.compile()

    events = []
    async for event in app.astream_events(
        {'messages': [HumanMessage(content='hi')]},
        version='v2',
    ):
        events.append(event)

    assert any(event.get('event') == 'on_tool_start' and event.get('name') == 'echo' for event in events)
    assert any(event.get('event') == 'on_tool_end' and event.get('name') == 'echo' for event in events)
