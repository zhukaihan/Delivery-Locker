# -*- coding: utf-8 -*-

# https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter

import tkinter as tk
from tkinter import font  as tkfont
import Wifi

class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.wm_attributes('-fullscreen', 'true')

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ConfigPage, AdPage, LockerPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ConfigPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class ConfigPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="设置Wifi", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        wifiList = tk.Listbox(controller, selectmode=tk.SINGLE)
        wifiList.pack()

        wifis = Wifi.Search()
        for cell in wifis:
            wifiList.insert(tk.END, cell.ssid)

        button1 = tk.Button(self, text="Go to AdPage",
                            command=lambda: controller.show_frame("AdPage"))
        button2 = tk.Button(self, text="Go to LockerPage",
                            command=lambda: controller.show_frame("LockerPage"))
        button1.pack()
        button2.pack()


class AdPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="广告", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Click to open locker",
                           command=lambda: controller.show_frame("LockerPage"))
        button.pack()


class LockerPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="放东西", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Play Ad after 30 secs",
                           command=lambda: controller.show_frame("AdPage"))
        button.pack()


if __name__ == "__main__":
    app = Application()
    app.mainloop()