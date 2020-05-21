import tkinter as tk
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


        frame_main = tk.Frame(window, bg="white")
        frame_main.grid(sticky='news')

        title_lbl = Label(frame_main,
                    text="Canvas Scraper",
                    font=("Arial Bold", 50))
        title_lbl.grid(column=0, row=0, columnspan=5)



        self.CWD = path.dirname(__file__)
        
        output_prompt_lbl = Label(frame_main,
                                  text="Output folder:",
                                  font=("Arial Bold",))
        output_prompt_lbl.grid(column=0, row=1)

        self.output_location_lbl = Label(frame_main,
                                         text=self.CWD,
                                         font=("Arial",))
        self.output_location_lbl.grid(column=1, row=1, columnspan=3)

        btn = Button(frame_main, text="Change", command=self.change_dir)
        btn.grid(column=4, row=1)


        optimize_storage_lbl = Label(frame_main,
                               text="Optimize Storage:",
                               font=("Arial Bold",))
        optimize_storage_lbl.grid(column=0, row=2)
        

        self.OptimizeSpace = BooleanVar(None, False)
        opTrue = Radiobutton(frame_main, text = "Yes", variable = self.OptimizeSpace, value = True)
        opFalse = Radiobutton(frame_main, text = "No", variable = self.OptimizeSpace, value = False)
        opTrue.grid(column=1, row=2)
        opFalse.grid(column=2, row=2)

        # Create a frame for the canvas with non-zero row&column weights
        frame_canvas = tk.Frame(frame_main)
        frame_canvas.grid(row=3, column=0, columnspan=5, pady=(5, 0), sticky='nw')
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)
        # Set grid_propagate to False to allow 5-by-5 buttons resizing later
        frame_canvas.grid_propagate(False)

        # Add a canvas in that frame
        canvas = tk.Canvas(frame_canvas, bg="lightgray")
        canvas.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame to contain the buttons
        frame_scrollable = tk.Frame(canvas, bg="lightgray")
        canvas.create_window((0, 0), window=frame_scrollable, anchor='nw')

        scrollable_lbl = Label(frame_scrollable,
                                  text="ASDF",
                                  font=("Arial Bold", 100))
        scrollable_lbl.grid(column=0, row=0)

        bar = Progressbar(frame_scrollable, length=200)#, style='black.Horizontal.TProgressbar')
        bar['value'] = 70
        bar.grid(column=0, row=1)
        
        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        frame_scrollable.update_idletasks()

        # Resize the canvas frame to show exactly 5-by-5 buttons and the scrollbar
        frame_canvas.config(width=window.winfo_width(), height=50)

        # Set the canvas scrolling region
        canvas.config(scrollregion=canvas.bbox("all"))
        


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
