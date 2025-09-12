"""
Routes view for AI Cycling Coach TUI.
Displays GPX routes, route management, and visualization.
"""
import math
from typing import List, Dict, Tuple, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, DataTable, Button, Input, TextArea, LoadingIndicator,
    TabbedContent, TabPane, Label, DirectoryTree
)
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message

from backend.app.database import AsyncSessionLocal
from tui.services.route_service import RouteService


class GPXVisualization(Widget):
    """ASCII-based GPX route visualization."""
    
    def __init__(self, route_data: Dict):
        super().__init__()
        self.route_data = route_data
    
    def compose(self) -> ComposeResult:
        """Create GPX visualization."""
        yield Label(f"Route: {self.route_data.get('name', 'Unknown')}")
        
        # Route summary
        distance = self.route_data.get('total_distance', 0)
        elevation = self.route_data.get('elevation_gain', 0)
        
        summary = f"Distance: {distance/1000:.2f} km | Elevation Gain: {elevation:.0f} m"
        yield Static(summary)
        
        # ASCII route visualization
        if self.route_data.get('track_points'):
            yield self.create_route_map()
            yield self.create_elevation_profile()
        else:
            yield Static("No track data available for visualization")
    
    def create_route_map(self) -> Static:
        """Create ASCII map of the route."""
        track_points = self.route_data.get('track_points', [])
        if not track_points:
            return Static("No track points available")
        
        # Extract coordinates
        lats = [float(p.get('lat', 0)) for p in track_points if p.get('lat')]
        lons = [float(p.get('lon', 0)) for p in track_points if p.get('lon')]
        
        if not lats or not lons:
            return Static("Invalid coordinate data")
        
        # Normalize coordinates to terminal space
        width, height = 60, 20
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Avoid division by zero
        lat_range = max_lat - min_lat if max_lat != min_lat else 1
        lon_range = max_lon - min_lon if max_lon != min_lon else 1
        
        # Create ASCII grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Plot route points
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            x = int((lon - min_lon) / lon_range * (width - 1))
            y = int((lat - min_lat) / lat_range * (height - 1))
            
            # Use different characters for start, end, and middle
            if i == 0:
                char = 'S'  # Start
            elif i == len(lats) - 1:
                char = 'E'  # End
            else:
                char = '●'  # Route point
            
            if 0 <= y < height and 0 <= x < width:
                grid[height - 1 - y][x] = char  # Flip Y axis
        
        # Convert grid to string
        map_lines = [''.join(row) for row in grid]
        map_text = "Route Map:\n" + '\n'.join(map_lines)
        map_text += f"\nS = Start, E = End, ● = Route"
        
        return Static(map_text)
    
    def create_elevation_profile(self) -> Static:
        """Create ASCII elevation profile."""
        track_points = self.route_data.get('track_points', [])
        elevations = [float(p.get('ele', 0)) for p in track_points if p.get('ele')]
        
        if not elevations:
            return Static("No elevation data available")
        
        # Normalize elevation data
        width = 60
        height = 10
        
        min_ele, max_ele = min(elevations), max(elevations)
        ele_range = max_ele - min_ele if max_ele != min_ele else 1
        
        # Sample elevations to fit width
        if len(elevations) > width:
            step = len(elevations) // width
            elevations = elevations[::step][:width]
        
        # Create elevation profile
        profile_lines = []
        for h in range(height):
            line = []
            threshold = min_ele + (height - h) / height * ele_range
            
            for ele in elevations:
                if ele >= threshold:
                    line.append('█')
                else:
                    line.append(' ')
            profile_lines.append(''.join(line))
        
        # Add elevation markers
        profile_text = f"Elevation Profile ({min_ele:.0f}m - {max_ele:.0f}m):\n"
        profile_text += '\n'.join(profile_lines)
        
        return Static(profile_text)


class RouteFileUpload(Widget):
    """File upload widget for GPX files."""
    
    def compose(self) -> ComposeResult:
        """Create file upload interface."""
        yield Label("Upload GPX Files")
        yield Button("Browse Files", id="browse-gpx-btn", variant="primary")
        yield Static("", id="upload-status")
        
        # Directory tree for local file browsing
        yield Label("Or browse local files:")
        yield DirectoryTree("./data/gpx", id="gpx-directory")


