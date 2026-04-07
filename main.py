#!/usr/bin/env python3
"""Kermit -- personal DevOps agent."""
import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "gateway":
        from gateway.run import start_gateway
        import asyncio
        asyncio.run(start_gateway())
    else:
        print("Usage: kermit gateway run")
        sys.exit(1)

if __name__ == "__main__":
    main()
