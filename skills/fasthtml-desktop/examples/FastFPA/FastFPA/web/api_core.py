"""FastSME API contract marker.

FastFPA uses a domain-specific FastAPI surface rather than generic table CRUD.
Public reads expose synthetic data; the selected draft POST is disabled unless
FASTSME_API_TOKEN is configured.
"""
