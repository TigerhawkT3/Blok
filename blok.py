try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
import itertools
import sys
import ast
class Blok:
    def __init__(self, parent):
        self.dotsize = 4
        self.arrowsize = 5
        self.portalsize = 40
        self.parent = parent
        self.running = False
        self.master_count = self.count = 50
        self.parent.title('Blok')
        self.canvas_width = 1280
        self.canvas_height = 900
        self.boards = itertools.cycle([
                                       {'name':'1',
                                        'targets':[(175, 165, 215, 205), (25, 165, 65, 205)]
                                       },
                                       {'name':'2',
                                        'bumpers':[(100, 100, 120, 120), (250, 250, 270, 270)],
                                        'targets':[(175, 165, 215, 205), (25, 165, 65, 205)]
                                       },
                                       {'name':'3',
                                        'bumpers':[(100, 100, 120, 120), (250, 250, 270, 270)],
                                        'targets':[(100, 240, 140, 280), (175, 165, 215, 205), (25, 165, 65, 205)]
                                       },
                                       {'name':'4',
                                        'bumpers':[(100, 100, 120, 120), (250, 250, 270, 270)],
                                        'targets':[(100, 240, 140, 280), (175, 165, 215, 205), (25, 165, 65, 205)],
                                        'shooters':[{'start':(120, 260, 140, 240),
                                          'bbox':(100, 240, 140, 280),
                                          'ms_per_rotation_tick':0,
                                          'shot':False},
                                          {'start':(120, 260, 140, 280),
                                          'bbox':(100, 240, 140, 280),
                                          'ms_per_rotation_tick':25,
                                          'shot':False}]
                                       },
                                       {'name':'5',
                                       'bumpers':[(100, 100, 120, 120), (250, 250, 270, 270), (15, 155, 75, 215)],
                                       'targets':[(100, 240, 140, 280), (175, 165, 215, 205), (25, 165, 65, 205)],
                                       'shooters':[{'start':(120, 260, 140, 240),
                                       'bbox':(100, 240, 140, 280),
                                       'ms_per_rotation_tick':0,
                                       'shot':False},
                                       {'start':(120, 260, 140, 280),
                                       'bbox':(100, 240, 140, 280),
                                       'ms_per_rotation_tick':25,
                                       'shot':False}]
                                       }
                                      ])
        try:
            with open(sys.argv[1]) as f:
                tmp = ast.literal_eval(f.read())
            self.boards = itertools.cycle(tmp)
            name = sys.argv[2]
            offset = sum(1 for i in itertools.takewhile(lambda x: x.get('name') != name, tmp))
            for i in range(offset):
                next(self.boards)
        except: # if it breaks for any reason
            pass # just keep the default
            
        self.draw_board()
        
    def draw_board(self, canvas=None, success=True):
        self.count = self.master_count
        self.portal_x_offset = 0
        self.portal_y_offset = 0
        if canvas:
            canvas.destroy()
        self.canvas = tk.Canvas(self.parent, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack()
        if success:
            self.objects = next(self.boards)
        self.bumper_coords = self.objects.get('bumpers', [])
        self.target_coords = self.objects.get('targets', [])[:] # make a copy so we can mutate it without clearing the board list
        self.shooter_coords = [{k:item[k] for k in item} for item in self.objects.get('shooters', [])]
        self.portal_coords = []
        self.bumpers = [self.canvas.create_rectangle(tup, fill='black', outline='black') for tup in self.bumper_coords]
        self.targets = [self.canvas.create_rectangle(tup, fill='red', outline='red') for tup in self.target_coords]
        self.shooters = [self.canvas.create_line(arrow['start'], fill='blue', width=self.arrowsize, arrow=tk.LAST) for arrow in self.shooter_coords]
        tmp = self.canvas.create_text(self.canvas_width, self.canvas_height, anchor=tk.SE, font=('Arial', 24), text=self.objects.get('name', ''))
        #self.parent.after(1000, lambda: self.canvas.coords(tmp, self.canvas_width, self.canvas_height)) # fails 5% of the time expecting 0 or 4 coords; no idea why
        self.portals = []
        for shooter,data in zip(self.shooters, self.shooter_coords):
            if data['ms_per_rotation_tick']:
                self.rotate(shooter, data)
        self.canvas.bind("<Button-1>", self.start)
        self.canvas.bind("<Button-3>", self.portal_entrance)
        self.all_good_things = self.parent.after(1, lambda: None)
        self.shooting = self.parent.after(1, lambda: None)
        self.decimate = 0 # counter for lower-res paintbrush
    
    def portal_entrance(self, event):
        self.canvas.bind("<ButtonRelease-3>", lambda x: self.portal_exit(x, event))
    
    def portal_exit(self, end, start):
        self.canvas.unbind("<ButtonRelease-3>")
        x_start, y_start, x_end, y_end = start.x, start.y, end.x, end.y
        if abs(x_start-x_end) < self.portalsize and abs(y_start-y_end) < self.portalsize:
            return # end if start/end portals overlap
        if not all((self.portalsize < x_start < self.canvas_width-self.portalsize,
                self.portalsize < x_end < self.canvas_width-self.portalsize,
                self.portalsize < y_start < self.canvas_height-self.portalsize,
                self.portalsize < y_end < self.canvas_height-self.portalsize)):
            return # end if either portal is off canvas
        for pair in self.portal_coords:
            for x1,y1,x2,y2 in pair:
                for x,y in (x_start, y_start), (x_end, y_end):
                    if x1-self.portalsize < x < x2+self.portalsize and y1-self.portalsize < y < y2+self.portalsize:
                        return # end if either portal overlaps another portal
        for x1, y1, x2, y2 in self.bumper_coords:
            for x,y in (x_start, y_start), (x_end, y_end):
                if x1-self.portalsize < x < x2+self.portalsize and y1-self.portalsize < y < y2+self.portalsize:
                    return # end if either portal overlaps a bumper
        for x1, y1, x2, y2 in self.target_coords:
            for x,y in (x_start, y_start), (x_end, y_end):
                if x1-self.portalsize < x < x2+self.portalsize and y1-self.portalsize < y < y2+self.portalsize:
                    return # end if either portal overlaps a target

        self.portal_coords.append(((x_start-self.portalsize, y_start-self.portalsize, x_start+self.portalsize, y_start+self.portalsize),
                                   (x_end-self.portalsize, y_end-self.portalsize, x_end+self.portalsize, y_end+self.portalsize)))
        options = {'dash':1, 'fill':'gray80', 'outline':'purple', 'width':20}
        self.portals.append((self.canvas.create_rectangle(self.portal_coords[-1][0], **options),
                             self.canvas.create_rectangle(self.portal_coords[-1][1], **options)))
    
    def cancel(self, event):
        self.count = 0
        self.repeat_count = 0
        for shooter,data in zip(self.shooters, self.shooter_coords):
            if data['shot']:
                self.canvas.coords(shooter, -20, -20, -10, -10)
    
    def start(self, event):
        for x1, y1, x2, y2 in self.target_coords:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                return
        for x1, y1, x2, y2 in self.bumper_coords:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                return
        if not self.dotsize < event.x < self.canvas_width-self.dotsize:
            return
        self.stuff = [[]]
        self.canvas.bind("<Button-1>", self.cancel)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.running = True
        self.check_win()
        self.draw(event, True)
        self.draw(event) # just in case the user clicks, doesn't move a single pixel, and releases
        self.canvas.bind("<ButtonRelease-1>", self.repeat)
        
    def draw(self, event, first=False):
        if not self.decimate or first: # only add an object at 0
            x = self.bounce(event.x, self.canvas_width) # "bounce" off the left and right screen edges
            d = self.dotsize
            self.stuff[-1].append((self.canvas.create_rectangle((x-d, event.y-d, x+d, event.y+d), fill='black', outline='black'),
                                   event.time))
            if self.collisions(event, square=self.stuff[-1][-1][0]):
                self.canvas.unbind("<B1-Motion>")
                self.canvas.unbind("<ButtonRelease-1>")
                self.canvas.unbind("<Button-3>")
        self.decimate += 1
        if self.decimate == 1: # decimate by 15, so 1/15 mouse draw events actually get drawn - leaving at 1 for now
            self.decimate = 0
            
    def repeat(self, event):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<Button-3>")
        collided = False
        if event:
            self.rep_time = event.time - self.stuff[-1][-1][1]
            current = event.x-self.dotsize, event.y-self.dotsize, event.x+self.dotsize, event.y+self.dotsize
            self.offset = self.offset_total = tuple(new-old for new, old in zip(current, self.canvas.bbox(self.stuff[0][0][0])))
        else:
            # need the last tuple in the trio to prevent the repeated line from shrinking
            self.offset_total = tuple(sum(trio) for trio in zip(self.offset, self.offset_total, (0,-1,0,1)))
        self.stuff.append([])
        self.repeat_count = len(self.stuff[0])-1
        self.repeat_cycle()
    def repeat_cycle(self):
        idx = len(self.stuff[0])-self.repeat_count-1
        item,timing = self.stuff[0][idx]
        coords = [sum(coords) for coords in zip(self.canvas.bbox(item), self.offset_total, (self.portal_x_offset, self.portal_y_offset, self.portal_x_offset, self.portal_y_offset))]
        mid = self.bounce((coords[0]+coords[2])//2, self.canvas_width)
        coords[0] = mid-self.dotsize
        coords[2] = mid+self.dotsize
        if self.repeat_count:
            self.stuff[-1].append((self.canvas.create_rectangle(tuple(coords), fill='black', outline='black'), None))
        try:
            collided = self.collisions(square=self.stuff[-1][-1][0])
        except IndexError:
            collided = True
        if collided:
            return
        if self.repeat_count > 0:
            self.repeat_count -= 1
            self.all_good_things = self.parent.after(self.stuff[0][idx+1][1] - timing, self.repeat_cycle)
        else:
            self.end_repeat(collided)
    def end_repeat(self, collided):
        if self.count > 0:
            self.count -= 1
            if not collided:
                self.all_good_things = self.parent.after(self.rep_time, lambda: self.repeat(None))
        else:
            self.running = False
    
    def bounce(self, num, maximum):
        while not 0 <= num <= maximum:
            num = min(abs(num), 2*maximum-num)
        return num
    
    def rotate(self, shooter, data):
        if data['shot']:
            return
        try:
            x1, y1, x, y = map(int, self.canvas.coords(shooter))
        except ValueError:
            return
        bx1, by1, bx2, by2 = data['bbox']
        
        if bx1 <= x < bx2 and y==by1:
            x+=1
        elif by1 <= y < by2 and x==bx2:
            y+=1
        elif by2==y and bx1 < x:
            x-=1
        else:
            y-=1
        
        self.canvas.coords(shooter, x1, y1, x, y)
        
        self.all_good_things = self.parent.after(data['ms_per_rotation_tick'], lambda: self.rotate(shooter, data))
    
    def shoot(self, shooter, data):
        x1, y1, x2, y2 = self.canvas.coords(shooter)
        width = x2-x1
        height = y2-y1
        x1 += width*.2
        x2 += width*.2
        y1 += height*.2
        y2 += height*.2
        self.canvas.coords(shooter, x1, y1, x2, y2)
        if not (0 < x1 < self.canvas_width and 0 < y1 < self.canvas_height):
            self.canvas.delete(shooter)
            return
        for idx, target in enumerate(self.target_coords):
            tx1, ty1, tx2, ty2 = target
            if tx1 < x2 < tx2 and ty1 < y2 < ty2:
                self.canvas.delete(self.targets[idx])
                self.canvas.delete(shooter)
                self.targets.pop(idx)
                self.target_coords.pop(idx)
                return
        self.shooting = self.parent.after(33, lambda: self.shoot(shooter,data))
        
    def collisions(self, event=None, square=None):
        self.all_good_things = self.parent.after(1000, lambda: self.canvas.itemconfig(square, fill='', outline=''))
        a,b,c,d = self.canvas.bbox(self.stuff[-1][-1][0])
        mid_x, mid_y = (c+a)//2, (d+b)//2
        dotsize = self.dotsize
        for bumper in self.bumper_coords:
            x1, y1, x2, y2 = bumper
            if x1-dotsize < mid_x < x2+dotsize and y1-dotsize < mid_y < y2+dotsize:
                self.all_good_things = self.parent.after(1000, lambda: self.reset(0))
                return True
        if event:
            if mid_x-dotsize <= 0 or mid_x+dotsize >= self.canvas_width:
                self.canvas.unbind("<B1-Motion>")
                self.canvas.unbind("<ButtonRelease-1>")
                self.canvas.unbind("<Button-3>")
                self.repeat(event)
                return True
        for (ax1,ay1,ax2,ay2),(bx1,by1,bx2,by2) in self.portal_coords:
            portaled=False
            if ax1-dotsize < mid_x < ax2+dotsize and ay1-dotsize < mid_y < ay2+dotsize:
                left = abs(mid_x-ax1)
                right = abs(mid_x-ax2)
                top = abs(mid_y-ay1)
                bottom = abs(mid_y-ay2)
                entrance = 1
                portaled=True
            elif bx1-dotsize < mid_x < bx2+dotsize and by1-dotsize < mid_y < by2+dotsize:
                left = abs(mid_x-bx1)
                right = abs(mid_x-bx2)
                top = abs(mid_y-by1)
                bottom = abs(mid_y-by2)
                entrance = -1
                portaled=True
            if portaled:
                extra = 2*self.portalsize + 2*dotsize
                if min(left, right, top, bottom) == left:
                    extra_x = extra
                    extra_y = 0
                elif min(right, top, bottom) == right:
                    extra_x = -extra
                    extra_y = 0
                elif min(top, bottom) == top:
                    extra_x = 0
                    extra_y = extra
                else:
                    extra_x = 0
                    extra_y = -extra
                self.portal_x_offset += (bx1-ax1)*entrance + extra_x
                self.portal_y_offset += (by1-ay1)*entrance + extra_y
                if event:
                    self.canvas.unbind("<B1-Motion>")
                    self.canvas.unbind("<ButtonRelease-1>")
                    self.canvas.unbind("<Button-3>")
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
                    self.canvas.unbind("<Button-3>")
                    self.repeat(event)
                    return True
        if not self.targets:
            return True
    
    def check_win(self):
        if not self.targets:
            self.parent.after_cancel(self.shooting)
            self.parent.after_cancel(self.all_good_things)
            self.reset(1)
            return
        shooting = []
        for shooter,data in zip(self.shooters, self.shooter_coords):
            if data['shot']:
                if self.canvas.coords(shooter):
                    shooting.append(shooter)
        if not (shooting or self.running):
            self.reset(0)
        else:
            self.all_good_things = self.parent.after(500, self.check_win)
        
    def reset(self, success):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<Button-3>")
        self.parent.after_cancel(self.shooting)
        self.parent.after_cancel(self.all_good_things)
        self.parent.after(1000, lambda: self.draw_board(self.canvas, success))
        
        
root = tk.Tk()
blok = Blok(root)
root.mainloop()