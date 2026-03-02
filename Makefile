.PHONY: help install setup start stop clean logs backend-start frontend-start backend-logs frontend-logs test

help:
	@echo "Infinite Story - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        - Install dependencies for both frontend and backend"
	@echo "  make setup          - Full setup (install + create .env if needed)"
	@echo ""
	@echo "Running:"
	@echo "  make start          - Start both backend and frontend (in parallel)"
	@echo "  make backend-start  - Start backend only (port 8000)"
	@echo "  make frontend-start - Start frontend only (port 5173)"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs           - View logs from all running processes"
	@echo "  make backend-logs   - View backend logs only"
	@echo "  make frontend-logs  - View frontend logs only"
	@echo ""
	@echo "Cleanup:"
	@echo "  make stop           - Stop all running processes"
	@echo "  make clean          - Remove node_modules, venv, and stop processes"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run backend tests"
	@echo ""

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ Dependencies installed"

setup: install
	@if [ ! -f backend/.env ]; then \
		echo "Creating backend/.env from .env.example..."; \
		cp backend/.env.example backend/.env; \
		echo "⚠ Please update backend/.env with your API keys"; \
	fi
	@echo "✓ Setup complete"

start: backend-start frontend-start
	@echo ""
	@echo "==============================================="
	@echo "Infinite Story is running!"
	@echo "==============================================="
	@echo ""
	@echo "Backend (API):  http://localhost:8000"
	@echo "Frontend (UI):  http://localhost:5173"
	@echo "Docs:           http://localhost:8000/docs"
	@echo ""
	@echo "Press Ctrl+C to stop"
	@echo ""
	@sleep 2
	@wait

backend-start:
	@echo "Starting backend (port 8000)..."
	cd backend && source venv/bin/activate && PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload > /tmp/infinite_story_backend.log 2>&1 &
	@sleep 2
	@echo "✓ Backend started"

frontend-start:
	@echo "Starting frontend (port 5173)..."
	cd frontend && npm run dev > /tmp/infinite_story_frontend.log 2>&1 &
	@sleep 3
	@echo "✓ Frontend started"

stop:
	@echo "Stopping all processes..."
	@pkill -f "uvicorn.*infinite" || true
	@pkill -f "vite" || true
	@sleep 1
	@echo "✓ All processes stopped"

backend-logs:
	@tail -f /tmp/infinite_story_backend.log

frontend-logs:
	@tail -f /tmp/infinite_story_frontend.log

logs:
	@echo "Backend logs (Ctrl+C to switch):"
	@tail -f /tmp/infinite_story_backend.log &
	@echo "Frontend logs:"
	@tail -f /tmp/infinite_story_frontend.log

clean: stop
	@echo "Cleaning up..."
	@rm -rf backend/venv backend/__pycache__ backend/.pytest_cache
	@rm -rf frontend/node_modules frontend/dist
	@rm -f /tmp/infinite_story_*.log
	@echo "✓ Cleanup complete"

test:
	@echo "Running backend tests..."
	cd backend && source venv/bin/activate && python -m pytest -v

.PHONY: start stop clean install setup help backend-start frontend-start backend-logs frontend-logs logs test
