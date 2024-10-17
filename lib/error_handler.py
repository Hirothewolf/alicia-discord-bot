import discord
from google.generativeai.types import BlockedPromptException, BrokenResponseError, IncompleteIterationError, StopCandidateException
from google.api_core.exceptions import PermissionDenied, ResourceExhausted, AlreadyExists, InvalidArgument, RetryError, InternalServerError, NotFound
from google.auth.exceptions import DefaultCredentialsError
from typing import Optional, Union
import logging
import asyncio

class ErrorHandler:
    ERROR_MESSAGES = {
        BlockedPromptException: "I'm sorry, but I can't respond to that due to safety restrictions. Your prompt may contain sensitive or inappropriate content.",
        BrokenResponseError: "Oops! There was an error processing the response. This could be due to an unexpected format in the AI's output. Please try rephrasing your question or request.",
        IncompleteIterationError: "My response isn't quite ready yet. The AI might need more time to process your request. Please wait a moment and try again.",
        StopCandidateException: "I had to stop mid-response. This usually happens when the AI detects potentially unsafe content. Could you rephrase your question and try again?",
        PermissionDenied: "Access denied. This could be due to an invalid API key or insufficient permissions. Please contact the bot administrator to verify the API key and permissions.",
        ResourceExhausted: "I'm a bit overwhelmed at the moment. You may have exceeded the rate limit for API requests. Please try again in a few minutes or consider upgrading your API plan.",
        AlreadyExists: "It seems something with that name or identifier already exists. This could be a duplicate request or a naming conflict. Please try a different name or check if the resource already exists.",
        InvalidArgument: "There was a problem with the request. This could be due to incorrect parameters or formatting. Please check your inputs, ensure they match the API requirements, and try again.",
        DefaultCredentialsError: "I'm having authentication issues. This could be due to missing or invalid credentials. Please let the bot administrator know to check the API authentication settings!",
        RetryError: "I'm having trouble connecting to the API. This might be due to network issues or temporary API unavailability. Please try again in a moment.",
        InternalServerError: "An internal server error occurred on the API side. This is likely a temporary issue. I'll keep trying to get a response, but if it persists, please report it to the bot administrator.",
        NotFound: "The requested resource wasn't found. This could be due to an invalid model name, non-existent file, or outdated API version. Please check your request parameters and try again.",
    }

    BACKEND_ERROR_CODES = {
        400: {
            "INVALID_ARGUMENT": "The request body is malformed. There might be a typo or a missing required field in your request. Please check the API reference for the correct request format.",
            "FAILED_PRECONDITION": "Gemini API free tier is not available in your country. To use the Gemini API, you'll need to set up a paid plan using Google AI Studio."
        },
        403: {
            "PERMISSION_DENIED": "Your API key doesn't have the required permissions. Please check that your API key is set correctly and has the right access."
        },
        404: {
            "NOT_FOUND": "The requested resource wasn't found. This could be due to an invalid model name, non-existent file, or outdated API version."
        },
        429: {
            "RESOURCE_EXHAUSTED": "You've exceeded the rate limit. Please ensure you're within the model's rate limit or request a quota increase if needed."
        },
        500: {
            "INTERNAL": "An unexpected error occurred on Google's side. This might be due to your input context being too long. Try reducing your input or switching to another model temporarily."
        },
        503: {
            "UNAVAILABLE": "The service may be temporarily overloaded or down. Try switching to another model temporarily or wait a bit before retrying your request."
        },
        504: {
            "DEADLINE_EXCEEDED": "The service is unable to finish processing within the deadline. Your prompt or context might be too large. Try setting a larger 'timeout' in your client request."
        }
    }

    def __init__(self):
        self.logger = logging.getLogger('AliciaBot')
        self.logger.setLevel(logging.ERROR)
        handler = logging.FileHandler('error.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    async def handle_error(self, error: Exception, channel: discord.TextChannel) -> Optional[discord.Embed]:
        """
        Handles various types of errors and sends user-friendly error messages in English using Discord embeds.
        """
        embed = discord.Embed(title="Error", color=discord.Color.red())
        
        if isinstance(error, InternalServerError):
            embed.description = self.ERROR_MESSAGES[InternalServerError]
            return None  # Signal to retry
        
        error_type = type(error)
        if error_type in self.ERROR_MESSAGES:
            embed.description = self.ERROR_MESSAGES[error_type]
        elif isinstance(error, Exception) and error.args:
            error_message = str(error.args[0])
            
            # Check for backend error codes
            for status_code, error_dict in self.BACKEND_ERROR_CODES.items():
                for error_key, error_description in error_dict.items():
                    if error_key in error_message:
                        embed.description = f"Backend Error ({status_code}): {error_description}"
                        break
                if embed.description:
                    break
            
            if not embed.description:
                if "FAILED_PRECONDITION" in error_message:
                    embed.description = "The Gemini API free tier is not available in your country. To use the Gemini API, you'll need to set up a paid plan using Google AI Studio. Please contact the bot administrator to upgrade the plan."
                elif "DEADLINE_EXCEEDED" in error_message:
                    embed.description = "The request took too long to process. This might be due to a very large input or complex task. Try simplifying your request or breaking it into smaller parts."
                elif "Unable to submit request because it has a topK value" in error_message:
                    embed.description = "The current model doesn't support the configured topK value. Please adjust the topK value in the bot settings to be within the supported range for this model."
                else:
                    embed.description = f"An unexpected error occurred: {error_type.__name__}. Please try again later or contact support if the problem persists."
        else:
            embed.description = f"An unexpected error occurred: {error_type.__name__}. Please try again later or contact support if the problem persists."
        
        embed.add_field(name="Error Type", value=error_type.__name__, inline=False)
        embed.add_field(name="Error Details", value=str(error)[:1024], inline=False)
        
        await channel.send(embed=embed)
        return embed

    async def log_error(self, error: Exception) -> None:
        """
        Logs the error for administrative purposes.
        This function can be expanded to log errors to a file or external service.
        """
        self.logger.error(f"Error occurred: {type(error).__name__} - {str(error)}")

    async def handle_and_log_error(self, error: Exception, channel: discord.TextChannel) -> None:
        """
        Handles the error by sending a message to the channel and logging it.
        """
        await asyncio.gather(
            self.handle_error(error, channel),
            self.log_error(error)
        )