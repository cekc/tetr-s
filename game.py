import tkinter as tk
from tkinter import messagebox
from random import shuffle, choice, getrandbits
from time import monotonic

COLORS = ['#07B978', '#C95710', '#6E7188', '#C04FDA', '#0F5FD0',
          '#7CC30A', '#F72B39']
shuffle(COLORS)

class Game(tk.Frame):

    def __init__(self, master):
        super().__init__(master)
        self.grid()

        self.master.protocol('WM_DELETE_WINDOW', self.abandon)

        self.canvas = tk.Canvas(self, width=200, height=400)
        self.canvas.grid(row=0, column=0)

        #self.sidebar = tk.Frame(self, width=200, height=400)
        #self.sidebar.grid(row=0, column=1)

        #self.scorelabel = tk.Label(self.sidebar, text='Score: 0')
        #self.scorelabel.grid(row=0, column=1, sticky=tk.N)

        print(self.master.geometry('204x404+400+100'))

        #self.master.bind('<space>', self.instantfall)
        self.speedup = HoldReleaseHandler(self.master, 'Down')
        self.movingleft = HoldReleaseHandler(self.master, 'Left')
        self.movingright = HoldReleaseHandler(self.master, 'Right')
        self.rotating = HoldReleaseHandler(self.master, 'Up')
        self.double_rot = HoldReleaseHandler(self.master, 'Shift_L')
        self.counter_rot = HoldReleaseHandler(self.master, 'Control_L')
        self.master.bind('<Escape>', self.pause)

        self.timequant = 0.025
        self.speedfactor = 20
        self.presshold_cooldown = 4

        self.solidtiles = {}
        self.piece = Tetramino.spawn(self.canvas)

        self.paused = False

        self.gameloop()

    def gameloop(self):
        falldelay = self.speedfactor
        lockdelay = self.speedfactor
        leftcooldown = 0
        rightcooldown = 0

        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.levelup_lines = 4

        self.waittime = monotonic()

        while True:

            if falldelay:
                falldelay -= 1
            if lockdelay > 0:
                lockdelay -= 1
            if leftcooldown:
                leftcooldown -= 1
            if rightcooldown:
                rightcooldown -= 1

            if not falldelay or self.speedup.held:
                falldelay = self.speedfactor
                if self.move(0, -1):
                    lockdelay = -1
                    if self.speedup.held:
                        self.score += self.level
                elif not lockdelay:
                    for t in self.piece.tiles:
                        if t.y >= 20:
                            self.gameover()
                        self.solidtiles[t.x, t.y] = t
                    self.canvas.dtag('piece', 'piece')
                    self.clearlines(self.piece.y, self.piece.boxsize)
                    self.piece = Tetramino.spawn(self.canvas)
                    lockdelay = -1
                elif lockdelay < 0:
                    lockdelay = self.speedfactor
                    
            if self.movingleft.pressed:
                self.movingleft.pressed = False
                leftcooldown =self.presshold_cooldown 
                self.move(-1, 0)
            elif not leftcooldown and self.movingleft.held:
                self.move(-1, 0)

            if self.movingright.pressed:
                self.movingright.pressed = False
                rightcooldown = self.presshold_cooldown
                self.move(1, 0)
            elif not rightcooldown and self.movingright.held:
                self.move(1, 0)
                
            if self.rotating.pressed:
                self.rotating.pressed = False
                if self.double_rot.held:
                    self.rotate(2)
                elif self.counter_rot.held:
                    self.rotate(3)
                else:
                    for i in (1, 3, 2):
                        if self.rotate(i):
                            break

            #self.master.update()
            while self.lines_cleared >= self.levelup_lines:
                self.level += 1
                self.speedfactor -= 1
                self.levelup_lines = self.level * (self.level + 1) * 2
                if self.level >= 15:
                    self.levelup_lines = float('inf')

            #self.scorelabel['text'] = 'Score: ' + str(self.score)
            self.wait()


    def move(self, x, y):
        will_occupy = self.piece.points(x, y)
        for x2, y2 in will_occupy:
            if x2 > 9 or x2 < 0 or y2 < 0 or self.solidtiles.get((x2, y2)):
                return False
        for t in self.piece.tiles:
            t.x += x
            t.y += y
        self.piece.x += x
        self.piece.y += y
        self.canvas.move('piece', 20*x, -20*y)
        return True

    def rotate(self, angle=1):
        if not (angle % self.piece.rot_order):
            return True
        for wkick in self.piece.wkicks_list():
            can_rotate = True
            will_occupy = self.piece.points(wkick[0], wkick[1], angle)
            for x2, y2 in will_occupy:
                if x2 > 9 or x2 < 0 or y2 < 0 or self.solidtiles.get((x2, y2)):
                    can_rotate = False
                    break
            if can_rotate:
                self.piece.x += wkick[0]
                self.piece.y += wkick[1]
                self.piece.angle = (self.piece.angle + angle) \
                                   % self.piece.rot_order
                self.canvas.delete('piece')
                self.piece.draw()
                return True
        return False
                
        
        
    def clearlines(self, y0=0, delta=20):
        filled = []
        for y in reversed(range(y0, y0 + delta)):
            if all(self.solidtiles.get((x, y)) for x in range(10)):
                filled.append(y)

        for x in (0, 9, 1, 8, 2, 7, 3, 6, 4, 5):
            for y in filled:
                self.canvas.delete(self.solidtiles[x, y].rectangle)
                for y1 in range(y + 1, 20):
                    self.solidtiles[x, y1-1] = self.solidtiles.get((x, y1))
            #self.master.update()
            self.score += 10*len(filled)*(len(filled)+1)
            #self.scorelabel['text'] = 'Score: ' + str(self.score)
            self.wait()

        for y in filled:
            self.canvas.addtag_enclosed('move', 3, 3, 201, 381-20*y)
            self.canvas.move('move', 0, 20)
            self.canvas.dtag('move', 'move')
            #self.master.update()
            self.wait()

        self.lines_cleared += len(filled)
        while self.lines_cleared >= self.levelup_lines:
            self.level += 1
            self.speedfactor -= 1
            self.levelup_lines += self.level * 3
            if self.level >= 15:
                self.levelup_lines = float('inf')

    def instantfall(self, event=None):
        pass

    def pause(self, event=None):
        self.paused ^= 1
        if self.paused:
            self.canvas.addtag_all('all')
            self.canvas.itemconfigure('all', stipple='gray50')
        else:
            self.canvas.itemconfigure('all', stipple='')
            self.canvas.dtag('all', 'all')
            self.waittime = monotonic()
            

    def wait(self):
        self.master.update()
        self.wait_quant()
        while self.paused:
            self.master.update()
            self.wait_quant()
        

    def wait_quant(self):
        self.waittime += self.timequant
        while monotonic() < self.waittime:
            pass

    def abandon(self):
        self.paused = False
        self.pause()
        if messagebox.askyesno('Abandon', 'Do you really want to quit?'): 
            try:
                self.master.destroy()
            except:
                pass
            finally:
                quit()
        else:
            self.pause()


