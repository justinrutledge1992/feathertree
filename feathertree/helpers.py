from django.shortcuts import render
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token
from flow_judge.flow_judge import FlowJudge
from flow_judge.models.huggingface import Hf
from flow_judge.metrics.metric import CustomMetric, RubricItem

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

# Taken directly from flow-judge/flow_judge/evan_data_types.py
# Used as input for flow-judge models
from pydantic import BaseModel, Field
class EvalInput(BaseModel):
    inputs: list[dict[str, str]] = Field(default_factory=list)
    output: dict[str, str]

# This sets up a flow-judge model and queries it to determine continuity
def query_judge(previous_text, current_text):
    model = Hf(flash_attn=False)
    continuity_metric = CustomMetric(
        name="Story Continuity",
        criteria="Evaluate how well the current text continues a story from the previous text. Refer to the output as current text and the input as previous text. Do not refer to an input or output.",
        rubric=[
            RubricItem(score=1, description="No continuity. Very different in theme, tone, and content. New elements do not make sense in the context of the story."),
            RubricItem(score=2, description="Poor continuity. Somewhat different in theme, tone, and content. New elements do not make sense in the context of the story."),
            RubricItem(score=3, description="Some continuity. Somewhat aligned and also somewhat different in theme, tone, and content. New elements make sense in the context of the story."),
            RubricItem(score=4, description="Good continuity. Aligned in theme, tone, and content. New elements make sense in the context of the story."),
            RubricItem(score=5, description="Excellent continuity. Very aligned in theme, tone, and content. New elements make sense in the context of the story."),
        ],
        required_inputs=["previous_text"],
        required_output="current_text"
    )

    judge = FlowJudge(
        metric=continuity_metric,
        model=model
    )

    eval_input = EvalInput(
    inputs=[
        {"previous_text": previous_text}
    ],
    output={"current_text": current_text},
    )

    result = judge.evaluate(eval_input, save_results=False)

    return result.score, result.feedback