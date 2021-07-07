import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy.interpolate import interp1d
from scipy.io import savemat, loadmat
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import json
from tkinter.filedialog import asksaveasfilename

class TkWindow(tk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master.geometry('700x600')
        self.master.title('深聪EQ')
        self.options = {'padx': 5, 'pady': 5}
        self.x_range = [2**i for i in range(5, 15)]  # Start at 16Hz (2^5), end at 16kHz (2^14)
        self.y_range = [-17, 3]
        self.x_display_labels = [f"{s} Hz" if s < 1000 else f"{s/1000:.0f} kHz" for s in self.x_range]

        # Color Scheme
        self.background = '#212529'#"#343a40"
        self.foreground = '#f0f6f6'
        self.grid_color = '#212529'
        self.graph_bg = '#000000' # "#403c42" # '#706c89'
        self.line_color = "#59A5D8"
        self.points_color = '#386FA4'

        # Converter related
        self.x_vars = None
        self.y_vars = None
        self.curve = None
        self.sample_size = 256

        self.x_new = None
        self.y_new = None

        # Title
        self.master['bg'] = self.background
        self.header_title = tk.Label(self.master, text="深聪智能均衡器", font=("Times New Roman", 36), bg=self.background, fg=self.foreground, pady=10)
        self.header_title.pack(side=tk.TOP)

        # Row 0: Init the Matplotlib
        matplotlib.use('TkAgg')
        self.fig = Figure((6.5, 2.5))
        self.fig_canvas = FigureCanvasTkAgg(self.fig, self.master)
        self.fig_canvas.get_tk_widget().pack()
        self.plt = None
        self.__clear_plot()

        # Row 1: Slider Pane
        self.slider_pane = tk.Frame(self.master, pady=30, bg=self.background)
        self.slider_pane.config()
        self.slider_pane.pack()
        self.slider_obj = {}
        self.slider_data = {}

        style = ttk.Style()
        style.configure('TSlider', background=self.background, foreground=self.foreground)
        for s, slider_name in enumerate(self.x_range):
            slider_frame = tk.Frame(self.slider_pane, bg=self.background)
            slider_name_display = self.x_display_labels[s]
            slider_var = tk.IntVar()
            self.slider_data[slider_name] = slider_var
            name_label = tk.Label(slider_frame, text=slider_name_display, bg=self.background, fg=self.foreground)
            slider = tk.Scale(slider_frame, variable=slider_var,
                              from_=self.y_range[1], to=self.y_range[0], orient=tk.VERTICAL, bg=self.background, fg=self.foreground)
            self.slider_obj[slider_name] = slider

            name_label.pack(**self.options)
            slider.pack(**self.options)
            slider_frame.pack(side=tk.LEFT, expand=True, **self.options)
        # Row 1: Edit pane
        self.edit_pane = tk.Frame(self.master, **self.options)
        self.edit_label = tk.Label(self.edit_pane, text="Edit")
        self.edit_choice = tk.StringVar()
        self.choice_box = ttk.Combobox(self.edit_pane, value=tuple(self.x_display_labels),
                                       textvariable=self.edit_choice, state="readonly")
        self.choice_box.current(0)
        self.slide_spinner = tk.Spinbox(self.edit_pane, from_=self.y_range[0], to=self.y_range[1], width=10)
        self.slide_spinner.delete(0, "end")
        self.slide_spinner.insert(0, 0)
        self.update_button = tk.Button(self.edit_pane, text="Update", command=
                            lambda: self.set_slider_values(self.edit_choice.get(), self.slide_spinner.get()))
        self.edit_label.pack(side=tk.LEFT, padx=10)
        self.choice_box.pack(side=tk.LEFT, padx=10)
        self.slide_spinner.pack(side=tk.LEFT, padx=10)
        self.update_button.pack(side=tk.LEFT, padx=10)
        # self.edit_pane.pack()

        # Row 2: View button, labels display
        self.view_download_buttons = tk.Frame(self.master, bg=self.background)
        self.show_button = tk.Button(self.view_download_buttons, text=u"更新", padx=30,
                                     command=self.calculate_slider_values, bg=self.background, fg=self.foreground)
        self.show_button.pack(side=tk.LEFT)
        self.download_button = tk.Button(self.view_download_buttons, text=u"导出", padx=30,
                                     command=self.download_button_action, bg=self.background, fg=self.foreground)
        self.download_button.pack(side=tk.LEFT)
        self.view_download_buttons.pack()
        # self.show_info_label = tk.Label(self.master)
        # self.show_info_label.pack()

    def set_slider_values(self, slider_name, value):
        slider = self.slider_obj[slider_name]
        slider.set(value)

    def calculate_slider_values(self, show=False):
        slider_val_dict = {k: v.get() for k, v in self.slider_data.items()}
        if show:
            print(slider_val_dict)
            self.show_info_label['text'] = slider_val_dict
        self.__converter_set(list(slider_val_dict.keys()), list(slider_val_dict.values()))
        self.__clear_plot()
        self.fit_curve()
        self.fig_canvas.draw()
        return slider_val_dict

    def __converter_set(self, x_arr, y_arr):
        self.x_vars = np.array(x_arr)
        self.y_vars = np.array(y_arr)

    def fit_curve(self):
        # bounds = (min(self.x_vars), max(self.x_vars))
        spline_f = interp1d(self.x_vars, self.y_vars, kind='cubic')
        self.x_new = np.linspace(min(self.x_vars), max(self.x_vars), self.sample_size)
        self.y_new = spline_f(self.x_new)
        self.plt.plot(np.log2(self.x_vars), self.y_vars, 'o', color=self.points_color)
        self.plt.plot(np.log2(self.x_new), self.y_new, '-', color=self.line_color)
        self.export('export.mat')

    def __clear_plot(self):
        self.fig.clear()
        self.plt = self.fig.add_subplot(1, 1, 1)
        self.plt.set_xlim(np.log2(min(self.x_range)) - 1, np.log2(max(self.x_range)) + 1)
        self.plt.set_ylim(self.y_range[0] - 1, self.y_range[1] + 1)
        # self.plt.set_xlabel("Frequency Hz (log2)")
        self.plt.set_title("Amplitude dB vs. Log2 Hertz", color=self.foreground)
        self.fig.set_facecolor(self.background)
        self.plt.set_facecolor(self.graph_bg)
        print(dir(self.plt))
        self.plt.grid(c=self.grid_color)
        self.plt.tick_params(axis='both', colors=self.foreground)
        self.plt.spines['left'].set_color(self.foreground)
        self.plt.spines['top'].set_color(self.foreground)
        self.plt.spines['bottom'].set_color(self.foreground)
        self.plt.spines['right'].set_color(self.foreground)

    def download_button_action(self):
        filename = asksaveasfilename()
        self.export(filename)

    def export(self, export_path):
        mode = export_path.split('.')[-1]
        out_dict = {self.x_new[i]: self.y_new[i] for i in range(len(self.x_new))}
        values_np = np.array([[k, v] for k, v in out_dict.items()])
        if mode == 'mat':
            savemat(export_path, {'values': values_np})
        elif mode == "json":
            json.dump(out_dict, open(export_path, 'w'), indent=1)
        elif mode == "csv":
            with open(export_path, 'w') as file:
                for key, value in out_dict.items():
                    file.write(f"{key},{value}\n")


if __name__ == "__main__":
    app = tk.Tk()
    main_window = TkWindow()
    app.mainloop()