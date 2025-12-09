"""
API Module - REST and WebSocket APIs for Budurasmala device control.
"""

try:
    from .rest_api import BudurasmalaRESTAPI
except ImportError:
    BudurasmalaRESTAPI = None

try:
    from .websocket_api import BudurasmalaWebSocketAPI
except ImportError:
    BudurasmalaWebSocketAPI = None

__all__ = ['BudurasmalaRESTAPI', 'BudurasmalaWebSocketAPI']

