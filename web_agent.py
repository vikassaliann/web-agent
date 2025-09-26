import asyncio
import json
from dataclasses import dataclass
from typing import List

from autogen_core import (
    AgentId,
    FunctionCall,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    message_handler,
)
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, SseServerParams

# Define the message type
@dataclass
class Message:
    content: str

# Define the agent that will use the workbench
class BrowserAgent(RoutedAgent):
    def __init__(
        self,
        model_client: ChatCompletionClient,
        model_context: BufferedChatCompletionContext,
        workbench: McpWorkbench,
    ) -> None:
        super().__init__("WebAgent")
        self._model_client = model_client
        self._model_context = model_context
        self._workbench = workbench
        self._system_messages: List[LLMMessage] = [
            SystemMessage(content="You are a helpful assistant with web browsing tools. Use them to answer questions.")
        ]

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        # Add the user message to the context for the LLM to remember
        await self._model_context.add_message(UserMessage(content=message.content, source="user"))

        # Main loop for tool calls and responses
        while True:
            # Get the full conversation history from the context
            history = self._system_messages + (await self._model_context.get_messages())
            
            # Ask the LLM to generate a response (which might be a tool call)
            create_result = await self._model_client.create(
                messages=history,
                tools=(await self._workbench.list_tools()),
                cancellation_token=ctx.cancellation_token,
            )

            # Check if the LLM provided a final answer
            if isinstance(create_result.content, str):
                await self._model_context.add_message(AssistantMessage(content=create_result.content, source="assistant"))
                return Message(content=create_result.content)

            # If the LLM wants to call a tool, execute the call
            assert isinstance(create_result.content, list)
            tool_calls = create_result.content
            await self._model_context.add_message(AssistantMessage(content=tool_calls, source="assistant"))

            # Execute all tool calls concurrently
            results = [
                await self._workbench.call_tool(call.name, arguments=json.loads(call.arguments))
                for call in tool_calls
            ]

            # Add the results of the tool execution back to the context
            exec_results = [
                FunctionExecutionResult(
                    call_id=call.id,
                    content=result.to_text(),
                    is_error=result.is_error,
                    name=result.name,
                )
                for call, result in zip(tool_calls, results, strict=False)
            ]
            await self._model_context.add_message(FunctionExecutionResultMessage(content=exec_results))

# Main function to run the agent
async def main():
    # Configure the Playwright MCP server
    playwright_server_params = SseServerParams(url="http://localhost:8931/sse")
    
    # Use a context manager to start and stop the workbench
    async with McpWorkbench(playwright_server_params) as workbench:
        # Create a single-threaded agent runtime
        runtime = SingleThreadedAgentRuntime()

        # Create the model client and context for the agent
        # Updated this line to include the API key.
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key='use-your-api-key'  # <-- Replace with your actual key
        )
        model_context = BufferedChatCompletionContext(buffer_size=10)

        # Register the agent with the runtime
        await BrowserAgent.register(
            runtime,
            "web_agent",
            lambda: BrowserAgent(model_client=model_client, model_context=model_context, workbench=workbench),
        )

        # Start the runtime
        runtime.start()

        # Altered the message content to a new task
        response = await runtime.send_message(
            Message(content="Use Bing to find out the number of employees at Microsoft."),
            recipient=AgentId("web_agent", "default"),
        )
        print(f"Final Answer:\n{response.content}")

        # Stop the runtime and close the client
        await runtime.stop_when_idle()
        await model_client.close()

if __name__ == "__main__":
    asyncio.run(main())