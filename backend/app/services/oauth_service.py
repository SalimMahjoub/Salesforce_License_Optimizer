"""
OAuth 2.0 Service for Salesforce authentication.

Implements OAuth flow with token management, refresh, and encryption.
"""
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from simple_salesforce import Salesforce
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OAuthService:
    """
    Salesforce OAuth 2.0 Service (Singleton pattern).
    
    Manages OAuth flow, token storage, and automatic refresh.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize OAuth service."""
        if self._initialized:
            return
            
        self.client_id = settings.sf_client_id
        self.client_secret = settings.sf_client_secret
        self.redirect_uri = settings.sf_redirect_uri
        
        # Token encryption
        self._cipher = Fernet(Fernet.generate_key())
        self._tokens: Dict[str, Dict] = {}
        
        self._initialized = True
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        base_url = "https://login.salesforce.com/services/oauth2/authorize"
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "api refresh_token"
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def exchange_code_for_token(
        self,
        code: str,
        org_id: str
    ) -> Dict[str, str]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            org_id: Organization identifier
            
        Returns:
            Token data including access_token and refresh_token
        """
        token_url = "https://login.salesforce.com/services/oauth2/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
        
        # Encrypt and store tokens
        encrypted_access = self._encrypt_token(token_data['access_token'])
        encrypted_refresh = self._encrypt_token(token_data['refresh_token'])
        
        self._tokens[org_id] = {
            'access_token': encrypted_access,
            'refresh_token': encrypted_refresh,
            'instance_url': token_data['instance_url'],
            'expires_at': datetime.utcnow() + timedelta(hours=2)
        }
        
        logger.info(f"OAuth tokens obtained for org {org_id}")
        
        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'instance_url': token_data['instance_url']
        }
    
    async def refresh_token(self, org_id: str) -> str:
        """
        Refresh access token using refresh token.
        
        Args:
            org_id: Organization identifier
            
        Returns:
            New access token
        """
        if org_id not in self._tokens:
            raise ValueError(f"No tokens found for org {org_id}")
        
        refresh_token = self._decrypt_token(
            self._tokens[org_id]['refresh_token']
        )
        
        token_url = "https://login.salesforce.com/services/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
        
        # Update stored token
        encrypted_access = self._encrypt_token(token_data['access_token'])
        self._tokens[org_id]['access_token'] = encrypted_access
        self._tokens[org_id]['expires_at'] = datetime.utcnow() + timedelta(hours=2)
        
        logger.info(f"Token refreshed for org {org_id}")
        
        return token_data['access_token']
    
    async def get_salesforce_client(self, org_id: str) -> Salesforce:
        """
        Get authenticated Salesforce client.
        
        Args:
            org_id: Organization identifier
            
        Returns:
            Authenticated Salesforce client
        """
        if org_id not in self._tokens:
            raise ValueError(f"No tokens found for org {org_id}")
        
        token_data = self._tokens[org_id]
        
        # Check if token needs refresh
        if datetime.utcnow() >= token_data['expires_at']:
            access_token = await self.refresh_token(org_id)
        else:
            access_token = self._decrypt_token(token_data['access_token'])
        
        return Salesforce(
            instance_url=token_data['instance_url'],
            session_id=access_token,
            version='58.0'
        )
    
    def _encrypt_token(self, token: str) -> bytes:
        """Encrypt token for storage."""
        return self._cipher.encrypt(token.encode())
    
    def _decrypt_token(self, encrypted_token: bytes) -> str:
        """Decrypt stored token."""
        return self._cipher.decrypt(encrypted_token).decode()


# Singleton instance
oauth_service = OAuthService()

