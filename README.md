# Sequel API – Open Source Framework for GenAI APIs

Sequel API is built with FastAPI and is designed to be a simple and flexible framework for building GenAI APIs. From integrating authentication and usage metering to handling LLM observability, Sequel API provides a comprehensive set of tools to build and deploy GenAI APIs from day 1.

## Features

### Authentication
Clerk is used as the default auth platform in the demo application, but we have support any authentication provider that implements either JWKS / OpenID Connect specifications.

Sequel API builds in authentication integrations in order to more seamlessly meter usage and offer deeper observability.

### Usage Metering
Sequel API uses OpenMeter for usage metering, and is compatible with any metering backend that implements the OpenMeter API specifications. By default, Sequel API uses FastAPI middleware to meter FastAPI requests and OpenAI responses, and sends the data to OpenMeter.

#### FastAPI Request Metrics (per request, only metered for responses with status code >= 200 and < 300)
- Duration
- Request UUID
- User ID
- Request Path Pattern
- Request Method

#### OpenAI Chat Completion Metrics (per response)
- OpenAI Chat Completion Response ID
- Platform (OpenAI)
- Model
- Prompt Tokens
- Reasoning Tokens
- Completion Tokens
- Total Tokens
- FastAPI Request UUID

These metrics are piped into OpenMeter and are versatile enough to tie most GenAI API consumption to the underlying billing model.

### Observability (coming soon)
Soon, Sequel API will offer out-of-the-box observability with features to better understand and monitor the API's usage patterns.

## Getting Started
All environment variables are exemplified in `.env.example`.

## Environment Variables
The following environment variables should be set in your `.env` file:

### Authentication
- `CLERK_PUBLIC_URL`: The public URL for your Clerk authentication service.

### Usage Metering
- `OPENMETER_API_SECRET_TOKEN`: The secret token for authenticating with the OpenMeter API.

### OpenAI
- `OPENAI_API_KEY`: Your OpenAI API key for accessing OpenAI services.

### Database (optional, only needed for automated Beanie models)
- `MONGODB_CONN_STRING`: The connection string for your MongoDB database.

Make sure to set these variables with appropriate values in your `.env` file before running the application.

## Running the Application
```bash
# Generate the FastAPI build
python3 sequel.py build # this will soon become `sequel build` & the lib folder will be imported as a package

# Run the Sequel API application
fastapi run dist/src/main.py
```

## Folder Structure
Sequel API offers native path routing to make FastAPI development easier – for example, the `GET /airports/[iata_airport_code]` endpoint is implemented in `src/api/airports/[iata_airport_code]/route.py`. All `route.py` scripts should expose a `router: APIRouter` object that FastAPI can use to register the endpoint(s).

The `plan` endpoint in `src/api/airports/[iata_airport_code]/plan/route.py` offers a good example of how to implement a more complex endpoint that includes a nested router and includes a path parameter.