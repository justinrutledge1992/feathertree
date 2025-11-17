# feathertree/tasks.py
from django.conf import settings
from celery import shared_task
from .models import Chapter
from .helpers import query_judge
import datetime
import logging

logger = logging.getLogger(__name__)

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
    if settings.DEVELOPMENT_MODE == False:
        try:
            score, feedback = query_judge(previous_text, chapter.content)
        except:
            logger.exception("Error in query_judge for chapter with ID: %s", chapter_id)
            score = 0
            feedback = "Error querying review system."
            chapter.submitted_for_review = False
            chapter.save()
    else:
        if chapter.content == "fail":
            score = 1
            feedback = "Terrible job!"
        else:
            score = 5
            feedback = "Great job!"

    # Mark as published (draft=False) if the score exceeds some threshold
    # And update the story last_updated field
    if score > 2:
        timestamp = datetime.date.today()
        chapter.draft = False
        chapter.timestamp = timestamp
        story = chapter.story
        story.last_updated = timestamp
        story.save()

    # Store score & feedback and indicate review is complete:
    chapter.score = score
    chapter.feedback = feedback
    chapter.submitted_for_review = False

    # Save the object:
    chapter.save()

    return score