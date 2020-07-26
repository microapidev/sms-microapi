FROM python:3

ENV PYTHONUNBUFFERED=1

RUN mkdir /myapp

# WORKDIR /code

# COPY . /code/

# RUN pip install -r requirements.txt --no-cache-dir

WORKDIR /myapp
COPY requirements.txt /myapp  
RUN pip install -r requirements.txt  
# RUN python manage.py makemigrations
RUN python manage.py migrate
RUN rm requirements.txt  

COPY . /myapp
WORKDIR /myapp
