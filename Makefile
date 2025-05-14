# Path to your virtual environment
VENV_PATH=../ai-assistant

# Python executable in the virtual environment
PYTHON=$(VENV_PATH)/bin/python3

# Install dependencies using the virtual environment
install:
	@echo "Installing dependencies..."
	$(VENV_PATH)/bin/pip install --upgrade pip
	$(VENV_PATH)/bin/pip install -r requirements.text

