"""
vKeyboard - an on-screen keyboard optimized for small screens (e.g. PiTFT)

Copyright (C) 2016  Fantilein1990

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

created on 2016-08-03
last changed on 2016-09-07 - version 1.0

vKeyboard is based upon tkinter-keyboard by petemojeiko
(https://github.com/petemojeiko/tkinter-keyboard/blob/master/keyboard.py)
"""

import tkinter as tk
import tkinter.ttk as ttk


# -- GUI's main class -- #
class GUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.wm_attributes('-fullscreen', True)

        container = ttk.Frame(self, width=self.winfo_screenwidth(), height=self.winfo_screenheight())
        container.pack()

        frame = StartPage(parent=container, controller=self)
        frame.pack()

class StartPage(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        self.entry1 = ttk.Entry(self)
        self.entry1.pack(side="top")

        self.entry2 = ttk.Entry(self)
        self.entry2.pack(side="top")

        self.controller = controller

        self.kb = vKeyboard(parent=self, attach=self.entry1)

        self.kb.listenForEntry(self.entry1)
        self.kb.listenForEntry(self.entry2)


class vKeyboard(ttk.Frame):
    # --- A frame for the keyboard(s) itself --- #
    def __init__(self, parent, attach, keysize=4):
        ttk.Frame.__init__(self, parent, takefocus=0, width=15 * keysize, height=280)

        self.attach = attach
        self.keysize = keysize

    # --- Different sub-keyboards (e.g. alphabet, symbols..) --- #
        # --- Lowercase alphabet sub-keyboard --- #
        self.alpha_Frame = ttk.Frame(self)
        self.alpha_Frame.grid(row=0, column=0, sticky="nsew")

        self.row1_alpha = ttk.Frame(self.alpha_Frame)
        self.row2_alpha = ttk.Frame(self.alpha_Frame)
        self.row3_alpha = ttk.Frame(self.alpha_Frame)
        self.row4_alpha = ttk.Frame(self.alpha_Frame)

        self.row1_alpha.grid(row=1)
        self.row2_alpha.grid(row=2)
        self.row3_alpha.grid(row=3)
        self.row4_alpha.grid(row=4)

        # --- Uppercase alphabet sub-keyboard --- #
        self.Alpha_Frame = ttk.Frame(self)
        self.Alpha_Frame.grid(row=0, column=0, sticky="nsew")

        self.row1_Alpha = ttk.Frame(self.Alpha_Frame)
        self.row2_Alpha = ttk.Frame(self.Alpha_Frame)
        self.row3_Alpha = ttk.Frame(self.Alpha_Frame)
        self.row4_Alpha = ttk.Frame(self.Alpha_Frame)

        self.row1_Alpha.grid(row=1)
        self.row2_Alpha.grid(row=2)
        self.row3_Alpha.grid(row=3)
        self.row4_Alpha.grid(row=4)

        # --- Initialize all sub-keyboards --- #
        self.keyState = 1
        self.init_keys()

        self.alpha_Frame.tkraise()

        self.pack()

    def init_keys(self):
        self.alpha = {
            'row1': ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Bksp'],
            'row2': ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
            'row3': ['ABC', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\''],
            'row4': ['[ space ]', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'],
        }
        self.Alpha = {
            'row1': ['~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', 'Bksp'],
            'row2': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '|'],
            'row3': ['abc', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"'],
            'row4': ['[ space ]', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?'],
        }

        for i in range(1, 3):
            if i == 1:
                self.keyStyle = self.alpha
                self.row1 = self.row1_alpha
                self.row2 = self.row2_alpha
                self.row3 = self.row3_alpha
                self.row4 = self.row4_alpha
            elif i == 2:
                self.keyStyle = self.Alpha
                self.row1 = self.row1_Alpha
                self.row2 = self.row2_Alpha
                self.row3 = self.row3_Alpha
                self.row4 = self.row4_Alpha

            for row in self.keyStyle:  # iterate over dictionary of rows
                if row == 'row1':  # TO-DO: re-write this method
                    j = 1  # for readability and functionality
                    for k in self.keyStyle[row]:
                        if k == 'Bksp':
                            ttk.Button(self.row1,
                                       text=k,
                                       width=self.keysize * 2,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        else:
                            ttk.Button(self.row1,
                                       text=k,
                                       width=self.keysize,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        j += 1
                elif row == 'row2':
                    j = 1
                    for k in self.keyStyle[row]:
                        if k == 'ABC' or k == 'abc':
                            ttk.Button(self.row2,
                                       text=k,
                                       width=self.keysize,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        else:
                            ttk.Button(self.row2,
                                       text=k,
                                       width=self.keysize,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        j += 1
                elif row == 'row3':
                    j = 1
                    for k in self.keyStyle[row]:
                        if k == 'ABC' or k == 'abc':
                            ttk.Button(self.row3,
                                       text=k,
                                       width=self.keysize,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        else:
                            ttk.Button(self.row3,
                                       text=k,
                                       width=self.keysize,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        j += 1
                else:
                    j = 1
                    for k in self.keyStyle[row]:
                        if k == '[ space ]':
                            ttk.Button(self.row4,
                                       text=' Space ',
                                       width=self.keysize * 2,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        else:
                            ttk.Button(self.row4,
                                       text=k,
                                       width=self.keysize,
                                       command=lambda k=k: self._attach_key_press(k)).grid(row=0, column=j)
                        j += 1

    def _attach_key_press(self, k):
        if k == 'abc':
            self.alpha_Frame.tkraise()
        elif k == 'ABC':
            self.Alpha_Frame.tkraise()
        elif k == 'Bksp':
            self.remaining = self.attach.get()[:-1]
            self.attach.delete(0, tk.END)
            self.attach.insert(0, self.remaining)
        elif k == '[ space ]':
            self.attach.insert(tk.END, ' ')
        else:
            self.attach.insert(tk.END, k)


    def setAttach(self, e):
        self.attach = e

    
    def listenForEntry(self, entry):
        entry.bind("<FocusIn>", lambda e: self.setAttach(entry))


if __name__ == "__main__":
    app = GUI()
    app.mainloop()
