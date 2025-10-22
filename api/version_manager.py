from fastapi import FastAPI
from typing import Dict, List

class APIVersionManager:
    def __init__(self):
        self.versions = {
            "v1": {
                "description": "Version 1 - Initial API release",
                "status": "stable",
                "deprecated": False
            },
            "v2": {
                "description": "Version 2 - Testing version",
                "status": "beta",
                "deprecated": False
            }
        }
        self.default_version = "v1"
    
    def get_available_versions(self) -> List[str]:
        return list(self.versions.keys())
    
    def get_version_info(self, version: str = None) -> Dict:
        if version and version in self.versions:
            return {
                "version": version,
                **self.versions[version]
            }
        return {
            "current_version": self.default_version,
            "available_versions": self.get_available_versions(),
            "default_version": self.default_version,
            "versions": self.versions
        }
    
    def register_version_routes(self, app: FastAPI):
        @app.get("/api/version")
        async def get_version_info():
            return self.get_version_info()
        
        @app.get("/api/v1/version")
        async def get_v1_version_info():
            return self.get_version_info("v1")
        
        @app.get("/api/v2/version")
        async def get_v2_version_info():
            return self.get_version_info("v2")

version_manager = APIVersionManager()