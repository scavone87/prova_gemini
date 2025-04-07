"""
Test di base per verificare le funzionalità di Streamlit.
"""
import pytest


def test_streamlit_import():
    """
    Verifica che Streamlit possa essere importato correttamente.
    """
    try:
        import streamlit as st
        assert True
    except ImportError:
        assert False, "Impossibile importare streamlit"


def test_pandas_import():
    """
    Verifica che pandas possa essere importato correttamente.
    """
    try:
        import pandas as pd
        assert True
    except ImportError:
        assert False, "Impossibile importare pandas"


def test_numpy_import():
    """
    Verifica che numpy possa essere importato correttamente.
    """
    try:
        import numpy as np
        assert True
    except ImportError:
        assert False, "Impossibile importare numpy"
