# -*- coding: utf-8 -*-

# https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter

import tkinter as tk
from tkinter import font as tkfont
import Wifi
from vKeyboard import vKeyboard
import requests

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
        for F in (WifiConfigPage, LockerConfigPage, AdPage, LockerPage):
            page_name = F.__name__
            page = F(parent=container, controller=self)
            self.pages[page_name] = page

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            page.grid(row=0, column=0, sticky="nsew")

        self.showPage("WifiConfigPage")

    def showPage(self, page_name):
        '''Show a frame for the given page name'''
        page = self.pages[page_name]
        page.tkraise()

        try:
            page.pageDidShown()
        except:
            pass


class WifiConfigPage(tk.Frame):

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
            self.goToNextPage()
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
                self.goToNextPage()
        except:
            self.wifiAlertLabelStr.set("WiFi无法连接，请检查密码是否正确")

    def goToNextPage(self):
        self.controller.showPage("LockerConfigPage")


class LockerConfigPage(tk.Frame):
    API_URL = "http://shgreenpool.com/Delivery-Locker-Server/locker.php"

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = tk.Label(self, text="设置设备")
        label.pack(side="top", fill="x", pady=10)

        # The verify button is initially unclickable. 
        self.verifyButton = tk.Button(self, text="验证", state=tk.DISABLED,
                            command=lambda: self.verifyLocker())
        self.verifyButton.pack()

        self.alertLabelStr = tk.StringVar()
        self.alertLabel = tk.Label(self, textvariable=self.alertLabelStr)
        self.alertLabel.pack()


    def pageDidShown(self):
        self.lockerId = None
        # Open the file "id" for lockerId. 
        try:
            with open("id","r") as idFile:
                self.lockerId = idFile.read()
        except:
            pass

        # If the file exists and its content is valid, the locker has a lockerId, which is its content. 
        if (not (self.lockerId is None)) and (self.lockerId != ""):
            self.controller.lockerId = self.lockerId
            self.goToNextPage()
            return
        
        # If the file doesn't exist, the locker does not have a lockerId. 
        # We need to do a POST to the server to get a new lockerId. 
        self.lockerId = "FAILED"
        i = 0
        while self.lockerId == "FAILED" and i < 10: # Try 10 times. 
            self.alertLabelStr.set("尝试连接中。。。")
            r = requests.post(url=self.API_URL)
            self.lockerId = r.text
            i += 1
        
        self.alertLabelStr.set("此设备ID为" + self.lockerId + "，请打开微信服务号添加此设备。添加完毕后点击下方按钮验证。")
        # Set the verifyButton to be clickable. 
        self.verifyButton.config(state="normal")

    def verifyLocker(self):
        # User should finished adding lockerId to the user's Wechat. 
        # Verify if added accountId by a GET request to the server. 
        r = requests.get(url=self.API_URL, params={"lockerId": self.lockerId})
        
        if r.text == "FAILED": # Have not yet added an accountId. 
            self.alertLabelStr.set("未验证成功。此设备ID为" + self.lockerId + "，请打开微信服务号添加此设备。添加完毕后点击下方按钮验证。")
        elif r.text == "SUCCESS": # Added an accountId. 
            self.alertLabelStr.set("验证成功。")

            # Recored the lockerId. 
            self.controller.lockerId = self.lockerId
            with open("id","w+") as idFile:
                idFile.write(self.lockerId)
            
            self.goToNextPage()
            

    def goToNextPage(self):
        self.controller.showPage("AdPage")
        

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