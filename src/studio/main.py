from collections import defaultdict
from fastmcp import FastMCP
from studio.mcp.employee_hours import mcp
import datetime


if __name__ == "__main__":
    mcp.settings.host="0.0.0.0"
    mcp.run(transport="sse")
