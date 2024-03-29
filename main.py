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
import os
import pyzbar.pyzbar as pyzbar
import multiprocessing
import subprocess
from io import BytesIO

LOCKER_CONFIG_FILE = "lockerConfig"
API_BASE_URL = "http://shgreenpool.com/Delivery-Locker-Server/"
LOCKER_CONFIG_API = "locker.php"
AD_CONFIG_API = "ad.php"
PACKAGE_STORE_API = "package.php"
OPEN_LOCKER_API = "openLockerRequest.php"

LOCK_GPIO_CHIP = "pinctrl-bcm2835"
LOCK_GPIO_PIN = 4
LOCK_OPEN_SECS = 2

class Lock():
    def open(self):
        # Set GPIO to on for a few secs. 
        cmd = "gpioset --mode=time --sec=" + str(LOCK_OPEN_SECS) + " " + LOCK_GPIO_CHIP + " " + str(LOCK_GPIO_PIN) + "=1"
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)

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

        self.lock = Lock()

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
        self.update()

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
        self.wifiAlertLabelStr.set("正在搜索附近WiFi。。。")
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
        self.wifiAlertLabelStr.set("WiFi正在连接")
        self.controller.update()
        ssid = self.wifiList.get(self.wifiList.curselection()[0])
        passwd = self.wifiPasswdEntry.get()
        
        connectResult = False
        try:
            connectResult = Wifi.Connect(str(ssid), str(passwd))
        except:
            pass
        if connectResult is False:
            self.wifiAlertLabelStr.set("WiFi无法连接，请检查密码是否正确")
        else:
            self.wifiAlertLabelStr.set("连接成功")
            self.goToNextPage()

    def goToNextPage(self):
        self.controller.showPage("LockerConfigPage")


