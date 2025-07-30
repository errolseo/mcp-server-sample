import logging
import yaml
from typing import Any

import click
import uvicorn
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route

from tools.weather import (
  get_current_datetime,
  get_current_location,
  get_current_weather,
)

logger = logging.getLogger(__name__)


@click.command()
@click.option("--port", default=8000, help="Port to listen on for HTTP")
@click.option(
  "--log-level",
  default="INFO",
  help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(
  port: int,
  log_level: str,
) -> int:
  """
  Starts the MCP (Multi-Agent Communication Protocol) server with defined tools
  for meeting room management.
  """
  # Configure logging
  logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  )
  logger.info(f"Starting server with log level: {log_level.upper()}")

  app = Server("mcp-sse-server")
      
  @app.list_tools()
  async def list_tools() -> list[types.Tool]:
    """
    Loads and returns a list of available tools from a YAML configuration file.
    """
    try:
      with open("./tool_list.yaml", "r") as f:
        tools_data = yaml.load(f, Loader=yaml.FullLoader)["tools"]
        
      tool_list = [
        types.Tool(
          name=tool["name"],
          description="\n".join(tool["description"]),
          inputSchema=tool["inputSchema"],
          outputSchema=tool["outputSchema"],
        )
        for tool in tools_data
      ]
      logger.info(f"Loaded {len(tool_list)} tools from tool_list.yaml")
      return tool_list
    except FileNotFoundError:
      logger.error("tool_list.yaml not found. No tools will be loaded.")
      return []
    except yaml.YAMLError as e:
      logger.error(f"Error parsing tool_list.yaml: {e}")
      return []
    except KeyError as e:
      logger.error(f"Missing key in tool_list.yaml: {e}")
      return []

  @app.call_tool()
  async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Executes the specified tool function with the given arguments.
    """
    tool_functions = {
      "get_current_datetime": get_current_datetime,
      "get_current_location": get_current_location,
      "get_current_weather": get_current_weather,
    }
    
    if name not in tool_functions:
      logger.error(f"Attempted to call unknown tool: {name}")
      raise NameError(f"Tool '{name}' does not exist.")
    
    try:
      # Evaluate the expression if present, otherwise use arguments directly
      if "expression" in arguments:
        # Security warning: Using eval() can be dangerous if the input
        # is not controlled. Ensure 'arguments["expression"]' comes
        # from a trusted source.
        result = eval(arguments["expression"])
        logger.debug(f"Evaluated expression for '{name}': {result}")
        # Pass the evaluated result to the tool function
        return tool_functions[name](result)
      else:
        # If no expression, pass the entire arguments dictionary (or specific keys if the tool expects them)
        # You might need to adjust this based on how your tools expect arguments.
        # For now, it assumes the tool can handle the arguments dictionary directly.
        logger.debug(f"Calling tool '{name}' with arguments: {arguments}")
        return tool_functions[name](**arguments) # Assuming tools expect keyword arguments
    except Exception as e:
      logger.error(f"Error calling tool '{name}': {e}", exc_info=True)
      raise ValueError(f"Error executing tool '{name}': {e}")

  sse = SseServerTransport("/messages/")

  async def handle_sse(request):
    """
    Handles Server-Sent Events (SSE) connections for MCP communication.
    """
    logger.info("SSE connection established.")
    async with sse.connect_sse(
      request.scope, request.receive, request._send
    ) as streams:
        await app.run(
          streams[0], streams[1], app.create_initialization_options()
        )
    logger.info("SSE connection closed.")
    return Response()
          
  # Create an ASGI application using Starlette
  starlette_app = Starlette(
    debug=True,
    routes=[
      Route("/sse", endpoint=handle_sse, methods=["GET"]),
      Mount("/messages/", app=sse.handle_post_message),
    ],
  )

  logger.info(f"Starting Uvicorn server on http://0.0.0.0:{port}")
  uvicorn.run(starlette_app, host="0.0.0.0", port=port)

  return 0
