# -*- coding: utf-8 -*-

# https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter

import tkinter as tk
from tkinter import font as tkfont
import Wifi
from vKeyboard import vKeyboard
import requests
import imageio
from PIL import ImageTk, Image
import json
import asyncio

LOCKER_CONFIG_FILE = "lockerConfig"
API_BASE_URL = "http://shgreenpool.com/Delivery-Locker-Server/"
LOCKER_CONFIG_API = "locker.php"
AD_CONFIG_API = "ad.php"

class Application(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.lockerConfig = {}
        try:
            with open(LOCKER_CONFIG_FILE,"r") as f:
                lockerConfigFileContent = f.read()
                if (lockerConfigFileContent != ""):
                    self.lockerConfig = json.loads(lockerConfigFileContent)
        except:
            pass

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

        self.showPage("AdPage")

    def showPage(self, page_name):
        '''Show a frame for the given page name'''
        page = self.pages[page_name]
        page.tkraise()

        try:
            page.pageDidShown()
        except:
            pass

    def setLockerConfig(self, params):
        for key in params:
            self.lockerConfig[key] = params[key]
        lockerConfigString = json.dumps(self.lockerConfig)
        with open(LOCKER_CONFIG_FILE,"w+") as f:
            f.write(lockerConfigString)
    
    def getLockerConfig(self, key):
        try:
            value = self.lockerConfig[key]
            return value
        except:
            return None



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
    API_URL = API_BASE_URL + LOCKER_CONFIG_API

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
        # Check if lockerId has been configured. 
        self.lockerId = self.controller.getLockerConfig("lockerId")

        # If the lockerId exists and it is valid, the locker has a lockerId, which is its content. 
        if (not (self.lockerId is None)) and (self.lockerId != ""):
            self.goToNextPage()
            return
        
        # If the lockerId doesn't exist, the locker does not have a lockerId. 
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
            self.controller.setLockerConfig({"lockerId": self.lockerId})
            
            self.goToNextPage()
            

    def goToNextPage(self):
        self.controller.showPage("AdPage")
        

class AdPage(tk.Frame):
    API_URL = API_BASE_URL + AD_CONFIG_API

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.adVideolabel = tk.Label(self, text="广告")
        self.adVideolabel.pack(side=tk.TOP, fill=tk.BOTH)

        button = tk.Button(self, text="Click to open locker",
                           command=lambda: controller.showPage("LockerPage"))
        button.pack(side=tk.BOTTOM, fill=tk.X)

        adFileName = self.controller.getLockerConfig("adFileName")
        
        r = requests.get(url=self.API_URL)
        if adFileName is None or r.text > adFileName: # The ad has been updated. Download new ad. 
            download_file(
                API_BASE_URL + r.text, 
                callback=(lambda filename: self.controller.setLockerConfig({"adFileName": filename}))
            )
        
        self.adVideoSource = None
        self.adVideoImgs = []
        self.adVideoI = 0
        self.isAdVideoFromImgs = False

    def pageDidShown(self):
        self.after(10, self.showFrame)
    
    def showFrame(self):
        if not self.isAdVideoFromImgs:
            if self.adVideoSource is None:
                if self.controller.getLockerConfig("adFileName") is None:
                    self.after(100, self.showFrame)
                    return
                adFileName = "/home/alarm/" + self.controller.getLockerConfig("adFileName")
                self.adVideoSource = imageio.get_reader(adFileName)
            
            try:
                image = self.adVideoSource.get_next_data()

                imgtk = ImageTk.PhotoImage(image=Image.fromarray(image))
                self.adVideoImgs.append(imgtk)
                self.adVideoI += 1
            except:
                self.adVideoI = 0
                self.isAdVideoFromImgs = True

        if self.isAdVideoFromImgs:
            imgtk = self.adVideoImgs[self.adVideoI]
            self.adVideoI = (self.adVideoI + 1) % len(self.adVideoImgs)

        self.adVideolabel.imgtk = imgtk
        self.adVideolabel.configure(image=imgtk)
        self.after(10, self.showFrame)


async def async_download_file(url, callback=None):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
    try:
        if not (callback is None):
            callback(local_filename)
    except:
        pass
    return local_filename

def download_file(url, callback=None):
    asyncio.run(async_download_file(url, callback))


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