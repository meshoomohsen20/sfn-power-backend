# SFN Power Backend

Upload-ready, configuration-only backend scaffold for the MTTL-W01 smart power strip project. It stores four user-defined outlet names in SQLite. **It does not connect to a strip, provision Wi-Fi, read telemetry, or switch relays.** The device adapter is intentionally disabled.

## Verified protocol and safety boundary

The strongest source found is [MTTL Control](https://github.com/AmrEmad0/MTTL-W01_APP), an open-source reverse-engineered controller for LG U+/TONLY MTTL-W01. Its protocol guide and earlier Python controller document the following:

- Provisioning is performed while connected to the strip's setup Wi-Fi, using TCP port `30300` and text commands. It stores the controller's **IPv4 address** in the strip.
- On normal operation, the strip initiates a TCP connection to the configured controller on port `10086`.
- Runtime messages are UTF-8 text lines terminated by CRLF; the tested firmware may NUL-pad transmissions.
- The documented protocol is plaintext and has no verified cryptographic authentication or TLS. The source's primary tested firmware is `0.1.54-1.0.66`; other firmware may differ.

The previous conversation mentioned `powerk`; searches did not identify a protocol source by that name. The source verified here is the MTTL Control project and its `power_d.py` reference implementation. Treat any different `powerk` link or device firmware as unverified until checked against its actual source and a physical strip.

The reference implementation is useful evidence, but this scaffold does not copy its relay-control code. The device protocol gives a remote peer no cryptographic identity, so an Internet-facing listener could accept forged device messages and commands. Do not create a public TCP route to port `10086` yet. A future adapter needs an explicit trust design, address/ownership binding, strict parser and connection limits, replay/command handling decisions, and real-device validation. Provisioning to a cloud endpoint also requires a stable IPv4 address reachable by the strip; DNS alone is not sufficient for the documented `up:ip:` provisioning field.

## API

All API routes require `Authorization: Bearer <API_TOKEN>`.

- `GET /healthz` — basic process health; reports that device control is disabled.
- `GET /api/outlets` — return the four configured labels.
- `PUT /api/outlets` — replace all four labels atomically.

Example request body:

```json
{
  "outlets": [
    {"name": "Router"},
    {"name": "Desk"},
    {"name": "Lamp"},
    {"name": "Spare"}
  ]
}
```

For local development, set a long random `API_TOKEN` and start `uvicorn main:app --host 127.0.0.1 --port 8080`. The API listens on the configured `PORT` inside the container. SQLite lives at `/data/config.sqlite3` by default.

## Deploy on Northflank

1. Upload these files to the empty GitHub repository and create its first commit on `main`.
2. In Northflank, create a **Service** from that GitHub repository and select Dockerfile build, using the repository root.
3. Configure one HTTP service port: container port `8080`, protocol **HTTP**, accessibility **Private**. The API includes a health route at `/healthz`. Do not expose the API publicly without adding and reviewing an authentication/access policy.
4. Add a persistent volume mounted at `/data` so the four labels survive redeployments. The service runs as an unprivileged user; ensure the mounted volume is writable by the container user or select a volume setting that permits writes.
5. Add `API_TOKEN` as a Northflank secret (generate your own long random value; do not commit it). Set `DATA_DIR=/data` and `PORT=8080` as needed.
6. Deploy and use Northflank's local port-forwarding feature to reach the private HTTP port while configuring it. Keep the token secret.

### TCP ingress for a future device adapter

Northflank's ordinary service ports do not provide public TCP ingress. Its current documentation says arbitrary TCP service ports are private/internal; Internet TCP requires a separate Layer 4 load balancer. Do not configure that load balancer for this scaffold: there is no device listener in this project. If a future reviewed adapter is added, the documented device side expects TCP `10086`; confirm that your Northflank account/region can provision a stable public Layer 4 address and configure the device with that reachable IPv4. Reassess the plaintext, unauthenticated protocol exposure before attaching it to the Internet.

## Evidence and references

- [MTTL Control source repository and README](https://github.com/AmrEmad0/MTTL-W01_APP)
- [Protocol guide](https://github.com/AmrEmad0/MTTL-W01_APP/blob/main/MTTL_CONTROLLER_PROTOCOL_GUIDE.md)
- [Earlier Python reference controller](https://github.com/AmrEmad0/MTTL-W01_APP/blob/main/power_d.py)
- [Northflank: Configure ports](https://northflank.com/docs/v1/application/network/configure-ports)
- [Northflank: Configure load balancers](https://northflank.com/docs/v1/application/network/configure-load-balancers)
- [Northflank: Forwarding](https://northflank.com/docs/v1/api/forwarding)

This is an independent scaffold and is not affiliated with LG U+, TONLY, or the reference project.
