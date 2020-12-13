# create docker image, if needed
FROM rackspacedot/python37
COPY . pybroker
WORKDIR pybroker
RUN python3 -m pip install -r requirements.txt
EXPOSE 8080
CMD ["gunicorn", "--bind=0.0.0.0:8080", "-c", "gunicorn.py", "broker:app"]
