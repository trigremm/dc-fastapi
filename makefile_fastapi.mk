# makefile_fastapi.mk
# FastAPI commands

.PHONY: shell logs-backend logs-worker test

shell:
	$(DC_BIN) exec backend bash

logs-backend:
	$(DC_BIN) logs -f backend

logs-worker:
	$(DC_BIN) logs -f worker

test:
	@echo "Starting all services..."
	$(DC_BIN) up -d
	@echo "Waiting for backend..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		curl -sf http://localhost:8000/health >/dev/null 2>&1 && break || sleep 5; \
	done
	@echo "Test health endpoint..."
	curl -sf http://localhost:8000/health | python3 -m json.tool && echo "PASS: health" || (echo "FAIL: health" && exit 1)
	@echo "Test document upload..."
	echo "<html><body><h1>Test</h1></body></html>" > /tmp/test_dc_fastapi.html
	curl -sf -X POST http://localhost:8000/documents/upload -F "file=@/tmp/test_dc_fastapi.html" | python3 -m json.tool && echo "PASS: upload" || (echo "FAIL: upload" && exit 1)
	@rm -f /tmp/test_dc_fastapi.html
	@echo "Test list documents..."
	curl -sf http://localhost:8000/documents/ | python3 -m json.tool && echo "PASS: list" || (echo "FAIL: list" && exit 1)
	@echo ""
	@echo "All tests passed!"
