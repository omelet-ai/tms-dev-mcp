# Python Project Template

This is a template for initiating a Python project. Please use it as a base and build your own code on top of it.

![image](https://github.com/user-attachments/assets/28ef1ba0-bd90-47a7-b388-a6d6f0a8e926)

## Pre-commit Hook

Install the necessary pre-commit hooks using the following command:

```
pre-commit install --install-hooks -t pre-commit -t commit-msg
```

## Add Environment variable

- See https://www.notion.so/omelet-ai/9487cc0526684453adc3c299e961f4c1
- On this template, it is managed by "myproject/config.py".

---

## Setup steps
Before you start, please follow steps below:
- Update folder name "myproject" to your own project name
- Update the pyproject.toml file with the name of your project:

```toml
name = "myproject"
```

### Install Dependencies with `uv`

Ensure `pip` is installed on your system, then install the `uv` tool:

```bash
pip install uv
```

#### Set Up Python Environment

 Install Python 3.xx using `uv`:

```bash
uv python install 3.xx
```

 Create a virtual environment:

```bash
uv venv --python 3.xx
source .venv/bin/activate
```

Synchronize required dependencies:

```bash
uv sync --all-groups
```
