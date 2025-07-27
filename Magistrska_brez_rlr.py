import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import math

class LaserDistanceMeterSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulator laserskega razdaljemera")
        self.root.geometry("800x600")
        
        # Constants
        self.ROOM_TYPES = ["Dnevna soba", "Kuhinja", "Kopalnica", "Spalnica", "Hodnik", "Pisarna", "Shramba", "Balkon"]
        self.METER_TO_PIXEL = 50
        self.FLOOR_COLORS = ["white", "cyan", "magenta", "green", "orange"]
        self.BASE_ZOOM = 1.0
        self.MIN_ZOOM = 0.1
        self.MAX_ZOOM = 10.0
        
        # Initialize state variables
        self.current_position = (400.0, 300.0)
        self.current_angle = 0
        self.current_floor = 0
        self.current_z = 0.0
        self.lines = []
        self.line_counter = 0
        self.selected_line_index = None
        self.selected_point = None
        self.rooms = []
        self.zoom_level = self.BASE_ZOOM
        self.view_offset = (0, 0)
        self.last_mouse_pos = (0, 0)
        
        # Get initial coordinates
        self.get_initial_coordinates()
        
        # Create UI
        self.create_widgets()
        
        # Draw initial layout
        self.center_view(initial=True)
        self.draw_layout()
    
    def get_initial_coordinates(self):
        """Prompt user for initial coordinates and floor level"""
        x = simpledialog.askfloat("Initial Position", "Enter initial X coordinate (meters):", parent=self.root)
        y = simpledialog.askfloat("Initial Position", "Enter initial Y coordinate (meters):", parent=self.root)
        floor = simpledialog.askinteger("Floor Level", "Enter initial floor level (0,1,2,...):", parent=self.root)
        z = simpledialog.askfloat("Floor Height", "Enter floor height (z) in meters:", parent=self.root)
        
        if x is not None and y is not None:
            self.current_position = (x * self.METER_TO_PIXEL, y * self.METER_TO_PIXEL)
        if floor is not None:
            self.current_floor = floor
        if z is not None:
            self.current_z = z
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Create toolbar frame
        self.toolbar = tk.Frame(self.root, bg="gray20")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Create buttons
        self.measure_btn = tk.Button(self.toolbar, text="Measure", command=self.measure)
        self.turn_left_btn = tk.Button(self.toolbar, text="Turn Left", command=self.turn_left)
        self.turn_right_btn = tk.Button(self.toolbar, text="Turn Right", command=self.turn_right)
        self.select_btn = tk.Button(self.toolbar, text="Select Line/Point", command=self.select_line_point)
        self.finish_btn = tk.Button(self.toolbar, text="Finish Room", command=self.finish_room)
        self.floor_btn = tk.Button(self.toolbar, text="Change Floor", command=self.change_floor)
        self.zoom_in_btn = tk.Button(self.toolbar, text="Zoom In", command=lambda: self.adjust_zoom(1.2))
        self.zoom_out_btn = tk.Button(self.toolbar, text="Zoom Out", command=lambda: self.adjust_zoom(0.8))
        self.center_btn = tk.Button(self.toolbar, text="Center View", command=lambda: self.center_view(initial=False))
        
        # Pack buttons
        buttons = [self.measure_btn, self.turn_left_btn, self.turn_right_btn, 
                  self.select_btn, self.finish_btn, self.floor_btn,
                  self.zoom_in_btn, self.zoom_out_btn, self.center_btn]
        for btn in buttons:
            btn.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create status bar
        self.status_bar = tk.Frame(self.root, bg="black")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create labels
        self.direction_label = tk.Label(self.status_bar, text=f"Direction: {self.current_angle}°", bg="black", fg="white")
        self.direction_label.pack(side=tk.LEFT, padx=5)
        
        self.floor_label = tk.Label(self.status_bar, text=f"Floor: {self.current_floor} (Z: {self.current_z}m)", bg="black", fg="white")
        self.floor_label.pack(side=tk.LEFT, padx=5)
        
        self.zoom_label = tk.Label(self.status_bar, text=f"Zoom: {self.zoom_level:.1f}x", bg="black", fg="white")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        # Bind mouse events
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<ButtonPress-2>", self.on_middle_press)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel zooming"""
        # Get mouse position before zoom
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Determine zoom factor
        zoom_factor = 1.1 if event.delta > 0 else 0.9
        self.adjust_zoom(zoom_factor, (x, y))
    
    def on_middle_press(self, event):
        """Start panning with middle mouse button"""
        self.last_mouse_pos = (event.x, event.y)
    
    def on_middle_drag(self, event):
        """Pan the view with middle mouse drag"""
        dx = event.x - self.last_mouse_pos[0]
        dy = event.y - self.last_mouse_pos[1]
        self.view_offset = (self.view_offset[0] + dx, self.view_offset[1] + dy)
        self.last_mouse_pos = (event.x, event.y)
        self.draw_layout()
    
    def adjust_zoom(self, factor, mouse_pos=None):
        """Adjust zoom level with bounds checking and centered zooming"""
        old_zoom = self.zoom_level
        self.zoom_level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom_level * factor))
        
        if mouse_pos:
            # Adjust view offset to zoom toward mouse position
            x, y = mouse_pos
            self.view_offset = (
                x - (x - self.view_offset[0]) * (self.zoom_level / old_zoom),
                y - (y - self.view_offset[1]) * (self.zoom_level / old_zoom)
            )
        
        self.zoom_label.config(text=f"Zoom: {self.zoom_level:.1f}x")
        self.draw_layout()
    
    def center_view(self, initial=False):
        """Center the view on the weighted center of all lines"""
        if not self.lines:
            # Default to center of canvas if no lines exist
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                self.view_offset = (
                    canvas_width/2 - self.current_position[0] * self.zoom_level,
                    canvas_height/2 - self.current_position[1] * self.zoom_level
                )
            return
        
        # Get lines for current floor
        floor_lines = [line for line in self.lines if line['floor_level'] == self.current_floor]
        if not floor_lines:
            return
        
        # Calculate bounding box
        all_points = []
        for line in floor_lines:
            all_points.append(line['start'])
            all_points.append(line['end'])
        
        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)
        
        # Calculate center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Calculate required zoom to fit all content
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Ensure canvas is sized
            content_width = max_x - min_x
            content_height = max_y - min_y
            
            # Calculate zoom with padding
            zoom_x = (canvas_width - 40) / content_width if content_width > 0 else 1.0
            zoom_y = (canvas_height - 40) / content_height if content_height > 0 else 1.0
            
            self.zoom_level = min(zoom_x, zoom_y, self.MAX_ZOOM)
            self.zoom_level = max(self.zoom_level, self.MIN_ZOOM)
            
            # Calculate new offset to center content
            self.view_offset = (
                canvas_width/2 - center_x * self.zoom_level,
                canvas_height/2 - center_y * self.zoom_level
            )
            
            self.zoom_label.config(text=f"Zoom: {self.zoom_level:.1f}x")
        
        if not initial:
            self.draw_layout()
    
    def transform_point(self, x, y):
        """Apply zoom and pan transformations to a point"""
        return (
            x * self.zoom_level + self.view_offset[0],
            y * self.zoom_level + self.view_offset[1]
        )
    
    def measure(self):
        """Measure a new wall"""
        distance = simpledialog.askfloat("Distance", "Enter distance in meters:", parent=self.root)
        if distance is None:  # User canceled
            return
            
        # Calculate end point
        angle_rad = math.radians(self.current_angle)
        dx = distance * self.METER_TO_PIXEL * math.cos(angle_rad)
        dy = distance * self.METER_TO_PIXEL * math.sin(angle_rad)
        end_point = (self.current_position[0] + dx, self.current_position[1] + dy)
        
        # Get room type
        room_type = self.get_room_type()
        if room_type is None:  # User canceled
            return
            
        # Create new line
        new_line = {
            'id': self.line_counter,
            'start': self.current_position,
            'end': end_point,
            'angle': self.current_angle,
            'length': distance,
            'room_type': room_type,
            'floor_level': self.current_floor,
            'z_level': self.current_z
        }
        
        self.lines.append(new_line)
        self.line_counter += 1
        self.current_position = end_point
        
        # Update display immediately
        self.draw_layout()
        self.center_view()
    
    def get_room_type(self):
        """Show dialog to select room type"""
        popup = tk.Toplevel(self.root)
        popup.title("Select Room Type")
        popup.geometry("300x100")
        
        label = tk.Label(popup, text="Choose room type:")
        label.pack(pady=5)
        
        combo = ttk.Combobox(popup, values=self.ROOM_TYPES, state="readonly")
        combo.pack(pady=5)
        combo.current(0)
        
        selected_type = None
        
        def on_ok():
            nonlocal selected_type
            selected_type = combo.get()
            popup.destroy()
        
        ok_btn = tk.Button(popup, text="OK", command=on_ok)
        ok_btn.pack(pady=5)
        
        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)
        
        return selected_type
    
    def turn_left(self):
        """Turn 90 degrees counterclockwise"""
        self.current_angle = (self.current_angle - 90) % 360
        self.update_direction_label()
        self.draw_layout()
    
    def turn_right(self):
        """Turn 90 degrees clockwise"""
        self.current_angle = (self.current_angle + 90) % 360
        self.update_direction_label()
        self.draw_layout()
    
    def update_direction_label(self):
        """Update the direction indicator label"""
        self.direction_label.config(text=f"Direction: {self.current_angle}°")
    
    def select_line_point(self):
        """Select an existing line and point to continue from"""
        if not self.lines:
            messagebox.showerror("Error", "No lines available to select")
            return
            
        # Create list of line IDs for selection
        line_ids = [str(line['id']) for line in self.lines]
        
        # Show selection dialog
        selected_id = simpledialog.askstring("Select Line", "Enter line ID to select:\nAvailable IDs: " + ", ".join(line_ids), parent=self.root)
        if selected_id is None:
            return
            
        try:
            selected_id = int(selected_id)
            line = next((line for line in self.lines if line['id'] == selected_id), None)
            if line is None:
                messagebox.showerror("Error", f"Line with ID {selected_id} not found")
                return
                
            # Ask for point selection
            point = simpledialog.askstring("Select Point", "Select point to continue from (start/end):", parent=self.root)
            if point is None:
                return
                
            point = point.lower()
            if point not in ['start', 'end']:
                messagebox.showerror("Error", "Must select 'start' or 'end'")
                return
                
            # Update state
            self.selected_line_index = self.lines.index(line)
            self.selected_point = point
            self.current_position = line[point]
            self.current_angle = line['angle']
            self.current_floor = line['floor_level']
            self.current_z = line['z_level']
            
            self.update_direction_label()
            self.update_floor_label()
            
            # Center view on selected point
            self.center_view()
            self.draw_layout()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid line ID")
    
    def finish_room(self):
        """Calculate and display room area"""
        # Get all lines on current floor
        floor_lines = [line for line in self.lines if line['floor_level'] == self.current_floor]
        
        if len(floor_lines) < 2:
            messagebox.showerror("Error", "At least 2 lines needed to form a room")
            return
            
        # Collect all points in order
        points = []
        for line in floor_lines:
            points.append((line['start'][0], line['start'][1]))
        points.append((floor_lines[-1]['end'][0], floor_lines[-1]['end'][1]))
        
        # Calculate area using shoelace formula
        area = 0.0
        n = len(points)
        for i in range(n):
            x_i, y_i = points[i]
            x_j, y_j = points[(i + 1) % n]
            area += (x_i * y_j) - (x_j * y_i)
        
        area = abs(area) / (2 * self.METER_TO_PIXEL ** 2)  # Convert back to square meters
        
        # Store room info
        room_info = {
            'floor': self.current_floor,
            'z_level': self.current_z,
            'area': area,
            'lines': floor_lines.copy()
        }
        self.rooms.append(room_info)
        
        # Show result
        messagebox.showinfo("Room Area", f"Room area: {area:.2f} square meters")
    
    def change_floor(self):
        """Change current floor level"""
        new_floor = simpledialog.askinteger("Change Floor", "Enter new floor level:", parent=self.root)
        if new_floor is None:
            return
            
        # Check if we have lines on the new floor to get z level
        floor_lines = [line for line in self.lines if line['floor_level'] == new_floor]
        if floor_lines:
            self.current_z = floor_lines[0]['z_level']
        else:
            z = simpledialog.askfloat("Floor Height", f"Enter height (z) for floor {new_floor} in meters:", parent=self.root)
            if z is not None:
                self.current_z = z
            else:
                return
                
        self.current_floor = new_floor
        self.update_floor_label()
        
        # Auto-center and zoom when changing floors
        self.center_view()
        self.draw_layout()
    
    def update_floor_label(self):
        """Update the floor indicator label"""
        self.floor_label.config(text=f"Floor: {self.current_floor} (Z: {self.current_z}m)")
    
    def draw_layout(self):
        """Redraw the entire layout on canvas"""
        self.canvas.delete("all")
        
        # Draw all lines for current floor
        for i, line in enumerate(self.lines):
            if line['floor_level'] == self.current_floor:
                color = self.FLOOR_COLORS[line['floor_level'] % len(self.FLOOR_COLORS)]
                if i == self.selected_line_index:
                    color = "yellow"  # Highlight selected line
                
                # Transform points with zoom and pan
                start_x, start_y = self.transform_point(line['start'][0], line['start'][1])
                end_x, end_y = self.transform_point(line['end'][0], line['end'][1])
                
                self.canvas.create_line(
                    start_x, start_y,
                    end_x, end_y,
                    fill=color, width=2
                )
                
                # Add line ID label at midpoint
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2
                self.canvas.create_text(mid_x, mid_y, text=str(line['id']), fill="white")
        
        # Draw current position
        x, y = self.transform_point(self.current_position[0], self.current_position[1])
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="red")
        
        # Draw direction indicator
        angle_rad = math.radians(self.current_angle)
        dx = 20 * math.cos(angle_rad)
        dy = 20 * math.sin(angle_rad)
        self.canvas.create_line(x, y, x+dx, y+dy, fill="green", arrow=tk.LAST, width=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = LaserDistanceMeterSimulator(root)
    root.mainloop()