class Tile:
    def __init__(self, x, y, canvas, tag=None, color='', fillpattern=''):
        self.x = x
        self.y = y
        #self.color = color
        #self.canvas = canvas
        self.rectangle = canvas.create_rectangle(
            3+20*x, 383-20*y, 21+20*x, 401-20*y, fill=color, width=0,
            stipple=fillpattern)
        if not tag is None:
            canvas.addtag_withtag(tag, self.rectangle)


class Tetramino: 
    def __init__(self, canvas, angle, x, y, appear):
        if self.__class__.__name__ == 'Tetramino':
            raise TypeError
        self.canvas = canvas
        self.angle = angle % self.rot_order
        self.x = x
        self.y = y
        if appear:
            self.draw()
            

    def clone(self, x=0, y=0, angle=0, appear=False, relative=True):
        if relative:
            x += self.x
            y += self.y
        return type(self)(
            self.canvas, self.angle+angle, x, y, appear)

    def points(self, x=0, y=0, angle=0):
        return ((self.x + x1 + x, self.y + y1 + y)
                for x1, y1 in
                self.bodies[(self.angle + angle) % self.rot_order])

    def draw(self, color=None):
        if color is None:
            color = self.color
        self.tiles = [
            Tile(self.x + x1, self.y + y1, self.canvas, 'piece', color)
            for x1, y1 in self.bodies[self.angle] ]

    def wkicks_list(self):
        return self.wallkicks[self.angle]

    @classmethod
    def spawn(cls, canvas, x=3, y=20):
        if cls == Tetramino:
            cls = choice(Tetramino.__subclasses__())

        return cls(canvas, getrandbits(2),
                     x + cls.spawnoffset_x, y + cls.spawnoffset_y)
        

