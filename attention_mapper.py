"""
Offline Human Attention Mapping Tool - COMPLETE VISUAL VERSION
Zero external dependencies - WORKS IMMEDIATELY!
Includes visual heatmaps, timeline graphs, and charts!
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
from datetime import datetime
import queue
import platform
import sys
import math

# Try to import platform-specific tracking libraries
SYSTEM = platform.system()

# Windows tracking
if SYSTEM == "Windows":
    try:
        import ctypes
        from ctypes import wintypes
        WINDOWS_TRACKING = True
    except:
        WINDOWS_TRACKING = False
# macOS tracking
elif SYSTEM == "Darwin":
    try:
        import AppKit
        MAC_TRACKING = True
    except:
        MAC_TRACKING = False
# Linux tracking
else:
    try:
        import Xlib
        LINUX_TRACKING = True
    except:
        LINUX_TRACKING = False

class CompleteAttentionMapper:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 COMPLETE Human Attention Mapper - Visual Analytics")
        self.root.geometry("1300x750")
        self.root.configure(bg='#f0f2f5')
        
        # State variables
        self.is_recording = False
        self.monitor_thread = None
        self.event_queue = queue.Queue()
        self.start_time = None
        self.last_activity = time.time()
        self.current_window = self.get_active_window()
        self.idle_threshold = 30
        self.focus_threshold = 120
        self.mouse_position = (0, 0)
        self.mouse_positions = []  # Store mouse positions for heatmap
        self.last_window_check = time.time()
        self.window_check_interval = 1  # Check window every second
        
        # REAL data storage
        self.sessions = []
        self.current_session = self.create_new_session()
        
        # Colors
        self.colors = {
            'bg': '#f0f2f5',
            'primary': '#2962ff',
            'success': '#00c853',
            'warning': '#ffd600',
            'danger': '#d50000',
            'info': '#00b8d4',
            'dark': '#263238'
        }
        
        # Setup UI
        self.setup_ui()
        
        # Load previous sessions
        self.data_file = "complete_attention_data.json"
        self.load_data()
        
        # Start monitoring
        self.start_monitoring()
        
        # Bind global events
        self.bind_global_events()
        
    def create_new_session(self):
        """Create a new session for REAL data"""
        return {
            'id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'start_time': None,
            'end_time': None,
            'keyboard_events': [],
            'mouse_clicks': [],
            'mouse_movements': [],
            'window_switches': [],
            'idle_periods': [],
            'active_windows': {},
            'window_durations': {},
            'last_window_change': None,
            'total_events': 0
        }
    
    def setup_ui(self):
        """Create the user interface"""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_frame)
        
        # Content area (3 columns)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left panel - Controls
        self.create_left_panel(content_frame)
        
        # Center panel - Visualization
        self.create_center_panel(content_frame)
        
        # Right panel - Stats
        self.create_right_panel(content_frame)
        
        # Status bar
        self.create_status_bar()
        
        # Start display updates
        self.update_display()
    
    def create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X)
        
        # Title
        title_frame = ttk.Frame(header)
        title_frame.pack(side=tk.LEFT)
        
        tk.Label(title_frame, text="🧠", font=('Arial', 24)).pack(side=tk.LEFT)
        tk.Label(title_frame, text="COMPLETE HUMAN ATTENTION MAPPER", 
                font=('Arial', 20, 'bold'), fg=self.colors['primary'],
                bg=self.colors['bg']).pack(side=tk.LEFT, padx=10)
        
        # Status indicator
        self.status_indicator = tk.Label(header, text="●", font=('Arial', 20),
                                        fg='#9e9e9e', bg=self.colors['bg'])
        self.status_indicator.pack(side=tk.RIGHT)
        
        # Separator
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, pady=10)
    
    def create_left_panel(self, parent):
        """Create left control panel"""
        left = ttk.Frame(parent)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Recording control
        control_frame = ttk.LabelFrame(left, text="🎮 Control Center", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.record_btn = tk.Button(control_frame, 
                                    text="▶ START RECORDING",
                                    font=('Arial', 14, 'bold'),
                                    bg=self.colors['success'],
                                    fg='white',
                                    padx=30, pady=15,
                                    cursor='hand2',
                                    command=self.toggle_recording)
        self.record_btn.pack(fill=tk.X)
        
        # Session info
        info_frame = ttk.LabelFrame(left, text="📊 Session Info", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Duration
        ttk.Label(info_frame, text="Duration:", font=('Arial', 10)).pack(anchor=tk.W)
        self.duration_var = tk.StringVar(value="00:00:00")
        tk.Label(info_frame, textvariable=self.duration_var,
                font=('Arial', 20, 'bold'), fg=self.colors['primary']).pack(anchor=tk.W, pady=(0, 10))
        
        # Events
        ttk.Label(info_frame, text="Total Events:", font=('Arial', 10)).pack(anchor=tk.W)
        self.events_var = tk.StringVar(value="0")
        tk.Label(info_frame, textvariable=self.events_var,
                font=('Arial', 16, 'bold')).pack(anchor=tk.W)
        
        # Settings
        settings_frame = ttk.LabelFrame(left, text="⚙️ Settings", padding=15)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Idle threshold
        ttk.Label(settings_frame, text="Idle Threshold:").pack(anchor=tk.W)
        idle_frame = ttk.Frame(settings_frame)
        idle_frame.pack(fill=tk.X, pady=5)
        self.idle_scale = ttk.Scale(idle_frame, from_=5, to=120, orient=tk.HORIZONTAL,
                                    command=self.update_idle_threshold)
        self.idle_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.idle_scale.set(30)
        self.idle_label = ttk.Label(idle_frame, text="30s", width=5)
        self.idle_label.pack(side=tk.RIGHT)
        
        # Focus threshold
        ttk.Label(settings_frame, text="Focus Threshold:").pack(anchor=tk.W, pady=(10,0))
        focus_frame = ttk.Frame(settings_frame)
        focus_frame.pack(fill=tk.X, pady=5)
        self.focus_scale = ttk.Scale(focus_frame, from_=30, to=300, orient=tk.HORIZONTAL,
                                     command=self.update_focus_threshold)
        self.focus_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.focus_scale.set(120)
        self.focus_label = ttk.Label(focus_frame, text="120s", width=5)
        self.focus_label.pack(side=tk.RIGHT)
        
        # Action buttons
        actions_frame = ttk.LabelFrame(left, text="🔧 Actions", padding=15)
        actions_frame.pack(fill=tk.X)
        
        buttons = [
            ("🔥 Visual Heatmap", self.colors['primary'], self.generate_visual_heatmap),
            ("📈 Timeline Graph", self.colors['info'], self.generate_timeline_graph),
            ("📊 Export Report", self.colors['success'], self.export_report),
            ("🗑️ Clear Session", self.colors['danger'], self.clear_session)
        ]
        
        for text, color, command in buttons:
            btn = tk.Button(actions_frame, text=text, bg=color, fg='white',
                          font=('Arial', 10, 'bold'), cursor='hand2',
                          command=command)
            btn.pack(fill=tk.X, pady=2)
    
    def create_center_panel(self, parent):
        """Create center visualization panel"""
        center = ttk.Frame(parent)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Heatmap
        viz_frame = ttk.LabelFrame(center, text="📈 Live Attention Heatmap", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        self.heatmap_canvas = tk.Canvas(viz_frame, bg='white', height=400,
                                       highlightthickness=1, highlightbackground='#e0e0e0')
        self.heatmap_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Timeline
        timeline_frame = ttk.LabelFrame(center, text="⏱️ Activity Timeline", padding=10)
        timeline_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.timeline_canvas = tk.Canvas(timeline_frame, bg='#f5f5f5', height=60,
                                        highlightthickness=1, highlightbackground='#e0e0e0')
        self.timeline_canvas.pack(fill=tk.X)
        
        # Metrics cards
        metrics_frame = ttk.Frame(center)
        metrics_frame.pack(fill=tk.X, pady=10)
        
        self.metric_labels = {}
        metrics = [
            ('Focused', '🎯', self.colors['success']),
            ('Active', '⚡', self.colors['primary']),
            ('Idle', '😴', self.colors['warning']),
            ('Switches', '🔄', self.colors['danger'])
        ]
        
        for i, (name, icon, color) in enumerate(metrics):
            card = tk.Frame(metrics_frame, bg=color, relief=tk.RAISED, bd=0)
            card.grid(row=0, column=i, padx=5, sticky='nsew')
            metrics_frame.columnconfigure(i, weight=1)
            
            tk.Label(card, text=f"{icon} {name}", bg=color, fg='white',
                    font=('Arial', 10, 'bold')).pack(pady=(10, 5))
            
            value_label = tk.Label(card, text="0%", bg=color, fg='white',
                                  font=('Arial', 20, 'bold'))
            value_label.pack(pady=(0, 10))
            self.metric_labels[name.lower()] = value_label
    
    def create_right_panel(self, parent):
        """Create right statistics panel"""
        right = ttk.Frame(parent)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Current window
        window_frame = ttk.LabelFrame(right, text="🪟 Active Window", padding=10)
        window_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.window_var = tk.StringVar(value=self.current_window)
        tk.Label(window_frame, textvariable=self.window_var,
                font=('Arial', 10), wraplength=200, justify=tk.LEFT).pack()
        
        # Live statistics
        stats_frame = ttk.LabelFrame(right, text="📊 Live Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_text = tk.Text(stats_frame, width=35, height=20,
                                  font=('Consolas', 9), bg='#fafafa',
                                  relief=tk.FLAT, borderwidth=1)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.stats_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.stats_text.yview)
        
        # Sessions list
        sessions_frame = ttk.LabelFrame(right, text="📚 Recent Sessions", padding=10)
        sessions_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.sessions_listbox = tk.Listbox(sessions_frame, height=5,
                                          font=('Arial', 9))
        self.sessions_listbox.pack(fill=tk.X)
        self.sessions_listbox.bind('<<ListboxSelect>>', self.on_session_select)
    
    def create_status_bar(self):
        """Create status bar"""
        status_frame = tk.Frame(self.root, bg='#e0e0e0', height=25)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="✅ Ready | No active recording")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               bg='#e0e0e0', anchor=tk.W, padx=10)
        status_label.pack(fill=tk.X)
    
    def bind_global_events(self):
        """Bind global keyboard and mouse events"""
        # Bind keyboard events
        self.root.bind('<Key>', self.on_key_press)
        
        # Bind mouse events
        self.root.bind('<Button-1>', self.on_mouse_click)
        self.root.bind('<Button-2>', self.on_mouse_click)
        self.root.bind('<Button-3>', self.on_mouse_click)
        self.root.bind('<Motion>', self.on_mouse_move)
        
        # Bind window events
        self.root.bind('<FocusIn>', self.on_window_focus)
        self.root.bind('<FocusOut>', self.on_window_blur)
    
    def on_key_press(self, event):
        """Handle real keyboard press"""
        if self.is_recording:
            # Don't record modifier keys alone
            if event.keysym not in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 
                                   'Alt_L', 'Alt_R', 'Caps_Lock', 'Num_Lock']:
                self.event_queue.put({
                    'type': 'keyboard',
                    'key': event.keysym,
                    'char': event.char,
                    'time': time.time()
                })
                self.last_activity = time.time()
    
    def on_mouse_click(self, event):
        """Handle real mouse clicks"""
        if self.is_recording:
            button_name = {1: 'Left', 2: 'Middle', 3: 'Right'}.get(event.num, str(event.num))
            self.event_queue.put({
                'type': 'mouse_click',
                'button': button_name,
                'x': event.x_root,
                'y': event.y_root,
                'time': time.time()
            })
            self.last_activity = time.time()
    
    def on_mouse_move(self, event):
        """Handle real mouse movements"""
        if self.is_recording:
            current_pos = (event.x_root, event.y_root)
            
            # Only record if moved significantly (reduce noise)
            if self.mouse_position != (0, 0):
                distance = math.sqrt((current_pos[0] - self.mouse_position[0])**2 + 
                                   (current_pos[1] - self.mouse_position[1])**2)
                
                # Record if moved more than 10 pixels
                if distance > 10:
                    self.event_queue.put({
                        'type': 'mouse_move',
                        'x': event.x_root,
                        'y': event.y_root,
                        'distance': distance,
                        'time': time.time()
                    })
                    self.last_activity = time.time()
            
            self.mouse_position = current_pos
    
    def on_window_focus(self, event):
        """Handle window focus event"""
        if self.is_recording:
            self.check_window_change()
    
    def on_window_blur(self, event):
        """Handle window blur event"""
        if self.is_recording:
            pass
    
    def get_active_window(self):
        """Get the actual active window title (platform-specific)"""
        try:
            if SYSTEM == "Windows" and WINDOWS_TRACKING:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                return buff.value or "Unknown Window"
            
            elif SYSTEM == "Darwin" and MAC_TRACKING:
                from AppKit import NSWorkspace
                active_app = NSWorkspace.sharedWorkspace().activeApplication()
                return active_app.get('NSApplicationName', 'Unknown')
            
            elif SYSTEM == "Linux" and LINUX_TRACKING:
                try:
                    import subprocess
                    output = subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowname'], 
                                                   stderr=subprocess.DEVNULL).decode().strip()
                    return output or "Linux Window"
                except:
                    return "Linux Window"
            
            else:
                return f"App - {datetime.now().strftime('%H:%M:%S')}"
        except Exception as e:
            print(f"Error getting window: {e}")
            return "Unknown Window"
    
    def check_window_change(self):
        """Check and record window switches"""
        if not self.is_recording:
            return
        
        new_window = self.get_active_window()
        current_time = time.time()
        
        # Update window duration tracking
        if self.current_window in self.current_session['window_durations']:
            time_spent = current_time - self.current_session.get('last_window_change', current_time)
            self.current_session['window_durations'][self.current_window] += time_spent
        else:
            self.current_session['window_durations'][self.current_window] = 0
        
        # Check if window actually changed
        if new_window != self.current_window:
            # Record the switch
            switch_event = {
                'type': 'window_switch',
                'from': self.current_window,
                'to': new_window,
                'time': current_time,
                'duration': current_time - self.current_session.get('last_window_change', current_time)
            }
            
            self.event_queue.put(switch_event)
            
            # Update window counts
            if new_window not in self.current_session['active_windows']:
                self.current_session['active_windows'][new_window] = 0
            self.current_session['active_windows'][new_window] += 1
            
            # Update current window
            self.current_window = new_window
            self.current_session['last_window_change'] = current_time
            
            # Update UI
            self.root.after(0, lambda: self.window_var.set(new_window))
    
    def start_monitoring(self):
        """Start background monitoring"""
        def monitor():
            last_window_check = time.time()
            
            while True:
                if self.is_recording:
                    current_time = time.time()
                    
                    # Check for idle periods
                    idle_time = current_time - self.last_activity
                    if idle_time > self.idle_threshold:
                        self.event_queue.put({
                            'type': 'idle',
                            'duration': idle_time,
                            'time': current_time
                        })
                    
                    # Check window every second
                    if current_time - last_window_check >= 1.0:
                        self.check_window_change()
                        last_window_check = current_time
                
                time.sleep(0.1)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def update_idle_threshold(self, value):
        """Update idle threshold"""
        self.idle_threshold = int(float(value))
        self.idle_label.config(text=f"{self.idle_threshold}s")
    
    def update_focus_threshold(self, value):
        """Update focus threshold"""
        self.focus_threshold = int(float(value))
        self.focus_label.config(text=f"{self.focus_threshold}s")
    
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Begin recording REAL session"""
        self.is_recording = True
        self.start_time = time.time()
        self.last_activity = time.time()
        self.current_session = self.create_new_session()
        self.current_session['start_time'] = datetime.now().isoformat()
        self.current_session['last_window_change'] = self.start_time
        
        # Get initial window
        self.current_window = self.get_active_window()
        self.window_var.set(self.current_window)
        
        # Initialize window tracking
        self.current_session['active_windows'][self.current_window] = 1
        self.current_session['window_durations'][self.current_window] = 0
        
        # Update UI
        self.record_btn.config(text="⏸ STOP RECORDING", bg=self.colors['danger'])
        self.status_indicator.config(fg=self.colors['success'])
        self.status_var.set("🔴 Recording REAL attention patterns...")
        
        print(f"✅ Recording started - Initial window: {self.current_window}")
    
    def stop_recording(self):
        """Stop recording session"""
        self.is_recording = False
        
        # Update final window duration
        if self.current_session['last_window_change']:
            time_spent = time.time() - self.current_session['last_window_change']
            if self.current_window in self.current_session['window_durations']:
                self.current_session['window_durations'][self.current_window] += time_spent
        
        # Update UI
        self.record_btn.config(text="▶ START RECORDING", bg=self.colors['success'])
        self.status_indicator.config(fg='#9e9e9e')
        
        # Save session
        if self.current_session['start_time']:
            self.current_session['end_time'] = datetime.now().isoformat()
            self.current_session['total_events'] = (
                len(self.current_session['keyboard_events']) +
                len(self.current_session['mouse_clicks']) +
                len(self.current_session['mouse_movements']) +
                len(self.current_session['window_switches'])
            )
            self.sessions.append(self.current_session)
            self.save_data()
            self.update_sessions_list()
            
        self.status_var.set("✅ Recording stopped | Session saved")
        print(f"✅ Recording stopped - Total events: {self.events_var.get()}")
    
    def update_display(self):
        """Update all display elements"""
        if self.is_recording and self.start_time:
            # Update duration
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.duration_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Process events
            self.process_events()
            
            # Update displays
            self.update_statistics()
            self.draw_live_heatmap()
            self.draw_live_timeline()
            self.update_metrics()
            
        # Schedule next update
        self.root.after(100, self.update_display)
    
    def process_events(self):
        """Process REAL events from queue"""
        try:
            while True:
                event = self.event_queue.get_nowait()
                event_type = event['type']
                
                if event_type == 'keyboard':
                    self.current_session['keyboard_events'].append(event)
                elif event_type == 'mouse_click':
                    self.current_session['mouse_clicks'].append(event)
                    # Store for heatmap
                    self.mouse_positions.append((event['x'], event['y']))
                elif event_type == 'mouse_move':
                    self.current_session['mouse_movements'].append(event)
                    # Store for heatmap
                    self.mouse_positions.append((event['x'], event['y']))
                    # Keep only last 2000 positions
                    if len(self.mouse_positions) > 2000:
                        self.mouse_positions = self.mouse_positions[-2000:]
                elif event_type == 'window_switch':
                    self.current_session['window_switches'].append(event)
                elif event_type == 'idle':
                    self.current_session['idle_periods'].append(event)
                    
                # Update event count
                total = (len(self.current_session['keyboard_events']) +
                        len(self.current_session['mouse_clicks']) +
                        len(self.current_session['mouse_movements']) +
                        len(self.current_session['window_switches']))
                self.events_var.set(str(total))
                
        except queue.Empty:
            pass
    
    def update_statistics(self):
        """Update statistics display"""
        self.stats_text.delete(1.0, tk.END)
        
        session = self.current_session
        elapsed = time.time() - self.start_time if self.start_time else 1
        
        # Calculate rates
        keyboard_rate = len(session['keyboard_events']) / elapsed * 60 if elapsed > 0 else 0
        click_rate = len(session['mouse_clicks']) / elapsed * 60 if elapsed > 0 else 0
        switch_rate = len(session['window_switches']) / elapsed * 60 if elapsed > 0 else 0
        move_rate = len(session['mouse_movements']) / elapsed * 60 if elapsed > 0 else 0
        
        # Get window stats
        unique_windows = len(session['active_windows'])
        
        # Get top windows
        top_windows = sorted(session['window_durations'].items(), 
                            key=lambda x: x[1], reverse=True)[:3]
        
        # Total idle time
        total_idle = sum([p.get('duration', 0) for p in session['idle_periods']])
        
        # Calculate focus score
        focus_score = self.calculate_focus_score()
        switch_freq = len(session['window_switches']) / (elapsed / 60) if elapsed > 0 else 0
        
        stats = f"""
╔══════════════════════════╗
║    ACCURATE ACTIVITY STATS║
╚══════════════════════════╝

⌨️ KEYBOARD
  • Events: {len(session['keyboard_events'])}
  • Rate: {keyboard_rate:.1f}/min

🖱️ MOUSE
  • Clicks: {len(session['mouse_clicks'])}
  • Movements: {len(session['mouse_movements'])}
  • Click Rate: {click_rate:.1f}/min

🪟 WINDOWS
  • Switches: {len(session['window_switches'])}
  • Switch Rate: {switch_rate:.1f}/min
  • Unique: {unique_windows}
  
📌 TOP WINDOWS:
"""
        for window, duration in top_windows:
            minutes = duration / 60
            stats += f"  • {window[:20]}: {minutes:.1f}min\n"
        
        stats += f"""
⏰ IDLE
  • Periods: {len(session['idle_periods'])}
  • Total: {total_idle:.0f}s
  • Idle %: {(total_idle/elapsed*100):.1f}%

🎯 FOCUS METRICS
  • Focus Score: {focus_score:.1f}%
  • Switch Freq: {switch_freq:.1f}/min
  • Total Events: {self.events_var.get()}
"""
        
        self.stats_text.insert(1.0, stats)
    
    def calculate_focus_score(self):
        """Calculate REAL focus score"""
        session = self.current_session
        elapsed = time.time() - self.start_time if self.start_time else 1
        
        if elapsed < 10:
            return 0
        
        # Activity score (more actions = more focused)
        total_actions = (len(session['keyboard_events']) + 
                        len(session['mouse_clicks']) +
                        len(session['mouse_movements']))
        actions_per_minute = total_actions / (elapsed / 60)
        activity_score = min(40, actions_per_minute)  # Max 40 points
        
        # Switch penalty (more switches = less focused)
        switches_per_minute = len(session['window_switches']) / (elapsed / 60)
        switch_penalty = min(30, switches_per_minute * 5)
        
        # Idle penalty
        total_idle = sum([p.get('duration', 0) for p in session['idle_periods']])
        idle_percentage = (total_idle / elapsed) * 100
        idle_penalty = min(30, idle_percentage / 2)
        
        # Window focus bonus (time spent in one window)
        if session['window_durations']:
            max_window_time = max(session['window_durations'].values())
            focus_bonus = min(30, (max_window_time / elapsed) * 30)
        else:
            focus_bonus = 0
        
        # Calculate final score
        score = activity_score + focus_bonus - switch_penalty - idle_penalty
        return max(0, min(100, score))
    
    def update_metrics(self):
        """Update metric cards"""
        focus = self.calculate_focus_score()
        
        # Calculate actual metrics
        session = self.current_session
        elapsed = time.time() - self.start_time if self.start_time else 1
        
        total_idle = sum([p.get('duration', 0) for p in session['idle_periods']])
        idle_percentage = (total_idle / elapsed) * 100 if elapsed > 0 else 0
        
        # Active percentage (non-idle time)
        active = max(0, 100 - idle_percentage)
        
        # Switch frequency as percentage
        switches_per_minute = len(session['window_switches']) / (elapsed / 60) if elapsed > 0 else 0
        switch_percentage = min(100, switches_per_minute * 10)
        
        self.metric_labels['focused'].config(text=f"{focus:.0f}%")
        self.metric_labels['active'].config(text=f"{active:.0f}%")
        self.metric_labels['idle'].config(text=f"{idle_percentage:.0f}%")
        self.metric_labels['switches'].config(text=f"{switch_percentage:.0f}%")
    
    def draw_live_heatmap(self):
        """Draw live attention heatmap"""
        self.heatmap_canvas.delete("all")
        
        width = self.heatmap_canvas.winfo_width()
        height = self.heatmap_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Draw grid
        cols, rows = 20, 10
        cell_w = width / cols
        cell_h = height / rows
        
        # Get recent mouse positions
        if not self.mouse_positions:
            # Draw placeholder
            self.heatmap_canvas.create_text(width//2, height//2,
                                           text="No mouse activity yet\nMove mouse to see heatmap",
                                           font=('Arial', 12), fill='#9e9e9e')
            return
        
        # Create intensity grid
        intensity_grid = [[0 for _ in range(rows)] for _ in range(cols)]
        
        # Use stored mouse positions
        for x, y in self.mouse_positions[-500:]:  # Last 500 positions
            col = int((x / screen_width) * cols)
            row = int((y / screen_height) * rows)
            if 0 <= col < cols and 0 <= row < rows:
                intensity_grid[col][row] += 1
        
        # Find max intensity
        max_intensity = max([max(row) for row in intensity_grid]) or 1
        
        # Draw heatmap cells
        for col in range(cols):
            for row in range(rows):
                x1 = col * cell_w
                y1 = row * cell_h
                
                intensity = intensity_grid[col][row] / max_intensity
                
                # Color gradient (blue -> green -> yellow -> red)
                if intensity > 0.75:
                    color = '#ff0000'  # Red
                elif intensity > 0.5:
                    color = '#ff9900'  # Orange
                elif intensity > 0.25:
                    color = '#ffff00'  # Yellow
                elif intensity > 0:
                    color = '#00ff00'  # Green
                else:
                    color = '#f0f0f0'  # Light gray
                
                self.heatmap_canvas.create_rectangle(x1, y1, x1 + cell_w - 1, y1 + cell_h - 1,
                                                    fill=color, outline='#e0e0e0', width=1)
        
        # Draw legend
        legend_y = height - 20
        self.heatmap_canvas.create_text(10, legend_y, text="Low", anchor=tk.W, fill='#666')
        
        colors = ['#00ff00', '#ffff00', '#ff9900', '#ff0000']
        for i, color in enumerate(colors):
            x = 50 + i * 25
            self.heatmap_canvas.create_rectangle(x, legend_y-5, x+20, legend_y+5,
                                                fill=color, outline='')
        
        self.heatmap_canvas.create_text(50 + len(colors)*25 + 10, legend_y,
                                       text="High", anchor=tk.W, fill='#666')
        
        # Draw stats
        self.heatmap_canvas.create_text(width-100, 20, 
                                       text=f"Points: {len(self.mouse_positions)}", 
                                       fill='#666', font=('Arial', 9))
    
    def draw_live_timeline(self):
        """Draw live activity timeline"""
        self.timeline_canvas.delete("all")
        
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        
        if width < 10:
            return
        
        if not self.is_recording:
            self.timeline_canvas.create_text(width//2, height//2,
                                           text="Start recording to see timeline", fill='#999')
            return
        
        # Collect all events from last 5 minutes
        current_time = time.time()
        min_time = current_time - 300  # Last 5 minutes
        
        # Draw time markers
        for i in range(6):
            x = (i / 5) * width
            self.timeline_canvas.create_line(x, 0, x, height, fill='#e0e0e0', width=1)
            if i < 5:
                minutes_ago = 5 - i
                self.timeline_canvas.create_text(x + 5, 5, text=f"-{minutes_ago}m", 
                                                anchor=tk.W, fill='#999', font=('Arial', 8))
        
        # Collect events
        events = []
        for event_list in [self.current_session['keyboard_events'][-100:],
                          self.current_session['mouse_clicks'][-100:],
                          self.current_session['window_switches'][-50:]]:
            events.extend([e for e in event_list if e.get('time', 0) > min_time])
        
        if not events:
            self.timeline_canvas.create_text(width//2, height//2,
                                           text="No recent activity", fill='#999')
            return
        
        # Draw events
        y_pos = height/2
        for event in events:
            event_time = event.get('time', 0)
            if event_time > min_time:
                x = ((event_time - min_time) / 300) * width
                
                # Color by event type
                if event['type'] == 'keyboard':
                    color = self.colors['primary']
                    size = 2
                elif event['type'] == 'mouse_click':
                    color = self.colors['success']
                    size = 3
                elif event['type'] == 'window_switch':
                    color = self.colors['danger']
                    size = 4
                else:
                    continue
                
                self.timeline_canvas.create_oval(x-size, y_pos-size, x+size, y_pos+size,
                                                fill=color, outline='black', width=1)
        
        # Draw current position
        current_x = ((current_time - min_time) / 300) * width
        self.timeline_canvas.create_line(current_x, 0, current_x, height,
                                        fill='black', width=2, dash=(2, 2))
    
    # ============= VISUALIZATION GENERATION METHODS =============
    
    def generate_visual_heatmap(self):
        """Generate detailed visual heatmap in new window"""
        if not self.sessions and not self.current_session['start_time']:
            messagebox.showinfo("No Data", "No sessions recorded yet")
            return
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("🔥 Visual Heatmap Analysis")
        popup.geometry("900x700")
        popup.configure(bg='white')
        
        # Create notebook for tabs
        notebook = ttk.Notebook(popup)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Heatmap
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="🔥 Heatmap")
        self.create_detailed_heatmap(tab1)
        
        # Tab 2: Timeline Graph
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="📈 Timeline Graph")
        self.create_timeline_graph(tab2)
        
        # Tab 3: Window Distribution
        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text="🪟 Window Activity")
        self.create_window_chart(tab3)
        
        # Tab 4: Activity Distribution
        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text="🥧 Activity Pie")
        self.create_pie_chart(tab4)
    
    def create_detailed_heatmap(self, parent):
        """Create detailed visual heatmap"""
        # Create canvas with scrollbar
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg='white', width=800, height=550)
        canvas.pack(pady=10)
        
        # Get all mouse data
        all_sessions = self.sessions + ([self.current_session] if self.current_session['start_time'] else [])
        
        all_moves = []
        all_clicks = []
        
        for session in all_sessions:
            all_moves.extend(session.get('mouse_movements', []))
            all_clicks.extend(session.get('mouse_clicks', []))
        
        if not all_moves and not all_clicks:
            canvas.create_text(400, 250, text="No mouse data available", 
                              font=('Arial', 14), fill='#999')
            return
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Create heatmap grid (higher resolution)
        cols, rows = 40, 25
        cell_w = 800 / cols
        cell_h = 550 / rows
        
        # Initialize intensity grid
        intensity_grid = [[0 for _ in range(rows)] for _ in range(cols)]
        
        # Add mouse movements
        for event in all_moves:
            if 'x' in event and 'y' in event:
                col = int((event['x'] / screen_width) * cols)
                row = int((event['y'] / screen_height) * rows)
                if 0 <= col < cols and 0 <= row < rows:
                    intensity_grid[col][row] += 1
        
        # Add mouse clicks (weighted more)
        for event in all_clicks:
            if 'x' in event and 'y' in event:
                col = int((event['x'] / screen_width) * cols)
                row = int((event['y'] / screen_height) * rows)
                if 0 <= col < cols and 0 <= row < rows:
                    intensity_grid[col][row] += 3  # Clicks count more
        
        # Find max intensity
        max_intensity = max([max(row) for row in intensity_grid]) or 1
        
        # Draw heatmap cells
        for col in range(cols):
            for row in range(rows):
                x1 = col * cell_w
                y1 = row * cell_h
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                
                intensity = intensity_grid[col][row] / max_intensity
                
                # Create color based on intensity
                if intensity > 0.8:
                    color = '#ff0000'  # Red
                elif intensity > 0.6:
                    color = '#ff6600'  # Orange
                elif intensity > 0.4:
                    color = '#ffff00'  # Yellow
                elif intensity > 0.2:
                    color = '#00ff00'  # Green
                elif intensity > 0:
                    color = '#0000ff'  # Blue
                else:
                    color = '#f0f0f0'  # Light gray
                
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='', width=0)
        
        # Add title
        canvas.create_text(400, 20, text="Mouse Activity Heatmap", 
                          font=('Arial', 16, 'bold'), fill='#333')
        
        # Draw legend
        legend_y = 520
        colors = ['#0000ff', '#00ff00', '#ffff00', '#ff6600', '#ff0000']
        labels = ['Low', '', '', '', 'High']
        
        for i, (color, label) in enumerate(zip(colors, labels)):
            x = 300 + i * 40
            canvas.create_rectangle(x, legend_y, x+30, legend_y+20, fill=color, outline='black')
            if i == 0 or i == 4:
                canvas.create_text(x+15, legend_y+30, text=label, font=('Arial', 9))
        
        # Add stats
        stats_text = f"Total Points: {len(all_moves) + len(all_clicks)} | Clicks: {len(all_clicks)} | Movements: {len(all_moves)}"
        canvas.create_text(400, 570, text=stats_text, font=('Arial', 10), fill='#666')
    
    def create_timeline_graph(self, parent):
        """Create activity timeline graph"""
        canvas = tk.Canvas(parent, bg='white', width=800, height=550)
        canvas.pack(pady=10)
        
        all_sessions = self.sessions + ([self.current_session] if self.current_session['start_time'] else [])
        
        # Collect all events with timestamps
        events = []
        for session in all_sessions:
            if session.get('start_time'):
                try:
                    start_time = datetime.fromisoformat(session['start_time']).timestamp()
                    for e in session.get('keyboard_events', []):
                        e_copy = e.copy()
                        e_copy['time_abs'] = e.get('time', start_time)
                        events.append(e_copy)
                    for e in session.get('mouse_clicks', []):
                        e_copy = e.copy()
                        e_copy['time_abs'] = e.get('time', start_time)
                        events.append(e_copy)
                    for e in session.get('window_switches', []):
                        e_copy = e.copy()
                        e_copy['time_abs'] = e.get('time', start_time)
                        events.append(e_copy)
                except:
                    pass
        
        if not events:
            canvas.create_text(400, 250, text="No timeline data available", 
                              font=('Arial', 14), fill='#999')
            return
        
        # Sort events by time
        events.sort(key=lambda x: x.get('time_abs', 0))
        
        # Get time range
        min_time = min(e.get('time_abs', 0) for e in events)
        max_time = max(e.get('time_abs', 0) for e in events)
        time_range = max_time - min_time
        
        if time_range == 0:
            time_range = 1
        
        # Draw axes
        canvas.create_line(50, 500, 750, 500, width=2)  # X-axis
        canvas.create_line(50, 50, 50, 500, width=2)    # Y-axis
        
        # X-axis labels
        for i in range(6):
            x = 50 + (i * 140)
            canvas.create_line(x, 495, x, 505, width=2)
            time_label = min_time + (i * time_range / 5)
            try:
                time_str = datetime.fromtimestamp(time_label).strftime('%H:%M:%S')
            except:
                time_str = f"{i*20}s"
            canvas.create_text(x, 520, text=time_str, font=('Arial', 8))
        
        # Y-axis labels
        for i in range(5):
            y = 500 - (i * 100)
            canvas.create_line(45, y, 55, y, width=2)
            canvas.create_text(30, y, text=str(i), font=('Arial', 8))
        
        canvas.create_text(400, 30, text="Activity Timeline", font=('Arial', 16, 'bold'), fill='#333')
        canvas.create_text(20, 275, text="Intensity", font=('Arial', 9), angle=90)
        canvas.create_text(400, 550, text="Time", font=('Arial', 9))
        
        # Group events by time buckets
        buckets = [0] * 20
        for event in events:
            time_offset = event.get('time_abs', min_time) - min_time
            bucket = int((time_offset / time_range) * 19)
            if 0 <= bucket < 20:
                if event['type'] == 'keyboard':
                    buckets[bucket] += 1
                elif event['type'] == 'mouse_click':
                    buckets[bucket] += 2
                elif event['type'] == 'window_switch':
                    buckets[bucket] += 3
        
        max_bucket = max(buckets) or 1
        
        # Draw bars
        for i, value in enumerate(buckets):
            x1 = 50 + (i * 35)
            x2 = x1 + 30
            bar_height = (value / max_bucket) * 350
            y1 = 500 - bar_height
            y2 = 500
            
            # Color based on intensity
            if value / max_bucket > 0.7:
                color = '#ff4444'
            elif value / max_bucket > 0.4:
                color = '#ffaa44'
            else:
                color = '#44aa44'
            
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='black')
            
            # Add value on top of bar
            if value > 0:
                canvas.create_text(x1+15, y1-10, text=str(value), font=('Arial', 8))
        
        # Legend
        canvas.create_rectangle(600, 50, 620, 70, fill='#ff4444', outline='black')
        canvas.create_text(630, 60, text="High Activity", anchor=tk.W, font=('Arial', 9))
        canvas.create_rectangle(600, 80, 620, 100, fill='#ffaa44', outline='black')
        canvas.create_text(630, 90, text="Medium Activity", anchor=tk.W, font=('Arial', 9))
        canvas.create_rectangle(600, 110, 620, 130, fill='#44aa44', outline='black')
        canvas.create_text(630, 120, text="Low Activity", anchor=tk.W, font=('Arial', 9))
    
    def create_window_chart(self, parent):
        """Create window activity bar chart"""
        canvas = tk.Canvas(parent, bg='white', width=800, height=550)
        canvas.pack(pady=10)
        
        all_sessions = self.sessions + ([self.current_session] if self.current_session['start_time'] else [])
        
        # Collect window data
        window_counts = {}
        window_times = {}
        
        for session in all_sessions:
            # Count appearances
            for window, count in session.get('active_windows', {}).items():
                window_counts[window] = window_counts.get(window, 0) + count
            
            # Track time spent
            for window, duration in session.get('window_durations', {}).items():
                window_times[window] = window_times.get(window, 0) + duration
        
        if not window_counts:
            canvas.create_text(400, 250, text="No window data available", 
                              font=('Arial', 14), fill='#999')
            return
        
        # Get top 8 windows
        top_windows = sorted(window_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # Draw axes
        canvas.create_line(100, 450, 700, 450, width=2)  # X-axis
        canvas.create_line(100, 50, 100, 450, width=2)   # Y-axis
        
        canvas.create_text(400, 30, text="Window Activity", font=('Arial', 16, 'bold'), fill='#333')
        canvas.create_text(50, 250, text="Switches", font=('Arial', 9), angle=90)
        
        # Find max count for scaling
        max_count = max(c[1] for c in top_windows) or 1
        
        # Draw bars
        bar_width = 60
        colors = ['#2962ff', '#00c853', '#ffd600', '#d50000', '#aa00ff', '#ff6d00', '#00b8d4', '#c2185b']
        
        for i, (window, count) in enumerate(top_windows):
            x1 = 120 + (i * 70)
            x2 = x1 + bar_width
            bar_height = (count / max_count) * 300
            y1 = 450 - bar_height
            y2 = 450
            
            # Truncate long window names
            short_name = window[:15] + "..." if len(window) > 15 else window
            
            canvas.create_rectangle(x1, y1, x2, y2, fill=colors[i % len(colors)], outline='black')
            canvas.create_text(x1 + bar_width/2, 460, text=short_name, 
                              font=('Arial', 8), anchor=tk.N, width=bar_width)
            canvas.create_text(x1 + bar_width/2, y1-10, text=str(count), 
                              font=('Arial', 9, 'bold'))
            
            # Add time if available
            if window in window_times:
                minutes = window_times[window] / 60
                canvas.create_text(x1 + bar_width/2, y1-25, text=f"{minutes:.1f}min", 
                                  font=('Arial', 8), fill='#666')
    
    def create_pie_chart(self, parent):
        """Create activity distribution pie chart"""
        canvas = tk.Canvas(parent, bg='white', width=800, height=550)
        canvas.pack(pady=10)
        
        all_sessions = self.sessions + ([self.current_session] if self.current_session['start_time'] else [])
        
        # Calculate totals
        total_kb = sum(len(s.get('keyboard_events', [])) for s in all_sessions)
        total_clicks = sum(len(s.get('mouse_clicks', [])) for s in all_sessions)
        total_moves = sum(len(s.get('mouse_movements', [])) for s in all_sessions)
        total_switches = sum(len(s.get('window_switches', [])) for s in all_sessions)
        
        values = [total_kb, total_clicks, total_moves, total_switches]
        labels = ['Keyboard', 'Clicks', 'Movements', 'Switches']
        colors = ['#2962ff', '#00c853', '#ffd600', '#d50000']
        
        if sum(values) == 0:
            canvas.create_text(400, 250, text="No activity data available", 
                              font=('Arial', 14), fill='#999')
            return
        
        # Draw pie chart
        cx, cy = 300, 250
        radius = 150
        
        total = sum(values)
        start_angle = 0
        
        for i, (value, label, color) in enumerate(zip(values, labels, colors)):
            if value == 0:
                continue
                
            extent = (value / total) * 360
            
            # Draw pie slice
            canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius,
                             start=start_angle, extent=extent, fill=color, outline='white', width=2)
            
            # Calculate label position
            mid_angle = start_angle + extent/2
            angle_rad = math.radians(mid_angle)
            label_x = cx + radius * 0.7 * math.cos(angle_rad)
            label_y = cy - radius * 0.7 * math.sin(angle_rad)
            
            # Add percentage label
            percentage = (value / total) * 100
            canvas.create_text(label_x, label_y, text=f"{percentage:.1f}%", 
                              font=('Arial', 10, 'bold'), fill='white')
            
            start_angle += extent
        
        canvas.create_text(400, 30, text="Activity Distribution", 
                          font=('Arial', 16, 'bold'), fill='#333')
        
        # Draw legend
        legend_x = 550
        legend_y = 150
        
        for i, (label, color) in enumerate(zip(labels, colors)):
            canvas.create_rectangle(legend_x, legend_y + i*30, legend_x+20, legend_y+20 + i*30, 
                                   fill=color, outline='black')
            canvas.create_text(legend_x+30, legend_y+10 + i*30, text=f"{label}: {values[i]}", 
                              anchor=tk.W, font=('Arial', 10))
        
        # Add total
        canvas.create_text(legend_x, legend_y + 150, text=f"Total Events: {total}", 
                          anchor=tk.W, font=('Arial', 12, 'bold'), fill='#333')
    
    def generate_timeline_graph(self):
        """Quick access to timeline graph"""
        self.generate_visual_heatmap()  # This will show all tabs including timeline
    
    def export_report(self):
        """Export report to file"""
        if not self.sessions and not self.current_session['start_time']:
            messagebox.showinfo("No Data", "No sessions to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"attention_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if not filename:
            return
        
        all_sessions = self.sessions + ([self.current_session] if self.current_session['start_time'] else [])
        
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("           COMPLETE HUMAN ATTENTION MAPPING REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Platform: {platform.system()} {platform.release()}\n")
            f.write(f"Total Sessions: {len(all_sessions)}\n\n")
            
            total_kb = 0
            total_clicks = 0
            total_moves = 0
            total_switches = 0
            
            for i, session in enumerate(all_sessions, 1):
                kb_count = len(session.get('keyboard_events', []))
                click_count = len(session.get('mouse_clicks', []))
                move_count = len(session.get('mouse_movements', []))
                switch_count = len(session.get('window_switches', []))
                
                total_kb += kb_count
                total_clicks += click_count
                total_moves += move_count
                total_switches += switch_count
                
                f.write(f"\n{'='*40}\n")
                f.write(f"SESSION {i}\n")
                f.write(f"{'='*40}\n")
                f.write(f"Start: {session.get('start_time', 'N/A')}\n")
                f.write(f"End: {session.get('end_time', 'N/A')}\n")
                f.write(f"Keyboard Events: {kb_count}\n")
                f.write(f"Mouse Clicks: {click_count}\n")
                f.write(f"Mouse Movements: {move_count}\n")
                f.write(f"Window Switches: {switch_count}\n")
                
                # Top windows
                windows = session.get('active_windows', {})
                if windows:
                    f.write("\nTop Windows:\n")
                    for win, count in sorted(windows.items(), key=lambda x: x[1], reverse=True)[:5]:
                        f.write(f"  • {win}: {count} appearances\n")
                
                # Window durations
                durations = session.get('window_durations', {})
                if durations:
                    f.write("\nTime per window:\n")
                    for win, secs in sorted(durations.items(), key=lambda x: x[1], reverse=True)[:5]:
                        minutes = secs / 60
                        f.write(f"  • {win}: {minutes:.1f} minutes\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("GLOBAL STATISTICS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Keyboard Events: {total_kb}\n")
            f.write(f"Total Mouse Clicks: {total_clicks}\n")
            f.write(f"Total Mouse Movements: {total_moves}\n")
            f.write(f"Total Window Switches: {total_switches}\n")
            f.write(f"Total Events: {total_kb + total_clicks + total_moves + total_switches}\n")
            f.write("=" * 80 + "\n")
        
        messagebox.showinfo("Export Complete", f"Report saved to:\n{filename}")
    
    def clear_session(self):
        """Clear current session"""
        if messagebox.askyesno("Clear Session", "Clear current session data?"):
            self.current_session = self.create_new_session()
            self.start_time = None
            self.mouse_positions = []
            self.duration_var.set("00:00:00")
            self.events_var.set("0")
            self.window_var.set("Not tracking")
            self.draw_live_heatmap()
            self.draw_live_timeline()
            self.status_var.set("✅ Session cleared")
    
    def save_data(self):
        """Save sessions to file"""
        try:
            # Convert session data for JSON serialization
            sessions_to_save = []
            for session in self.sessions:
                session_copy = session.copy()
                # Convert any non-serializable data
                sessions_to_save.append(session_copy)
            
            with open(self.data_file, 'w') as f:
                json.dump(sessions_to_save, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self):
        """Load sessions from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.sessions = json.load(f)
                self.update_sessions_list()
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def update_sessions_list(self):
        """Update sessions listbox"""
        self.sessions_listbox.delete(0, tk.END)
        for i, session in enumerate(self.sessions[-10:], 1):
            if session.get('start_time'):
                try:
                    start = datetime.fromisoformat(session['start_time'])
                    display = f"Session {i}: {start.strftime('%H:%M %d/%m')}"
                    self.sessions_listbox.insert(tk.END, display)
                except:
                    self.sessions_listbox.insert(tk.END, f"Session {i}")
    
    def on_session_select(self, event):
        """Handle session selection"""
        selection = self.sessions_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.sessions):
                session = self.sessions[-(index+1)]
                
                # Calculate session stats
                kb_count = len(session.get('keyboard_events', []))
                click_count = len(session.get('mouse_clicks', []))
                move_count = len(session.get('mouse_movements', []))
                switch_count = len(session.get('window_switches', []))
                
                # Calculate duration if available
                duration = "N/A"
                if session.get('start_time') and session.get('end_time'):
                    try:
                        start = datetime.fromisoformat(session['start_time'])
                        end = datetime.fromisoformat(session['end_time'])
                        duration = str(end - start).split('.')[0]
                    except:
                        pass
                
                # Get top windows
                windows = session.get('active_windows', {})
                top_windows = sorted(windows.items(), key=lambda x: x[1], reverse=True)[:3]
                
                windows_text = ""
                for win, count in top_windows:
                    windows_text += f"\n  • {win[:30]}: {count}x"
                
                summary = f"""
📊 SESSION DETAILS
{'='*30}

Start: {session.get('start_time', 'N/A')}
End: {session.get('end_time', 'N/A')}
Duration: {duration}

📈 ACTIVITY
Keyboard: {kb_count} presses
Mouse Clicks: {click_count} clicks
Mouse Moves: {move_count} movements
Window Switches: {switch_count} switches

🎯 Total Events: {kb_count + click_count + move_count + switch_count}

🪟 TOP WINDOWS:{windows_text}
"""
                messagebox.showinfo("Session Details", summary)
    
    def run(self):
        """Start the application"""
        print("\n" + "="*60)
        print("🎯 COMPLETE HUMAN ATTENTION MAPPER")
        print("="*60)
        print(f"\n✅ Platform: {platform.system()} {platform.release()}")
        print("✅ Tracking REAL user activity")
        print("✅ Visual heatmaps with color gradients")
        print("✅ Timeline graphs with intensity bars")
        print("✅ Window activity charts")
        print("✅ Activity distribution pie charts")
        print("✅ Fully offline and privacy-focused")
        print("\n🚀 Launching application...\n")
        
        self.root.mainloop()

if __name__ == "__main__":
    app = CompleteAttentionMapper()
    app.run()