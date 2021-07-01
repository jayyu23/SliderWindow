import tkinter as tk
from tkinter import ttk


class TkWindow(tk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master.geometry('900x350')
        self.master.title('深聪智能')
        self.options = {'padx': 5, 'pady': 5}

        # Row 0: Title
        self.header_title = tk.Label(self.master, text="深聪智能", font=(None, 36))
        self.header_title.pack(side=tk.TOP)

        # Row 1: Slider Pane
        self.slider_pane = tk.Frame(self.master)
        self.slider_pane.config()
        self.slider_pane.pack()
        self.slider_obj = {}
        self.slider_data = {}

        for s in range(10):
            slider_frame = tk.Frame(self.slider_pane)
            slider_name, slider_var = f"Option {s + 1}", tk.IntVar()
            self.slider_data[slider_name] = slider_var
            name_label = tk.Label(slider_frame, text=slider_name)
            slider = tk.Scale(slider_frame, variable=slider_var,
                              from_=100, to=0, orient=tk.VERTICAL)
            self.slider_obj[slider_name] = slider

            name_label.pack(**self.options)
            slider.pack(**self.options)
            slider_frame.pack(side=tk.LEFT, expand=True, **self.options)
        # Row 1: Edit pane
        self.edit_pane = tk.Frame(self.master, **self.options)
        self.edit_label = tk.Label(self.edit_pane, text="Edit")
        self.edit_choice = tk.StringVar()
        self.choice_box = ttk.Combobox(self.edit_pane, value=tuple(self.slider_data.keys()),
                                       textvariable=self.edit_choice, state="readonly")
        self.choice_box.current(0)
        self.slide_spinner = tk.Spinbox(self.edit_pane, from_=0, to=100, width=10)
        self.update_button = tk.Button(self.edit_pane, text="Update", command=
                            lambda: self.set_slider_values(self.edit_choice.get(), self.slide_spinner.get()))
        self.edit_label.pack(side=tk.LEFT, padx=10)
        self.choice_box.pack(side=tk.LEFT, padx=10)
        self.slide_spinner.pack(side=tk.LEFT, padx=10)
        self.update_button.pack(side=tk.LEFT, padx=10)
        self.edit_pane.pack()

        # Row 2: Show button, labels display
        self.show_button = tk.Button(self.master, text="Submit Values", padx=20,
                                     command=self.get_slider_values)
        self.show_button.pack()
        self.show_info_label = tk.Label(self.master)
        self.show_info_label.pack()

    def set_slider_values(self, slider_name, value):
        slider = self.slider_obj[slider_name]
        slider.set(value)

    def get_slider_values(self):
        slider_val_dict = {k: v.get() for k, v in self.slider_data.items()}
        print(slider_val_dict)
        self.show_info_label['text'] = slider_val_dict
        return slider_val_dict


if __name__ == "__main__":
    app = tk.Tk()
    main_window = TkWindow()
    app.mainloop()