# src/gui.py — MainWindow layout modernized (Iteration 1)

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo, askquestion

class MainWindow(tk.Tk):
    def __init__(self, main_func):
        super().__init__()
        self.title('KAI — Calcium Signal Processor')
        self.geometry('400x500')

        # Global Parameters
        global_frame = ttk.LabelFrame(self, text='Global Parameters')
        global_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        labels = ['Pacing Frequency (Hz)', 'OY Transposition', 'Verbose (0/1/2)']
        self.entries = []
        for i, label_text in enumerate(labels):
            label = ttk.Label(global_frame, text=label_text)
            label.grid(row=i, column=0, sticky='w', padx=5, pady=5)
            entry = ttk.Entry(global_frame)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            self.entries.append(entry)

        global_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        self.btn_quick_start = ttk.Button(button_frame, text='Open Quick Start Guide', command=self.show_guide)
        self.btn_quick_start.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))

        self.btn_set_params = ttk.Button(button_frame, text='Set Parameters', command=self.set_parameters)
        self.btn_set_params.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))

        self.btn_load_input = ttk.Button(button_frame, text='Load Input File', state='disabled')
        self.btn_load_input.grid(row=2, column=0, sticky='ew', padx=(0, 5))

        self.btn_load_ambient = ttk.Button(button_frame, text='Load Ambient File', state='disabled')
        self.btn_load_ambient.grid(row=2, column=1, sticky='ew', padx=(5, 0))

        self.btn_output_path = ttk.Button(button_frame, text='Set Output File', state='disabled')
        self.btn_output_path.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10, 10))

        self.btn_start = ttk.Button(button_frame, text='Start Processing', state='disabled', command=main_func)
        self.btn_start.grid(row=4, column=0, sticky='ew', padx=(0, 5))

        self.btn_abort = ttk.Button(button_frame, text='Abort', state='disabled')
        self.btn_abort.grid(row=4, column=1, sticky='ew', padx=(5, 0))

        self.btn_exit = ttk.Button(button_frame, text='Exit', command=self.destroy)
        self.btn_exit.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(10, 0))

        for i in range(2):
            button_frame.columnconfigure(i, weight=1)

    def show_guide(self):
        showinfo("Quick Start", "Quick Start Guide will appear here.")

    def set_parameters(self):
        pacing_freq = self.entries[0].get()
        oy_trans = self.entries[1].get()
        verbose = self.entries[2].get()
        showinfo("Parameters", f"Pacing Frequency: {pacing_freq}\nOY Transposition: {oy_trans}\nVerbose: {verbose}")
        self.btn_load_input.config(state='normal')
        self.btn_load_ambient.config(state='normal')
        self.btn_output_path.config(state='normal')
        self.btn_start.config(state='normal')
        self.btn_abort.config(state='normal')