class RouteView(Widget):
    """Route management and visualization view."""
    
    # Reactive attributes
    routes = reactive([])
    selected_route = reactive(None)
    loading = reactive(True)
    
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
    
    .route-column {
        width: 1fr;
        margin: 0 1;
    }
    
    .upload-container {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .button-row {
        margin: 1 0;
    }
    
    .visualization-container {
        border: solid $secondary;
        padding: 1;
        margin: 1 0;
        min-height: 30;
    }
    """
    
    class RouteSelected(Message):
        """Message sent when a route is selected."""
        def __init__(self, route_id: int):
            super().__init__()
            self.route_id = route_id
    
    class RouteUploaded(Message):
        """Message sent when a route is uploaded."""
        def __init__(self, route_data: Dict):
            super().__init__()
            self.route_data = route_data
    
    def compose(self) -> ComposeResult:
        """Create route view layout."""
        yield Static("Routes & GPX Files", classes="view-title")
        
        if self.loading:
            yield LoadingIndicator(id="routes-loader")
        else:
            with TabbedContent():
                with TabPane("Route List", id="route-list-tab"):
                    yield self.compose_route_list()
                
                with TabPane("Upload GPX", id="upload-gpx-tab"):
                    yield self.compose_file_upload()
                
                if self.selected_route:
                    with TabPane("Route Visualization", id="route-viz-tab"):
                        yield self.compose_route_visualization()
    
    def compose_route_list(self) -> ComposeResult:
        """Create route list view."""
        with Container():
            with Horizontal(classes="button-row"):
                yield Button("Refresh", id="refresh-routes-btn")
                yield Button("Import GPX", id="import-gpx-btn", variant="primary")
                yield Button("Analyze Routes", id="analyze-routes-btn")
            
            # Routes table
            routes_table = DataTable(id="routes-table")
            routes_table.add_columns("Name", "Distance", "Elevation", "Sections", "Actions")
            yield routes_table
            
            # Route sections (if any)
            yield Static("Route Sections", classes="section-title")
            sections_table = DataTable(id="sections-table")
            sections_table.add_columns("Section", "Distance", "Grade", "Difficulty")
            yield sections_table
    
    def compose_file_upload(self) -> ComposeResult:
        """Create file upload view."""
        with Container(classes="upload-container"):
            yield RouteFileUpload()
    
    def compose_route_visualization(self) -> ComposeResult:
        """Create route visualization view."""
        if not self.selected_route:
            yield Static("No route selected")
            return
        
        with Container(classes="visualization-container"):
            yield GPXVisualization(self.selected_route)
    
    async def on_mount(self) -> None:
        """Load route data when mounted."""
        try:
            await self.load_routes_data()
        except Exception as e:
            self.log(f"Routes loading error: {e}", severity="error")
            self.loading = False
            self.refresh()
    
    async def load_routes_data(self) -> None:
        """Load routes data."""
        try:
            async with AsyncSessionLocal() as db:
                route_service = RouteService(db)
                self.routes = await route_service.get_routes()
                
                # Update loading state
                self.loading = False
                self.refresh()
                
                # Populate UI elements
                await self.populate_routes_table()
                
        except Exception as e:
            self.log(f"Error loading routes data: {e}", severity="error")
            self.loading = False
            self.refresh()
    
    async def populate_routes_table(self) -> None:
        """Populate the routes table."""
        try:
            routes_table = self.query_one("#routes-table", DataTable)
            routes_table.clear()
            
            for route in self.routes:
                distance_km = route.get("total_distance", 0) / 1000
                elevation_m = route.get("elevation_gain", 0)
                
                routes_table.add_row(
                    route.get("name", "Unknown"),
                    f"{distance_km:.1f} km",
                    f"{elevation_m:.0f} m",
                    "0",  # TODO: Count sections
                    "View | Edit"
                )
                
        except Exception as e:
            self.log(f"Error populating routes table: {e}", severity="error")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        try:
            if event.button.id == "refresh-routes-btn":
                await self.refresh_routes()
            elif event.button.id == "import-gpx-btn":
                await self.show_file_upload()
            elif event.button.id == "browse-gpx-btn":
                await self.browse_gpx_files()
            elif event.button.id == "analyze-routes-btn":
                await self.analyze_routes()
                
        except Exception as e:
            self.log(f"Button press error: {e}", severity="error")
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in routes table."""
        try:
            if event.data_table.id == "routes-table":
                # Get route index from row selection
                row_index = event.row_key.value if hasattr(event.row_key, 'value') else event.cursor_row
                
                if 0 <= row_index < len(self.routes):
                    selected_route = self.routes[row_index]
                    await self.show_route_visualization(selected_route)
                    
        except Exception as e:
            self.log(f"Row selection error: {e}", severity="error")
    
    async def on_directory_tree_file_selected(self, event) -> None:
        """Handle file selection from directory tree."""
        try:
            file_path = str(event.path)
            if file_path.lower().endswith('.gpx'):
                await self.load_gpx_file(file_path)
                
        except Exception as e:
            self.log(f"File selection error: {e}", severity="error")
    
    async def show_route_visualization(self, route_data: Dict) -> None:
        """Show visualization for a route."""
        try:
            # Load additional route data if needed
            async with AsyncSessionLocal() as db:
                route_service = RouteService(db)
                full_route_data = await route_service.load_gpx_file(
                    route_data.get("gpx_file_path", "")
                )
                
                self.selected_route = full_route_data
                self.refresh()
                
                # Switch to visualization tab
                tabs = self.query_one(TabbedContent)
                tabs.active = "route-viz-tab"
                
                # Post message that route was selected
                self.post_message(self.RouteSelected(route_data["id"]))
                
        except Exception as e:
            self.log(f"Error showing route visualization: {e}", severity="error")
    
    async def refresh_routes(self) -> None:
        """Refresh the routes list."""
        self.loading = True
        self.refresh()
        await self.load_routes_data()
    
    async def show_file_upload(self) -> None:
        """Switch to the file upload tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "upload-gpx-tab"
    
    async def browse_gpx_files(self) -> None:
        """Browse for GPX files."""
        try:
            # Update status
            status = self.query_one("#upload-status", Static)
            status.update("Click on a .gpx file in the directory tree below")
            
        except Exception as e:
            self.log(f"Error browsing files: {e}", severity="error")
    
    async def load_gpx_file(self, file_path: str) -> None:
        """Load a GPX file and create route visualization."""
        try:
            self.log(f"Loading GPX file: {file_path}", severity="info")
            
            async with AsyncSessionLocal() as db:
                route_service = RouteService(db)
                route_data = await route_service.load_gpx_file(file_path)
                
                # Create visualization
                self.selected_route = route_data
                self.refresh()
                
                # Switch to visualization tab
                tabs = self.query_one(TabbedContent)
                tabs.active = "route-viz-tab"
                
                # Update upload status
                status = self.query_one("#upload-status", Static)
                status.update(f"Loaded: {route_data.get('name', 'Unknown Route')}")
                
                # Post message about route upload
                self.post_message(self.RouteUploaded(route_data))
                
        except Exception as e:
            self.log(f"Error loading GPX file: {e}", severity="error")
            
            # Update status with error
            try:
                status = self.query_one("#upload-status", Static)
                status.update(f"Error: {str(e)}")
            except:
                pass
    
    async def analyze_routes(self) -> None:
        """Analyze all routes for insights."""
        try:
            if not self.routes:
                self.log("No routes to analyze", severity="warning")
                return
            
            # Calculate route statistics
            total_distance = sum(r.get("total_distance", 0) for r in self.routes) / 1000
            total_elevation = sum(r.get("elevation_gain", 0) for r in self.routes)
            avg_distance = total_distance / len(self.routes)
            
            analysis = f"""Route Analysis:
• Total Routes: {len(self.routes)}
• Total Distance: {total_distance:.1f} km
• Total Elevation: {total_elevation:.0f} m
• Average Distance: {avg_distance:.1f} km
• Average Elevation: {total_elevation / len(self.routes):.0f} m"""
            
            self.log("Route Analysis Complete", severity="info")
            self.log(analysis, severity="info")
            
        except Exception as e:
            self.log(f"Error analyzing routes: {e}", severity="error")
    
    def watch_loading(self, loading: bool) -> None:
        """React to loading state changes."""
        if hasattr(self, '_mounted') and self._mounted:
            self.refresh()