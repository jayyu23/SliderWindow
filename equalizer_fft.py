"""
Equalizer Class: FFT Transform + Audio Parsing Included
"""

# UI and IO
import tkinter as tk
from tkinter.filedialog import asksaveasfilename, askopenfilename
import json

# Data-Analysis
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.interpolate import interp1d
from scipy.io import savemat, wavfile

# Graphing
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure



class TkWindow(tk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master.geometry('700x600')
        self.master.title('深聪EQ')
        self.options = {'padx': 5, 'pady': 5}
        self.x_range = [2**i for i in range(6, 14)]  # Start at 32Hz (2^5), end at 8kHz (2^14)
        self.y_range = [-17, 3]
        self.x_display_labels = [f"{s} Hz" if s < 1000 else f"{s/1000:.0f} kHz" for s in self.x_range]

        # Color Scheme
        self.background = '#212529'
        self.foreground = '#f0f6f6'
        self.grid_color = '#212529'
        self.graph_bg = '#000000'
        self.line_color = "#59A5D8"
        self.points_color = '#386FA4'

        # Re-sampling related
        self.x_old = np.array([])  # Input from the EQ UI. Numpy array
        self.y_old = np.array([])  # Input from the EQ UI. Numpy array
        self.x_new = np.array([])  # Re-sampled x-values
        self.y_new = np.array([])  # Re-sampled y-values
        self.point_sample_size = 256  # No. of points to be sampled

        # Audio input
        self.audio_file = 'audio_files/1001552.kai1-ji1.wav'  # Default audio
        self.SAMPLE_RATE = int()

        # Title
        self.master['bg'] = self.background
        self.header_title = tk.Label(self.master, text="深聪智能均衡器", font=("Times New Roman", 36), bg=self.background,
                                     fg=self.foreground, pady=10)
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

        # Loop to create the Slider UI objects
        for s, slider_name in enumerate(self.x_range):
            slider_frame = tk.Frame(self.slider_pane, bg=self.background)
            slider_name_display = self.x_display_labels[s]
            slider_var = tk.IntVar()
            self.slider_data[slider_name] = slider_var
            name_label = tk.Label(slider_frame, text=slider_name_display, bg=self.background, fg=self.foreground)
            slider = tk.Scale(slider_frame, variable=slider_var,
                              from_=self.y_range[1], to=self.y_range[0], orient=tk.VERTICAL, bg=self.background,
                              fg=self.foreground)
            self.slider_obj[slider_name] = slider

            name_label.pack(**self.options)
            slider.pack(**self.options)
            slider_frame.pack(side=tk.LEFT, expand=True, **self.options)

        # Row 2: Select Audio Button, Update Button, Export Button
        self.button_pane = tk.Frame(self.master, bg=self.background)
        self.select_audio_button = tk.Button(self.button_pane, text=u"选择音频", padx=30,
                                             command=self.select_audio_button_action,
                                             bg=self.background, fg=self.foreground)
        self.select_audio_button.pack(side=tk.LEFT)
        self.update_button = tk.Button(self.button_pane, text=u"更新", padx=30,
                                       command=self.update_button_action, bg=self.background, fg=self.foreground)
        self.update_button.pack(side=tk.LEFT)
        self.export_button = tk.Button(self.button_pane, text=u"导出", padx=30,
                                       command=self.export_button_action, bg=self.background, fg=self.foreground)
        self.export_button.pack(side=tk.LEFT)
        self.button_pane.pack()

    def select_audio_button_action(self):
        """
        Called when '选择音频' (Select Audio) button clicked. Select the desired .wav audio from a Dialog Box
        :return: None
        """
        file_path = askopenfilename(filetypes=[('.wav Audio Files', '*.wav')])
        if file_path:
            self.audio_file = file_path

    def update_button_action(self):
        """
        Called when the '更新' (Update) button is clicked
        Will set the input arrays from the values in the UI, then draw the appropriate curve and display
        :return: None
        """
        slider_val_dict = {k: v.get() for k, v in self.slider_data.items()}
        self.__set_input_arrays(list(slider_val_dict.keys()), list(slider_val_dict.values()))
        self.__clear_plot()
        self.fit_curve()
        self.fig_canvas.draw()

    def export_button_action(self):
        """
        Called when '导出' (Export) button is clicked. Will first open a file-save dialog,
        then export to the selected location
        :return: None
        """
        filename = asksaveasfilename()
        self.export(filename)

    def __set_input_arrays(self, x_arr, y_arr):
        """
        Update the values of the input arrays from a given x_array and a given y_array
        :param x_arr: x_array values (Python list)
        :param y_arr: y_array values (Python list)
        :return: None. Updates x_old and y_old.
        """
        self.x_old = np.array(x_arr)
        self.y_old = np.array(y_arr)

    def fit_curve(self, kind='quadratic'):
        """
        Fits the curve given by a x_old and y_old onto the audio, using the scipy.interpolate.interp1d package
        :param kind: Type of curve to be fit in. See scipy documentation
        :return: None. Updates x_new and y_new.
        """
        # Get the audio and apply rFFT to get the 256 points (for x and y)
        self.SAMPLE_RATE, signal = wavfile.read(self.audio_file)
        y_fft = rfft(signal, self.point_sample_size)
        x_fft = rfftfreq(self.point_sample_size, 1 / self.SAMPLE_RATE)
        # Create our interpolation curve (spline_f)
        spline_f = interp1d(self.x_old, self.y_old, kind=kind, fill_value="extrapolate")
        self.x_new = x_fft  # Our new points are given by the FFT x-values (as opposed to doing a np.linspace)
        y_filter = spline_f(self.x_new)  # We graph out the interpolation filter only. Do not graph original wave
        self.y_new = y_filter + y_fft  # But the output is the original y_fft + the interpolation filter
        # + 0.001 So that can log2 does not have log(0) error
        self.plt.plot(np.log2(self.x_old + 0.001), self.y_old, 'o', color=self.points_color)
        self.plt.plot(np.log2(self.x_new + 0.001), y_filter, '-', color=self.line_color)

    def __clear_plot(self):
        """
        Clear the current matplotlib plot. Called every time the graph UI is updated. Makes sure the UI has the
        correct color scheme etc.
        :return: None
        """
        self.fig.clear()
        self.plt = self.fig.add_subplot(1, 1, 1)
        self.plt.set_xlim(np.log2(min(self.x_range)) - 1, np.log2(max(self.x_range)) + 1)
        self.plt.set_ylim(self.y_range[0] - 1, self.y_range[1] + 1)
        self.plt.set_xlabel("Frequency Hz (log2)")
        self.plt.set_title("Amplitude dB vs. Log2 Hertz", color=self.foreground)
        self.fig.set_facecolor(self.background)
        self.plt.set_facecolor(self.graph_bg)

        self.plt.grid(c=self.grid_color)
        self.plt.tick_params(axis='both', colors=self.foreground)
        self.plt.spines['left'].set_color(self.foreground)
        self.plt.spines['top'].set_color(self.foreground)
        self.plt.spines['bottom'].set_color(self.foreground)
        self.plt.spines['right'].set_color(self.foreground)

    def export(self, export_path):
        """
        Exports the re-sampled 256 points to the location indicated in export_path.
        Supports 3 file-extensions: MAT, JSON, CSV
        :param export_path: Export path of the file (str)
        :return: None
        """
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


# Main loop to start the App
if __name__ == "__main__":
    app = tk.Tk()
    main_window = TkWindow()
    app.mainloop()