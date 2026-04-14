import asyncio
from typing import Optional
from contextlib import AsyncExitStack

import anyio

from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
import httpx
from open_webui.env import AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL


def create_insecure_httpx_client(headers=None, timeout=None, auth=None):
    """Create an httpx AsyncClient with SSL verification disabled.

    Note: verify=False must be passed at construction time because httpx
    configures the SSL context during __init__. Setting client.verify = False
    after construction does not affect the underlying transport's SSL context.
    """
    kwargs = {
        'follow_redirects': True,
        'verify': False,
    }
    if timeout is not None:
        kwargs['timeout'] = timeout
    if headers is not None:
        kwargs['headers'] = headers
    if auth is not None:
        kwargs['auth'] = auth
    return httpx.AsyncClient(**kwargs)


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = None
        self._transport_type: Optional[str] = None

    async def connect(
        self,
        url: Optional[str] = None,
        headers: Optional[dict] = None,
        transport: str = 'http_streamable',
        # stdio-specific params
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
    ):
        self._transport_type = transport

        async with AsyncExitStack() as exit_stack:
            try:
                if transport == 'http_streamable':
                    if AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL:
                        self._streams_context = streamablehttp_client(url, headers=headers)
                    else:
                        self._streams_context = streamablehttp_client(
                            url,
                            headers=headers,
                            httpx_client_factory=create_insecure_httpx_client,
                        )
                    streams = await exit_stack.enter_async_context(self._streams_context)
                    read_stream, write_stream, _ = streams

                elif transport == 'sse':
                    if AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL:
                        self._streams_context = sse_client(url, headers=headers)
                    else:
                        self._streams_context = sse_client(
                            url,
                            headers=headers,
                            httpx_client_factory=create_insecure_httpx_client,
                        )
                    streams = await exit_stack.enter_async_context(self._streams_context)
                    read_stream, write_stream = streams

                elif transport == 'stdio':
                    server_params = StdioServerParameters(
                        command=command or '',
                        args=args or [],
                        env=env,
                    )
                    self._streams_context = stdio_client(server_params)
                    streams = await exit_stack.enter_async_context(self._streams_context)
                    read_stream, write_stream = streams

                else:
                    raise ValueError(f'Unsupported MCP transport: {transport}')

                self._session_context = ClientSession(read_stream, write_stream)

                self.session = await exit_stack.enter_async_context(self._session_context)
                with anyio.fail_after(10):
                    await self.session.initialize()
                self.exit_stack = exit_stack.pop_all()
            except Exception as e:
                await asyncio.shield(self.disconnect())
                raise e

    async def list_tool_specs(self) -> Optional[dict]:
        if not self.session:
            raise RuntimeError('MCP client is not connected.')

        result = await self.session.list_tools()
        tools = result.tools

        tool_specs = []
        for tool in tools:
            name = tool.name
            description = tool.description

            inputSchema = tool.inputSchema

            # TODO: handle outputSchema if needed
            outputSchema = getattr(tool, 'outputSchema', None)

            # MCP Apps spec: tools may declare an associated UI resource at
            # definition time via `_meta.ui.resourceUri`. The Python MCP SDK
            # exposes this under `.meta` (pydantic alias) or in the dumped
            # `_meta` key.
            tool_meta = getattr(tool, 'meta', None)
            if tool_meta is None:
                try:
                    dumped = tool.model_dump(mode='json', by_alias=True)
                    tool_meta = dumped.get('_meta') or dumped.get('meta')
                except Exception:
                    tool_meta = None

            tool_specs.append(
                {
                    'name': name,
                    'description': description,
                    'parameters': inputSchema,
                    'meta': tool_meta,
                }
            )

        return tool_specs

    async def call_tool(self, function_name: str, function_args: dict) -> Optional[dict]:
        if not self.session:
            raise RuntimeError('MCP client is not connected.')

        result = await self.session.call_tool(function_name, function_args)
        if not result:
            raise Exception('No result returned from MCP tool call.')

        result_dict = result.model_dump(mode='json')
        result_content = result_dict.get('content', {})

        if result.isError:
            raise Exception(result_content)
        else:
            return result_content

    async def call_tool_with_meta(self, function_name: str, function_args: dict) -> dict:
        """Like call_tool but also returns the `_meta` from the CallToolResult.

        Returns {'content': ..., 'meta': ...}. Used to support the MCP Apps spec
        where tools attach a UI resource reference via `_meta.ui.resourceUri`.
        """
        if not self.session:
            raise RuntimeError('MCP client is not connected.')

        result = await self.session.call_tool(function_name, function_args)
        if not result:
            raise Exception('No result returned from MCP tool call.')

        result_dict = result.model_dump(mode='json')
        result_content = result_dict.get('content', {})
        result_meta = result_dict.get('_meta') or result_dict.get('meta') or {}
        result_structured = (
            result_dict.get('structuredContent')
            or result_dict.get('structured_content')
        )

        if result.isError:
            raise Exception(result_content)

        return {
            'content': result_content,
            'meta': result_meta,
            'structuredContent': result_structured,
        }

    async def list_resources(self, cursor: Optional[str] = None) -> Optional[dict]:
        if not self.session:
            raise RuntimeError('MCP client is not connected.')

        result = await self.session.list_resources(cursor=cursor)
        if not result:
            raise Exception('No result returned from MCP list_resources call.')

        result_dict = result.model_dump()
        resources = result_dict.get('resources', [])

        return resources

    async def read_resource(self, uri: str) -> Optional[dict]:
        if not self.session:
            raise RuntimeError('MCP client is not connected.')

        result = await self.session.read_resource(uri)
        if not result:
            raise Exception('No result returned from MCP read_resource call.')
        # mode='json' coerces pydantic types like AnyUrl -> str so the payload
        # is safe to pass to json.dumps / Socket.IO emitters downstream.
        result_dict = result.model_dump(mode='json')

        return result_dict

    async def disconnect(self):
        # Clean up and close the session
        if self.exit_stack:
            await self.exit_stack.aclose()

    async def __aenter__(self):
        if self.exit_stack:
            await self.exit_stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.exit_stack:
            await self.exit_stack.__aexit__(exc_type, exc_value, traceback)
        await self.disconnect()
