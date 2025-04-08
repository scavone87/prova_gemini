"""
Configurazione per i test con pytest.
"""
import pytest
import os

@pytest.fixture
def funnel_id():
    """
    Fixture che fornisce un ID di funnel valido per i test.
    
    Può essere sovrascritto passando la variabile d'ambiente TEST_FUNNEL_ID.
    Altrimenti, utilizza un ID di default (1).
    """
    # Controlla se è stata specificata una variabile d'ambiente
    env_funnel_id = os.environ.get('TEST_FUNNEL_ID')
    if env_funnel_id:
        return int(env_funnel_id)
    
    # Altrimenti, utilizza un ID di default
    return 1
