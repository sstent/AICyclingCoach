"""
Rules view for AI Cycling Coach TUI.
Manages training rules with CRUD functionality.
"""
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, DataTable, Button, Input, TextArea, LoadingIndicator,
    TabbedContent, TabPane, Label, Select, ContentSwitcher
)
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from typing import List, Dict, Optional

from backend.app.database import AsyncSessionLocal
from tui.services.rule_service import RuleService


class RuleForm(Widget):
    """Form for creating/editing training rules."""
    
    def __init__(self, rule_data: Optional[Dict] = None):
        super().__init__()
        self.rule_data = rule_data
        
    def compose(self) -> ComposeResult:
        """Create rule form layout."""
        with Vertical():
            # Rule name
            yield Label("Rule Name:")
            yield Input(
                value=self.rule_data.get("name", "") if self.rule_data else "",
                placeholder="e.g., Recovery Day Rule",
                id="rule-name"
            )
            
            # Rule description
            yield Label("Description:")
            yield TextArea(
                text=self.rule_data.get("description", "") if self.rule_data else "",
                id="rule-description",
                language="markdown"
            )
            
            # Rule text (YAML)
            yield Label("Rule Definition (YAML):")
            yield TextArea(
                text=self.rule_data.get("rule_text", "") if self.rule_data else "",
                id="rule-text",
                language="yaml"
            )
            
            # Rule type
            yield Label("Rule Type:")
            rule_type = Select(
                [
                    ("intensity", "Intensity"),
                    ("recovery", "Recovery"),
                    ("progression", "Progression"),
                    ("frequency", "Frequency"),
                    ("other", "Other")
                ],
                value=self.rule_data.get("rule_type", "intensity") if self.rule_data else "intensity",
                id="rule-type"
            )
            yield rule_type
            
            # Buttons
            with Horizontal():
                yield Button("Save", id="save-rule-btn", variant="primary")
                yield Button("Cancel", id="cancel-rule-btn")