class LockerConfigPage(tk.Frame):
    API_URL = API_BASE_URL + LOCKER_CONFIG_API

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = tk.Label(self, text="设置设备")
        label.pack(side="top", fill="x", pady=10)

        self.alertLabelStr = tk.StringVar()
        self.alertLabel = tk.Label(self, textvariable=self.alertLabelStr)
        self.alertLabel.pack()

        self.qrImgLabel = tk.Label(self)
        self.qrImgLabel.pack()

        # The verify button is initially unclickable. 
        self.verifyButton = tk.Button(self, text="验证", state=tk.DISABLED,
                            command=lambda: self.verifyLocker())
        self.verifyButton.pack()


    def pageDidShown(self):
        self.alertLabelStr.set("正在设置设备ID")
        self.controller.update()

        # Check if lockerId has been configured. 
        self.lockerId = self.controller.getLockerConfig("lockerId")

        # If the lockerId exists and it is valid, the locker has a lockerId, which is its content. 
        if (not (self.lockerId is None)) and (self.lockerId != ""):
            self.goToNextPage()
            return
        
        # If the lockerId doesn't exist, the locker does not have a lockerId. 
        # We need to do a POST to the server to get a new lockerId. 
        lockerIdResponse = "FAILED"
        i = 0
        while lockerIdResponse == "FAILED" and i < 10: # Try 10 times. 
            self.alertLabelStr.set("正在尝试获取新的设备ID")
            self.controller.update()
            r = requests.post(url=self.API_URL, timeout=10)
            lockerIdResponse = r.text
            i += 1

        # If get new lockerId failed. 
        if lockerIdResponse == "FAILED":
            self.alertLabelStr.set("获取新的设备ID失败")
            self.controller.update()
            return
        
        # Parse JSON and get lockerId and qrUrl. 
        try:
            lockerIdJson = json.loads(lockerIdResponse)
        except:
            self.alertLabelStr.set("获取新的设备ID失败")
            self.controller.update()
            return
        self.lockerId = lockerIdJson["lockerId"]
        self.lockerName = lockerIdJson["lockerName"]
        lockerIdQrUrl = lockerIdJson["qrUrl"]

        # Load and display QR code. 
        r = requests.get(lockerIdQrUrl, timeout=30)
        imgData = BytesIO(r.content)
        imgtk = ImageTk.PhotoImage(Image.open(imgData).resize((300, 300)))
        self.qrImgLabel.imgtk = imgtk
        self.qrImgLabel.configure(image=imgtk)
        
        self.alertLabelStr.set("请打开微信扫描下方二维码以添加此设备，编号为" + self.lockerName + "。添加完毕后点击下方按钮验证。")
        # Set the verifyButton to be clickable. 
        self.verifyButton.config(state="normal")
        self.controller.update()

    def verifyLocker(self):
        self.alertLabelStr.set("正在尝试验证设备ID")
        self.controller.update()
        # User should finished adding lockerId to the user's Wechat. 
        # Verify if added accountId by a GET request to the server. 
        r = requests.get(url=self.API_URL, params={"lockerId": self.lockerId}, timeout=30)

        if r.text == "FAILED": # Have not yet added an accountId. 
            self.alertLabelStr.set("未验证成功。请打开微信扫描下方二维码以添加此设备，编号为" + self.lockerName + "。添加完毕后点击下方按钮验证。")
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

        self.loadingLabel = tk.Label(self, text="正在加载")
        self.loadingLabel.pack()

        self.adVideoButton = tk.Button(self, text="触摸屏幕以开始", compound="center", command=self.goToNextPage)
        self.adVideoButton.pack(fill=tk.BOTH, expand=1)

        self.adVideoSource = None
        self.adVideoImgs = []
        self.adVideoI = 0
        self.adVideoFPS = 100
        self.isAdVideoFromImgs = False
        

    def downloadedAd(self, filename):
        try:
            if filename != self.controller.getLockerConfig("adFileName"):
                os.remove(self.controller.getLockerConfig("adFileName"))
        except:
            pass

        # After download, load the new file. 
        self.controller.setLockerConfig({"adFileName": filename})
        self.adVideoSource = imageio.get_reader(filename)

    def setAdVideoSource(self):
        # Check if a download is required. 
        r = requests.get(url=self.API_URL, timeout=30)
        adFileName = self.controller.getLockerConfig("adFileName")
        if adFileName is None or r.text > adFileName: # The ad has been updated or has never downloaded an ad. Remove old ad. Download new ad. 
            download_file(API_BASE_URL + r.text, self.downloadedAd)
        else:
            try:
                # Open existing ad. 
                self.adVideoSource = imageio.get_reader(adFileName)
            except:
                # File corrupted, download again. 
                download_file(API_BASE_URL + r.text, self.downloadedAd)
        

    def pageDidShown(self):
        if self.adVideoSource is None:
            self.setAdVideoSource()
        self.loadingLabel.pack_forget()
        self.pageIsShown = True
        self.after(10, self.showFrame)
    
    def showFrame(self):
        if not self.pageIsShown:
            # Stop updating frames when page is not shown. 
            return
        
        if not self.isAdVideoFromImgs:
            # Ad video frames are from the imageio reader. 

            if self.adVideoSource is None:
                # Keep checking if a new ad has not yet been opened or downloaded. 
                self.after(100, self.showFrame)
                return
            
            try:
                # Get image frame from imageio reader. 
                image = Image.fromarray(self.adVideoSource.get_next_data()).resize((self.controller.winfo_screenwidth(), self.controller.winfo_screenheight()))

                imgtk = ImageTk.PhotoImage(image=image)
                self.adVideoImgs.append(imgtk)
                self.adVideoI += 1
            except:
                # Get image frame from imageio reader failed, all frames has read to adVideoImgs. 
                # From now on, read frames from adVideoImgs. 
                self.adVideoI = 0
                self.isAdVideoFromImgs = True
                self.adVideoFPS = self.adVideoSource.get_meta_data()["fps"]

        if self.isAdVideoFromImgs:
            # Ad video frames are from the images. 
            imgtk = self.adVideoImgs[self.adVideoI]
            self.adVideoI = (self.adVideoI + 1) % len(self.adVideoImgs)

        # Show frame. 
        self.adVideoButton.imgtk = imgtk
        self.adVideoButton.configure(image=imgtk)
        # Schedule next frame. 
        self.after(int(1000 / self.adVideoFPS), self.showFrame)

    def goToNextPage(self):
        self.pageIsShown = False
        self.controller.showPage("LockerPage")


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
        
        self.adButton = tk.Button(self, text="取消", command=self.goToAdPage)
        self.adButton.pack()

        self.trackingNumImg = tk.Label(self)
        self.trackingNumImg.pack()

        self.trackingAlertStr = tk.Variable()
        self.trackingAlertStr.set("请扫描或手动输入快递跟踪码：")
        self.trackingAlertLabel = tk.Label(self, textvariable=self.trackingAlertStr)
        self.trackingAlertLabel.pack()

        self.trackingNumEntry = tk.Entry(self)
        self.trackingNumEntry.pack(pady=10)
        
        self.confirmTrackingNumButton = tk.Button(self, text="确认", command=self.sendTrackingNumber)
        self.confirmTrackingNumButton.pack()

        self.kb = vKeyboard(parent=self, attach=self.trackingNumEntry)
        self.kb.listenForEntry(self.trackingNumEntry)

        self.camera = imageio.get_reader("<video0>", size="1280x720", pixelformat="yuyv422")
        cmd = "v4l2-ctl -c focus_auto=0,focus_absolute=200"
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        _, _ = p.communicate()

    def pageDidShown(self):
        self.pageIsShown = True
        self.trackingNumEntry.delete(0, tk.END)
        self.isProcessing = False
        self.trackingAlertStr.set("请扫描或手动输入快递跟踪码：")
        self.after(100, self.cameraFindZBar)

    def cameraFindZBar(self):
        if not self.pageIsShown:
            return

        image = Image.fromarray(self.camera.get_next_data()).convert("L")
        imgtk = ImageTk.PhotoImage(image=image.resize((320, 200)))
        self.trackingNumImg.imgtk = imgtk
        self.trackingNumImg.configure(image=imgtk)

        decodedObjects = pyzbar.decode(image)

        if (len(decodedObjects) > 0):
            self.trackingNum = decodedObjects[0].data.decode("utf-8")

            if (self.trackingNum[:10] == "OPENLOCKER"):
                self.openLocker(self.trackingNum)
            else:
                # self.after(1, lambda: self.sendTrackingNumber(self.trackingNum))
                self.sendTrackingNumber(self.trackingNum)

        self.after(100, self.cameraFindZBar)

    def openLocker(self, passwd):
        if (self.isProcessing):
            return
            
        self.trackingAlertStr.set("正在处理开箱请求。。。")
        self.controller.update()
        
        self.isProcessing = True

        r = requests.put(
            url=API_BASE_URL + OPEN_LOCKER_API, 
            data={
                "lockerId": self.controller.getLockerConfig("lockerId"), 
                "passwd": passwd
            }, 
            timeout=30
        )
        if (r.text == "SUCCESS"):
            self.trackingAlertStr.set("开箱成功。")
            self.controller.update()
            self.controller.lock.open()
            self.after(5000, self.goToAdPage)
        else:
            self.trackingAlertStr.set("不正确，请重试。")
            self.controller.update()
            self.isProcessing = False

    def sendTrackingNumber(self, trackingNum):
        if (self.isProcessing):
            return
            
        self.trackingNumEntry.delete(0, tk.END)
        self.trackingNumEntry.insert(0, self.trackingNum)
        self.trackingAlertStr.set("正在处理。。。")
        self.controller.update()
        
        self.isProcessing = True
        r = requests.post(
            url=API_BASE_URL + PACKAGE_STORE_API, 
            data={
                "packageId": trackingNum, 
                "lockerId": self.controller.getLockerConfig("lockerId")
            }, 
            timeout=30
        )
        if (r.text != "FAILED"):
            packageInfo = json.loads(r.text)
            self.trackingAlertStr.set("请将快递放入箱子中，谢谢。")
            self.controller.update()
            self.controller.lock.open()
            self.after(5000, self.goToAdPage)
            # self.goToNextPage()
        else:
            self.trackingAlertStr.set("无法识别此快递码")
            self.controller.update()
            self.isProcessing = False

    def goToNextPage(self):
        self.pageIsShown = False
        self.controller.showPage("OpenLockerForDeliveryPage")

    def goToAdPage(self):
        self.pageIsShown = False
        self.controller.showPage("AdPage")



if __name__ == "__main__":
    app = Application()
    app.mainloop()