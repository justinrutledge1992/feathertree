from django.shortcuts import render
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token
from django.conf import settings
import requests
from requests.exceptions import RequestException, Timeout
import re
import logging

logger = logging.getLogger(__name__)

# Include any miscellanous helper functions here
def generate_new_user_activation_url(user):
    domain_name = "feathertree.net"
    base_url = "https://" + domain_name + "/user/activation/"
    url_safe_user_id = urlsafe_base64_encode(force_bytes(user.pk))
    activation_token = account_activation_token.make_token(user)
    unique_url = base_url + url_safe_user_id + "/" + activation_token
    return unique_url

def form_invalid_response(request, form, template):
    return render(
        request,
        template,
        {
            "error_message": "Invalid form submission. Please make sure all fields are filled out properly and try again.",
            "form": form
        },
    )

def form_invalid_response_w_msg(request, form, template, error_message):
    return render(
        request,
        template,
        {
            "error_message": error_message,
            "form": form
        },
    )

def chunk_list(lst, chunk_size):
    chunks = []
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        while len(chunk) < chunk_size:  # Fill the chunk up to chunk_size
            chunk.append(None)
        chunks.append(chunk)
    return chunks

def build_continuity_prompt(previous_text: str,
                            current_text: str,
                            criteria: str,
                            rubric: str) -> str:
    return f"""
# GOAL
Your job is to evaluate how well a story continues from one passage to the next.

You will be provided with:
1. A previous section of story text ("previous text")
2. A new continuation written after it ("current text")
3. Continuity evaluation criteria
4. A scoring rubric (1–5)

Your task is to evaluate the continuity between previous text and current text.

# PREVIOUS TEXT
<previous_text>
{previous_text}
</previous_text>

# CURRENT TEXT
<current_text>
{current_text}
</current_text>

# CONTINUITY EVALUATION CRITERIA
<evaluation_criteria>
{criteria}
</evaluation_criteria>

# CONTINUITY SCORING RUBRIC
<scoring_rubric>
{rubric}
</scoring_rubric>

# INSTRUCTIONS FOR THE EVALUATION
1. Compare the current text to the previous text.
2. Evaluate continuity in theme, tone, narrative flow, logic, and character consistency.
3. Identify whether new elements introduced in the current text make sense within the story.
4. Identify any breaks in logic, tone, or narrative structure.
5. Use the scoring rubric to determine the appropriate score.
6. Justify your evaluation with specific references to both passages.

## FORMAT FOR THE EVALUATION
- Write verbal feedback inside <feedback> tags without any surrounding text.
- Write the numeric score inside <score> tags, without any surrounding text and always after the feedback.

Please evaluate the story continuation accurately.
"""

def parse_featherjudge_response(text: str) -> tuple[int, str]:
    """
    Parse <feedback>...</feedback> and <score>...</score> from a string.

    Returns:
        (score, feedback)

    Raises:
        TypeError: if `text` is not a string.
        ValueError: if feedback/score blocks are missing or score is not an int.
    """
    # Guard against accidentally passing a tuple or other type
    if not isinstance(text, str):
        logger.error(
            "parse_featherjudge_response expected a string, got %r: %r",
            type(text),
            text,
        )
        raise TypeError(
            f"parse_featherjudge_response expected a string, got {type(text)!r}"
        )

    # Try to extract feedback and score blocks
    feedback_match = re.search(
        r"<feedback>(.*?)</feedback>", text, re.DOTALL | re.IGNORECASE
    )
    score_match = re.search(
        r"<score>(.*?)</score>", text, re.DOTALL | re.IGNORECASE
    )

    if not feedback_match:
        # Log a snippet so you can see what the model actually returned
        logger.error(
            "No <feedback>...</feedback> block found in FeatherJudge response. "
            "First 500 chars: %r",
            text[:500],
        )
        raise ValueError("No <feedback>...</feedback> block found.")

    if not score_match:
        logger.error(
            "No <score>...</score> block found in FeatherJudge response. "
            "First 500 chars: %r",
            text[:500],
        )
        raise ValueError("No <score>...</score> block found.")

    feedback = feedback_match.group(1).strip()
    score_str = score_match.group(1).strip()

    try:
        score = int(score_str)
    except ValueError as e:
        # This gives you full traceback + context in DO logs
        logger.exception(
            "Score is not a valid integer. Got %r from response. "
            "First 500 chars of response: %r",
            score_str,
            text[:500],
        )
        raise ValueError(f"Score is not a valid integer: {score_str!r}") from e

    return score, feedback

# Creates Baseten API call to the LLM
def call_featherjudge(payload):
    url = (
        f"https://model-{settings.FEATHERJUDGE_MODEL_ID}.api.baseten.co/"
        f"{settings.BASETEN_DEPLOYMENT_TYPE}/predict"
    )

    try:
        resp = requests.post(
            url,
            headers={"Authorization": f"Api-Key {settings.BASETEN_API_KEY}"},
            json=payload,
            timeout=30,
        )

        resp.raise_for_status()
        data = resp.json()
        text = data.get("text")

        if text is None:
            logger.error(
                "FeatherJudge response missing 'text' key. Full JSON: %r", data
            )
            raise KeyError("Missing 'text' in Baseten response")

        return text

    except Timeout:
        logger.warning("FeatherJudge request timed out for URL %s", url, exc_info=True)
        return None, "The FeatherJudge model timed out while generating a response."

    except RequestException as e:
        logger.exception("Network error while calling FeatherJudge at %s", url)
        return None, f"Network error while calling FeatherJudge: {e}"

    except (ValueError, KeyError) as e:
        logger.exception("Invalid or malformed FeatherJudge response from %s", url)
        return None, f"Invalid response from FeatherJudge: {e}"

    except Exception as e:
        logger.exception("Unexpected error while calling FeatherJudge at %s", url)
        return None, f"Unexpected error while calling FeatherJudge: {e}"


# This tries to query the Baseten API setup running a modified version of Flow-Judge
# https://github.com/flowaicom/flow-judge
# Baseten implementation:
# https://app.baseten.co/models/rwny1n13
def query_judge(previous_text, current_text):
    criteria = (
        "Evaluate how well the current text continues the story from the previous text. "
        "Focus on tone, theme, narrative flow, and logical coherence. "
    )

    rubric = """
    - Score 1: No continuity. Very different in theme, tone, and content. New elements do not make sense in the context of the story.
    - Score 2: Poor continuity. Somewhat different in theme, tone, and content. New elements do not make sense in the context of the story.
    - Score 3: Some continuity. Somewhat aligned and somewhat different in theme, tone, and content. New elements make sense in the context of the story.
    - Score 4: Good continuity. Aligned in theme, tone, and content. New elements make sense in the context of the story.
    - Score 5: Excellent continuity. Very aligned in theme, tone, and content. New elements make sense in the context of the story.
    """

    flow_judge_prompt = build_continuity_prompt(
        previous_text,
        current_text,
        criteria,
        rubric
    )

    payload = {
        "prompt": flow_judge_prompt,
        "max_tokens": 512,
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40
    }
    
    response = call_featherjudge(payload)

    score, feedback = parse_featherjudge_response(response)

    return score, feedback