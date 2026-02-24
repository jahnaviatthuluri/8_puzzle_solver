import tkinter as tk
from tkinter import messagebox, font, ttk
import heapq
import threading
import time
import random
import json
import os
from datetime import datetime


# --- Solver Logic (Works with Custom Goal State) ---

def get_goal_positions(goal_state):
    """Creates a dictionary mapping tile values to their (row, col) coordinates for quick lookup."""
    positions = {}
    for r, row in enumerate(goal_state):
        for c, tile in enumerate(row):
            positions[tile] = (r, c)
    return positions


def calculate_manhattan_distance(state, goal_positions):
    """Calculates Manhattan distance for a given state against custom goal positions."""
    distance = 0
    for r in range(3):
        for c in range(3):
            tile = state[r][c]
            if tile != 0:
                goal_r, goal_c = goal_positions[tile]
                distance += abs(r - goal_r) + abs(c - goal_c)
    return distance


def solve_puzzle(initial_state, goal_state, callback=None):
    """A* solver that works with a custom goal state."""
    goal_positions = get_goal_positions(goal_state)
    goal_state_tuple = tuple(map(tuple, goal_state))

    pq = []
    initial_heuristic = calculate_manhattan_distance(initial_state, goal_positions)
    initial_cost = 0 + initial_heuristic
    initial_path = [initial_state]
    heapq.heappush(pq, (initial_cost, 0, initial_state, initial_path))
    visited = {tuple(map(tuple, initial_state))}
    nodes_explored = 0

    while pq:
        _, moves, current_state, path = heapq.heappop(pq)
        nodes_explored += 1

        if callback and nodes_explored % 100 == 0:
            callback(nodes_explored, len(visited))

        if tuple(map(tuple, current_state)) == goal_state_tuple:
            return path, nodes_explored

        blank_r, blank_c = find_blank(current_state)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_r, new_c = blank_r + dr, blank_c + dc
            if 0 <= new_r < 3 and 0 <= new_c < 3:
                new_state = [row[:] for row in current_state]
                new_state[blank_r][blank_c], new_state[new_r][new_c] = new_state[new_r][new_c], new_state[blank_r][
                    blank_c]
                new_state_tuple = tuple(map(tuple, new_state))
                if new_state_tuple not in visited:
                    visited.add(new_state_tuple)
                    new_moves = moves + 1
                    new_heuristic = calculate_manhattan_distance(new_state, goal_positions)
                    new_cost = new_moves + new_heuristic
                    new_path = path + [new_state]
                    heapq.heappush(pq, (new_cost, new_moves, new_state, new_path))
    return None, nodes_explored


# --- Unchanged Helper Functions ---
def find_blank(state):
    for r in range(3):
        for c in range(3):
            if state[r][c] == 0: return (r, c)
    return None


def generate_random_puzzle(moves=50):
    state = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
    for _ in range(moves):
        blank_r, blank_c = find_blank(state)
        possible_moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_r, new_c = blank_r + dr, blank_c + dc
            if 0 <= new_r < 3 and 0 <= new_c < 3: possible_moves.append((new_r, new_c))
        if possible_moves:
            new_r, new_c = random.choice(possible_moves)
            state[blank_r][blank_c], state[new_r][new_c] = state[new_r][new_c], state[blank_r][blank_c]
    return state


# --- History Manager (Unchanged) ---
class HistoryManager:
    def __init__(self, filename='puzzle_history.json'):
        self.filename = filename;
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_history(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.history[-50:], f, indent=2)
        except IOError:
            print("Warning: Could not save history.")

    def add_solve(self, moves, time, nodes, difficulty):
        self.history.append(
            {'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'moves': moves, 'time': round(time, 2),
             'nodes': nodes, 'difficulty': difficulty});
        self.save_history()

    def get_stats(self):
        if not self.history: return None
        total = len(self.history)
        return {'total': total, 'avg_moves': sum(h['moves'] for h in self.history) / total,
                'avg_time': sum(h['time'] for h in self.history) / total,
                'best_time': min(h['time'] for h in self.history)}


