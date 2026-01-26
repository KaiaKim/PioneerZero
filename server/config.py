"""
Application configuration settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""
    
    # Google OAuth Configuration
    GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    GOOGLE_OAUTH_REDIRECT_URI: str = os.getenv(
        "GOOGLE_OAUTH_REDIRECT_URI", 
        "http://localhost:8000/auth/google/callback"
    )
    GOOGLE_OAUTH_SCOPES: list[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "main.db")
    
    # Allowed Members (TODO: move to database)
    ALLOWED_MEMBERS: list[str] = ["kaiakim0727@gmail.com"]
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    def validate(self):
        """Validate required configuration settings"""
        if not self.GOOGLE_OAUTH_CLIENT_ID or not self.GOOGLE_OAUTH_CLIENT_SECRET:
            raise ValueError(
                "Missing required environment variables: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET. "
                "Please create a .env file with these variables. See .env.example for reference."
            )


# Global settings instance
settings = Settings()

# Validate settings on import
settings.validate()
