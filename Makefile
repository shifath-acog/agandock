JP_IMAGE := kailash-agandock-jupyter
JP_CONTAINER := ${USER}-jupyter-agandock
JP_PORT := $(shell shuf -i 8000-17999 -n 1)

SL_IMAGE := kailash-agandock-streamlit
SL_CONTAINER := docking-dashboard

SL_PORT := 8501

SERVICE_NAME := ${USER}-agandock

build-image:
	@cd devops && \
		JP_IMAGE=$(JP_IMAGE) JP_CONTAINER=$(JP_CONTAINER) JP_PORT=$(JP_PORT) \
		SL_IMAGE=$(SL_IMAGE) SL_CONTAINER=$(SL_CONTAINER) SL_PORT=$(SL_PORT) \
		docker compose build 

start-container:
	@docker ps --format '{{.Names}}' | grep -q "^$(JP_CONTAINER)$$" && echo "Already running container: \\e[1;32m$(JP_CONTAINER)\\e[0m" || true
	@docker ps --format '{{.Names}}' | grep -q "^$(SL_CONTAINER)$$" && echo "Already running container: \\e[1;32m$(SL_CONTAINER)\\e[0m" || true

	@if ! docker ps --format '{{.Names}}' | grep -q -e "^$(JP_CONTAINER)$$" -e "^$(MF_CONTAINER)$$" -e "^$(SL_CONTAINER)$$"; then \
		cd devops && \
			JP_IMAGE=$(JP_IMAGE) JP_CONTAINER=$(JP_CONTAINER) JP_PORT=$(JP_PORT) \
			SL_IMAGE=$(SL_IMAGE) SL_CONTAINER=$(SL_CONTAINER) SL_PORT=$(SL_PORT) \
			docker compose -p $(SERVICE_NAME) up -d > /dev/null 2>&1 && \
		echo "Successfully started containers: \\e[1;32m$(JP_CONTAINER)\\e[0m"; \
		echo "Successfully started containers: \\e[1;32m$(SL_CONTAINER)\\e[0m"; \
	fi

start-streamlit-container:
	@docker ps --format '{{.Names}}' | grep -q "^$(SL_CONTAINER)$$" && echo "Already running container: \\e[1;32m$(SL_CONTAINER)\\e[0m" || true

	@if ! docker ps --format '{{.Names}}' | grep -q -e "^$(SL_CONTAINER)$$"; then \
		cd devops && \
			SL_IMAGE=$(SL_IMAGE) SL_CONTAINER=$(SL_CONTAINER) SL_PORT=$(SL_PORT) \
			docker compose -p $(SERVICE_NAME) up -d streamlit > /dev/null 2>&1 && \
		echo "Successfully started container: \\e[1;32m$(SL_CONTAINER)\\e[0m"; \
	fi

enter-jupyter-container:
	@echo "You are inside the Container: \033[1;33m$(JP_CONTAINER)\033[0m"
	@docker exec -u root -it $(JP_CONTAINER) bash || true

enter-streamlit-container:
	@echo "You are inside the Container: \033[1;33m$(SL_CONTAINER)\033[0m"
	@docker exec -u root -it $(SL_CONTAINER) bash || true

stop-container:
	@if docker ps -a --format '{{.Names}}' | grep -q -e "^$(JP_CONTAINER)$$" -e "^$(MF_CONTAINER)$$" -e "^$(SL_CONTAINER)$$"; then \
		echo "Stopped and removed container: \033[1;31m$(JP_CONTAINER)\033[0m"; \
		docker rm -f $(JP_CONTAINER) > /dev/null 2>&1; \
		echo "Stopped and removed container: \033[1;31m$(SL_CONTAINER)\033[0m"; \
		docker rm -f $(SL_CONTAINER) > /dev/null 2>&1; \
	else echo "\033[1;31mThere are no running containers to stop.\033[0m"; \
	fi
