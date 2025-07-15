import pytest
from unittest.mock import patch, MagicMock
from services.agent_service import process_query

# We use @patch to temporarily replace parts of our code with mock objects
@patch('services.agent_service.llm') # Mock the LLM object
@patch('services.agent_service.engine') # Mock the database engine
@patch('services.agent_service.routing_chain')
@patch('services.agent_service.get_layer_as_geojson')
def test_process_query_gis_intent(mock_get_layer, mock_routing_chain, mock_engine, mock_llm):
    """
    Tests if the function correctly calls the GIS tool when intent is 'get_gis_data'.
    """
    # Arrange: Configure our mocks
    mock_routing_chain.invoke.return_value = {'route': {"intent": "get_gis_data", "layer_name": "parcels"}}
    mock_get_layer.invoke.return_value = '{"type": "FeatureCollection", "features": []}'

    # Act: Call the function we are testing
    result = process_query("pokaż działki")

    # Assert: Check if the results are as expected
    mock_routing_chain.invoke.assert_called_once_with({"query": "pokaż działki"})
    mock_get_layer.invoke.assert_called_once()
    assert result["type"] == "geojson"
    assert "FeatureCollection" in result["data"]

@patch('services.agent_service.llm') # Mock the LLM object
@patch('services.agent_service.engine') # Mock the database engine
@patch('services.agent_service.routing_chain')
@patch('services.agent_service.chat_chain')
def test_process_query_chat_intent(mock_chat_chain, mock_routing_chain, mock_engine, mock_llm):
    """
    Tests if the function correctly calls the chat chain when intent is 'chat'.
    """
    # Arrange
    mock_routing_chain.invoke.return_value = {'route': {"intent": "chat"}}
    # Mock the response from the chat model
    mock_chat_response = MagicMock()
    mock_chat_response.content = "Witaj! Jestem asystentem GIS."
    mock_chat_chain.invoke.return_value = mock_chat_response

    # Act
    result = process_query("hej")

    # Assert
    mock_routing_chain.invoke.assert_called_once_with({"query": "hej"})
    mock_chat_chain.invoke.assert_called_once_with({"query": "hej"})
    assert result["type"] == "text"
    assert result["data"] == "Witaj! Jestem asystentem GIS."

@patch('services.agent_service.llm') # Mock the LLM object
@patch('services.agent_service.engine') # Mock the database engine
@patch('services.agent_service.routing_chain')
def test_process_query_gis_intent_no_layer(mock_routing_chain, mock_engine, mock_llm):
    """
    Tests the response when the GIS intent is detected but no layer name is provided.
    """
    # Arrange
    mock_routing_chain.invoke.return_value = {'route': {"intent": "get_gis_data", "layer_name": None}}

    # Act
    result = process_query("pokaż dane")

    # Assert
    assert result["type"] == "text"
    assert "Nie sprecyzowałeś, którą warstwę wyświetlić." in result["data"]
