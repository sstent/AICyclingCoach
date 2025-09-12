"""
Plan view for AI Cycling Coach TUI.
Displays training plans, plan generation, and plan management.
"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, DataTable, Button, Input, TextArea, Select, LoadingIndicator,
    Collapsible, TabbedContent, TabPane, Label
)
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from typing import List, Dict, Optional

from backend.app.database import AsyncSessionLocal
from tui.services.plan_service import PlanService
from tui.services.rule_service import RuleService


class PlanGenerationForm(Widget):
    """Form for generating new training plans."""
    
    def compose(self) -> ComposeResult:
        """Create plan generation form."""
        yield Label("Plan Generation")
        
        with Vertical():
            yield Label("Training Goals:")
            yield Input(placeholder="e.g., Build endurance, Improve power", id="goals-input")
            
            yield Label("Weekly Training Days:")
            yield Select(
                [(str(i), str(i)) for i in range(1, 8)],
                value="4",
                id="training-days-select"
            )
            
            yield Label("Select Training Rules:")
            yield Select(
                [("loading", "Loading rules...")],
                id="rules-select",
                allow_multiple=True
            )
            
            with Horizontal():
                yield Button("Generate Plan", id="generate-plan-btn", variant="primary")
                yield Button("Clear Form", id="clear-form-btn")


class PlanDetailsModal(Widget):
    """Modal for viewing plan details."""
    
    def __init__(self, plan_data: Dict):
        super().__init__()
        self.plan_data = plan_data
    
    def compose(self) -> ComposeResult:
        """Create plan details modal."""
        yield Label(f"Plan Details - Version {self.plan_data.get('version', 'N/A')}")
        
        with ScrollableContainer():
            yield Label(f"Created: {self.plan_data.get('created_at', 'Unknown')[:10]}")
            
            # Display plan content
            plan_content = str(self.plan_data.get('plan_data', {}))
            yield TextArea(plan_content, read_only=True, id="plan-content")
            
            with Horizontal():
                yield Button("Close", id="close-modal-btn")
                yield Button("Edit Plan", id="edit-plan-btn", variant="primary")


class PlanView(Widget):
    """Training plan management view."""
    
    # Reactive attributes
    plans = reactive([])
    rules = reactive([])
    loading = reactive(True)
    current_view = reactive("list")  # list, generate, details
    selected_plan = reactive(None)
    
    DEFAULT_CSS = """
    .view-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    .plan-column {
        width: 1fr;
        margin: 0 1;
    }
    
    .form-container {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .button-row {
        margin: 1 0;
    }
    """
    
    class PlanSelected(Message):
        """Message sent when a plan is selected."""
        def __init__(self, plan_id: int):
            super().__init__()
            self.plan_id = plan_id
    
    class PlanGenerated(Message):
        """Message sent when a new plan is generated."""
        def __init__(self, plan_data: Dict):
            super().__init__()
            self.plan_data = plan_data
    
    def compose(self) -> ComposeResult:
        """Create plan view layout."""
        yield Static("Training Plans", classes="view-title")
        
        if self.loading:
            yield LoadingIndicator(id="plans-loader")
        else:
            with TabbedContent():
                with TabPane("Plan List", id="plan-list-tab"):
                    yield self.compose_plan_list()
                
                with TabPane("Generate Plan", id="generate-plan-tab"):
                    yield self.compose_plan_generator()
    
    def compose_plan_list(self) -> ComposeResult:
        """Create plan list view."""
        with Container():
            with Horizontal(classes="button-row"):
                yield Button("Refresh", id="refresh-plans-btn")
                yield Button("New Plan", id="new-plan-btn", variant="primary")
            
            # Plans table
            plans_table = DataTable(id="plans-table")
            plans_table.add_columns("ID", "Version", "Created", "Actions")
            yield plans_table
    
    def compose_plan_generator(self) -> ComposeResult:
        """Create plan generation view."""
        with Container():
            yield PlanGenerationForm()
    
    async def on_mount(self) -> None:
        """Load plan data when mounted."""
        try:
            await self.load_plans_data()
        except Exception as e:
            self.log(f"Plans loading error: {e}", severity="error")
            self.loading = False
            self.refresh()
    
    async def load_plans_data(self) -> None:
        """Load plans and rules data."""
        try:
            async with AsyncSessionLocal() as db:
                plan_service = PlanService(db)
                rule_service = RuleService(db)
                
                # Load plans and rules
                self.plans = await plan_service.get_plans()
                self.rules = await rule_service.get_rules()
                
                # Update loading state
                self.loading = False
                self.refresh()
                
                # Populate UI elements
                await self.populate_plans_table()
                await self.populate_rules_select()
                
        except Exception as e:
            self.log(f"Error loading plans data: {e}", severity="error")
            self.loading = False
            self.refresh()
    
    async def populate_plans_table(self) -> None:
        """Populate the plans table."""
        try:
            plans_table = self.query_one("#plans-table", DataTable)
            plans_table.clear()
            
            for plan in self.plans:
                created_date = "Unknown"
                if plan.get("created_at"):
                    created_date = plan["created_at"][:10]  # Extract date part
                
                plans_table.add_row(
                    str(plan["id"]),
                    f"v{plan['version']}",
                    created_date,
                    "View | Edit"
                )
                
        except Exception as e:
            self.log(f"Error populating plans table: {e}", severity="error")
    
    async def populate_rules_select(self) -> None:
        """Populate the rules select dropdown."""
        try:
            rules_select = self.query_one("#rules-select", Select)
            
            # Create options from rules
            options = [(str(rule["id"]), f"{rule['name']} (v{rule['version']})")
                      for rule in self.rules]
            
            rules_select.set_options(options)
            
        except Exception as e:
            self.log(f"Error populating rules select: {e}", severity="error")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        try:
            if event.button.id == "refresh-plans-btn":
                await self.refresh_plans()
            elif event.button.id == "new-plan-btn":
                await self.show_plan_generator()
            elif event.button.id == "generate-plan-btn":
                await self.generate_new_plan()
            elif event.button.id == "clear-form-btn":
                await self.clear_generation_form()
                
        except Exception as e:
            self.log(f"Button press error: {e}", severity="error")
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in plans table."""
        try:
            if event.data_table.id == "plans-table":
                # Get selected plan ID from the first column
                row_data = event.data_table.get_row(event.row_key)
                plan_id = int(row_data[0])
                
                # Find the selected plan
                selected_plan = next((p for p in self.plans if p["id"] == plan_id), None)
                if selected_plan:
                    self.selected_plan = selected_plan
                    await self.show_plan_details(selected_plan)
                    
        except Exception as e:
            self.log(f"Row selection error: {e}", severity="error")
    
    async def refresh_plans(self) -> None:
        """Refresh the plans list."""
        self.loading = True
        self.refresh()
        await self.load_plans_data()
    
    async def show_plan_generator(self) -> None:
        """Switch to the plan generator tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "generate-plan-tab"
    
    async def show_plan_details(self, plan_data: Dict) -> None:
        """Show detailed view of a plan."""
        # For now, just log the plan details
        # In a full implementation, this would show a modal or detailed view
        self.log(f"Showing details for plan {plan_data['id']}")
        
        # Post message that plan was selected
        self.post_message(self.PlanSelected(plan_data["id"]))
    
    async def generate_new_plan(self) -> None:
        """Generate a new training plan."""
        try:
            # Get form values
            goals_input = self.query_one("#goals-input", Input)
            training_days_select = self.query_one("#training-days-select", Select)
            rules_select = self.query_one("#rules-select", Select)
            
            goals_text = goals_input.value.strip()
            if not goals_text:
                self.log("Please enter training goals", severity="warning")
                return
            
            # Get selected rule IDs
            selected_rule_ids = []
            if hasattr(rules_select, 'selected') and rules_select.selected:
                if isinstance(rules_select.selected, list):
                    selected_rule_ids = [int(rule_id) for rule_id in rules_select.selected]
                else:
                    selected_rule_ids = [int(rules_select.selected)]
            
            if not selected_rule_ids:
                self.log("Please select at least one training rule", severity="warning")
                return
            
            # Generate plan
            async with AsyncSessionLocal() as db:
                plan_service = PlanService(db)
                
                goals_dict = {
                    "description": goals_text,
                    "training_days_per_week": int(training_days_select.value),
                    "focus": "general_fitness"
                }
                
                result = await plan_service.generate_plan(
                    rule_ids=selected_rule_ids,
                    goals=goals_dict
                )
                
                # Add new plan to local list
                self.plans.insert(0, result["plan"])
                
                # Refresh the table
                await self.populate_plans_table()
                
                # Post message about new plan
                self.post_message(self.PlanGenerated(result["plan"]))
                
                # Switch back to list view
                tabs = self.query_one(TabbedContent)
                tabs.active = "plan-list-tab"
                
                self.log(f"Successfully generated new training plan!", severity="info")
                
        except Exception as e:
            self.log(f"Error generating plan: {e}", severity="error")
    
    async def clear_generation_form(self) -> None:
        """Clear the plan generation form."""
        try:
            self.query_one("#goals-input", Input).value = ""
            self.query_one("#training-days-select", Select).value = "4"
            # Note: Rules select clearing might need different approach depending on Textual version
            
        except Exception as e:
            self.log(f"Error clearing form: {e}", severity="error")
    
    def watch_loading(self, loading: bool) -> None:
        """React to loading state changes."""
        if hasattr(self, '_mounted') and self._mounted:
            self.refresh()