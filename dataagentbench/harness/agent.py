"""Claude agentic loop with tool use for DataAgentBench."""

from __future__ import annotations

import json
import os

import anthropic
import pandas as pd

from .tools import TOOL_DEFINITIONS, get_column_stats, get_dataframe_info, run_code
from .tracer import Trace, Tracer

DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a expert data scientist working on a benchmark task.
You have access to a pandas DataFrame called `df` loaded with the task dataset.
Use the provided tools to analyse the data. After completing your analysis,
write a clear, structured final answer that directly addresses all sub-questions
in the task description. Be precise — include exact numeric values where computed."""


class Agent:
    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None):
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def run(
        self,
        task_description: str,
        dataframe: pd.DataFrame,
        task_id: str,
        max_steps: int = 10,
        timeout_seconds: int = 120,
        allowed_tools: list[str] | None = None,
    ) -> Trace:
        tracer = Tracer(task_id=task_id, model=self.model)

        # Filter tools based on allowed list
        tools = TOOL_DEFINITIONS
        if allowed_tools:
            tools = [t for t in TOOL_DEFINITIONS if t["name"] in allowed_tools]

        messages: list[dict] = [{"role": "user", "content": task_description}]

        for step in range(max_steps):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Collect text and tool use blocks
            assistant_text = ""
            tool_uses = []

            for block in response.content:
                if block.type == "text":
                    assistant_text += block.text
                elif block.type == "tool_use":
                    tool_uses.append(block)

            tracer.record(
                role="assistant",
                content=assistant_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            # If no tool calls, agent is done
            if response.stop_reason == "end_turn" or not tool_uses:
                return tracer.finalize(final_answer=assistant_text)

            # Add assistant message to conversation
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for tool_use in tool_uses:
                result = self._dispatch_tool(tool_use.name, tool_use.input, dataframe)
                result_str = json.dumps(result) if isinstance(result, dict) else str(result)

                tracer.record(
                    role="tool",
                    content=result_str,
                    tool_name=tool_use.name,
                    tool_input=tool_use.input,
                    tool_output=result,
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result_str,
                })

            messages.append({"role": "user", "content": tool_results})

        # Max steps reached — return whatever the last assistant text was
        last_text = ""
        for msg in reversed(messages):
            if msg["role"] == "assistant":
                content = msg["content"]
                if isinstance(content, list):
                    for block in content:
                        if hasattr(block, "text"):
                            last_text = block.text
                            break
                elif isinstance(content, str):
                    last_text = content
                break

        return tracer.finalize(
            final_answer=last_text,
            error=f"Reached max_steps={max_steps} without end_turn",
        )

    def _dispatch_tool(self, name: str, inputs: dict, dataframe: pd.DataFrame):
        if name == "run_code":
            return run_code(inputs["code"], dataframe)
        elif name == "get_dataframe_info":
            return get_dataframe_info(dataframe)
        elif name == "get_column_stats":
            return get_column_stats(inputs["column_name"], dataframe)
        else:
            return {"error": f"Unknown tool: {name!r}"}
