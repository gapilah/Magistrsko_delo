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
        
        # UI state variables
        self.current_menu = "main"
        self.selected_option = 0
        self.room_type_var = tk.StringVar()
        self.point_var = tk.StringVar(value="end")
        
        # Create UI
        self.create_widgets()
        self.get_initial_coordinates()
        self.center_view(initial=True)
        self.draw_layout()
    
    def transform_point(self, x, y):
        return (
            x * self.zoom_level + self.view_offset[0],
            y * self.zoom_level + self.view_offset[1]
        )
    
    def get_initial_coordinates(self):
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
        # Main container
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menu toolbar - now using a single frame that gets cleared
        self.menu_toolbar = tk.Frame(self.main_frame, bg="gray20")
        self.menu_toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Canvas
        self.canvas = tk.Canvas(self.main_frame, bg="black")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Navigation buttons
        self.button_frame = tk.Frame(self.main_frame, bg="gray20")
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.left_btn = tk.Button(self.button_frame, text="← Back", command=self.left_pressed, 
                                font=('Arial', 12), width=8)
        self.right_btn = tk.Button(self.button_frame, text="Next →", command=self.right_pressed, 
                                 font=('Arial', 12), width=8)
        self.ok_btn = tk.Button(self.button_frame, text="OK", command=self.ok_pressed, 
                              font=('Arial', 12), width=8)
        
        self.left_btn.pack(side=tk.LEFT, padx=5, pady=2)
        self.right_btn.pack(side=tk.LEFT, padx=5, pady=2)
        self.ok_btn.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Status bar
        self.status_bar = tk.Frame(self.root, bg="black")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.direction_label = tk.Label(self.status_bar, text=f"Direction: {self.current_angle}°", 
                                      bg="black", fg="white")
        self.direction_label.pack(side=tk.LEFT, padx=5)
        
        self.floor_label = tk.Label(self.status_bar, text=f"Floor: {self.current_floor} (Z: {self.current_z}m)", 
                                  bg="black", fg="white")
        self.floor_label.pack(side=tk.LEFT, padx=5)
        
        self.zoom_label = tk.Label(self.status_bar, text=f"Zoom: {self.zoom_level:.1f}x", 
                                 bg="black", fg="white")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        self.help_label = tk.Label(self.status_bar, text="← Back to cancel | → Next | OK to confirm", 
                                 bg="black", fg="yellow")
        self.help_label.pack(side=tk.RIGHT, padx=5)
        
        self.show_main_menu()
    
    def clear_menu_toolbar(self):
        """Clear all widgets from the menu toolbar"""
        for widget in self.menu_toolbar.winfo_children():
            widget.destroy()
    
    def show_main_menu(self):
        """Show the main menu options"""
        self.clear_menu_toolbar()
        self.current_menu = "main"
        self.menu_options = ["Measure", "Turn Left", "Turn Right", "Select Line", "Finish Room", "Change Floor"]
        self.selected_option = 0
        
        for i, option in enumerate(self.menu_options):
            btn = tk.Button(
                self.menu_toolbar,
                text=option,
                width=10,
                command=lambda i=i: self.menu_button_clicked(i)
            )
            btn.pack(side=tk.LEFT, padx=2)
            if i == self.selected_option:
                btn.config(bg="yellow", fg="black")
        
        self.update_help_text("Use ← → to navigate | OK to select")
    
    def menu_button_clicked(self, index):
        if index < len(self.menu_options):
            self.selected_option = index
            self.ok_pressed()
    
    def update_help_text(self, text):
        self.help_label.config(text=text)
    
    def left_pressed(self):
        if self.current_menu == "select_room_type":
            self.selected_option = (self.selected_option - 1) % len(self.ROOM_TYPES)
            self.highlight_selected_option()
        elif self.current_menu == "select_line":
            self.selected_option = (self.selected_option - 1) % len(self.lines)
            self.highlight_selected_option()
        elif self.current_menu == "select_point":
            self.selected_option = (self.selected_option - 1) % 2
            self.point_var.set("start" if self.selected_option == 0 else "end")
            self.highlight_selected_option()
        elif self.current_menu != "main":
            self.show_main_menu()
        else:
            self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            self.highlight_selected_option()
    
    def right_pressed(self):
        if self.current_menu == "select_room_type":
            self.selected_option = (self.selected_option + 1) % len(self.ROOM_TYPES)
            self.highlight_selected_option()
        elif self.current_menu == "select_line":
            self.selected_option = (self.selected_option + 1) % len(self.lines)
            self.highlight_selected_option()
        elif self.current_menu == "select_point":
            self.selected_option = (self.selected_option + 1) % 2
            self.point_var.set("start" if self.selected_option == 0 else "end")
            self.highlight_selected_option()
        elif self.current_menu == "main":
            self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            self.highlight_selected_option()
    
    def highlight_selected_option(self):
        """Highlight the currently selected option in the current menu"""
        for i, btn in enumerate(self.menu_toolbar.winfo_children()):
            if i == self.selected_option:
                btn.config(bg="yellow", fg="black")
            else:
                btn.config(bg="SystemButtonFace", fg="black")
    
    def ok_pressed(self):
        if self.current_menu == "main":
            selected_action = self.menu_options[self.selected_option]
            if selected_action == "Measure":
                self.start_measurement()
            elif selected_action == "Turn Left":
                self.turn_left()
            elif selected_action == "Turn Right":
                self.turn_right()
            elif selected_action == "Select Line":
                self.start_line_selection()
            elif selected_action == "Finish Room":
                self.finish_room()
            elif selected_action == "Change Floor":
                self.start_floor_change()
        elif self.current_menu == "select_room_type":
            self.complete_measurement()
        elif self.current_menu == "select_line":
            self.selected_line_index = self.selected_option  # Store selected line index
            self.show_point_selection()
        elif self.current_menu == "select_point":
            self.complete_line_selection()
    
    def start_measurement(self):
        distance = simpledialog.askfloat("Distance", "Enter distance in meters:", parent=self.root)
        if distance is None:
            return
            
        angle_rad = math.radians(self.current_angle)
        dx = distance * self.METER_TO_PIXEL * math.cos(angle_rad)
        dy = distance * self.METER_TO_PIXEL * math.sin(angle_rad)
        self.temp_end_point = (self.current_position[0] + dx, self.current_position[1] + dy)
        self.temp_distance = distance
        
        self.current_menu = "select_room_type"
        self.selected_option = 0
        self.update_help_text("← Back to previous | → Next room type | OK to confirm")
        self.show_room_type_selection()
    
    def show_room_type_selection(self):
        self.clear_menu_toolbar()
        
        for i, room_type in enumerate(self.ROOM_TYPES):
            btn = tk.Button(
                self.menu_toolbar,
                text=room_type,
                width=15,
                command=lambda i=i: self.select_option(i)
            )
            btn.pack(side=tk.LEFT, padx=2)
            if i == self.selected_option:
                btn.config(bg="yellow", fg="black")
    
    def select_option(self, index):
        self.selected_option = index
        self.highlight_selected_option()
    
    def complete_measurement(self):
        room_type = self.ROOM_TYPES[self.selected_option]
        
        new_line = {
            'id': self.line_counter,
            'start': self.current_position,
            'end': self.temp_end_point,
            'angle': self.current_angle,
            'length': self.temp_distance,
            'room_type': room_type,
            'floor_level': self.current_floor,
            'z_level': self.current_z
        }
        
        self.lines.append(new_line)
        self.line_counter += 1
        self.current_position = self.temp_end_point
        
        del self.temp_end_point
        del self.temp_distance
        
        self.show_main_menu()
        self.draw_layout()
        self.center_view()
    
    def start_line_selection(self):
        if not self.lines:
            messagebox.showerror("Error", "No lines available to select")
            return
            
        self.current_menu = "select_line"
        self.selected_option = 0
        self.update_help_text("← Back to previous | → Next line | OK to select")
        self.show_line_selection()
    
    def show_line_selection(self):
        self.clear_menu_toolbar()
        
        for i, line in enumerate(self.lines):
            btn = tk.Button(
                self.menu_toolbar,
                text=f"Line {line['id']} - {line['room_type']}",
                width=20,
                command=lambda i=i: self.select_option(i)
            )
            btn.pack(side=tk.LEFT, padx=2)
            if i == self.selected_option:
                btn.config(bg="yellow", fg="black")
    
    def show_point_selection(self):
        self.current_menu = "select_point"
        self.selected_option = 0
        self.point_var.set("start")
        self.update_help_text("← Back to line selection | → Switch point | OK to confirm")
        self.show_point_options()
    
    def show_point_options(self):
        self.clear_menu_toolbar()
        
        options = ["Start Point", "End Point"]
        for i, option in enumerate(options):
            btn = tk.Button(
                self.menu_toolbar,
                text=option,
                width=15,
                command=lambda i=i: self.select_option(i)
            )
            btn.pack(side=tk.LEFT, padx=2)
            if i == self.selected_option:
                btn.config(bg="yellow", fg="black")
    
    def complete_line_selection(self):
        point = "start" if self.selected_option == 0 else "end"
        line = self.lines[self.selected_line_index]
        
        self.current_position = line[point]
        self.current_angle = line['angle']
        self.current_floor = line['floor_level']
        self.current_z = line['z_level']
        
        self.selected_line_index = None
        self.update_direction_label()
        self.update_floor_label()
        self.show_main_menu()
        self.draw_layout()
        self.center_view()
    
    def start_floor_change(self):
        new_floor = simpledialog.askinteger("Change Floor", "Enter new floor level:", parent=self.root)
        if new_floor is None:
            return
            
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
        self.show_main_menu()
        self.draw_layout()
        self.center_view()
    
    def turn_left(self):
        self.current_angle = (self.current_angle - 90) % 360
        self.update_direction_label()
        self.draw_layout()
    
    def turn_right(self):
        self.current_angle = (self.current_angle + 90) % 360
        self.update_direction_label()
        self.draw_layout()
    
    def update_direction_label(self):
        self.direction_label.config(text=f"Direction: {self.current_angle}°")
    
    def update_floor_label(self):
        self.floor_label.config(text=f"Floor: {self.current_floor} (Z: {self.current_z}m)")
    
    def finish_room(self):
        floor_lines = [line for line in self.lines if line['floor_level'] == self.current_floor]
        
        if len(floor_lines) < 2:
            messagebox.showerror("Error", "At least 2 lines needed")
            return
            
        points = []
        for line in floor_lines:
            points.append((line['start'][0], line['start'][1]))
        points.append((floor_lines[-1]['end'][0], floor_lines[-1]['end'][1]))
        
        area = 0.0
        n = len(points)
        for i in range(n):
            x_i, y_i = points[i]
            x_j, y_j = points[(i + 1) % n]
            area += (x_i * y_j) - (x_j * y_i)
        
        area = abs(area) / (2 * self.METER_TO_PIXEL ** 2)
        
        room_info = {
            'floor': self.current_floor,
            'z_level': self.current_z,
            'area': area,
            'lines': floor_lines.copy()
        }
        self.rooms.append(room_info)
        
        messagebox.showinfo("Room Area", f"Room area: {area:.2f} square meters")
    
    def center_view(self, initial=False):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        if not self.lines or initial:
            self.view_offset = (
                canvas_width/2 - self.current_position[0],
                canvas_height/2 - self.current_position[1]
            )
        else:
            floor_lines = [line for line in self.lines if line['floor_level'] == self.current_floor]
            if not floor_lines:
                return
                
            all_points = []
            for line in floor_lines:
                all_points.append(line['start'])
                all_points.append(line['end'])
            
            min_x = min(p[0] for p in all_points)
            max_x = max(p[0] for p in all_points)
            min_y = min(p[1] for p in all_points)
            max_y = max(p[1] for p in all_points)
            
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            content_width = max_x - min_x
            content_height = max_y - min_y
            
            zoom_x = (canvas_width - 40) / content_width if content_width > 0 else 1.0
            zoom_y = (canvas_height - 40) / content_height if content_height > 0 else 1.0
            
            self.zoom_level = min(zoom_x, zoom_y, self.MAX_ZOOM)
            self.zoom_level = max(self.zoom_level, self.MIN_ZOOM)
            
            self.view_offset = (
                canvas_width/2 - center_x * self.zoom_level,
                canvas_height/2 - center_y * self.zoom_level
            )
        
        self.draw_layout()
    
    def draw_layout(self):
        self.canvas.delete("all")
        
        for i, line in enumerate(self.lines):
            if line['floor_level'] == self.current_floor:
                color = self.FLOOR_COLORS[line['floor_level'] % len(self.FLOOR_COLORS)]
                if i == self.selected_line_index:
                    color = "yellow"
                
                start_x, start_y = self.transform_point(line['start'][0], line['start'][1])
                end_x, end_y = self.transform_point(line['end'][0], line['end'][1])
                
                self.canvas.create_line(
                    start_x, start_y,
                    end_x, end_y,
                    fill=color, width=2
                )
                
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2
                self.canvas.create_text(mid_x, mid_y, text=str(line['id']), fill="white")
        
        x, y = self.transform_point(self.current_position[0], self.current_position[1])
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="red")
        
        angle_rad = math.radians(self.current_angle)
        dx = 20 * math.cos(angle_rad)
        dy = 20 * math.sin(angle_rad)
        self.canvas.create_line(x, y, x+dx, y+dy, fill="green", arrow=tk.LAST, width=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = LaserDistanceMeterSimulator(root)
    root.mainloop()
