# AutoGen Web-Browsing Agent

A simple multi-agent application built with AutoGen Core that uses Playwright to perform web searches and extract information. This project demonstrates how an AI agent can be equipped with external tools to perform actions on the web.

## Features

-   **Intelligent Web Browsing**: The agent can reason about a task and use a web browser to find information.
-   **Multi-Turn Conversations**: Uses a memory buffer to maintain context across multiple turns of a conversation.
-   **Tool Integration**: Connects to an external Playwright server to execute browser commands.
-   **Flexible & Reusable**: The `BrowserAgent` is a template that can be easily adapted to perform other web-related tasks.

## Prerequisites

Before you begin, ensure you have the following installed:

-   **Python 3.10+**
-   **Node.js (v18+) and npm**
-   **A valid OpenAI API Key**

## Setup and Installation

1.  **Clone the repository and navigate to the project folder:**
    ```bash
    git clone [your-repository-url]
    cd autogen-web-agent
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install "autogen-ext[openai, playwright_mcp]"
    ```

4.  **Install Playwright browser dependencies:**
    ```bash
    npx playwright install chrome
    ```

5.  **Set your OpenAI API Key:**
    Replace the placeholder in `web_agent.py` with your actual API key, or set it as an environment variable in your terminal.
    
    _Recommended Method (Terminal):_
    ```bash
    export OPENAI_API_KEY='YOUR_API_KEY_HERE'
    ```

## How to Run the Project

The project requires two terminals to run.

1.  **Start the Playwright MCP Server:**
    Open the **first terminal** and run the following command. Keep this terminal window open and running.
    ```bash
    npx @playwright/mcp@latest --port 8931
    ```

2.  **Run the Python Agent Script:**
    Open the **second terminal**, activate your virtual environment, and run the main Python script.
    ```bash
    source venv/bin/activate
    python web_agent.py
    ```
    The agent will then execute the task and print the final answer in this terminal.

## Project Workflow

The project's workflow is a simple, automated loop:

1.  The `main()` function sends a message to the `BrowserAgent`.
2.  The agent's `handle_user_message` method receives the message and sends it to an LLM, along with a list of available tools.
3.  The LLM generates a tool call (e.g., `browser_navigate`).
4.  The agent uses the `McpWorkbench` to execute the tool call on the Playwright server.
5.  Playwright performs the action (e.g., searches Bing) and sends the results back to the agent.
6.  The agent sends the tool's results back to the LLM, which uses the information to generate a final, human-readable response.
7.  The agent returns this final response, and the script prints it to the console.

## Credits

-   **AutoGen**: The open-source framework used for building the multi-agent system.
-   **Playwright**: The web browsing automation tool.
-   **OpenAI**: The provider of the LLM model used for the agent's intelligence.
