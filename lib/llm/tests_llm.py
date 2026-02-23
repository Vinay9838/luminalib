from django.test import TestCase
from unittest.mock import patch, MagicMock

from lib.llm.factory import get_llm_client
from lib.llm.base import BaseLLM


class LLMFactoryTest(TestCase):
    """Test cases for LLM factory"""

    @patch.dict('os.environ', {'LLM_TYPE': 'azure'})
    @patch('lib.llm.factory.AzureClient')
    def test_get_azure_client(self, mock_azure):
        """Test getting Azure LLM client"""
        mock_instance = MagicMock()
        mock_azure.return_value = mock_instance
        
        client = get_llm_client()
        
        self.assertIsNotNone(client)

    @patch.dict('os.environ', {'LLM_TYPE': 'ollama'})
    @patch('lib.llm.factory.OllamaClient')
    def test_get_ollama_client(self, mock_ollama):
        """Test getting Ollama LLM client"""
        mock_instance = MagicMock()
        mock_ollama.return_value = mock_instance
        
        client = get_llm_client()
        
        self.assertIsNotNone(client)

    @patch.dict('os.environ', {'LLM_TYPE': 'unknown'})
    def test_unsupported_llm_type(self):
        """Test error with unsupported LLM type"""
        with self.assertRaises(ValueError):
            get_llm_client()

    @patch.dict('os.environ', {}, clear=True)
    @patch('lib.llm.factory.AzureClient')
    def test_default_llm_client(self, mock_azure):
        """Test default LLM client when LLM_TYPE not set"""
        mock_instance = MagicMock()
        mock_azure.return_value = mock_instance
        
        client = get_llm_client()
        
        self.assertIsNotNone(client)


class BaseLLMTest(TestCase):
    """Test cases for BaseLLM"""

    def test_base_llm_abstract(self):
        """Test that BaseLLM cannot be instantiated"""
        with self.assertRaises(TypeError):
            BaseLLM()

    def test_base_llm_requires_generate_summary(self):
        """Test that subclasses must implement generate_summary"""
        class IncompleteLLM(BaseLLM):
            def analyze_sentiment(self, text: str) -> float:
                return 0.5
        
        with self.assertRaises(TypeError):
            IncompleteLLM()

    def test_base_llm_requires_analyze_sentiment(self):
        """Test that subclasses must implement analyze_sentiment"""
        class IncompleteLLM(BaseLLM):
            def generate_summary(self, text: str) -> str:
                return "Summary"
        
        with self.assertRaises(TypeError):
            IncompleteLLM()

    def test_llm_contract_implementation(self):
        """Test that complete implementation works"""
        class CompleteLLM(BaseLLM):
            def generate_summary(self, text: str) -> str:
                return "Summary of " + text
            
            def analyze_sentiment(self, text: str) -> float:
                return 0.75
        
        llm = CompleteLLM()
        self.assertEqual(llm.generate_summary("test"), "Summary of test")
        self.assertEqual(llm.analyze_sentiment("test"), 0.75)
