"""Tests for the ask command."""

import pytest
from unittest.mock import AsyncMock, patch

from ai_cli.commands.ask import ask_question


class TestAskCommand:
    """Test ask command functionality."""
    
    @pytest.mark.asyncio
    async def test_ask_question_success(self):
        """Test successful question asking."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = "This is a test response"
        mock_response.model = "gpt-4"
        mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 20}
        mock_client.chat_completion.return_value = mock_response
        
        with patch("ai_cli.commands.ask.get_client", return_value=mock_client):
            await ask_question(
                question="What is 2+2?",
                model="gpt-4",
                provider="openai",
                temperature=0.7,
                max_tokens=100
            )
            
            # Verify the client was called correctly
            mock_client.chat_completion.assert_called_once()
            call_args = mock_client.chat_completion.call_args
            assert call_args[1]["model"] == "gpt-4"
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["max_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_ask_question_with_system_prompt(self):
        """Test asking question with system prompt."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = "Response with system prompt"
        mock_response.model = "gpt-4"
        mock_response.usage = None
        mock_client.chat_completion.return_value = mock_response
        
        with patch("ai_cli.commands.ask.get_client", return_value=mock_client):
            await ask_question(
                question="What is 2+2?",
                model="gpt-4",
                provider="openai",
                temperature=0.7,
                max_tokens=100,
                system_prompt="You are a helpful assistant."
            )
            
            # Verify system prompt was included
            call_args = mock_client.chat_completion.call_args
            messages = call_args[1]["messages"]
            assert len(messages) == 2
            assert messages[0].role == "system"
            assert messages[0].content == "You are a helpful assistant."
            assert messages[1].role == "user"
            assert messages[1].content == "What is 2+2?"
    
    @pytest.mark.asyncio
    async def test_ask_question_client_error(self):
        """Test handling of client errors."""
        mock_client = AsyncMock()
        mock_client.chat_completion.side_effect = Exception("API Error")
        
        with patch("ai_cli.commands.ask.get_client", return_value=mock_client):
            # Should not raise an exception, just log the error
            await ask_question(
                question="What is 2+2?",
                model="gpt-4",
                provider="openai",
                temperature=0.7,
                max_tokens=100
            ) 