FROM library/python:3.6
ENV FAIRING_RUNTIME 1
RUN pip install fairing
COPY ./ /app/
RUN pip install --no-cache -r /app/requirements.txt
CMD python /app/knative-builder/main.py