FROM 823367020558.dkr.ecr.us-east-1.amazonaws.com/kencologistics/codebase13@sha256:528f1e05bf119f3fe0327fb37e4e66fbedb6813a32da7bbefe1a19b11e2ca9f3


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