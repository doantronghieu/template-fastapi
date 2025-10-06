"""Extension-specific prompts.

Usage:
    from app.extensions._example.resources.llm import load_prompt
    prompt = load_prompt("example_feature")

To use core prompts:
    from app.resources.llm import load_prompt as load_core_prompt
    system = load_core_prompt("common/system")
"""
