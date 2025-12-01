# Python Simulation of Flip7 Game

Motivation:
- Applying best practices: Logging, Testing, Pydantic, Code quality, etc.
- Coding Experience
- Deployment Practice
- Basis for RL Training

Requirements:
- [X] Fully functional interactive flip7 game round
- [X] Play GameRounds until first player reaches 200 points
- [X] Different Player types: Interactive vs. simple AI
- [X] Object oriented programming
- [X] Pydantic strong typing
- [X] Logging System
- [X] Pytest Test Suite
- [ ] Train RL policy on as Player
- [X] Create simple local server
- [X] Deploy to local podman docker container (playable over wifi)
- [ ] Deploy to remote container (Google cluster?)

# Quick local development setup
Prerequisite: uv Python package manager
1. $ uv sync
2. $ uv run python flip7.py
3. $ uv run pytest -v


# Server deployment
## Simple local server
1. Terminal 1: $ uv run uvicorn server:app --port 8000
2. Terminal 2: $ curl http://localhost:8000

## Run wifi internally
1. Macbook Terminal: $ uv run uvicorn server:app --host 0.0.0.0 --port 8000
2. Find macbook ip address: ipconfig getifaddr en0
3. Smartphone Browser search ip-address: <LOCAL_MACHINE_IP>:8000

## Deploy to local podman container. Wifi internal access
0. Create podman VM (=1.1GB): $ podman machine init
0. podman machine start
1. Build image: $ podman build -t flip7-game .
2. Run container: $ podman run -d -p 8000:8000 flip7-game

This makes API available at:
- local machine: http://localhost:8000
- Other devices in Wifi: http://LOCAL_MACHINE_IP:8000

## Stop podman container
1. Find running container id: $ podman ps
2. $ podman stop <container_id>
3. $ podman machine stop

