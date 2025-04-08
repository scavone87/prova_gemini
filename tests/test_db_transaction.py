"""
Test per verificare il funzionamento del modulo db_transaction.
"""

import pytest
from unittest.mock import MagicMock, patch

from utils.db_transaction import standardized_db_operation, log_db_operation, with_retry
from sqlalchemy.exc import OperationalError


def test_standardized_db_operation():
    """
    Verifica che il decoratore standardized_db_operation funzioni correttamente.
    """
    # Mock della sessione
    mock_session = MagicMock()
    
    # Funzione di test
    @standardized_db_operation("test operation")
    def test_function(session, arg1, arg2=None):
        assert session is mock_session
        assert arg1 == "test"
        assert arg2 == "optional"
        return {"success": True}
    
    # Patch delle funzioni utilizzate dal decoratore
    with patch("utils.db_transaction.get_db_session", return_value=mock_session):
        with patch("utils.db_transaction.close_db_session") as mock_close:
            # Esegui la funzione
            result = test_function("test", arg2="optional")
            
            # Verifica che la sessione sia stata gestita correttamente
            mock_session.begin.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_close.assert_called_once_with(mock_session)
            
            # Verifica il risultato
            assert result == {"success": True}


def test_standardized_db_operation_with_exception():
    """
    Verifica che il decoratore standardized_db_operation gestisca correttamente le eccezioni.
    """
    # Mock della sessione
    mock_session = MagicMock()
    
    # Funzione di test che solleva un'eccezione
    @standardized_db_operation("test operation with exception")
    def test_function_with_exception(session):
        raise ValueError("Test exception")
    
    # Patch delle funzioni utilizzate dal decoratore
    with patch("utils.db_transaction.get_db_session", return_value=mock_session):
        with patch("utils.db_transaction.close_db_session") as mock_close:
            # Esegui la funzione
            result = test_function_with_exception()
            
            # Verifica che la sessione sia stata gestita correttamente
            mock_session.begin.assert_called_once()
            mock_session.commit.assert_not_called()
            mock_session.rollback.assert_called_once()
            mock_close.assert_called_once_with(mock_session)
            
            # Verifica il risultato
            assert result["error"] is True
            assert "Test exception" in result["message"]
            assert result["error_type"] == "general"


def test_with_retry():
    """
    Verifica che il decoratore with_retry funzioni correttamente.
    """
    # Contatore per tenere traccia del numero di chiamate
    call_count = 0
    
    # Funzione di test che fallisce le prime due volte
    @with_retry(max_attempts=3, retry_delay=0.01)
    def test_function_with_retry():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise OperationalError("Test retry", None, None)
        return "success"
    
    # Esegui la funzione
    with patch("utils.db_transaction.time.sleep"):  # Evita i ritardi nei test
        result = test_function_with_retry()
    
    # Verifica che la funzione sia stata chiamata il numero corretto di volte
    assert call_count == 3
    assert result == "success"


def test_with_retry_all_attempts_fail():
    """
    Verifica che il decoratore with_retry sollevi l'eccezione se tutti i tentativi falliscono.
    """
    # Funzione di test che fallisce sempre
    @with_retry(max_attempts=3, retry_delay=0.01)
    def test_function_always_fails():
        raise OperationalError("Test retry failure", None, None)
    
    # Esegui la funzione e verifica che sollevi l'eccezione
    with patch("utils.db_transaction.time.sleep"):  # Evita i ritardi nei test
        with pytest.raises(OperationalError):
            test_function_always_fails()


def test_log_db_operation():
    """
    Verifica che la funzione log_db_operation funzioni correttamente.
    """
    with patch("utils.db_transaction.logger.info") as mock_logger:
        # Esegui la funzione
        log_db_operation("insert", {"entity": "test", "id": 123})
        
        # Verifica che il logger sia stato chiamato correttamente
        mock_logger.assert_called_once()
        log_message = mock_logger.call_args[0][0]
        assert "DB Operation" in log_message
        assert "insert" in log_message
        assert "test" in log_message
        assert "123" in log_message
