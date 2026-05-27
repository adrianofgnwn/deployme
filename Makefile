# DeployMe — common developer commands.
.DEFAULT_GOAL := help
.PHONY: help install dev dev-backend dev-frontend seed reset-db docker-up docker-down audit

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev: ## Start backend and frontend dev servers (needs two terminals; see dev-backend / dev-frontend)
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals,"
	@echo "or use 'make docker-up' to run the full stack in Docker."

dev-backend: ## Run the FastAPI backend with autoreload
	cd backend && uvicorn main:app --reload --port $${BACKEND_PORT:-8000}

dev-frontend: ## Run the Vite frontend dev server
	cd frontend && npm run dev

seed: ## Load seed job listings into ChromaDB (Phase 1+)
	cd backend && python -m scripts.seed

reset-db: ## Delete the local ChromaDB store
	rm -rf backend/chroma_data && echo "ChromaDB store cleared."

docker-up: ## Build and start the full stack with Docker Compose
	docker compose up --build

docker-down: ## Stop the Docker Compose stack
	docker compose down

audit: ## Check Python dependencies for known vulnerabilities
	cd backend && pip install pip-audit && pip-audit -r requirements.txt
