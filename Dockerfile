FROM wbuchwalter/metaml

COPY ./ /app/
RUN pip install --no-cache -r /app/requirements.txt

CMD python /app/testmp.py
