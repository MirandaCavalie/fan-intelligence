# FanIQ API Contracts

Core endpoints:

- `GET /health`
- `POST /scan`
- `GET /scan/{job_id}`
- `GET /fans/{creator_handle}`
- `GET /fan/{creator_handle}/{fan_handle}`
- `POST /vapi/llm`
- `POST /publish/{creator_handle}`

Redis keys:

- `fans:{creator}`
- `fan_profile:{creator}:{fan}`
- `events:{creator}`
- `scan:{job_id}`
- `scan_events:{job_id}`
- `publish:{creator}`
- `sponsor_trace:{creator}`
