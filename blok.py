import tkinter as tk
import itertools
class Blok:
    def __init__(self, parent):
        self.dotsize = 10
        self.arrowsize = 5
        self.parent = parent
        self.running = False
        self.parent.title('Blok')
        self.canvas_width = 640
        self.canvas_height = 480
        self.boards = itertools.cycle([([(100, 100, 120, 120), (250, 250, 270, 270)],
                                        [(100, 240, 140, 280), (175, 165, 215, 205)],
                                        [{'start':(120, 260, 140, 240),
                                          'bbox':(100, 240, 140, 280),
                                          'ms_per_rotation_tick':0,
                                          'shot':False}])])
        self.draw_board()
        
    def draw_board(self, canvas=None, success=True):
        if canvas:
            canvas.destroy()
        self.canvas = tk.Canvas(self.parent, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack()
        if success:
            self.objects = next(self.boards)
        self.bumper_coords = self.objects[0]
        self.target_coords = self.objects[1][:] # make a copy so we can mutate it without clearing the board list
        self.shooter_coords = [{k:item[k] for k in item} for item in self.objects[2]]
        self.bumpers = [self.canvas.create_rectangle(tup, fill='black', outline='black') for tup in self.bumper_coords]
        self.targets = [self.canvas.create_rectangle(tup, fill='red', outline='red') for tup in self.target_coords]
        self.shooters = [self.canvas.create_line(arrow['start'], fill='blue', width=self.arrowsize, arrow=tk.LAST) for arrow in self.shooter_coords]
        for shooter,data in zip(self.shooters, self.shooter_coords):
            if data['ms_per_rotation_tick']:
                self.rotate(shooter, data['ms_per_rotation_tick'])
        self.canvas.bind("<Button-1>", self.start)
        self.canvas.bind("<Button-3>", lambda x: print(self.shooter_coords))
        self.all_good_things = self.parent.after(1, lambda: None)
        self.shooting = self.parent.after(1, lambda: None)
        self.decimate = 0 # counter for lower-res paintbrush
        
    def start(self, event):
        for x1, y1, x2, y2 in self.target_coords:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                return
        for x1, y1, x2, y2 in self.bumper_coords:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                return
        self.stuff = [[]]
        self.canvas.bind("<Button-1>", lambda x: self.reset(0))
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.repeat)
        self.running = True
        self.draw(event, True)
        
    def draw(self, event, first=False):
        if not self.decimate or first: # only add an object at 0
            x = self.bounce(event.x, self.canvas_width) # "bounce" off the left and right screen edges
            d = self.dotsize
            self.stuff[-1].append((self.canvas.create_rectangle((x-d, event.y-d, x+d, event.y+d), fill='black', outline='black'),
                                   event.time))
            if self.collisions(event, square=self.stuff[-1][-1][0]):
                self.canvas.unbind("<B1-Motion>")
                self.canvas.unbind("<ButtonRelease-1>")
        self.decimate += 1
        if self.decimate == 1: # decimate by 15, so 1/15 mouse draw events actually get drawn - leaving at 1 for now
            self.decimate = 0
            
    def repeat(self, event, count=2):
        collided = False
        if event:
            self.rep_time = event.time - self.stuff[-1][-1][1]
            current = event.x-self.dotsize, event.y-self.dotsize, event.x+self.dotsize, event.y+self.dotsize
            self.offset = self.offset_total = tuple(new-old for new, old in zip(current, self.canvas.bbox(self.stuff[0][0][0])))
        else:
            self.offset_total = tuple(sum(pair) for pair in zip(self.offset, self.offset_total))
        self.stuff.append([])
        self.repeat_cycle(count, len(self.stuff[0])-1)
    def repeat_cycle(self, count, repeat_count):
        idx = len(self.stuff[0])-repeat_count-1
        item,timing = self.stuff[0][idx]
        coords = [sum(coords) for coords in zip(self.canvas.bbox(item), self.offset_total)]
        mid = self.bounce((coords[0]+coords[2])//2, self.canvas_width)
        coords[0] = mid-self.dotsize
        coords[2] = mid+self.dotsize
        self.stuff[-1].append((self.canvas.create_rectangle(tuple(coords), fill='black', outline='black'), None))
        collided = self.collisions(square=self.stuff[-1][-1][0])
        if collided:
            return
        if repeat_count:
            try:
                self.all_good_things = self.parent.after(self.stuff[0][idx+1][1] - timing, lambda: self.repeat_cycle(count, repeat_count-1))
            except IndexError:
                print(len(self.stuff[0])-1, idx+1, count, repeat_count)
        else:
            self.end_repeat(count, collided)
    def end_repeat(self, count, collided):
        if count:
            if not collided:
                self.all_good_things = self.parent.after(self.rep_time, lambda: self.repeat(None, count-1))
        else:
            self.running = False
            if not any(shooter['shot'] for shooter in self.shooter_coords):
                self.parent.after(1000, lambda: self.reset(0))
    
    def bounce(self, num, maximum):
        while not 0 <= num <= maximum:
            num = min(abs(num), 2*maximum-num)
        return num
    
    def rotate(self, shooter):
        print('turn')
        tick = shooter['ms_per_rotation_tick']
        tick and self.parent.after(tick, lambda: self.rotate(tick))
    
    def shoot(self, shooter, data):
        x1, y1, x2, y2 = self.canvas.coords(shooter)
        width = x2-x1
        height = y2-y1
        x1 += 2
        x2 += 2
        dy = height / width * 2
        y1 += dy
        y2 += dy
        self.canvas.coords(shooter, x1, y1, x2, y2)
        if not (0 < x1 < self.canvas_width and 0 < y1 < self.canvas_height):
            self.canvas.delete(shooter)
            if not self.running:
                self.parent.after(1000, self.reset(0))
            return
        for idx, target in enumerate(self.target_coords):
            tx1, ty1, tx2, ty2 = target
            if tx1 < x2 < tx2 and ty1 < y2 < ty2:
                self.canvas.delete(self.targets[idx])
                self.canvas.delete(shooter)
                self.targets.pop(idx)
                self.target_coords.pop(idx)
                if not self.targets:
                    if not self.running:
                        self.parent.after(1000, lambda: self.reset(1))
                return
        self.shooting = self.parent.after(15, lambda: self.shoot(shooter,data))
        
    def collisions(self, event=None, square=None):
        self.all_good_things = self.parent.after(1000, lambda: self.canvas.itemconfig(square, fill='', outline=''))
        a,b,c,d = self.canvas.bbox(self.stuff[-1][-1][0])
        mid_x, mid_y = (c+a)//2, (d+b)//2
        dotsize = self.dotsize
        for bumper in self.bumper_coords:
            x1, y1, x2, y2 = bumper
            if x1-dotsize < mid_x < x2+dotsize and y1-dotsize < mid_y < y2+dotsize:
                self.parent.after(1000, lambda: self.reset(0))
                return True
        if event and (mid_x-dotsize <= 0 or mid_x+dotsize >= self.canvas_width):
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.repeat(event)
            return True
        for idx,(shooter,data) in enumerate(zip(self.shooters, self.shooter_coords)):
            if data['shot']:
                continue
            x1, y1, x2, y2 = data['bbox']
            if x1-dotsize < mid_x < x2+dotsize and y1-dotsize < mid_y < y2+dotsize:
                data['shot'] = True
                self.shoot(shooter, data)
        for idx, target in enumerate(self.target_coords):
            x1, y1, x2, y2 = target
            if x1-dotsize < mid_x < x2+dotsize and y1-dotsize < mid_y < y2+dotsize:
                self.canvas.delete(self.targets[idx])
                self.targets.pop(idx)
                self.target_coords.pop(idx)
                if event:
                    self.canvas.unbind("<B1-Motion>")
                    self.canvas.unbind("<ButtonRelease-1>")
                    self.repeat(event)
                    return True
        if not self.targets:
            self.parent.after_cancel(self.shooting)
            self.parent.after(1000, lambda: self.reset(1))
            return True
            
    def reset(self, success):
        print(('lose', 'win')[success])
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.parent.after_cancel(self.shooting)
        self.parent.after_cancel(self.all_good_things)
        self.parent.after(1000, self.draw_board(self.canvas, success))
        
        
root = tk.Tk()
blok = Blok(root)
root.mainloop()