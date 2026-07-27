FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY invoicepdf ./invoicepdf
COPY web ./web
COPY wsgi.py ./
RUN useradd --system --create-home app && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["gunicorn", "--bind=0.0.0.0:8000", "wsgi:app"]
