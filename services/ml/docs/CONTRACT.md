# ML ↔ Backend Integration Contract

The ML service consumes one canonical internal backend surface under `/api/v1/ml`.

## Authentication

In production, requests include `X-Civitas-Internal-Key: <CIVITAS_INTERNAL_API_KEY>`. Development may omit it.

## Endpoints

### `POST /api/v1/ml/nearby-candidates`

Accepts report id, coordinates, timestamp, category, radius, time window and limit. Returns the standard Civitas success envelope whose `data` validates as `NearbyCandidatesResponse`.

### `GET /api/v1/ml/landmarks`

Returns the standard success envelope whose `data` validates as `LandmarkSet`.

### `GET /api/v1/ml/media/{media_id}`

Returns raw media bytes.

### `GET /api/v1/ml/media/{media_id}/metadata`

Returns the standard success envelope whose `data` validates as `MediaReference`.

The backend owns persistence and PostGIS. The ML layer owns model behavior and consumes only these contracts.
