# Usage Guide

## Send a request

1. Open **Request Lab**.
2. Select an HTTP method.
3. Enter the target URL.
4. Add JSON headers when required.
5. Add a JSON or raw body for methods that need one.
6. Click **Send Request**.
7. Inspect status, response time, response size and response content.

## Save a request

Give the request a name and save it to the collection. Saved requests can be loaded later without rebuilding the request manually.

## Use environments

Create an environment and add reusable variables.

Example:

```text
base_url = https://httpbin.org
token = example-token
```

Use:

```text
{{base_url}}/get
```

or:

```json
{
  "Authorization": "Bearer {{token}}"
}
```

## Inspect responses

The response inspector provides:

- Pretty JSON/text view
- Raw response view
- Response headers
- HTTP status
- Response duration
- Response size

## Generate cURL

After preparing a request, use the cURL generator to create a command that can be copied into a terminal.

## Export data

Use the export function to download saved requests, history and environments as JSON.
