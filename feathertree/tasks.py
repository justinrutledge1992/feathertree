# feathertree/tasks.py
from celery import shared_task
from .models import Chapter
import time

@shared_task
def divide(x, y):
    time.sleep(1)
    return x / y

@shared_task
def review_chapter(chapter_id):
    # Get chapter by ID
    try:
        chapter = Chapter.objects.get(pk=chapter_id)
    except Chapter.DoesNotExist:
        return 0, f"Chapter with ID {chapter_id} not found."
    
    content = chapter.content
    score = 0
    feedback = ""

    # Call LLM and generate score w/ feedback
    # This is just placeholder code for now...
    if len(content) > 20:
        score = 10
        feedback = "Great stuff! A true masterpiece."
    else:
        score = 1
        feedback = "way too short. Try again."

    # Mark as published (draft=False) if the score exceeds some threshold
    if score > 5:
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