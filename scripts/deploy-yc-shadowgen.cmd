@echo off
setlocal

cd /d "%~dp0.."

echo [ShadowGen] Build and push images first if needed.
echo [ShadowGen] Deploy API gateway:
yc serverless api-gateway update --name shadowgen-api-gw --spec infra/yc/api-gateway.shadowgen-api.yaml
echo [ShadowGen] Deploy Web gateway:
yc serverless api-gateway update --name shadowgen-web-gw --spec infra/yc/api-gateway.shadowgen-web.yaml