# --- Custom Rounded Button Class (Unchanged) ---
class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, corner_radius, padding, color, bg, text, command):
        tk.Canvas.__init__(self, parent, borderwidth=0, relief="flat", highlightthickness=0, bg=bg)
        self.command, self.color, self.hover_color, self.text = command, color, self._lighten_color(color), text
        self.width, self.height, self.corner_radius, self.padding = width, height, corner_radius, padding
        self.text_color = '#ffffff';
        self.config(width=width, height=height);
        self._draw()
        self.bind("<Enter>", self._on_enter);
        self.bind("<Leave>", self._on_leave);
        self.bind("<Button-1>", self._on_click)

    def _draw(self, color=None):
        if color is None: color = self.color
        self.delete("all")
        x1, y1, x2, y2, r = self.padding, self.padding, self.width - self.padding, self.height - self.padding, self.corner_radius
        self.create_oval(x1, y1, x1 + 2 * r, y1 + 2 * r, fill=color, outline=color)
        self.create_oval(x2 - 2 * r, y1, x2, y1 + 2 * r, fill=color, outline=color)
        self.create_oval(x1, y2 - 2 * r, x1 + 2 * r, y2, fill=color, outline=color)
        self.create_oval(x2 - 2 * r, y2 - 2 * r, x2, y2, fill=color, outline=color)
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline=color)
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline=color)
        self.create_text(self.width / 2, self.height / 2, text=self.text, fill=self.text_color,
                         font=("Segoe UI", 11, "bold"))

    def _on_enter(self, e):
        self._draw(self.hover_color)

    def _on_leave(self, e):
        self._draw()

    def _on_click(self, e):
        if self.command: self.command()

    def _lighten_color(self, color_hex, factor=0.2):
        r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
        r = min(255, int(r + (255 - r) * factor));
        g = min(255, int(g + (255 - g) * factor));
        b = min(255, int(b + (255 - b) * factor))
        return f'#{r:02x}{g:02x}{b:02x}'


