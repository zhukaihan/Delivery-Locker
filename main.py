# -*- coding: utf-8 -*-

# https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter

import tkinter as tk
from tkinter import font as tkfont
import Wifi
from vKeyboard import vKeyboard

class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.wm_attributes('-fullscreen', True)
        # w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        # # use the next line if you also want to get rid of the titlebar
        # self.overrideredirect(1)
        # self.geometry("%dx%d+0+0" % (w, h))

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        for F in (ConfigPage, AdPage, LockerPage):
            page_name = F.__name__
            page = F(parent=container, controller=self)
            self.pages[page_name] = page

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            page.grid(row=0, column=0, sticky="nsew")

        self.showPage("ConfigPage")

    def showPage(self, page_name):
        '''Show a frame for the given page name'''
        page = self.pages[page_name]
        page.tkraise()

        try:
            page.pageDidShown()
        except:
            pass


class ConfigPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="设置Wifi")
        label.pack(side="top", fill="x", pady=10)

        self.wifiList = tk.Listbox(self, selectmode=tk.SINGLE)
        self.wifiList.configure(exportselection=False)
        self.wifiList.pack()

        self.wifiPasswdEntry = tk.Entry(self)
        self.wifiPasswdEntry.pack()

        wifiConnectButton = tk.Button(self, text="连接Wifi",
                            command=lambda: self.connectWifi())
        wifiConnectButton.pack()

        self.wifiAlertLabelStr = tk.StringVar()
        self.wifiAlertLabel = tk.Label(self, textvariable=self.wifiAlertLabelStr)
        self.wifiAlertLabel.pack()

        
        self.kb = vKeyboard(parent=self, attach=self.wifiPasswdEntry)
        self.kb.listenForEntry(self.wifiPasswdEntry)

    def pageDidShown(self):
        wifis = Wifi.SearchAndConnectKnown()
        if wifis is True: # Wifi is successfully connected to a known network. 
            self.controller.showPage("AdPage")
        else:
            for cell in wifis:
                self.wifiList.insert(tk.END, cell.ssid)

    def connectWifi(self):
        ssid = self.wifiList.get(self.wifiList.curselection()[0])
        passwd = self.wifiPasswdEntry.get()
        
        try:
            connectResult = Wifi.Connect(str(ssid), str(passwd))
        
            if connectResult is False:
                self.wifiAlertLabelStr.set("WiFi无法连接，请检查密码是否正确")
            else:
                self.wifiAlertLabelStr.set("连接成功")
                self.controller.showPage("AdPage")
        except:
            self.wifiAlertLabelStr.set("WiFi无法连接，请检查密码是否正确")


class AdPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="广告")
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Click to open locker",
                           command=lambda: controller.showPage("LockerPage"))
        button.pack()


class LockerPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="放东西")
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Play Ad after 30 secs",
                           command=lambda: controller.showPage("AdPage"))
        button.pack()


if __name__ == "__main__":
    app = Application()
    app.mainloop()