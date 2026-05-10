import os
import json
import time
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"


def summarise(theme: dict, viral_tweet: dict) -> dict:
    """
    Inject the viral tweet into the theme prompt and call GPT-4o.
    Returns dict with keys: hook, expansion, reply.
    """
    prompt = theme["prompt"]
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

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    logger.info(f"Calling {MODEL} for theme: {theme['name']} ...")

    for attempt in range(1, 6):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            break
        except Exception as e:
            wait = 10 * attempt
            logger.warning(f"OpenAI API error (attempt {attempt}/5): {e}. Retrying in {wait}s ...")
            if attempt == 5:
                raise
            time.sleep(wait)

    raw = response.choices[0].message.content.strip()
    logger.info("GPT-4o response received.")

    try:
        output = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"Could not parse JSON from GPT-4o: {raw[:200]}")
        output = json.loads(raw[start:end])

    for key in ("hook", "expansion", "reply"):
        if key not in output:
            raise ValueError(f"GPT-4o response missing key: {key}")

    logger.info(f"Hook: {output['hook'][:80]}...")
    return output
