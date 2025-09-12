"""
TUI Views package.
Contains all the main view components for the application screens.
"""

from .dashboard import DashboardView
from .workouts import WorkoutView
from .plans import PlanView
from .rules import RuleView
from .routes import RouteView

__all__ = [
    'DashboardView',
    'WorkoutView', 
    'PlanView',
    'RuleView',
    'RouteView'
]