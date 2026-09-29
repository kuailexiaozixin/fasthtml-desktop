"""Developer surface compatibility module.

Navigation contract:
href="/api/docs"
href="/swagger.json"

Public reads use synthetic data. Selected draft writes require
FASTSME_API_TOKEN and never apply changes to an authoritative scenario.
"""
from .views import developer_page

__all__ = ["developer_page"]