class I(Tetramino):
    bodies = (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((1, 0), (1, 1), (1, 2), (1, 3))
        )
    wallkicks = (
        ((0, 0),),
        ((0, 0), (-1, 0), (1, 0), (-2, 0))
        )
    boxsize = 4
    spawnoffset_x, spawnoffset_y = (0, 0)
    rot_order = 2
    color = COLORS[0]
    def __init__(self, canvas, angle, x=0, y=0, appear=True):
        Tetramino.__init__(self, canvas, angle, x, y, appear)

class O(Tetramino):
    bodies = (
        ((0, 0), (1, 0), (0, 1), (1, 1)), 
        )
    wallkicks = (((0, 0),),)
    boxsize = 2
    spawnoffset_x, spawnoffset_y = (1, 0)
    rot_order = 1
    color = COLORS[1]
    def __init__(self, canvas, angle, x=0, y=0, appear=True):
        Tetramino.__init__(self, canvas, angle, x, y, appear)

class L(Tetramino):
    bodies = (
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (2, 1))
        )
    wallkicks = (
        ((0, 0), (1, 0)),
        ((0, 0),),
        ((0, 0), (-1, 0)),
        ((0, 0),)
        )
    boxsize = 3
    spawnoffset_x, spawnoffset_y = (0, 0)
    rot_order = 4
    color = COLORS[2]
    def __init__(self, canvas, angle, x=0, y=0, appear=True):
        Tetramino.__init__(self, canvas, angle, x, y, appear)
            
class J(Tetramino):
    bodies = (
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 0), (2, 1))
        )
    wallkicks = (
        ((0, 0), (-1, 0)),
        ((0, 0),),
        ((0, 0), (1, 0)),
        ((0, 0),)
        )
    boxsize = 3
    spawnoffset_x, spawnoffset_y = (1, 0)
    rot_order = 4
    color = COLORS[3]
    def __init__(self, canvas, angle, x=0, y=0, appear=True):
        Tetramino.__init__(self, canvas, angle, x, y, appear)

class T(Tetramino):
    bodies = (
        ((0, 1), (1, 0), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
        ((0, 1), (1, 0), (1, 1), (1, 2))
        )
    wallkicks = (
        ((0, 0),),
        ((0, 0), (1, 0)),
        ((0, 0),),
        ((0, 0), (-1, 0))
        )
    boxsize = 3
    spawnoffset_x, spawnoffset_y = (0, 0)
    rot_order = 4
    color = COLORS[4]
    def __init__(self, canvas, angle, x=0, y=0, appear=True):
        Tetramino.__init__(self, canvas, angle, x, y, appear)

class S(Tetramino):
    bodies = (
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1))
        )
    boxsize = 3
    wallkicks = (
        ((0, 0), (-1, 0)),
        ((0, 0),)
        )
    spawnoffset_x, spawnoffset_y = (1, 0)
    rot_order = 2
    color = COLORS[5]
    def __init__(self, canvas, angle, x=0, y=0, appear=True):
        Tetramino.__init__(self, canvas, angle, x, y, appear)

class Z(Tetramino):
    bodies = (
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (2, 0))
        )
    wallkicks = (
        ((0, 0), (1, 0)),
        ((0, 0),)
        )
    boxsize = 3
    spawnoffset_x, spawnoffset_y = (0, 0)
    rot_order = 2
    color = COLORS[6]
    def __init__(self, canvas, angle, x=0, y=0, appear=True):
        Tetramino.__init__(self, canvas, angle, x, y, appear)
            

class HoldReleaseHandler:
    def __init__(self, widget, keysym):
        self.held = False
        self.pressed = False
        self.widget = widget
        self.press_str = '<KeyPress-' + keysym + '>'
        self.release_str = '<KeyRelease-' + keysym + '>'
        self.hh_id = self.widget.bind(self.press_str, self.hold_handler, '+')
        self.rh_id = self.widget.bind(self.release_str, self.release_handler,
                                      '+')

    def hold_handler(self, event=None):
        self.held = True
        self.pressed = True
        self.widget.unbind(self.press_str, self.hh_id)

    def release_handler(self, event=None):
        self.held = False
        self.hh_id = self.widget.bind(self.press_str, self.hold_handler, '+')

    def __del__(self):
        self.widget.unbind(self.press_str, self.hh_id)
        self.widget.unbind(self.release_str, self.rh_id)
        
    
def start_app():    
    root = tk.Tk()
    root.title("Who cares 'bout name")
    root.resizable(False, False)
    app = Game(master=root)
    app.mainloop()

if __name__=='__main__':
    start_app()
