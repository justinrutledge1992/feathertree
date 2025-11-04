# start_feathertree.ps1 — run from your project folder
# this works to launch a Redis, a Celery worker, and the Web service / database
# Docker Redis Image must be installed and running for this to work
$workDir  = (Get-Location).Path

# Celery Worker in a CMD tab
wt -w 0 new-tab -d "$workDir" --title "Celery" -p "Command Prompt" `
  cmd /k "call .\venv\Scripts\activate && celery -A feathertree_project worker -l info -P solo"

# Flower in a CMD tab
wt -w 0 new-tab -d "$workDir" --title "Flower" -p "Command Prompt" `
  cmd /k "call .\venv\Scripts\activate && celery -A feathertree_project flower --port=5555"

# Django in a CMD tab
wt -w 0 new-tab -d "$workDir" --title "Django" -p "Command Prompt" `
  cmd /k "call .\venv\Scripts\activate && python manage.py runserver"
