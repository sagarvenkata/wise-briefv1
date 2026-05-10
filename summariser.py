import os
import json
import time
import logging
from groq import Groq

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"


def summarise(theme: dict, viral_tweet: dict) -> dict:
    """
    Inject the viral tweet into the theme prompt and call Groq.
    Returns dict with keys: hook, expansion, reply.
    """
    prompt = theme["prompt"]
    prompt = prompt.replace("[PASTE TWEET HERE]", viral_tweet["text"])
    prompt = prompt.replace("[X likes]", str(viral_tweet["likes"]))
    prompt = prompt.replace("[X views]", str(viral_tweet["views"]))

    system = (
        "You are the content engine behind Wise Brief on X (Twitter). "
        "You decode viral stories for a global audience. "
        "Your output must be a valid JSON object with exactly two keys: "
        "\"content\" and \"reply\". "
        "\n\n"
        "\"content\": The full post. Start with a punchy hook line opening with a number or stat, no questions, ends with 🧵. "
        "Then a blank line. Then 6 to 10 paragraphs separated by blank lines. "
        "Each paragraph must be 2 to 3 full sentences minimum. Never one-liners. "
        "Follow all paragraph instructions from the user prompt (P1 through P6 and BONUS). "
        "No em-dashes. Plain conversational language. Always use real numbers and named examples. "
        "\n\n"
        "\"reply\": Start with exactly: "
        "\"Thank you for spending time on our post! If you liked the content, follow @TheWiseBrief for more.\n\n—————\n\nSources:\n\" "
        "Then list 3 to 5 real, specific sources with full clickable URLs on separate lines. "
        "Every source MUST include a real working https:// URL. "
        "Format each as: Description — https://full-url-here"
        "\n\n"
        "Output JSON only. No markdown fences. No extra commentary."
    )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    logger.info(f"Calling Groq ({MODEL}) for theme: {theme['name']} ...")

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
            logger.warning(f"Groq API error (attempt {attempt}/5): {e}. Retrying in {wait}s ...")
            if attempt == 5:
                raise
            time.sleep(wait)

    raw = response.choices[0].message.content.strip()
    logger.info("Groq response received.")

    try:
        output = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"Could not parse JSON from Groq: {raw[:200]}")
        output = json.loads(raw[start:end])

    for key in ("content", "reply"):
        if key not in output:
            raise ValueError(f"Groq response missing key: {key}")

    logger.info(f"Content preview: {output['content'][:80]}...")
    return output