class RuleView(Widget):
    """Training rules management view."""
    
    # Reactive attributes
    rules = reactive([])
    loading = reactive(True)
    current_view = reactive("list")  # list, create, edit, detail
    selected_rule = reactive(None)
    error_message = reactive("")
    show_delete_confirm = reactive(False)
    
    DEFAULT_CSS = """
    .header-row {
        layout: horizontal;
        width: 100%;
        margin-bottom: 1;
    }
    
    .header-title {
        width: 1fr;
        color: $accent;
        text-style: bold;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }
    
    .rule-column {
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
    
    .error-message {
        color: $error;
        padding: 1;
        border: solid $error;
        margin: 1 0;
    }
    
    .confirm-dialog {
        border: solid $warning;
        padding: 1;
        margin: 1 0;
        background: $panel;
    }
    """
    
    class RuleSelected(Message):
        """Message sent when a rule is selected."""
        def __init__(self, rule_id: int):
            super().__init__()
            self.rule_id = rule_id
    
    class RuleCreated(Message):
        """Message sent when a new rule is created."""
        def __init__(self, rule_data: Dict):
            super().__init__()
            self.rule_data = rule_data
    
    class RuleUpdated(Message):
        """Message sent when a rule is updated."""
        def __init__(self, rule_data: Dict):
            super().__init__()
            self.rule_data = rule_data
    
    class RuleDeleted(Message):
        """Message sent when a rule is deleted."""
        def __init__(self, rule_id: int):
            super().__init__()
            self.rule_id = rule_id
    
    def compose(self) -> ComposeResult:
        """Create rules view layout."""
        # Header with title and Add Rule button
        with Horizontal(classes="header-row"):
            yield Static("Training Rules", classes="header-title")
            yield Button("Add Rule", id="header-add-rule-btn", variant="primary")
        
        if self.loading:
            yield LoadingIndicator(id="rules-loader")
        else:
            with ContentSwitcher(initial=self.current_view):
                # List view
                with Container(id="list-view"):
                    yield self.compose_rule_list()
                
                # Create view
                with Container(id="create-view"):
                    yield RuleForm()
                
                # Edit view
                with Container(id="edit-view"):
                    yield RuleForm(self.selected_rule) if self.selected_rule else Static("No rule selected")
            
            # Error message display
            if self.error_message:
                yield Static(self.error_message, classes="error-message")
            
            # Delete confirmation dialog
            if self.show_delete_confirm and self.selected_rule:
                with Container(classes="confirm-dialog"):
                    yield Static(f"Delete rule '{self.selected_rule.get('name', '')}'? This cannot be undone.")
                    with Horizontal():
                        yield Button("Confirm Delete", id="confirm-delete-btn", variant="error")
                        yield Button("Cancel", id="cancel-delete-btn")
    
    def compose_rule_list(self) -> ComposeResult:
        """Create rule list view."""
        with Container():
            with Horizontal(classes="button-row"):
                yield Button("Refresh", id="refresh-rules-btn")
                yield Button("New Rule", id="new-rule-btn", variant="primary")
            
            # Rules table
            rules_table = DataTable(id="rules-table")
            rules_table.add_columns("ID", "Name", "Type", "Version", "Last Updated", "Actions")
            yield rules_table
            
            # Action buttons for selected rule
            with Horizontal(id="rule-actions", classes="button-row"):
                yield Button("Edit Rule", id="edit-rule-btn", disabled=True)
                yield Button("Delete Rule", id="delete-rule-btn", variant="error", disabled=True)
    
    async def on_mount(self) -> None:
        """Load rules when mounted."""
        await self.load_rules()
    
    async def load_rules(self) -> None:
        """Load rules from database."""
        self.loading = True
        self.refresh()
        
        try:
            async with AsyncSessionLocal() as db:
                rule_service = RuleService(db)
                self.rules = await rule_service.get_rules()
                self.log(f"Loaded {len(self.rules)} rules from database")
                await self.populate_rules_table()
        except Exception as e:
            error_msg = f"Error loading rules: {str(e)}"
            self.error_message = error_msg
            self.log(error_msg, severity="error")
        finally:
            self.loading = False
            self.refresh()
    
    async def populate_rules_table(self) -> None:
        """Populate rules table with data."""
        try:
            rules_table = self.query_one("#rules-table", DataTable)
            if not rules_table:
                self.log("Rules table widget not found", severity="error")
                return
                
            rules_table.clear()
            self.log(f"Populating table with {len(self.rules)} rules")
            
            if not self.rules:
                # Add placeholder row when no rules exist
                rules_table.add_row("No rules found", "", "", "", "")
                self.log("No rules to display")
                return
                
            for rule in self.rules:
                last_updated = "N/A"
                if rule.get("created_at"):
                    try:
                        dt = datetime.fromisoformat(rule["created_at"].replace('Z', '+00:00'))
                        last_updated = dt.strftime("%m/%d/%Y")
                    except:
                        last_updated = rule["created_at"][:10]
                
                rules_table.add_row(
                    str(rule["id"]),
                    rule.get("name", "Unknown"),
                    rule.get("rule_type", "N/A"),
                    str(rule.get("version", "1")),
                    last_updated,
                    "Edit | Delete"
                )
            self.log("Rules table populated successfully")
        except Exception as e:
            error_msg = f"Error populating table: {str(e)}"
            self.error_message = error_msg
            self.log(error_msg, severity="error")
            self.refresh()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        try:
            if event.button.id == "refresh-rules-btn":
                await self.refresh_rules()
            elif event.button.id == "header-add-rule-btn" or event.button.id == "new-rule-btn":
                await self.show_create_view()
            elif event.button.id == "edit-rule-btn":
                await self.show_edit_view()
            elif event.button.id == "delete-rule-btn":
                self.show_delete_confirm = True
                self.refresh()
            elif event.button.id == "save-rule-btn":
                await self.save_rule()
            elif event.button.id == "cancel-rule-btn":
                await self.show_list_view()
            elif event.button.id == "confirm-delete-btn":
                await self.delete_rule()
            elif event.button.id == "cancel-delete-btn":
                self.show_delete_confirm = False
                self.refresh()
        except Exception as e:
            self.error_message = f"Button error: {str(e)}"
            self.refresh()
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle rule selection in table."""
        try:
            if event.data_table.id == "rules-table":
                row_index = event.row_key.value if hasattr(event.row_key, 'value') else event.cursor_row
                if 0 <= row_index < len(self.rules):
                    self.selected_rule = self.rules[row_index]
                    self.post_message(self.RuleSelected(self.selected_rule["id"]))
                    
                    # Enable action buttons
                    self.query_one("#edit-rule-btn").disabled = False
                    self.query_one("#delete-rule-btn").disabled = False
        except Exception as e:
            self.error_message = f"Selection error: {str(e)}"
            self.refresh()
    
    async def refresh_rules(self) -> None:
        """Reload rules from database."""
        self.loading = True
        self.refresh()
        await self.load_rules()
    
    async def show_create_view(self) -> None:
        """Switch to rule creation view."""
        self.current_view = "create"
        self.error_message = ""
        self.refresh()
    
    async def show_edit_view(self) -> None:
        """Switch to rule edit view."""
        if self.selected_rule:
            self.current_view = "edit"
            self.error_message = ""
            self.refresh()
    
    async def show_list_view(self) -> None:
        """Switch back to list view."""
        self.current_view = "list"
        self.error_message = ""
        self.show_delete_confirm = False
        self.refresh()
    
    async def save_rule(self) -> None:
        """Save new or updated rule."""
        try:
            name_input = self.query_one("#rule-name", Input)
            description_text = self.query_one("#rule-description", TextArea)
            rule_text = self.query_one("#rule-text", TextArea)
            rule_type = self.query_one("#rule-type", Select)
            
            rule_data = {
                "name": name_input.value.strip(),
                "description": description_text.text,
                "rule_text": rule_text.text,
                "rule_type": rule_type.value
            }
            
            if not rule_data["name"]:
                raise ValueError("Rule name is required")
            if not rule_data["rule_text"]:
                raise ValueError("Rule definition is required")
            
            async with AsyncSessionLocal() as db:
                rule_service = RuleService(db)
                
                if self.current_view == "create":
                    result = await rule_service.create_rule(
                        name=rule_data["name"],
                        description=rule_data["description"],
                        rule_text=rule_data["rule_text"],
                        rule_type=rule_data["rule_type"]
                    )
                    self.post_message(self.RuleCreated(result))
                else:
                    if not self.selected_rule:
                        raise ValueError("No rule selected for editing")
                    result = await rule_service.update_rule(
                        self.selected_rule["id"],
                        name=rule_data["name"],
                        description=rule_data["description"],
                        rule_text=rule_data["rule_text"],
                        rule_type=rule_data["rule_type"]
                    )
                    self.post_message(self.RuleUpdated(result))
                
                # Refresh rules list
                await self.refresh_rules()
                await self.show_list_view()
                
        except Exception as e:
            self.error_message = f"Save failed: {str(e)}"
            self.refresh()
    
    async def delete_rule(self) -> None:
        """Delete the selected rule."""
        try:
            if not self.selected_rule:
                raise ValueError("No rule selected for deletion")
            
            async with AsyncSessionLocal() as db:
                rule_service = RuleService(db)
                rule_id = self.selected_rule["id"]
                await rule_service.delete_rule(rule_id)
                self.post_message(self.RuleDeleted(rule_id))
                
                # Clear selection and refresh list
                self.selected_rule = None
                self.show_delete_confirm = False
                await self.refresh_rules()
                await self.show_list_view()
                
        except Exception as e:
            self.error_message = f"Delete failed: {str(e)}"
            self.refresh()