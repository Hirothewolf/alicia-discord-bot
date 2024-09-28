import discord
from google.generativeai.types import BlockedPromptException, BrokenResponseError, IncompleteIterationError, StopCandidateException
from google.api_core.exceptions import PermissionDenied, ResourceExhausted, AlreadyExists, InvalidArgument, RetryError, InternalServerError, NotFound
from google.auth.exceptions import DefaultCredentialsError

async def handle_error(error, channel):
    """
    Handles various types of errors and sends user-friendly error messages in English using Discord embeds.
    """
    embed = discord.Embed(title="Error", color=discord.Color.red())
    
    if isinstance(error, BlockedPromptException):
        embed.description = "I'm sorry, but I can't respond to that due to safety restrictions. Your prompt may contain sensitive or inappropriate content."
    
    elif isinstance(error, BrokenResponseError):
        embed.description = "Oops! There was an error processing the response. This could be due to an unexpected format in the AI's output. Please try rephrasing your question or request."
    
    elif isinstance(error, IncompleteIterationError):
        embed.description = "My response isn't quite ready yet. The AI might need more time to process your request. Please wait a moment and try again."
    
    elif isinstance(error, StopCandidateException):
        embed.description = "I had to stop mid-response. This usually happens when the AI detects potentially unsafe content. Could you rephrase your question and try again?"
    
    elif isinstance(error, PermissionDenied):
        embed.description = "Access denied. This could be due to an invalid API key or insufficient permissions. Please contact the bot administrator to verify the API key and permissions."
    
    elif isinstance(error, ResourceExhausted):
        embed.description = "I'm a bit overwhelmed at the moment. You may have exceeded the rate limit for API requests. Please try again in a few minutes or consider upgrading your API plan."
    
    elif isinstance(error, AlreadyExists):
        embed.description = "It seems something with that name or identifier already exists. This could be a duplicate request or a naming conflict. Please try a different name or check if the resource already exists."
    
    elif isinstance(error, InvalidArgument):
        embed.description = "There was a problem with the request. This could be due to incorrect parameters or formatting. Please check your inputs, ensure they match the API requirements, and try again."
    
    elif isinstance(error, DefaultCredentialsError):
        embed.description = "I'm having authentication issues. This could be due to missing or invalid credentials. Please let the bot administrator know to check the API authentication settings!"
    
    elif isinstance(error, RetryError):
        embed.description = "I'm having trouble connecting to the API. This might be due to network issues or temporary API unavailability. Please try again in a moment."
    
    elif isinstance(error, InternalServerError):
        embed.description = "An internal server error occurred on the API side. This is likely a temporary issue. I'll keep trying to get a response, but if it persists, please report it to the bot administrator."
        return None  # Signal to retry
    
    elif isinstance(error, NotFound):
        embed.description = "The requested resource wasn't found. This could be due to an invalid model name, non-existent file, or outdated API version. Please check your request parameters and try again."
    
    elif isinstance(error, Exception) and error.args and "FAILED_PRECONDITION" in str(error.args[0]):
        embed.description = "The Gemini API free tier is not available in your country. To use the Gemini API, you'll need to set up a paid plan using Google AI Studio. Please contact the bot administrator to upgrade the plan."
    
    elif isinstance(error, Exception) and error.args and "DEADLINE_EXCEEDED" in str(error.args[0]):
        embed.description = "The request took too long to process. This might be due to a very large input or complex task. Try simplifying your request or breaking it into smaller parts."
    
    else:
        embed.description = f"An unexpected error occurred: {type(error).__name__}. Please try again later or contact support if the problem persists."
    
    embed.add_field(name="Error Type", value=type(error).__name__, inline=False)
    embed.add_field(name="Error Details", value=str(error)[:1024], inline=False)
    
    await channel.send(embed=embed)
    return embed

def log_error(error):
    """
    Logs the error for administrative purposes.
    This function can be expanded to log errors to a file or external service.
    """
    print(f"Error occurred: {type(error).__name__} - {str(error)}")