podman build -t matcher:latest .

podman run \
  -d \
  --name matcher \
  --device nvidia.com/gpu=all \
  -v ".env:/app/.env" \
  matcher:latest \
  python3 -u runner.py
