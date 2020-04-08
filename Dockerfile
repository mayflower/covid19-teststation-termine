FROM python:3.7-slim-buster as base

FROM base as base_pipenv

RUN pip install pipenv
COPY termine-be/Pipfile .
COPY termine-be/Pipfile.lock .
RUN pipenv lock --requirements > requirements.txt
RUN pipenv lock --dev --requirements > dev_requirements.txt

FROM base as base_python
WORKDIR /app

COPY --from=base_pipenv requirements.txt .
RUN pip install -r requirements.txt

# FROM base_python as tester
# COPY --from=base_pipenv dev_requirements.txt .
# RUN pip install -r dev_requirements.txt
# COPY src/* ./src/
# ENTRYPOINT ["pytest", "./src/"]

FROM node:13 as yarn_fe_installer
WORKDIR /app
COPY termine-fe/package.json .
COPY termine-fe/yarn.lock .
RUN yarn install

FROM yarn_fe_installer as yarn_fe_builder
COPY termine-fe/src src/
COPY termine-fe/public public/
RUN yarn build
# for debugging
CMD bash

FROM node:13 as yarn_bo_installer
WORKDIR /app
COPY termine-bo/package.json .
COPY termine-bo/yarn.lock .
RUN yarn install

FROM yarn_bo_installer as yarn_bo_builder
COPY termine-bo/src src/
COPY termine-bo/public public/
ENV PUBLIC_URL "/admin"
RUN yarn build
# for debugging
CMD bash

FROM base_python as base_server
RUN pip install gunicorn

FROM base as deployer
RUN pip install awscli
COPY cloudformation/ cloudformation/
CMD bash

FROM base_server as server
COPY termine-be/ .
COPY --from=yarn_fe_builder /app/build/ build_fe/
COPY --from=yarn_bo_builder /app/build/ build_bo/
ENV FE_STATICS_DIR "build_fe"
ENV BO_STATICS_DIR "build_bo"
CMD ["gunicorn", "--bind=0.0.0.0:8000", "main:__hug_wsgi__"]