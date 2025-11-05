# feathertree/tasks.py
from django.conf import settings
from celery import shared_task
from .models import Chapter
from .helpers import query_judge

@shared_task
def review_chapter(chapter_id):
    # Get chapter by ID
    try:
        chapter = Chapter.objects.get(pk=chapter_id)
    except Chapter.DoesNotExist:
        return 0, f"Chapter with ID {chapter_id} not found."

    previous_text = ""
    # Walk backward through linked chapters
    current = chapter
    while current.previous_chapter is not None:
        current = current.previous_chapter
        previous_text = current.content + "\n" + previous_text  # prepend previous content

    # Call LLM and generate score w/ feedback
    if settings.DEVELOPMENT_MODE is False:
        score, feedback = query_judge(previous_text, chapter.content)
    else:
        score = 3
        feedback = "Good stuff."

    # Mark as published (draft=False) if the score exceeds some threshold
    if score > 2:
        chapter.draft = False
    else:
        chapter.draft = True

    # Store score & feedback and indicate review is complete:
    chapter.score = score
    chapter.feedback = feedback
    chapter.submitted_for_review = False

    # Save the object:
    chapter.save()

    return score