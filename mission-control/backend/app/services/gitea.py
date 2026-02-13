"""
Gitea API Service - Manage Git repositories
"""
import httpx
import logging
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)


class GiteaService:
    """Service for interacting with Gitea API"""

    def __init__(self):
        self.base_url = settings.GITEA_URL
        self.token = settings.GITEA_TOKEN
        self.user = settings.GITEA_USER
        self.headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

    async def create_repo(self, name: str, description: str = "", private: bool = False) -> Optional[dict]:
        """
        Create a new repository in Gitea

        Args:
            name: Repository name (will be slugified)
            description: Repository description
            private: Whether the repo is private

        Returns:
            Repository info dict or None if failed
        """
        # Slugify the name
        repo_name = self._slugify(name)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/user/repos",
                    headers=self.headers,
                    json={
                        "name": repo_name,
                        "description": description,
                        "private": private,
                        "auto_init": True,  # Create with README
                        "default_branch": "main",
                        "gitignores": "Python,Node",
                        "readme": "Default"
                    }
                )

                if response.status_code == 201:
                    repo = response.json()
                    logger.info(f"Created Gitea repo: {repo_name}")
                    return {
                        "id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "clone_url": repo["clone_url"],
                        "ssh_url": repo["ssh_url"],
                        "html_url": repo["html_url"],
                    }
                elif response.status_code == 409:
                    # Repo already exists, get it
                    logger.info(f"Repo already exists: {repo_name}")
                    return await self.get_repo(repo_name)
                else:
                    logger.error(f"Failed to create repo: {response.status_code} - {response.text}")
                    return None

            except Exception as e:
                logger.error(f"Error creating repo: {e}")
                return None

    async def get_repo(self, name: str) -> Optional[dict]:
        """Get repository info"""
        repo_name = self._slugify(name)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/repos/{self.user}/{repo_name}",
                    headers=self.headers
                )

                if response.status_code == 200:
                    repo = response.json()
                    return {
                        "id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "clone_url": repo["clone_url"],
                        "ssh_url": repo["ssh_url"],
                        "html_url": repo["html_url"],
                    }
                return None

            except Exception as e:
                logger.error(f"Error getting repo: {e}")
                return None

    async def delete_repo(self, name: str) -> bool:
        """Delete a repository"""
        repo_name = self._slugify(name)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/api/v1/repos/{self.user}/{repo_name}",
                    headers=self.headers
                )

                if response.status_code == 204:
                    logger.info(f"Deleted repo: {repo_name}")
                    return True
                return False

            except Exception as e:
                logger.error(f"Error deleting repo: {e}")
                return False

    async def list_repos(self) -> list:
        """List all repositories for the user"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/user/repos",
                    headers=self.headers
                )

                if response.status_code == 200:
                    repos = response.json()
                    return [
                        {
                            "id": r["id"],
                            "name": r["name"],
                            "full_name": r["full_name"],
                            "html_url": r["html_url"],
                            "description": r.get("description", ""),
                            "updated_at": r["updated_at"],
                        }
                        for r in repos
                    ]
                return []

            except Exception as e:
                logger.error(f"Error listing repos: {e}")
                return []

    def get_clone_url_with_token(self, repo_name: str) -> str:
        """Get clone URL with embedded token for authentication"""
        repo_name = self._slugify(repo_name)
        # Format: http://token@host:port/user/repo.git
        url_parts = self.base_url.replace("http://", "").replace("https://", "")
        protocol = "https" if "https" in self.base_url else "http"
        return f"{protocol}://{self.token}@{url_parts}/{self.user}/{repo_name}.git"

    def _slugify(self, name: str) -> str:
        """Convert name to valid repo name"""
        import re
        # Convert to lowercase, replace spaces with hyphens
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')


# Singleton instance
gitea_service = GiteaService()