# --- Enhanced GUI ---
class ProfessionalPuzzleGUI:
    def __init__(self, root):
        self.root = root;
        self.root.title("8-Puzzle Solver AI");
        self.root.minsize(1100, 720)
        self.theme = {"bg_grad_start": "#141e30", "bg_grad_end": "#243b55", "card": "#2c3e50", "card_border": "#34495e",
                      "primary": "#00a896", "success": "#02c39a", "warning": "#fbc490", "danger": "#e74c3c",
                      "purple": "#9b59b6", "text_light": "#ecf0f1", "text_medium": "#bdc3c7", "tile": "#34495e",
                      "tile_text": "#ecf0f1"}
        self.fonts = {"title": ("Segoe UI Black", 32, "bold"), "playback_heading": ("Segoe UI", 12, "bold"),
                      "heading": ("Segoe UI", 14, "bold"), "tile": ("Segoe UI", 38, "bold"), "text": ("Segoe UI", 10),
                      "stat_label": ("Segoe UI", 10, "bold"), "stat_value": ("Segoe UI", 24, "bold")}
        self.input_tiles, self.display_tiles = {}, {}
        self.animation_speed = tk.IntVar(value=300)
        self.is_solving, self.is_paused = False, False
        self.history, self.solution_path, self.current_step = HistoryManager(), None, 0
        self.goal_state = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        self.root.geometry(
            f"1200x800+{(self.root.winfo_screenwidth() - 1200) // 2}+{(self.root.winfo_screenheight() - 800) // 2}")
        self._create_gradient_background();
        self.create_ui();
        self.update_stats_display()

    def _create_gradient_background(self):
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0);
        self.bg_canvas.pack(fill="both", expand=True);
        self.root.bind("<Configure>", self._on_resize_gradient)

    def _draw_gradient(self, event=None):
        self.bg_canvas.delete("gradient");
        width, height = self.bg_canvas.winfo_width(), self.bg_canvas.winfo_height()
        if width < 2 or height < 2: return
        (r1, g1, b1), (r2, g2, b2) = self.root.winfo_rgb(self.theme["bg_grad_start"]), self.root.winfo_rgb(
            self.theme["bg_grad_end"])
        r, g, b = float(r2 - r1) / height, float(g2 - g1) / height, float(b2 - b1) / height
        for i in range(height):
            nr, ng, nb = int(r1 + (r * i)), int(g1 + (g * i)), int(b1 + (b * i))
            self.bg_canvas.create_line(0, i, width, i, tags=("gradient",), fill=f"#{nr:04x}{ng:04x}{nb:04x}")

    def _on_resize_gradient(self, event):
        self._draw_gradient()

    def create_ui(self):
        header = tk.Frame(self.bg_canvas, bg=self.theme["bg_grad_start"], height=50);
        header.pack(fill='x', side='top')
        content_frame = tk.Frame(self.bg_canvas, bg=self.theme["bg_grad_start"]);
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        left = self.create_card(content_frame);
        left.pack(side='left', fill='y', padx=(0, 25))
        center = self.create_card(content_frame, width=500);
        center.pack(side='left', padx=25)
        right = self.create_card(content_frame);
        right.pack(side='left', fill='y', padx=(25, 0))
        tk.Label(left, text="Statistics", font=self.fonts["heading"], bg=self.theme["card"],
                 fg=self.theme["text_light"]).pack(pady=(25, 15))
        self.moves_label, self.time_label, self.nodes_label = self.create_stat_row(left, "Moves", "0", self.theme[
            "primary"]), self.create_stat_row(left, "Time", "0.00s", self.theme["success"]), self.create_stat_row(left,
                                                                                                                  "Nodes",
                                                                                                                  "0",
                                                                                                                  self.theme[
                                                                                                                      "purple"])
        tk.Frame(left, bg=self.theme["card_border"], height=1).pack(fill='x', padx=30, pady=20)
        tk.Label(left, text="Overall", font=self.fonts["heading"], bg=self.theme["card"],
                 fg=self.theme["text_light"]).pack(pady=(0, 15))
        self.total_label, self.avg_moves_label, self.best_time_label = self.create_stat_row(left, "Solved", "0",
                                                                                            self.theme[
                                                                                                "primary"]), self.create_stat_row(
            left, "Avg Moves", "--", self.theme["warning"]), self.create_stat_row(left, "Best Time", "--",
                                                                                  self.theme["danger"])
        RoundedButton(left, 200, 50, 15, 5, self.theme["primary"], self.theme["card"], "📥 Export History",
                      self.export_history).pack(side='bottom', pady=(25, 25))
        tk.Label(center, text="8-PUZZLE SOLVER", font=self.fonts["title"], bg=self.theme["card"],
                 fg=self.theme["text_light"]).pack(pady=(30, 15))
        puzzle_inner_frame = tk.Frame(center, bg=self.theme["card"]);
        puzzle_inner_frame.pack(expand=True)
        self.input_frame, self.display_frame = tk.Frame(puzzle_inner_frame, bg=self.theme["card"]), tk.Frame(
            puzzle_inner_frame, bg=self.theme["card"]);
        self.input_frame.pack()
        self.create_input_grid();
        self.create_display_grid()
        diff_frame = tk.Frame(center, bg=self.theme["card"]);
        diff_frame.pack(side='bottom', pady=(15, 25))
        tk.Label(diff_frame, text="Difficulty:", font=self.fonts["text"], bg=self.theme["card"],
                 fg=self.theme["text_medium"]).pack(side='left', padx=(0, 8))
        self.difficulty_label = tk.Label(diff_frame, text="--", font=self.fonts["heading"], bg=self.theme["card"],
                                         fg=self.theme["text_light"]);
        self.difficulty_label.pack(side='left')
        controls_inner = tk.Frame(right, bg=self.theme["card"]);
        controls_inner.pack(fill='both', expand=True, padx=30, pady=30)
        RoundedButton(controls_inner, 220, 50, 15, 5, self.theme["primary"], self.theme["card"], "🚀 Solve Puzzle",
                      self.solve_puzzle_threaded).pack(pady=8)
        RoundedButton(controls_inner, 220, 50, 15, 5, self.theme["purple"], self.theme["card"], "🎲 Random Puzzle",
                      self.generate_random).pack(pady=8)
        RoundedButton(controls_inner, 220, 50, 15, 5, self.theme["warning"], self.theme["card"], "🎯 Set Goal State",
                      self.open_goal_state_editor).pack(pady=8)
        RoundedButton(controls_inner, 220, 50, 15, 5, self.theme["danger"], self.theme["card"], "🔄 Reset Board",
                      self.reset_board).pack(pady=8)
        tk.Frame(controls_inner, bg=self.theme["card_border"], height=1).pack(fill='x', padx=0, pady=20)
        tk.Label(controls_inner, text="Playback Controls", font=self.fonts["playback_heading"], bg=self.theme["card"],
                 fg=self.theme["text_light"]).pack()
        playback_buttons_frame = tk.Frame(controls_inner, bg=self.theme["card"]);
        playback_buttons_frame.pack(pady=10)
        self.step_back_btn, self.pause_play_btn, self.step_fwd_btn = self.create_playback_button(playback_buttons_frame,
                                                                                                 "⏪",
                                                                                                 self.step_backward), self.create_playback_button(
            playback_buttons_frame, "⏸", self.toggle_pause_play), self.create_playback_button(playback_buttons_frame,
                                                                                               "⏩", self.step_forward)
        self.step_back_btn.pack(side='left', padx=10);
        self.pause_play_btn.pack(side='left', padx=10);
        self.step_fwd_btn.pack(side='left', padx=10)
        speed_frame = tk.Frame(controls_inner, bg=self.theme["card"]);
        speed_frame.pack(fill='x', pady=(5, 0))
        tk.Label(speed_frame, text="Fast", font=self.fonts["text"], bg=self.theme["card"],
                 fg=self.theme["text_medium"]).pack(side='left', padx=(5, 0))
        tk.Label(speed_frame, text="Slow", font=self.fonts["text"], bg=self.theme["card"],
                 fg=self.theme["text_medium"]).pack(side='right', padx=(0, 5))
        style = ttk.Style();
        style.configure("TScale", background=self.theme["card"], troughcolor=self.theme["card_border"])
        ttk.Scale(speed_frame, from_=50, to=1000, orient='horizontal', variable=self.animation_speed).pack(side='left',
                                                                                                           fill='x',
                                                                                                           expand=True,
                                                                                                           padx=5)

    def create_card(self, parent, **kwargs):
        return tk.Frame(parent, bg=self.theme["card"], highlightbackground=self.theme["card_border"],
                        highlightthickness=1, **kwargs)

    def create_stat_row(self, parent, label, value, color):
        frame = tk.Frame(parent, bg=self.theme["card"]);
        frame.pack(fill='x', padx=30, pady=8)
        tk.Label(frame, text=label, font=self.fonts["stat_label"], bg=self.theme["card"], fg=self.theme["text_medium"],
                 anchor='w').pack(side='left')
        val_widget = tk.Label(frame, text=value, font=self.fonts["stat_value"], bg=self.theme["card"], fg=color,
                              anchor='e');
        val_widget.pack(side='right');
        return val_widget

    def create_input_grid(self):
        for r in range(3):
            for c in range(3):
                frame = tk.Frame(self.input_frame, bg=self.theme["card"], highlightbackground=self.theme["card_border"],
                                 highlightthickness=2);
                frame.grid(row=r, column=c, padx=8, pady=8)
                tile = tk.Entry(frame, width=2, font=self.fonts["tile"], justify='center', bd=0, relief='flat',
                                bg=self.theme["tile"], fg=self.theme["tile_text"],
                                insertbackground=self.theme["primary"]);
                tile.pack(padx=30, pady=22)
                tile.bind('<KeyRelease>', lambda e: self.update_difficulty())
                tile.bind('<FocusIn>', lambda e, f=frame: f.config(highlightbackground=self.theme["primary"]));
                tile.bind('<FocusOut>', lambda e, f=frame: f.config(highlightbackground=self.theme["card_border"]))
                self.input_tiles[(r, c)] = tile

    def create_display_grid(self):
        for r in range(3):
            for c in range(3):
                tile = tk.Label(self.display_frame, text="", width=3, font=self.fonts["tile"], relief='flat',
                                bg=self.theme["tile"], fg=self.theme["tile_text"],
                                highlightbackground=self.theme["card_border"], highlightthickness=2);
                tile.grid(row=r, column=c, padx=8, pady=8, ipadx=24, ipady=16);
                self.display_tiles[(r, c)] = tile

    def get_board_state_from_entries(self, entry_widgets):
        state, flat_list = [], []
        try:
            for r in range(3):
                row = []
                for c in range(3):
                    val_str = entry_widgets[(r, c)].get()
                    val = int(val_str if val_str else '0')
                    if val in flat_list: return None  # Duplicate check
                    row.append(val);
                    flat_list.append(val)
                state.append(row)
            return state if sorted(flat_list) == list(range(9)) else None
        except ValueError:
            return None

    def update_difficulty(self, *args):
        state = self.get_board_state_from_entries(self.input_tiles)
        if state:
            goal_pos = get_goal_positions(self.goal_state)
            diff = calculate_manhattan_distance(state, goal_pos)
            if diff == 0:
                label, color = "Solved", self.theme["success"]
            elif diff < 10:
                label, color = f"{diff} - Easy", self.theme["success"]
            elif diff < 20:
                label, color = f"{diff} - Medium", self.theme["warning"]
            else:
                label, color = f"{diff} - Hard", self.theme["danger"]
            self.difficulty_label.config(text=label, fg=color)
        else:
            self.difficulty_label.config(text="--", fg=self.theme["text_medium"])

    def update_stats_display(self):
        stats = self.history.get_stats()
        if stats:
            self.total_label.config(text=str(stats['total'])); self.avg_moves_label.config(
                text=f"{stats['avg_moves']:.1f}"); self.best_time_label.config(text=f"{stats['best_time']:.2f}s")
        else:
            self.total_label.config(text="0"); self.avg_moves_label.config(text="--"); self.best_time_label.config(
                text="--")

    def generate_random(self):
        self.reset_board()
        puzzle = generate_random_puzzle(random.randint(20, 60))
        for r in range(3):
            for c in range(3):
                val = puzzle[r][c];
                self.input_tiles[(r, c)].delete(0, tk.END);
                self.input_tiles[(r, c)].insert(0, str(val) if val != 0 else "")
        self.update_difficulty()

    def reset_board(self):
        self.solution_path = None
        self.display_frame.pack_forget();
        self.input_frame.pack()
        for r in range(3):
            for c in range(3): self.input_tiles[(r, c)].delete(0, tk.END)
        self.moves_label.config(text="0");
        self.time_label.config(text="0.00s");
        self.nodes_label.config(text="0")
        self.is_solving, self.is_paused = False, False;
        self.update_difficulty()
        self.set_playback_buttons_state('disabled');
        self.pause_play_btn.config(text="⏸")

    def solve_puzzle_threaded(self):
        if self.is_solving or self.solution_path: return
        initial_state = self.get_board_state_from_entries(self.input_tiles)
        if not initial_state: messagebox.showerror("Invalid Puzzle",
                                                   "Please enter a valid puzzle (numbers 0-8, no duplicates)."); return
        flat_puzzle = [num for row in initial_state for num in row]
        flat_goal = [num for row in self.goal_state for num in row]

        def count_inversions(p):
            return sum(1 for i in range(9) for j in range(i + 1, 9) if p[i] and p[j] and p[i] > p[j])

        if count_inversions(flat_puzzle) % 2 != count_inversions(flat_goal) % 2: messagebox.showerror(
            "Unsolvable Puzzle", "This puzzle configuration is not solvable for the current goal state."); return
        self.is_solving, self.current_puzzle = True, initial_state
        goal_pos = get_goal_positions(self.goal_state)
        difficulty = calculate_manhattan_distance(initial_state, goal_pos)
        threading.Thread(target=self._run_solver, args=(initial_state, difficulty), daemon=True).start()

    def _run_solver(self, initial_state, difficulty):
        start_time = time.time()
        # --- FIX IS HERE ---
        # The callback lambda now uses root.after() to schedule the GUI update on the main thread,
        # preventing thread-safety issues that were causing the animation to glitch.
        path, nodes = solve_puzzle(initial_state, self.goal_state, lambda n, v: self.root.after(0, self._update_nodes_display, n))
        solve_time = time.time() - start_time
        self.root.after(0, self.start_animation, path, nodes, solve_time, difficulty)

    def _update_nodes_display(self, nodes_count):
        """Safely updates the nodes label from the main thread."""
        self.nodes_label.config(text=str(nodes_count))

    def start_animation(self, path, nodes, solve_time, difficulty):
        if path is None: self.is_solving = False; messagebox.showerror("Error", "No solution found."); return
        self.solution_path, self.current_step = path, 0
        moves = len(path) - 1
        self.moves_label.config(text=str(moves));
        self.time_label.config(text=f"{solve_time:.2f}s");
        self.nodes_label.config(text=str(nodes))
        self.history.add_solve(moves, solve_time, nodes, difficulty)
        self.update_stats_display();
        self.input_frame.pack_forget();
        self.display_frame.pack()
        self.set_playback_buttons_state('normal');
        self.step_back_btn.config(state='disabled')
        self.is_paused = False;
        self.animate_next_step()

    def _draw_current_step(self):
        if not self.solution_path: return
        state = self.solution_path[self.current_step]
        moved_pos = find_blank(self.solution_path[self.current_step - 1]) if self.current_step > 0 else None
        is_final = self.current_step == len(self.solution_path) - 1
        for r, row in enumerate(state):
            for c, num in enumerate(row):
                tile = self.display_tiles[(r, c)]
                if num == 0:
                    tile.config(text="", bg=self.theme["card"], highlightthickness=0)
                else:
                    bg = self.theme["success"] if is_final else (
                        self.theme["primary"] if (r, c) == moved_pos else self.theme["tile"])
                    border = self.theme["success"] if is_final else (
                        self.theme["primary"] if (r, c) == moved_pos else self.theme["card_border"])
                    tile.config(text=str(num), bg=bg, fg=self.theme["tile_text"], highlightthickness=2,
                                highlightbackground=border)
        self.root.update_idletasks()

    def animate_next_step(self):
        if self.is_paused or not self.is_solving: return
        self._draw_current_step()
        if self.current_step < len(self.solution_path) - 1:
            self.current_step += 1;
            self.root.after(self.animation_speed.get(), self.animate_next_step)
        else:
            self.is_solving, self.is_paused = False, True
            self.pause_play_btn.config(state='disabled', text="▶")
            self.step_back_btn.config(state='normal');
            self.step_fwd_btn.config(state='disabled')

    def set_playback_buttons_state(self, state):
        self.step_back_btn.config(state=state);
        self.pause_play_btn.config(state=state);
        self.step_fwd_btn.config(state=state)

    def toggle_pause_play(self):
        if not self.is_solving: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_play_btn.config(text="▶")
        else:
            self.pause_play_btn.config(text="⏸"); self.animate_next_step()

    def step_forward(self):
        if self.solution_path and self.current_step < len(self.solution_path) - 1:
            self.current_step += 1;
            self._draw_current_step()
            self.step_back_btn.config(state='normal')
            if self.current_step == len(self.solution_path) - 1: self.step_fwd_btn.config(state='disabled')

    def step_backward(self):
        if self.solution_path and self.current_step > 0:
            self.current_step -= 1;
            self._draw_current_step()
            self.step_fwd_btn.config(state='normal')
            if self.current_step == 0: self.step_back_btn.config(state='disabled')

    def open_goal_state_editor(self):
        editor = tk.Toplevel(self.root);
        editor.title("Set Custom Goal State");
        editor.config(bg=self.theme["card"])
        editor.transient(self.root);
        editor.grab_set()
        entries = {}
        for r in range(3):
            for c in range(3):
                frame = tk.Frame(editor, bg=self.theme["card"], highlightbackground=self.theme["card_border"],
                                 highlightthickness=1);
                frame.grid(row=r, column=c, padx=5, pady=5)
                entry = tk.Entry(frame, width=2, font=self.fonts["tile"], justify='center', bd=0, relief='flat',
                                 bg=self.theme["tile"], fg=self.theme["tile_text"]);
                entry.pack(padx=15, pady=10)
                val = self.goal_state[r][c];
                entry.insert(0, str(val) if val != 0 else "")
                entries[(r, c)] = entry
        btn_frame = tk.Frame(editor, bg=self.theme["card"]);
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)

        def save():
            new_goal = self.get_board_state_from_entries(entries)
            if new_goal:
                self.goal_state = new_goal; self.update_difficulty(); editor.destroy()
            else:
                messagebox.showerror("Invalid Goal", "Please enter a valid puzzle configuration (0-8, no duplicates).",
                                     parent=editor)

        tk.Button(btn_frame, text="Save", command=save, bg=self.theme["success"], fg="#ffffff", bd=0,
                  font=("Segoe UI", 10, "bold"), padx=10, pady=5).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Cancel", command=editor.destroy, bg=self.theme["danger"], fg="#ffffff", bd=0,
                  font=("Segoe UI", 10, "bold"), padx=10, pady=5).pack(side='left', padx=10)

    def create_playback_button(self, parent, text, command):
        return tk.Button(parent, text=text, font=("Segoe UI", 14), bd=0, bg=self.theme["card"],
                         fg=self.theme["text_light"], activebackground=self.theme["card_border"],
                         activeforeground=self.theme["text_light"], relief='flat', command=command, state='disabled')

    def show_hint(self):
        messagebox.showinfo("Hint", "Hint functionality to be implemented.")

    def export_history(self):
        messagebox.showinfo("Export", "History export functionality to be implemented.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalPuzzleGUI(root)
    root.mainloop()