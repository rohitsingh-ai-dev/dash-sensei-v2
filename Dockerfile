FROM 823367020558.dkr.ecr.us-east-1.amazonaws.com/kencologistics/codebase13@sha256:2d5f38b1638663162182bb38aea7bbdb3c51ccda2c19d396c18e141ad8ad1ff8


COPY ./requirements.txt /app/requirements.txt
RUN uv pip install --system -r /app/requirements.txt
# RUN pip install Jinja2==2.11.3 # This will cause a pip conflict with Prefect -- it seems to not cause issue, however.

COPY ./ /app
WORKDIR /app

## Setup prod indicators
ARG PROD_FLAG
ENV DAVINCI_PROD=$PROD_FLAG

# Prod command
CMD ["gunicorn", "app:server", "--workers=1", "--timeout", "1000", "--capture-output", "--bind", "0.0.0.0:80"]