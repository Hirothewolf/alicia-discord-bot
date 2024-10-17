# Alicia: Advanced Discord Bot with Gemini LLM

Alicia is an open-source Discord bot that leverages Google's Gemini Large Language Model (LLM) to provide advanced conversational AI capabilities within Discord servers.

This bot offers a wide range of features, customizable settings, and robust error handling, making it a powerful tool for enhancing user interactions in your Discord community.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Key Management](#api-key-management)
- [Privacy and Terms of Service](#privacy-and-terms-of-service)
- [Contributing](#contributing)
- [License](#license)

## Features

- Advanced conversational AI powered by Google's Gemini LLM
- Customizable LLM parameters (temperature, top_p, top_k, max_tokens, System Instructions)
- Role-playing mode for immersive interactions
- Configurable safety settings to filter inappropriate content
- Channel-specific bot interactions
- Conversation history management with SQLite database
- Interactive help menu with detailed command explanations
- Robust API key management and error handling
- Asynchronous design for efficient performance

## Installation

1. Download the latest release and extract the downloaded file:
   ```
   wget https://github.com/Hirothewolf/Alicia-Discord-LLM/releases/latest/download/alicia_discordbot-1.x.x.tar
   tar -xvf alicia_discordbot-1.x.x.tar
   cd alicia_discordbot-1.0.0
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Discord bot token and Gemini API key:
   - Create a `.env` file in the project root
   - Add your Discord token: `DISCORD_TOKEN=your_token_here`

4. Run the bot:
   ```
   python main.py
   ```

## Usage

Once the bot is running and invited to your Discord server, you can interact with it using various commands. **The bot will respond to messages ONLY in allowed channels and can engage in conversations using the Gemini LLM.**

## Configuration

Administrators can configure various aspects of the bot using the following commands:

- `/settings`: Configure LLM parameters (API Keys, temperature, top_p, top_k, max_tokens, system instruction)
- `/filter_safety`: Adjust content filtering settings
- `/manage_allowed_channel`: Add or remove channels where the bot can interact

For a full list of commands and their usage, use the `/help` command in Discord.

## API Key Management

To use the Gemini LLM, you need to obtain an API key from the Google AI Studio. Administrators can manage API keys using the `/api_manager` command. The bot supports multiple API keys per server and implements key rotation for efficient quota management.

To obtain a Gemini API key:

1. Visit the [Google AI Studio](https://ai.google.dev/)
2. Click on "Get API key in Google AI Studio"
3. Review and accept the terms of service
4. Create your API key in a new or existing project

## Privacy and Terms of Service

This bot adheres to Google's Gemini API Terms of Service and privacy policies. By using this bot, you agree to comply with these terms. Key points:

- The bot does not store personal information beyond conversation interaction and LLM Settings
- Conversation interactions are stored locally and can be cleared at any time
- Administrators can configure safety settings to filter potentially inappropriate content
- Users are responsible for the content they generate through the bot

Please review Google's [Gemini API Additional Terms of Service](https://ai.google.dev/terms) for more information.

## Contributing

Contributions to Alicia are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch: `git checkout -b feature-branch-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-branch-name`
5. Submit a pull request

Please ensure your code adheres to the project's coding standards and include tests for new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```

MIT License

Copyright (c) 2024 Hirothewolf

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
