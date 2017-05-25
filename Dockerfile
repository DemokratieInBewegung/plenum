FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD ./voty /code/voty
ADD ./templates /code/templates
ADD ./static /code/static
ADD ./scripts /code/scripts