from tkinter import *
from tkinter import ttk, filedialog, Menu, messagebox
from tkinter.ttk import Progressbar
from os import path


class GUI(object):
    def __init__(self):     
        self.window = window = Tk()
        window.geometry('600x700')
        window.title("Canvas Scraper v1.0")

        menu = Menu(window)
        about_item = Menu(menu)
        about_item.add_command(label='About', command=self.show_about)
        menu.add_cascade(label='Help', menu=about_item)
        window.config(menu=menu)

        title_lbl = Label(window,
                    text="Canvas Scraper",
                    font=("Arial Bold", 50))
        title_lbl.grid(column=0, row=0, columnspan=5)



        self.CWD = path.dirname(__file__)
        
        output_prompt_lbl = Label(window,
                                  text="Output folder:",
                                  font=("Arial Bold",))
        output_prompt_lbl.grid(column=0, row=1)

        self.output_location_lbl = Label(window,
                                         text=self.CWD,
                                         font=("Arial",))
        self.output_location_lbl.grid(column=1, row=1, columnspan=3)

        btn = Button(window, text="Change", command=self.change_dir)
        btn.grid(column=4, row=1)


        optimize_storage_lbl = Label(window,
                               text="Optimize Storage:",
                               font=("Arial Bold",))
        optimize_storage_lbl.grid(column=0, row=2)
        

        self.OptimizeSpace = BooleanVar(None, True)
        opTrue = Radiobutton(window, text = "Yes", variable = self.OptimizeSpace, value = True)
        opFalse = Radiobutton(window, text = "No", variable = self.OptimizeSpace, value = False)
        opTrue.grid(column=1, row=2)
        opFalse.grid(column=2, row=2)

        style = ttk.Style()
        style.theme_use('default')
        style.configure("black.Horizontal.TProgressbar", background='blue')
        bar = Progressbar(window, length=200, style='black.Horizontal.TProgressbar')
        bar['value'] = 70
        bar.grid(column=0, row=3, columnspan=4)

        #window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(4, weight=1)

    def mainloop(self):
        self.window.mainloop()

    def change_dir(self):
        q = filedialog.askdirectory(initialdir= self.CWD)
        if q:
            self.CWD = q
            self.output_location_lbl.configure(text=self.CWD)

    def show_about(self):
        messagebox.showinfo('About',
                            "\n".join(['Canvas Scraper v1.0',
                                       'Questions? Contact:',
                                       'AdamAlonIL@gmail.com',
                                       'This program is in beta. Use at your own risk.',
                                       'All rights reserved.']))

        
def clicked():
    lbl.configure(text="Button was clicked !!")

def query_dir():
    return filedialog.askdirectory(initialdir= CWD)

if __name__ == "__main__":
    g = GUI()
    g.mainloop()
