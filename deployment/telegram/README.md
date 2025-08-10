# AI-CRM Telegram Bot Deployment

This document provides instructions on how to deploy and run the AI-CRM Telegram Bot.

The bot acts as a bridge between Telegram and the AI-CRM's PM Agent, allowing users to interact with the CRM through Telegram messages.

## Prerequisites

- Python 3.8+
- Access to the project's repository.
- A Telegram Bot Token. You can get one by talking to the [BotFather](https://t.me/botfather) on Telegram.

## 1. Installation

First, navigate to the `our_crm_ai` directory and install the required Python dependencies:

```bash
cd our_crm_ai
pip install -r requirements.txt
```

This will install `python-telegram-bot` along with all other necessary packages.

## 2. Configuration

The bot requires a Telegram Bot Token to authenticate with the Telegram API. This token should be set as an environment variable.

### Set the Environment Variable

- **Linux/macOS:**
  ```bash
  export TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
  ```

- **Windows (Command Prompt):**
  ```cmd
  set TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
  ```

- **Windows (PowerShell):**
  ```powershell
  $env:TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
  ```

Replace `"YOUR_TELEGRAM_BOT_TOKEN_HERE"` with the actual token you received from BotFather.

**Important:** Do not hard-code your token in the script. Using an environment variable is more secure.

## 3. Running the Bot

Once the dependencies are installed and the environment variable is set, you can run the bot from the **root of the project directory**:

```bash
python3 integrations/telegram_integration.py
```

The bot will start polling for new messages. You can now go to your Telegram client, find your bot, and start sending it commands.

### Example Commands:
- `/start` - Welcome message.
- `/help` - Shows available commands.
- `list tasks` - Lists all tasks.

## 4. Running as a Service (Deployment)

For production use, you should run the bot as a long-running service. Here are some common ways to do this:

### Using `systemd` (Linux)

1.  Create a `systemd` service file:
    ```bash
    sudo nano /etc/systemd/system/ai_crm_telegram_bot.service
    ```

2.  Add the following content to the file, adjusting paths as necessary:
    ```ini
    [Unit]
    Description=AI-CRM Telegram Bot
    After=network.target

    [Service]
    User=your_user                 # Replace with the user that runs the script
    Group=your_group               # Replace with the group for the user
    WorkingDirectory=/path/to/your/project # Replace with your project's root path
    Environment="TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ExecStart=/usr/bin/python3 /path/to/your/project/integrations/telegram_integration.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

3.  Reload `systemd`, enable, and start the service:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable ai_crm_telegram_bot.service
    sudo systemctl start ai_crm_telegram_bot.service
    ```

### Using `docker-compose`

You can also containerize the bot. You would need to add a new service to your `docker-compose.yml` file.

**Example service definition:**
```yaml
services:
  # ... other services
  telegram-bot:
    build:
      context: .
      dockerfile: Dockerfile  # Assuming a Dockerfile in the root
    command: python3 integrations/telegram_integration.py
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    restart: always
```
You would also need to ensure your main `Dockerfile` can run the integration.
