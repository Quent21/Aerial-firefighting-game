from tkinter import *
from PIL import Image, ImageTk
from random import randint

BLOCK = 80
COLS = 20
ROWS = 10
HEADER = BLOCK

SPEED_PLANE = 1
SPEED_DROP = 1
DELAY_GAME = 10
DELAY_STOCK = 2
DELAY_FIRE = 30
DELAY_FRAME = 50

MAXI_STOCK = 20
MIN_INITIAL_FIRE = 3
MAX_INITIAL_FIRE = 5
FRAMES_FIRE = 2

KEY_DROP = "<space>"
KEY_BIG_DROP = "l"
KEY_MANY_DROP = "m"

IMG_PLANE = "salameche.png"
IMG_DROP = "tiplouf.png"
IMG_BIG_DROP = "pikachu.png"

WIDTH = COLS * BLOCK
HEIGHT = ROWS * BLOCK

class Game:
    def __init__(self, win):
        self.win = win
        self.win.geometry(str(self.win.winfo_screenwidth()) + "x" + str(self.win.winfo_screenheight()))
        self.can = Canvas(self.win, width = WIDTH, height = HEIGHT + HEADER)
        self.can.pack()

        self.stock = Stock(self.can)
        self.plane = Plane(self.can)
        self.drops = [[] for i in range(COLS)]
        self.fire = [Fire(self.can, i, randint(MIN_INITIAL_FIRE, MAX_INITIAL_FIRE)) for i in range(COLS)]

        self.dropUsed = False
        self.nextGrow = 0
        self.firesLeft = COLS
        self.nextClock = None

        self.win.bind(KEY_DROP, self.drop)
        self.win.bind(KEY_BIG_DROP, self.bigDrop)
        self.win.bind(KEY_MANY_DROP, self.manyDrop)

        self.tick = 0
        self.clock()

    def useDrop(self, quantity = 1):
        if not self.dropUsed and self.stock.use(quantity):
            self.dropUsed = True
            return True
        else:
            return False

    def newDrop(self, x = 0, y = 0, big = False):
        if 0 <= self.plane.x + x < COLS:
            if big:
                drop = BigDrop(self.can, self.plane.x + x, self.plane.y + y)
            else:
                drop = Drop(self.can, self.plane.x + x, self.plane.y + y)
            self.drops[self.plane.x + x].append(drop)

    def drop(self, event):
        if self.useDrop():
            self.newDrop()

    def bigDrop(self, event):
        if self.useDrop(3):
            self.newDrop(big = True)

    def manyDrop(self, event):
        if self.useDrop(3):
            self.newDrop(-1)
            self.newDrop()
            self.newDrop(1)

    def growFire(self):
        for i in self.fire:
            i.grow()

    def clock(self):
        self.nextClock = self.win.after(DELAY_FRAME, self.clock)
        self.tick += 1
        frame = self.tick % DELAY_GAME
        if frame == 0:
            self.stock.update()
            self.plane.update()
            if self.fire[self.plane.x].height >= ROWS - self.plane.y:
                self.end(False)
            for i, l in enumerate(self.drops):
                newL = []
                for j in l:
                    j.update()
                    if self.fire[i].height >= ROWS - j.y:
                        res = self.fire[i].reduce(j)
                        if res:
                            self.firesLeft -= 1
                            if self.firesLeft == 0:
                                self.end(True)
                    elif j.y < ROWS - 1:
                        newL.append(j)
                self.drops[i] = newL
            self.dropUsed = False
            if self.nextGrow + 1 < DELAY_FIRE:
                self.nextGrow += 1
            else:
                self.nextGrow = 0
                self.growFire()
        self.show(frame)

    def show(self, frame):
        self.stock.show(frame)
        self.plane.show(frame)
        for i in self.drops:
            for j in i:
                j.show(frame)
        for i in self.fire:
            i.show(frame)

    def end(self, win):
        self.win.after_cancel(self.nextClock)
        self.win.unbind(KEY_DROP)
        self.win.unbind(KEY_BIG_DROP)
        self.win.unbind(KEY_MANY_DROP)
        # self.can.delete(ALL)
        if win:
            text = "Gagné !"
        else:
            text = "Perdu !"
        self.can.create_text(WIDTH // 2, HEIGHT // 2, text = text, font = ("Caladea", 50, "bold underline"))

    def mainloop(self):
        self.win.mainloop()

class Plane:
    def __init__(self, can):
        self.can = can
        self.x = 0
        self.y = 0
        self.vx = 1
        self.image = ImageTk.PhotoImage(Image.open(IMG_PLANE).resize((BLOCK, BLOCK), Image.LANCZOS))
        self.img = self.can.create_image(0, 0, image = self.image, anchor = "nw")

    def update(self):
        self.x += self.vx
        if self.x <= 0:
            self.vx = 1
        elif self.x >= COLS - 1:
            self.vx = -1

    def show(self, frame):
        self.can.coords(self.img, (self.x + frame * self.vx / DELAY_GAME) * BLOCK, self.y + HEADER)

class Drop:
    imageName = IMG_DROP
    power = 1

    def __init__(self, can, x, y):
        self.can = can
        self.x = x * BLOCK
        self.y = y
        self.image = ImageTk.PhotoImage(Image.open(self.imageName).resize((BLOCK, BLOCK), Image.LANCZOS))
        x, y = self.getCoords()
        self.img = self.can.create_image(x, y, image = self.image, anchor = "nw")

    def update(self):
        self.y += SPEED_DROP

    def show(self, frame):
        x, y = self.getCoords(frame)
        self.can.coords(self.img, x, y)

    def getCoords(self, frame = 0):
        return self.x, (self.y + frame * SPEED_DROP / DELAY_GAME) * BLOCK + HEADER

class BigDrop(Drop):
    imageName = IMG_BIG_DROP
    power = 3

class Fire:
    def __init__(self, can, x, height):
        self.can = can
        self.x = x * BLOCK
        self.height = height
        if self.height == 0:
            self.img = None
        else:
            self.img = self.can.create_image(0, 0, image = fireImages[self.height - 1][0], anchor = "sw")

    def reduce(self, drop):
        if self.img is not None:
            self.height -= drop.power
            if self.height <= 0:
                self.can.delete(self.img)
                self.height = 0
                self.img = None
                return True
        return False

    def grow(self):
        if self.img is not None and self.height < ROWS:
            self.height += 1

    def show(self, frame):
        if self.img is not None:
            self.can.itemconfig(self.img, image = fireImages[self.height - 1][frame % FRAMES_FIRE])
            self.can.coords(self.img, self.x, HEIGHT + HEADER)

class Stock:
    def __init__(self, can):
        self.can = can
        self.stock = MAXI_STOCK
        self.next = 0
        self.x1 = HEADER // 4
        self.x2 = WIDTH - self.x1
        self.y1 = HEADER // 4
        self.y2 = self.y1 * 3
        self.img = self.can.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill = "blue", width = 0)
        self.can.create_rectangle(self.x1, self.y1, self.x2, self.y2)
        for i in range(MAXI_STOCK):
            x = self.x1 + (self.x2 - self.x1) * i / MAXI_STOCK
            self.can.create_line(x, self.y1, x, self.y2)

    def use(self, quantity = 1):
        if self.stock < quantity:
            return False
        else:
            self.stock -= quantity
            return True

    def update(self):
        if self.stock < MAXI_STOCK:
            if self.next + 1 < DELAY_STOCK:
                self.next += 1
            else:
                self.next = 0
                self.stock += 1

    def show(self, frame):
        if self.stock < MAXI_STOCK:
            sup = (DELAY_GAME * self.next + frame) / (DELAY_GAME * DELAY_STOCK)
        else:
            sup = 0
        x2 = self.x1 + (self.x2 - self.x1) * (self.stock + sup) / MAXI_STOCK
        self.can.coords(self.img, self.x1, self.y1, x2, self.y2)

def loadFireImages():
    fireImages = []

    for i in range(ROWS):
        l = []
        for j in ("fire1.jpeg", "fire2.jpeg"):
            l.append(ImageTk.PhotoImage(Image.open(j).resize((BLOCK, (i + 1) * BLOCK), Image.LANCZOS)))
        fireImages.append(l)

    return fireImages

win = Tk()
fireImages = loadFireImages()
game = Game(win)
game.mainloop()
