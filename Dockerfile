FROM tiangolo/meinheld-gunicorn-flask:python3.7

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY ./ikdoeaws /app

ENV PORT="8080"

EXPOSE 8080