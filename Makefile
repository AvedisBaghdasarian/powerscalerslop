.PHONY: build-frontend copy-frontend clean-frontend

# Build the Svelte frontend
build-frontend:
	@echo "Building Svelte frontend..."
	cd packages/frontend && npm run build

# Copy the built frontend to backend
copy-frontend:
	@echo "Copying frontend build to backend..."
	@mkdir -p backend/frontend_dist
	cp -r packages/frontend/dist/* backend/frontend_dist/

# Clean frontend build artifacts
clean-frontend:
	@echo "Cleaning frontend build artifacts..."
	rm -rf packages/frontend/dist
	rm -rf backend/frontend_dist

# Build and copy frontend in one command
build: build-frontend copy-frontend 