# Backend API Reference

The Flask backend exposes a small JSON API used by the dashboard.

## `POST /api/send`

Execute an HTTP request.

Typical payload:

```json
{
  "method": "GET",
  "url": "https://httpbin.org/get",
  "headers": {},
  "body": ""
}
```

The backend resolves `{{variable}}` placeholders using saved environments before making the request.

The response includes request/result information such as HTTP status, response time, response size and response content.

## `GET /api/saved`

Returns saved requests.

## `POST /api/saved`

Stores a request in the local SQLite database.

## `DELETE /api/saved/<id>`

Deletes one saved request.

## `GET /api/history`

Returns recent request history.

## `DELETE /api/history`

Clears request history.

## `GET /api/env`

Returns configured environments.

## `POST /api/env`

Creates or updates an environment.

## `GET /api/export`

Returns application data as JSON for backup/export purposes.

> These endpoints are designed for the local dashboard. If you deploy the application remotely, add authentication and authorization before exposing them publicly.
