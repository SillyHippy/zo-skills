#!/usr/bin/env python3
"""End-to-end MCP transport test: spawn server.py via stdio, list tools, call fill_flat_pdf."""
import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = "/home/workspace/flat-pdf-fill/server.py"


async def main():
    params = StdioServerParameters(command="python3", args=[SERVER])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print("TOOLS:", names)

            # call detect_fields first
            r1 = await session.call_tool(
                "detect_fields",
                {"input_pdf": "/home/workspace/flat-pdf-fill/tests/test_blank.pdf", "page": 1},
            )
            txt1 = r1.content[0].text
            det = json.loads(txt1)
            print("detect_fields lines:", [l["text"] for l in det["lines"]])

            # call fill_flat_pdf
            r2 = await session.call_tool(
                "fill_flat_pdf",
                {
                    "input_pdf": "/home/workspace/flat-pdf-fill/tests/test_blank.pdf",
                    "output_pdf": "/home/workspace/flat-pdf-fill/tests/test_filled_via_mcp.pdf",
                    "fields": {
                        "Name": "Jane Smith",
                        "Address": "456 Oak Ave",
                        "City, State, ZIP": "Tulsa, OK 74116",
                        "Case No.": "FD-2026-9999",
                        "Phone": "405-555-6789",
                    },
                },
            )
            txt2 = r2.content[0].text
            res = json.loads(txt2)
            print("placed:", [(p["label"], p["value"], p["underscore"], p["fits"]) for p in res["placed"]])
            print("missing:", res["missing"])
            print("output_pdf exists:", __import__("os").path.exists(res["output_pdf"]))
            assert len(res["placed"]) == 5 and not res["missing"], "MCP fill failed"
            print("MCP TRANSPORT TEST: PASS")


if __name__ == "__main__":
    asyncio.run(main())
