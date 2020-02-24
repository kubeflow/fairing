#This container contains your model and any helper scripts specific to your model.
# When building the image inside mnist.ipynb the base docker image will be overwritten
FROM tensorflow/tensorflow:1.15.2-py3

ADD mnist.py /opt/mnist.py
RUN chmod +x /opt/mnist.py

ENTRYPOINT ["/usr/bin/python"]
CMD ["/opt/mnist.py"]
