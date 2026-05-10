import os
import json
import logging
import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"


def summarise(theme: dict, viral_tweet: dict) -> dict:
    """
    Inject the viral tweet into the theme prompt and call Claude.
    Returns dict with keys: hook, expansion, reply.
    """
    prompt = theme["prompt"]

    # Inject the viral tweet details into the prompt placeholders
    prompt = prompt.replace("[PASTE TWEET HERE]", viral_tweet["text"])
    prompt = prompt.replace("[X likes]", str(viral_tweet["likes"]))
    prompt = prompt.replace("[X views]", str(viral_tweet["views"]))

    system = (
        "You are the content engine behind Wise Brief on X (Twitter). "
        "You decode viral stories for a global audience. "
        "Your output must be a valid JSON object with exactly three keys: "
        "\"hook\" (string, under 280 chars, ends with 🧵), "
        "\"expansion\" (string, 6-10 paragraphs, each under 300 chars, separated by double newline), "
        "\"reply\" (string, 3 sources + follow CTA). "
        "Output JSON only. No markdown. No extra commentary."
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    logger.info(f"Calling Claude ({MODEL}) for theme: {theme['name']} ...")

    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    logger.info("Claude response received.")

    # Parse JSON — strip markdown fences if Claude added them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        output = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"Could not parse JSON from Claude: {raw[:200]}")
        output = json.loads(raw[start:end])

    for key in ("hook", "expansion", "reply"):
        if key not in output:
            raise ValueError(f"Claude response missing key: {key}")

    logger.info(f"Hook: {output['hook'][:80]}...")
    return output
