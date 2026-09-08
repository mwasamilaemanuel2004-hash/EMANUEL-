web: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000}
worker: celery -A app.tasks worker --loglevel=info --concurrency=4
beat: celery -A app.tasks beat --loglevel=info
release: echo "Deployment complete"
