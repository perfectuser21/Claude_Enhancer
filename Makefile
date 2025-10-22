# =============================================================================
# Claude Enhancer 5.1 - Docker Operations Makefile
# Simplified commands for development and deployment
# =============================================================================

.PHONY: help build dev prod deploy health test clean backup rollback logs

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_NAME := claude-enhancer
VERSION := 1.0.0
COMPOSE_FILE := docker-compose.yml
COMPOSE_DEV_FILE := docker-compose.dev.yml
ENV_FILE := .env

# Colors
RED    := \033[31m
GREEN  := \033[32m
YELLOW := \033[33m
BLUE   := \033[34m
RESET  := \033[0m

# Help target
help: ## Show this help message
	@echo "$(BLUE)Claude Enhancer 5.1 - Docker Operations$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(RESET)"
	@cp -n .env.example .env 2>/dev/null || true
	@docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) up -d
	@echo "$(GREEN)Development environment started$(RESET)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8001"
	@echo "API Docs: http://localhost:8001/docs"
	@echo "pgAdmin: http://localhost:5050"

dev-build: ## Build and start development environment
	@echo "$(BLUE)Building development environment...$(RESET)"
	@docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) up -d --build

dev-logs: ## Show development logs
	@docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) logs -f

dev-stop: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(RESET)"
	@docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) down

# Production commands
prod: ## Start production environment
	@echo "$(BLUE)Starting production environment...$(RESET)"
	@./scripts/deploy.sh deploy

prod-build: ## Build production images
	@echo "$(BLUE)Building production images...$(RESET)"
	@./scripts/build.sh all

prod-stop: ## Stop production environment
	@echo "$(YELLOW)Stopping production environment...$(RESET)"
	@docker-compose down

# Build commands
build: ## Build all images
	@echo "$(BLUE)Building all images...$(RESET)"
	@./scripts/build.sh all

build-backend: ## Build backend image only
	@./scripts/build.sh backend

build-frontend: ## Build frontend image only
	@./scripts/build.sh frontend

build-cache: ## Build with cache optimization
	@./scripts/build.sh cache

# Health and monitoring
health: ## Run health checks
	@echo "$(BLUE)Running health checks...$(RESET)"
	@./scripts/health-check.sh all

health-backend: ## Check backend health
	@./scripts/health-check.sh backend

health-frontend: ## Check frontend health
	@./scripts/health-check.sh frontend

health-db: ## Check database health
	@./scripts/health-check.sh database

health-redis: ## Check Redis health
	@./scripts/health-check.sh redis

# Testing commands
test: ## Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	@docker-compose exec backend python -m pytest tests/ -v
	@docker-compose exec frontend npm test

test-backend: ## Run backend tests
	@docker-compose exec backend python -m pytest tests/ -v

test-frontend: ## Run frontend tests
	@docker-compose exec frontend npm test

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	@./scripts/health-check.sh all
	@curl -f http://localhost:8000/health
	@curl -f http://localhost:80/health

# Database operations
db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	@docker-compose exec backend alembic upgrade head

db-backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(RESET)"
	@./scripts/deploy.sh backup

db-restore: ## Restore database from backup
	@echo "$(YELLOW)Restoring database...$(RESET)"
	@./scripts/deploy.sh rollback

# Monitoring commands
monitor: ## Start monitoring services
	@echo "$(BLUE)Starting monitoring services...$(RESET)"
	@docker-compose --profile monitoring up -d
	@echo "$(GREEN)Monitoring started$(RESET)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001"

monitor-stop: ## Stop monitoring services
	@docker-compose --profile monitoring down

# Maintenance commands
logs: ## Show all logs
	@docker-compose logs -f

logs-backend: ## Show backend logs
	@docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	@docker-compose logs -f frontend

logs-db: ## Show database logs
	@docker-compose logs -f database

logs-redis: ## Show Redis logs
	@docker-compose logs -f cache

clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(RESET)"
	@docker-compose down --remove-orphans
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)Cleanup completed$(RESET)"

deep-clean: ## Deep clean (remove images, volumes, networks)
	@echo "$(RED)Deep cleaning Docker resources...$(RESET)"
	@docker-compose down --remove-orphans --volumes
	@docker system prune -af --volumes
	@echo "$(GREEN)Deep cleanup completed$(RESET)"

# Deployment commands
deploy: ## Deploy to production
	@./scripts/deploy.sh deploy

rollback: ## Rollback deployment
	@echo "$(YELLOW)Rolling back deployment...$(RESET)"
	@./scripts/deploy.sh rollback

backup: ## Create deployment backup
	@./scripts/deploy.sh backup

# Utility commands
shell-backend: ## Open shell in backend container
	@docker-compose exec backend bash

shell-frontend: ## Open shell in frontend container
	@docker-compose exec frontend sh

shell-db: ## Open PostgreSQL shell
	@docker-compose exec database psql -U claude_user -d claude_enhancer