class FiltersUtilityWindow(tk.Toplevel):
    def __init__(self, x_data, y_data):
        super().__init__()
        self.title("Filter Selection")
        self.geometry("600x500")
        self.x, self.y = x_data, y_data

        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.tab_gauss = self.create_gaussian_tab(notebook)
        self.tab_lowpass = self.create_lowpass_tab(notebook)
        self.tab_savgol = self.create_savgol_tab(notebook)

        notebook.add(self.tab_gauss, text="Gaussian")
        notebook.add(self.tab_lowpass, text="Lowpass")
        notebook.add(self.tab_savgol, text="Savgol")

        self.btn_apply = ttk.Button(self, text="Apply Filter", command=self.apply_filter)
        self.btn_apply.pack(pady=10)

    def create_gaussian_tab(self, notebook):
        frame = ttk.Frame(notebook)
        ttk.Label(frame, text="Sigma:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.gauss_sigma = ttk.Scale(frame, from_=1, to=20, orient='horizontal')
        self.gauss_sigma.set(6)
        self.gauss_sigma.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Truncate:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.gauss_truncate = ttk.Scale(frame, from_=1, to=10, orient='horizontal')
        self.gauss_truncate.set(4)
        self.gauss_truncate.grid(row=1, column=1, sticky='ew', padx=5)

        frame.columnconfigure(1, weight=1)
        return frame

    def create_lowpass_tab(self, notebook):
        frame = ttk.Frame(notebook)
        ttk.Label(frame, text="Cutoff Frequency:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.lowpass_cutoff = ttk.Scale(frame, from_=10, to=500, orient='horizontal')
        self.lowpass_cutoff.set(75)
        self.lowpass_cutoff.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Sample Rate:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.lowpass_samplerate = ttk.Scale(frame, from_=1000, to=10000, orient='horizontal')
        self.lowpass_samplerate.set(2000)
        self.lowpass_samplerate.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Poles:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.lowpass_poles = ttk.Scale(frame, from_=1, to=10, orient='horizontal')
        self.lowpass_poles.set(2)
        self.lowpass_poles.grid(row=2, column=1, sticky='ew', padx=5)

        frame.columnconfigure(1, weight=1)
        return frame

    def create_savgol_tab(self, notebook):
        frame = ttk.Frame(notebook)
        ttk.Label(frame, text="Window Length:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.savgol_window = ttk.Scale(frame, from_=5, to=101, orient='horizontal')
        self.savgol_window.set(41)
        self.savgol_window.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Polynomial Order:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.savgol_poly = ttk.Scale(frame, from_=1, to=5, orient='horizontal')
        self.savgol_poly.set(2)
        self.savgol_poly.grid(row=1, column=1, sticky='ew', padx=5)

        frame.columnconfigure(1, weight=1)
        return frame

    def apply_filter(self):
        # Example: capture Gaussian filter settings
        sigma = self.gauss_sigma.get()
        truncate = self.gauss_truncate.get()

        # You could add logic here to apply the filter and preview the result
        # e.g., call use_gaussian_filter1d(self.y, sigma, truncate) if this filter is selected

        summary = f"Applying Gaussian filter with:\n\
        - Sigma: {sigma:.2f}\n\
        - Truncate: {truncate:.2f}"
        showinfo("Selected Filter", summary)

class PeriodsWindow(tk.Toplevel):
    def __init__(self, peaks_min):
        super().__init__()
        self.title('Select Periods to Remove')
        self.geometry('400x600')

        self.peaks_min = peaks_min
        self.num_periods = len(peaks_min) - 1
        self.check_vars = []

        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        label = ttk.Label(frame, text="Check the periods you want to remove:", font=('Segoe UI', 10))
        label.pack(pady=(0, 10))

        checkbox_frame = ttk.Frame(frame)
        checkbox_frame.pack(fill='both', expand=True)

        for i in range(self.num_periods):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(checkbox_frame, text=f"Period {i+1}", variable=var)
            chk.grid(row=i//3, column=i%3, sticky='w', padx=5, pady=2)
            self.check_vars.append(var)

        action_frame = ttk.Frame(frame)
        action_frame.pack(fill='x', pady=15)

        self.btn_confirm = ttk.Button(action_frame, text="Confirm Selection", command=self.confirm_selection)
        self.btn_confirm.pack(fill='x', pady=5)

        self.btn_exit = ttk.Button(action_frame, text="Exit (Back to Main Program)", command=self.confirm_exit)
        self.btn_exit.pack(fill='x', pady=5)
        self.btn_exit.state(['disabled'])

        self.periods_to_delete = []

    def confirm_selection(self):
        self.periods_to_delete = [i+1 for i, var in enumerate(self.check_vars) if var.get()]
        msg = "No periods selected for removal." if not self.periods_to_delete else \
              f"You selected to remove: {', '.join(f'Period {p}' for p in self.periods_to_delete)}"
        showinfo("Selection Confirmed", msg)
        self.btn_exit.state(['!disabled'])

    def confirm_exit(self):
        if askquestion("Confirm Exit", "Did you close all plot windows?") == 'yes':
            self.destroy()

    def setPeriodsToDelete(self):
        return self.periods_to_delete        