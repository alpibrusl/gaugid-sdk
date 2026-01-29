# Gaugid SDK Jupyter Notebooks

Interactive Jupyter notebooks for learning and experimenting with Gaugid SDK framework integrations.

## Setup

1. **Install Jupyter**:
```bash
uv pip install jupyter ipykernel
```

2. **Install framework dependencies**:
```bash
cd ../../docs
uv pip install -e .[all]  # or specific framework like [langchain]
```

3. **Start Jupyter**:
```bash
jupyter notebook
# or
jupyter lab
```

## Notebooks

### LangChain Integration
- `langchain_gaugid.ipynb` - Complete LangChain + Gaugid integration example

### Anthropic Claude Integration
- `anthropic_gaugid.ipynb` - Claude 4.5 + Gaugid integration example

### Google Gemini Integration
- `gemini_gaugid.ipynb` - Gemini 3 + Gaugid integration example

### Google ADK Integration
- `google_adk_gaugid.ipynb` - Google Agent Development Kit (ADK) + Gaugid multi-agent system

### CrewAI Integration
- `crewai_gaugid.ipynb` - CrewAI + Gaugid personalized research team

## Usage

1. Open a notebook in Jupyter
2. Set your API keys in the first code cell
3. Run cells sequentially to see the integration in action
4. Modify and experiment with the code

## Features

Each notebook demonstrates:
- Loading user context from Gaugid profiles
- Personalizing AI responses
- Proposing memories learned during conversations
- Best practices for integration

## Model Versions

All notebooks use the latest model versions as of January 2026:
- GPT-5.2
- Claude 4.5
- Gemini 3 Flash/Pro