shell-redis: ## Open Redis shell
	@docker-compose exec cache redis-cli

# Security commands
security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(RESET)"
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD):/tmp/app --workdir /tmp/app \
		clair-scanner:latest --ip $(shell hostname -I | cut -d' ' -f1) \
		$(PROJECT_NAME)-backend:latest || true
	@echo "$(GREEN)Security scan completed$(RESET)"

# Performance commands
performance: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(RESET)"
	@./scripts/build.sh performance

# Status commands
status: ## Show service status
	@echo "$(BLUE)Service Status:$(RESET)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)Resource Usage:$(RESET)"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Environment commands
env-check: ## Check environment configuration
	@echo "$(BLUE)Checking environment configuration...$(RESET)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(YELLOW)Warning: .env file not found, copying from .env.example$(RESET)"; \
		cp .env.example .env; \
		echo "$(YELLOW)Please update .env file with your values$(RESET)"; \
	else \
		echo "$(GREEN).env file found$(RESET)"; \
	fi

env-example: ## Create .env from example
	@cp .env.example .env
	@echo "$(GREEN).env file created from example$(RESET)"

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	@docker-compose exec backend python -c "
import subprocess
subprocess.run(['python', '-m', 'pydoc', '-w', '.'])
"
	@echo "$(GREEN)Documentation generated$(RESET)"

# Quick start command
quickstart: env-check dev health ## Quick start development environment
	@echo "$(GREEN)Quick start completed!$(RESET)"
	@echo "$(BLUE)Next steps:$(RESET)"
	@echo "1. Open http://localhost:3000 for frontend"
	@echo "2. Open http://localhost:8001/docs for API documentation"
	@echo "3. Use 'make logs' to view logs"
	@echo "4. Use 'make dev-stop' to stop services"

# All-in-one production deployment
prod-deploy: env-check prod-build deploy health monitor ## Complete production deployment
	@echo "$(GREEN)Production deployment completed!$(RESET)"
# =============================================================================
# Dual-Language Checklist System (v7.1.0)
# =============================================================================

.PHONY: checklist checklist-validate checklist-report checklist-clean checklist-test checklist-help

checklist-help: ## Show checklist system help
	@echo "$(BLUE)Claude Enhancer 7.1.0 - Dual-Language Checklist System$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available checklist commands:$(RESET)"
	@echo "  $(GREEN)checklist$(RESET)          - Generate dual-language checklists from user_request.md"
	@echo "  $(GREEN)checklist-validate$(RESET) - Validate checklist mapping consistency"
	@echo "  $(GREEN)checklist-report$(RESET)   - Generate acceptance report"
	@echo "  $(GREEN)checklist-clean$(RESET)    - Remove all generated checklist files"
	@echo "  $(GREEN)checklist-test$(RESET)     - Test complete checklist flow"
	@echo ""
	@echo "Example workflow:"
	@echo "  1. make checklist          # Generate checklists"
	@echo "  2. make checklist-validate # Validate mappings"
	@echo "  3. make checklist-report   # Generate acceptance report"
	@echo "  4. make checklist-clean    # Clean up (when done)"

checklist: ## Generate dual-language checklists from user_request.md
	@echo "$(BLUE)Generating dual-language checklists...$(RESET)"
	@bash .claude/hooks/checklist_generator.sh .workflow/user_request.md
	@echo "$(GREEN)✓ Checklists generated successfully$(RESET)"

checklist-validate: ## Validate checklist mapping
	@echo "$(BLUE)Validating checklist system...$(RESET)"
	@bash .claude/hooks/validate_checklist_mapping.sh
	@echo "$(GREEN)✓ Validation complete$(RESET)"

checklist-report: ## Generate acceptance report
	@echo "$(BLUE)Generating acceptance report...$(RESET)"
	@bash .claude/hooks/acceptance_report_generator.sh
	@echo "$(GREEN)✓ Acceptance report generated$(RESET)"

checklist-clean: ## Clean generated checklists
	@echo "$(YELLOW)Cleaning generated checklists...$(RESET)"
	@rm -f .workflow/ACCEPTANCE_CHECKLIST.md
	@rm -f .workflow/TECHNICAL_CHECKLIST.md
	@rm -f .workflow/TRACEABILITY.yml
	@rm -f .workflow/ACCEPTANCE_REPORT.md
	@echo "$(GREEN)✓ Checklists cleaned$(RESET)"

checklist-test: checklist-clean checklist checklist-validate checklist-report ## Test complete checklist flow
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)✓ Complete checklist flow tested successfully$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(RESET)"
	@echo ""
	@echo "Generated files:"
	@ls -lh .workflow/ACCEPTANCE_CHECKLIST.md .workflow/TECHNICAL_CHECKLIST.md .workflow/TRACEABILITY.yml .workflow/ACCEPTANCE_REPORT.md 2>/dev/null || echo "  (some files may not exist)"
