"""Shared objects the routes need, taken from the app's state (built at startup)."""

from fastapi import Request

from app.core.config import Settings
from app.workflows.review_graph import ReviewGraph


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


def get_graph(request: Request) -> ReviewGraph:
    return request.app.state.graph
