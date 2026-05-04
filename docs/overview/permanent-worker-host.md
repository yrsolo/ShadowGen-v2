# Permanent Worker Host

This guide is for moving `apps/worker` to another computer and keeping it running there in Docker.

The intended production shape is:

```text
public web/api in Yandex Cloud -> YMQ + Object Storage -> Docker worker on your always-on machine -> local ML service
```

## 1. Prepare The Computer

Install:

- Git
- Docker Desktop on Windows, or Docker Engine on Linux
- access to the ML service from this computer

Clone the repository:

```powershell
git clone <repo-url> ShadowGen-v2
cd ShadowGen-v2
```

If the ML service runs on the same Windows Docker Desktop host, make sure it listens on the host and is reachable as:

```text
http://host.docker.internal:9001
```

If the ML service runs on another LAN machine, use its LAN IP, for example:

```text
http://192.168.1.5:9001
```

If you prefer a hostname such as `http://gtx6:9001`, verify that the Docker container can resolve it. If jobs fail with:

```text
[Errno -5] No address associated with hostname
```

either use the LAN IP directly in `LEGACY_ML_BASE_URL` or set:

```dotenv
LEGACY_ML_BASE_URL=http://gtx6:9001
LEGACY_ML_HOST_IP_OVERRIDE=192.168.1.5
```

The worker Docker scripts pass that mapping to Docker as `--add-host gtx6:192.168.1.5`.

## 2. Create `.env.shadowgen`

Copy the template:

```powershell
copy .env.shadowgen.example .env.shadowgen
```

Open `.env.shadowgen` and fill:

- `S3_BUCKET`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `YMQ_QUEUE_URL`
- `LEGACY_ML_BASE_URL`
- `LEGACY_ML_HOST_IP_OVERRIDE`, only if the Docker container cannot resolve the ML hostname
- `WORKER_CONTROL_TOKEN`

For production, keep:

```dotenv
APP_ENV=prod
STATE_BACKEND=s3
QUEUE_BACKEND=ymq
S3_ENDPOINT_URL=https://storage.yandexcloud.net
YMQ_ENDPOINT=https://message-queue.api.cloud.yandex.net
S3_REGION=ru-central1
YMQ_REGION=ru-central1
S3_PREFIX=shadowgen-v2
WORKER_SELF_MANAGE_ENABLED=false
```

The Yandex static access key must be allowed to read/write the Object Storage bucket and consume/delete messages from the YMQ queue.

Do not commit `.env.shadowgen`.

### ML URL Priority

The worker chooses the ML URL in this order:

1. runtime override stored in Object Storage at `S3_PREFIX/runtime/config.json`
2. `LEGACY_ML_BASE_URL` from `.env.shadowgen`

This means editing `.env.shadowgen` is not enough if an old runtime override was previously saved from the web engineering panel or worker control flow.

After changing `LEGACY_ML_BASE_URL`, check the worker UI field:

```text
Effective ML URL
```

If it still shows the old address:

1. press `Clear ML override` in the worker control UI
2. press `Restart process`, or restart the container

From PowerShell, the equivalent cloud action is:

```powershell
Invoke-RestMethod https://api.shadowgen.solofarm.ru/v1/system/worker-actions `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"action":"clear_runtime_override"}'
```

## 3. Start The Always-On Docker Worker

Run:

```powershell
scripts\run-worker-cloud-container-detached.cmd
```

The script:

- builds `shadowgen-worker-local` from the current checkout
- starts container `shadowgen-worker` in detached mode
- uses `--restart unless-stopped`
- loads runtime settings from `.env.shadowgen`
- publishes the worker control UI on `WORKER_CONTROL_HOST_PORT`
- does not mount the repository
- does not mount Docker socket
- disables in-UI self-update/rebuild actions

Check the container:

```powershell
docker ps --filter "name=shadowgen-worker"
docker logs -f shadowgen-worker
```

Open the local control UI:

```text
http://localhost:8081
```

Or from another machine on the LAN:

```text
http://<worker-host-ip>:8081
```

## 4. Verify It Is Connected

Check JSON status:

```powershell
Invoke-RestMethod http://localhost:8081/api/status | ConvertTo-Json -Depth 6
```

The status should show:

- storage backend `s3`
- queue backend `ymq`
- an effective ML URL matching `LEGACY_ML_BASE_URL`
- fresh worker heartbeat/state after the loop starts

Then submit a render from:

```text
https://shadowgen.solofarm.ru
```

The worker should consume the job from YMQ, call the ML service, and write the result back to Object Storage.

## 5. Update The Worker Later

On the worker host:

```powershell
git pull
scripts\run-worker-cloud-container-detached.cmd
```

The script removes the previous `shadowgen-worker` container, rebuilds the image, and starts a new detached container with the same restart policy.

## 6. Stop Or Restart

Stop:

```powershell
docker stop shadowgen-worker
```

Start again without rebuilding:

```powershell
docker start shadowgen-worker
```

Rebuild and restart from repo code:

```powershell
scripts\run-worker-cloud-container-detached.cmd
```

## 7. When To Use Self-Managed Mode

The normal permanent host should use `scripts\run-worker-cloud-container-detached.cmd`.

Use `scripts\run-worker-cloud-container-self-managed.cmd` only when you explicitly accept both of these risks:

- the repository is bind-mounted into the container
- Docker socket is mounted into the container, giving it host-level Docker control

That mode is useful for operator experiments with in-UI git update/rebuild controls. It is not the recommended always-on production mode.
