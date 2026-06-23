$ErrorActionPreference = "Stop"

function Read-DotEnv {
  param([string]$Path)
  $values = @{}
  if (-not (Test-Path $Path)) {
    throw "Missing env file: $Path"
  }
  Get-Content -Path $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) {
      return
    }
    $parts = $line.Split("=", 2)
    if ($parts.Count -ne 2) {
      return
    }
    $name = $parts[0].Trim()
    $value = $parts[1].Trim().Trim('"').Trim("'")
    $values[$name] = $value
  }
  return $values
}

function Resolve-LocalPath {
  param([string]$Path)
  if ($Path.StartsWith("~")) {
    return (Join-Path $HOME $Path.Substring(2))
  }
  return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$envValues = Read-DotEnv -Path ".env"
$required = @("DEPLOY_HOST", "DEPLOY_USER", "DEPLOY_PATH", "SSH_KEY")
foreach ($name in $required) {
  if (-not $envValues.ContainsKey($name) -or -not $envValues[$name]) {
    throw "Missing required .env value: $name"
  }
}

$deployHost = $envValues["DEPLOY_HOST"]
$deployUser = $envValues["DEPLOY_USER"]
$deployPath = $envValues["DEPLOY_PATH"]
$sshKey = Resolve-LocalPath $envValues["SSH_KEY"]
$sshTarget = "$deployUser@$deployHost"
$archive = Join-Path $env:TEMP ("shadowgen-realtime-" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + ".tar.gz")
$remoteArchive = "$deployPath/shadowgen-realtime.tar.gz"

if (-not (Test-Path $sshKey)) {
  throw "SSH key not found: $sshKey"
}

Write-Host "Packaging realtime service..."
tar -czf $archive `
  pyproject.toml `
  requirements.txt `
  README.md `
  apps/api/src `
  apps/realtime `
  apps/worker/src `
  packages

Write-Host "Preparing remote path $deployPath..."
$prepareRemote = @"
set -eu
DEPLOY_PATH='$deployPath'
DEPLOY_USER='$deployUser'
if [ -d "`$DEPLOY_PATH" ]; then
  exit 0
fi
if mkdir -p "`$DEPLOY_PATH" 2>/dev/null; then
  exit 0
fi
if command -v sudo >/dev/null 2>&1; then
  sudo -n mkdir -p "`$DEPLOY_PATH"
  sudo -n chown "`$DEPLOY_USER:`$DEPLOY_USER" "`$DEPLOY_PATH"
  exit 0
fi
echo "Cannot create `$DEPLOY_PATH. Create it manually or allow passwordless sudo." >&2
exit 1
"@
($prepareRemote -replace "`r`n", "`n") | ssh -i $sshKey $sshTarget "tr -d '\r' | bash -s"

Write-Host "Uploading package..."
scp -i $sshKey $archive "${sshTarget}:${remoteArchive}"

$remoteScript = @"
set -eu

DEPLOY_PATH='$deployPath'
IMAGE_NAME='shadowgen-realtime:latest'
CONTAINER_NAME='shadowgen-realtime'

secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'
  fi
}

cd "`$DEPLOY_PATH"
if docker ps >/dev/null 2>&1; then
  USE_SUDO_DOCKER=0
elif command -v sudo >/dev/null 2>&1 && sudo -n docker ps >/dev/null 2>&1; then
  USE_SUDO_DOCKER=1
else
  echo "Docker is not available for this user. Add the user to the docker group or allow passwordless sudo." >&2
  exit 1
fi

dockercmd() {
  if [ "`$USE_SUDO_DOCKER" = "1" ]; then
    sudo -n docker "`$@"
  else
    docker "`$@"
  fi
}

rm -rf src
mkdir -p src
tar -xzf shadowgen-realtime.tar.gz -C src

if [ ! -f .env.realtime ]; then
  umask 077
  cat > .env.realtime <<EOF
APP_ENV=prod
PORT=8082
VPS_PUBLIC_BASE_URL=http://$deployHost:8082
VPS_INTERNAL_TOKEN=`$(secret)
WORKER_VPS_TOKEN=`$(secret)
VPS_REALTIME_SIGNING_SECRET=`$(secret)
ALLOWED_ORIGINS=https://shadowgen.solofarm.ru,http://localhost:3000,http://127.0.0.1:3000
EVENT_RETENTION_SEC=300
HEARTBEAT_INTERVAL_SEC=15
EOF
fi

dockercmd build -f src/apps/realtime/Dockerfile -t "`$IMAGE_NAME" src
dockercmd rm -f "`$CONTAINER_NAME" >/dev/null 2>&1 || true
dockercmd run -d \
  --name "`$CONTAINER_NAME" \
  --restart unless-stopped \
  --env-file "`$DEPLOY_PATH/.env.realtime" \
  -p 8082:8082 \
  "`$IMAGE_NAME"

dockercmd ps --filter "name=`$CONTAINER_NAME"
for attempt in `$(seq 1 20); do
  if curl -fsS 'http://127.0.0.1:8082/health' 2>/dev/null; then
    exit 0
  fi
  sleep 1
done
echo "Realtime health check did not pass." >&2
exit 1
"@

Write-Host "Building and restarting remote container..."
($remoteScript -replace "`r`n", "`n") | ssh -i $sshKey $sshTarget "tr -d '\r' | bash -s"

Remove-Item -LiteralPath $archive -Force
Write-Host "Realtime service deployed to $($sshTarget):$deployPath"
