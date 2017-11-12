import tkinter as tk
import pprint

class Maker:
    def __init__(self, parent):
        self.parent = parent
        self.kind = 'targets'
        self.arrowsize = 5
        self.colors = {'bumpers':'black', 'targets':'red', 'shooters':'blue'}
        self.canvas = None
        self.location = tk.StringVar(self.parent)
        self.loc_menu = tk.OptionMenu(self.parent, self.location, 'NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W')
        self.location.set('SE')
        self.rate = tk.StringVar(self.parent)
        self.rate_menu = tk.OptionMenu(self.parent, self.rate, 'static', '0.5', '1', '1.5', '2', '2.5', '3', '3.5', '4', '4.5', '5')
        self.rate.set('static')
        self.loc_menu.grid(row=0, column=0, sticky='E')
        self.rate_menu.grid(row=0, column=1, sticky='W')
        self.boards = []
        self.draw_board()
    def draw_board(self, save=False):
        if self.canvas:
            self.canvas.destroy()
        self.canvas = tk.Canvas(self.parent, width=1280, height=900)
        self.canvas.grid(row=1, column=0, columnspan=2)
        if save:
            self.boards.append(self.coord_objects)
        self.coord_objects = {'name':'Custom {}'.format(len(self.boards)+1), 'bumpers':[], 'targets':[], 'shooters':[]}
        self.canvas_objects = {'bumpers':[], 'targets':[], 'shooters':[]}
        self.canvas.bind('<Button-1>', self.start_square)
        self.canvas.bind('<ButtonRelease-1>', self.end_square)
        self.parent.bind('<F1>', self.help)
        self.parent.bind('e', lambda x: self.export(self.boards))
        self.parent.bind('p', lambda x: self.export(self.coord_objects))
        self.parent.bind('d', lambda x: self.draw_board(False)) # discard
        self.parent.bind('k', lambda x: self.draw_board(True)) # keep
        self.parent.bind('b', lambda x: self.change_kind('bumpers'))
        self.parent.bind('t', lambda x: self.change_kind('targets'))
        self.parent.bind('s', lambda x: self.change_kind('shooters'))
        self.parent.bind('z', self.undo)
    def help(self, event=None):
        t = tk.Toplevel(self.parent)
        t.focus_set()
        m = tk.Message(t, text='''    Click, drag, and release to create an object of the currently-selected type. It will be a square, constrained within the drawn rectangle.
    When drawing a shooter, the arrow will point in the direction indicated in the left menu at the top of the window. '''
'''The right menu lets you select how many seconds it takes for the arrow to make one complete circuit. The "static" option means that the shooter will not rotate. '''
'''Note that this applies to the next shooter you draw. If you draw a shooter with the wrong configuration, undo it with "z" and then choose a new configuration before trying again.
    An exported list of boards can be copied into a text editor, saved, and directly loaded into the game. The preview function only shows a single board, so you'll need '''
'''to either add it to an existing list of boards or put it into its own list by wrapping it in square brackets ("[" and "]").

Hotkeys:
F1: this help message
b: switch to drawing bumpers
t: switch to drawing targets
s: switch to drawing shooters
z: undo the most recently created item of the currently selected type
d: discard the current board, clear the area, and start a new one
k: keep the current board, add it to the list, clear the area, and start a new one
p: preview the current board in a popup window
e: export all saved boards (doesn't include the current board) and view them in a popup window''')
        m.pack()
    def undo(self, event=None):
        self.coord_objects[self.kind].pop()
        self.canvas.delete(self.canvas_objects[self.kind].pop())
    def change_kind(self, kind):
        self.kind = kind
    def export(self, obj):
        self.export_window = tk.Toplevel(self.parent)
        self.export_window.focus_set()
        self.export_window.title("Output")
        self.export_scrollbar = tk.Scrollbar(self.export_window, orient=tk.VERTICAL)
        self.export_text = tk.Text(self.export_window, yscrollcommand=self.export_scrollbar.set)
        self.export_scrollbar.config(command=self.export_text.yview)
        self.export_scrollbar.grid(row=0, column=1, sticky='NS')
        self.export_text.grid(row=0, column=0)
        self.export_text.focus_set()
        self.export_text.insert(tk.END, pprint.pformat(obj))
    def start_square(self, event):
        self.event = event
    def end_square(self, event):
        if abs(event.x-self.event.x) < 5 or abs(event.y-self.event.y) < 5:
            return
        x1 = min(self.event.x, event.x)
        y1 = min(self.event.y, event.y)
        x2 = max(self.event.x, event.x)
        y2 = max(self.event.y, event.y)
        width = min(x2-x1, y2-y1)
        x2 = x1 + width
        y2 = y1 + width
        coords = (x1, y1, x2, y2)
        color = self.colors[self.kind]
        if self.kind == 'shooters':
            rate = {'static':0, '0.5':125, '1':250, '1.5':375, '2':500, '2.5':625, '3':750, '3.5':875, '4':1000, '4.5':1125, '5':1250}[self.rate.get()]//width
            x, y = {'NW':(x1, y1), 'N':(x1+width//2, y1), 'NE':(x2, y1), 'E':(x2, y1+width//2), 'SE':(x2, y2), 'S':(x1+width//2, y2), 'SW':(x1, y2), 'W':(x1, y1+width//2)}[self.location.get()]
            self.coord_objects[self.kind].append({'start':(x1+width//2, y1+width//2, x, y), 'bbox':coords, 'ms_per_rotation_tick':rate, 'shot':False})
            self.canvas_objects[self.kind].append(self.canvas.create_line((x1+width//2, y1+width//2, x, y), fill=color, width=self.arrowsize, arrow=tk.LAST))
        else:
            self.coord_objects[self.kind].append(coords)
            self.canvas_objects[self.kind].append(self.canvas.create_rectangle(coords, fill=color, outline=color))
            
root = tk.Tk()
maker = Maker(root)
root.mainloop()