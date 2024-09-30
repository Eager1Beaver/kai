import tkinter as tk
from tkinter.messagebox import showinfo, askquestion, WARNING
from tkinter import filedialog
import tkinter.scrolledtext as scrolledtext
import matplotlib.pyplot as plt
from filters import *
import os

# to check that input file (name, sheet names) and output file (name) are correct
from pandas import read_excel

class Checkbox(tk.Checkbutton):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.variable = tk.IntVar(self) #tk.BooleanVar(self)
            self.config(variable=self.variable)

        def checked(self):
            return self.variable.get()

        def check(self):
            self.variable.set(True)

        def uncheck(self):
            self.variable.set(False)

class MainWindow(tk.Tk):
    def __init__(self, main_func):
        super().__init__()

        self.title('KAI')  
        self.geometry('350x800')
        # 'C:\\Users\\Pc\\Desktop\\icon.png'
        cwd = os.getcwd()
        icon_path = cwd + '/kai_icon.png'
        #icon_path = 'C:\\Users\\user\\Dropbox\\Mine\\WorkSpace\\solutions\\calcium_transient\\kai_icon.png'
        #icon_path = 'C:/custom/src_prog_gui/kai_icon.png'
        self.iconphoto( True, tk.PhotoImage(file=icon_path) )
        self.main_func = main_func

        self.labelFrame_global_params = tk.LabelFrame(self, text='Global parameters')
        self.labelFrame_global_params.pack(side='top', ipadx=10, ipady=10)

        self.global_lables = ['Pacing frequency, Hz (default: 1)', 
                 'OY transposition (default: auto)', 
                 'Verbose (default: 1)']
        
        self.col1 = tk.LabelFrame(self.labelFrame_global_params, borderwidth=0)
        self.col1.pack(side='left') # top

        self.labelPaceFreq = tk.Label(self.col1, text=self.global_lables[0])
        self.labelPaceFreq.pack(side='top'
                                #, anchor='nw'
                                ) # side='top',
        self.labelYtrans = tk.Label(self.col1, text=self.global_lables[1])
        self.labelYtrans.pack(side='top'
                              #, anchor='w'
                              ) # side='top',
        self.labelVerbose = tk.Label(self.col1, text=self.global_lables[2])
        self.labelVerbose.pack(side='top'
                                #anchor='e'
                               #, anchor='e'
                               #, expand=1
                               ) # side='top',

        self.col2 = tk.LabelFrame(self.labelFrame_global_params, borderwidth=0)
        self.col2.pack(side='left') # top

        self.entryPaceFreq = tk.Entry(self.col2)
        self.entryPaceFreq.pack(side='top'
                                #, anchor='ne'
                                ) # side='left',         
        self.entryYtrans = tk.Entry(self.col2)
        self.entryYtrans.pack(side='top'
                              #, anchor='e'
                              ) # side='left',
        self.entryVerbose = tk.Entry(self.col2)
        self.entryVerbose.pack(side='top'
                                #anchor='w'
                               #, anchor='w'
                               #, fill='x'
                               ) # side='left',
        
         # Set global parameters
        self.labelDummy_21 = tk.Label(self, text='').pack(side='top', ipady=10)
        self.buttonOpenQuickStartGuide = tk.Button(self, text="Open quick start guide", command=self.openQuickStartGuide)  
        self.buttonOpenQuickStartGuide.pack(side='top')
        self.buttonOpenQuickStartGuide.config(foreground='green')

        # Set global parameters
        self.labelDummy_41 = tk.Label(self, text='').pack(side='top', ipady=10)
        self.buttonGetGlobalParams = tk.Button(self, text="Set global parameters", command=self.getGlobalParams)  
        self.buttonGetGlobalParams.pack(side='top')
        self.buttonGetGlobalParams.config(foreground='green')

        # Select input file path
        self.labelDummy_61 = tk.Label(self, text='').pack(side='top', ipady=10)
        self.buttonGetInputDataPath = tk.Button(self, text='Select input file path', command=self.getInputDataPath)   
        self.buttonGetInputDataPath.pack(side='top', ipady=10)
        self.buttonGetInputDataPath.config(state='disabled') # inaccasable before setting global params

        # Select input file path for baseline signal
        self.labelDummy_61b = tk.Label(self, text='').pack(side='top', ipady=10)
        self.buttonGetInputBaselineDataPath = tk.Button(self, text='Select input file path of ambient signal (optional)', command=self.getInputBaselineDataPath)   
        self.buttonGetInputBaselineDataPath.pack(side='top', ipady=1)
        self.buttonGetInputBaselineDataPath.config(state='disabled')

        # Select output file path
        self.labelDummy_101 = tk.Label(self, text='').pack(side='top', ipady=10)
        self.buttonGetOutputDataPath = tk.Button(self, text='Select output file path', command=self.getOutputDataPath)   
        self.buttonGetOutputDataPath.pack(side='top', ipady=10)
        self.buttonGetOutputDataPath.config(state='disabled') # inaccasable before choosing input file path 

        # Start main programme
        self.labelDummy_81 = tk.Label(self, text='').pack(side='top', ipady=10)  
        self.buttonStartMain = tk.Button(self, text='Start', width=25, command=self.main_func) #main
        self.buttonStartMain.pack(side='top', ipady=10)
        self.buttonStartMain.config(state='disabled') # inaccasable before choosing output file path

        # Interrupt main programme
        self.labelDummy_91 = tk.Label(self, text='').pack(side='top', ipady=10)  
        self.buttonAbortMain = tk.Button(self, text='Abort the processing', width=25, command=self.abort_main_func) #main
        self.buttonAbortMain.pack(side='top', ipady=10)
        self.buttonAbortMain.config(state='disabled') # inaccasable before choosing output file path

        # Close programme window
        self.labelDummy_121 = tk.Label(self, text='').pack(side='top', ipady=10)
        self.buttonExit = tk.Button(self, text='Exit', width=25, command=self.destroy, fg='darkred')#.grid(row=5, column=1)
        self.buttonExit.pack(side='top', ipady=1)
    
    def getGlobalParams(self) -> list:
        self.listGlobalParams = []
        #global glistGlobalParams
        self.listGlobalParams.append(self.entryPaceFreq.get())
        self.listGlobalParams.append(self.entryYtrans.get())
        self.listGlobalParams.append(self.entryVerbose.get())

        if self.listGlobalParams[0] != '': self.listGlobalParams[0] = float(self.listGlobalParams[0])
        else: self.listGlobalParams[0] = 1 # pace freq
        if self.listGlobalParams[1] != '': self.listGlobalParams[1] = float(self.listGlobalParams[1])
        else: self.listGlobalParams[1] = 'variable' # Y transpone
        if self.listGlobalParams[2] != '': self.listGlobalParams[2] = int(self.listGlobalParams[2])
        else: self.listGlobalParams[2] = 1 # verbose
 
        #if self.listGlobalParams[0] == '': self.listGlobalParams[0] = 1 # pace freq
        #if self.listGlobalParams[1] == '': self.listGlobalParams[1] = -1 # Y transpone
        #if self.listGlobalParams[2] == '': self.listGlobalParams[2] = 1 # verbose
        #print(f'listGlobalParams: {listGlobalParams}')
        #glistGlobalParams = listGlobalParams
        showinfo(title='Global parameters settings', 
                    message=f'Global parameters set:\
                            \n\nPacing frequency = {self.listGlobalParams[0]} Hz\
                            \nOY transposition = {self.listGlobalParams[1]}\
                            \nVerbose = {self.listGlobalParams[2]}'
                            )
        self.buttonGetGlobalParams.config(fg='black')
        self.buttonGetInputDataPath.config(state='normal', fg='green')
        self.buttonGetInputBaselineDataPath.config(state='normal')
        return self.listGlobalParams[0], self.listGlobalParams[1], self.listGlobalParams[2]

    # inputExcel
    def getInputDataPath(self):
        #global gInputDataPath
        filetypes = (('Excel files', '*.xlsx'), ('CSV files', '*.csv'))
        input_file_name = filedialog.askopenfilename(title='Select input data', filetypes=filetypes) # , initialdir='/'
        if len(input_file_name) == 0: 
            input_file_name = 'Data not selected';
            showinfo(title='Data not selected', message=f'Data not selected') 
        else: 
            try:
                data = read_excel(input_file_name, sheet_name='data')
                data['t']; data['i'] 
                showinfo(title='Success!', message=f'Input data path:\n{input_file_name}')
                self.buttonGetOutputDataPath.config(state='normal', fg='green')
                self.buttonGetInputDataPath.config(fg='black')
            except:
                error_message = f'Input EXCEL data file with path:\n{input_file_name}\\ \
                                    DOES NOT have a sheet named "data" OR \\ \
                                    DOES NOT have columns named "t" and "i" OR \\ \
                                    has INVALID data format'
                showinfo(title='Error', message=error_message, icon=WARNING)

        self.InputDataPath = input_file_name
        return self.InputDataPath
    
    def getInputBaselineDataPath(self):
        filetypes = (('Excel files', '*.xlsx'), ('CSV files', '*.csv'))
        input_file_name = filedialog.askopenfilename(title='Select input ambient data', filetypes=filetypes) # , initialdir='/'
        if len(input_file_name) == 0: 
            input_file_name = 'Data not selected';
            showinfo(title='Data not selected', message=f'Data not selected')
        else:
            try:
                data = read_excel(input_file_name, sheet_name='data')
                data['t']; data['i'] 
                showinfo(title='Success!', message=f'Input ambient data path:\n{input_file_name}')
            except:
                error_message = f'Input EXCEL baseline data file with path:\n{input_file_name}\\ \
                                    DOES NOT have a sheet named "data" OR \\ \
                                    DOES NOT have columns named "t" and "i" OR \\ \
                                    has INVALID data format'
                showinfo(title='Error', message=error_message, icon=WARNING)
        
        self.InputBaselineDataPath = input_file_name
        return self.InputBaselineDataPath
    
    def getOutputDataPath(self):
        #global gOutputDataPath
        #default_output_name = 'default_output_name'
        filetypes = (('Excel files', '*.xlsx'), ('CSV files', '*.csv'))
        output_file_name = filedialog.asksaveasfilename(title='Select output file name', filetypes=filetypes) # , initialdir='/'
        if len(output_file_name) == 0: output_file_name = 'Output path not selected'
        else: 
            self.buttonStartMain.config(state='normal', fg='green')
            self.buttonAbortMain.config(state='normal', fg='darkred')
            self.buttonGetOutputDataPath.config(fg='black')
            output_file_name += '.xlsx'
        showinfo(title='Output data path', message=f'Output data path:\n{output_file_name}')
        self.OutputDataPath = output_file_name
        return self.OutputDataPath
    
    def setGlobalParams(self):
        return self.listGlobalParams[0], self.listGlobalParams[1], self.listGlobalParams[2]

    def setInputDataPath(self):
        return self.InputDataPath
    
    def setInputBaselineDataPath(self):
        try:
            self.InputBaselineDataPath
        except AttributeError: # NameError AttributeError
            self.InputBaselineDataPath = -1 # nonesence        
        return self.InputBaselineDataPath
    
    def setOutputDataPath(self):
        return self.OutputDataPath

    def repeatPeriodsStage(self):
        answer = askquestion(title='Repeat period removal stage', message='Would you like to remove other periods as well?', icon=WARNING)
        if answer == 'yes':
            self.out = 0
        else: self.out = 1
        return self.out

    def abort_main_func(self):
        self.isExit = 'yes'
        message = 'The program will abort shorty. Then you may choose other parameters and press "Start" again.'
        showinfo(title='Abort initiated', message=message)
        return self.isExit

    def setIsExit(self):
        return self.isExit     

    def openQuickStartGuide(self):
        qst = QuickStartGuideWindow()
        qst.open_file()
        
class QuickStartGuideWindow(tk.Toplevel):
    def __init__(self): # , parent
        super().__init__() # parent

        self.title('Quick Start Guide')  
        self.geometry('800x800')

        self.text_widget = scrolledtext.ScrolledText(self, wrap="word", width=100, height=50) # tk.Text
        self.text_widget.pack(pady=10)

    def open_file(self):
        cwd = os.getcwd()
        file_path = cwd + '/quick_start_guide.txt'
        with open(file_path, 'r') as file:
            content = file.read()
            self.text_widget.delete(1.0, tk.END)  # Clear previous content
            self.text_widget.insert(tk.END, content)

class PeriodsWindow(tk.Toplevel):
    def __init__(self, peaks_min): # , parent
        super().__init__() # parent
        self.peaks_min = peaks_min
        #self.parent = parent
        self.grab_set()

        self.title('KAI: periods to remove')
        self.geometry('300x600')
        
        #column_number_zero = 0
        periods_number = len(self.peaks_min)-1
        self.boxes = []

        self.period_selector = tk.LabelFrame(self, borderwidth=0)
        self.period_selector.pack(side='top')
        self.col1 = tk.LabelFrame(self.period_selector, borderwidth=0)
        self.col1.pack(side='left')
        self.col2 = tk.LabelFrame(self.period_selector, borderwidth=0)
        self.col2.pack(side='left')
        self.col3 = tk.LabelFrame(self.period_selector, borderwidth=0)
        self.col3.pack(side='left')

        for p in range(periods_number):
            if p > 19:
                self.checkbox = Checkbox(self.col3, text=f'period {p+1}') # , command=checkbox_clicked
                self.boxes.append(self.checkbox)
                self.checkbox.pack(side='top', ipadx=5, ipady=5)
            elif p > 9:
                self.checkbox = Checkbox(self.col2, text=f'period {p+1}') # , command=checkbox_clicked
                self.boxes.append(self.checkbox)
                self.checkbox.pack(side='top', ipadx=5, ipady=5)
            else:    
                self.checkbox = Checkbox(self.col1, text=f'period {p+1}') # , command=checkbox_clicked
                self.boxes.append(self.checkbox)
                self.checkbox.pack(side='top', ipadx=5, ipady=5)
        # Set periods to delete
        self.buttonGetPeriodsToDelete_border = tk.Label(self, bg='green', highlightthickness=3)
        self.buttonGetPeriodsToDelete_border.pack(side='top', fill='x')
        self.buttonGetPeriodsToDelete = tk.Button(self.buttonGetPeriodsToDelete_border,
                                                text="Set periods to be removed\n(Click here in any case)", 
                                                command=self.getPeriodsToDelete,
                                                bd=10, fg='green')    
        self.buttonGetPeriodsToDelete.pack(side='top', fill='x' ,ipadx=30, ipady=10)

        # Close programme window
        self.labelDummyPeriodsDelFrame_exit = tk.Label(self, text='').pack(side='top', ipadx=10, ipady=10)
        self.buttonPeriodsDelFrameExit = tk.Button(self, text='Exit\n(return to the main program)', width=10, command=self.confirm_exit, fg='darkred')#.grid(row=5, column=1)
        self.buttonPeriodsDelFrameExit.pack(side='top', fill='x', ipady=1)
        self.buttonPeriodsDelFrameExit.config(state='disabled') # inaccasable before choosing periods to del
    
    def confirm_exit(self):
        answer = askquestion(title='Confirm exit', message='Did you close all Figures (plots)?', icon=WARNING)
        if answer == 'yes':
            self.destroy()
            #if showinfo('Close', 'Closing...'):
            #    self.destroy()

    def getPrdsNmbrToDel(self, seq, item):
        start_at = -1
        locs = []
        while True:
            try:
                loc = seq.index(item,start_at+1)
            except ValueError:
                break
            else:
                locs.append(loc+1)
                start_at = loc
        return locs
    
    def getPeriodsToDelete(self):
        mask_clicked = []
        #global periods_to_del_nmb
        for b, val in enumerate(self.boxes):
            mask_val = val.checked()
            #print(f"\nNew state of box {b}:", mask_val)
            mask_clicked.append(mask_val)
        # TODO: find indexes where vals = 1 in gmask_clicked
        self.periods_to_del_nmb = self.getPrdsNmbrToDel(mask_clicked, 1)
        if all(x == 0 for x in mask_clicked): message = 'No periods will be removed';
        else: message = f'These periods will be removed:\n{self.periods_to_del_nmb}'
        showinfo(title='Periods to be removed', message=message)
        self.buttonPeriodsDelFrameExit.config(state='normal')
        return self.periods_to_del_nmb
    
    def setPeriodsToDelete(self):
        return self.periods_to_del_nmb
    
class FiltersUtilityWindow(tk.Toplevel):
    def __init__(self, x, y): # , parent
        super().__init__() # parent
        self.x = x
        self.y = y
        self.grab_set()

        self.title('KAI: filters utility')
        self.geometry('500x800') # w x h

        ipadx, ipady = 5, 5

        self.labelFrame_all_filters = tk.LabelFrame(self, text='Choose filters parameters')
        self.labelFrame_all_filters.pack(side='top', ipadx=ipadx, ipady=ipady)
        
        # Gaussian filter
        self.modeVal_gaussian_filter = tk.IntVar(self, 0)
        self.labelFrame_gaussian_filter1d = tk.LabelFrame(self.labelFrame_all_filters, text='Gaussian filter')
        self.labelFrame_gaussian_filter1d.pack(side='top', ipadx=ipadx, ipady=ipady)
        self.radioButton_gaussian_filter1d_mode_1 = tk.Radiobutton(self.labelFrame_gaussian_filter1d, text='Mode 1', variable=self.modeVal_gaussian_filter, value=1, command=self.getMode_gaussian_filter)
        self.radioButton_gaussian_filter1d_mode_1.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_gaussian_filter1d_mode_2 = tk.Radiobutton(self.labelFrame_gaussian_filter1d, text='Mode 2', variable=self.modeVal_gaussian_filter, value=2, command=self.getMode_gaussian_filter)
        self.radioButton_gaussian_filter1d_mode_2.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_gaussian_filter1d_mode_3 = tk.Radiobutton(self.labelFrame_gaussian_filter1d, text='Mode 3', variable=self.modeVal_gaussian_filter, value=3, command=self.getMode_gaussian_filter)
        self.radioButton_gaussian_filter1d_mode_3.pack(side='left', ipadx=ipadx, ipady=ipady)

        # Lowpass filter
        self.modeVal_lowpass_filter = tk.IntVar(self, 0)
        self.labelFrame_lowpass_filter = tk.LabelFrame(self.labelFrame_all_filters, text='Lowpass filter')
        self.labelFrame_lowpass_filter.pack(side='top', ipadx=ipadx, ipady=ipady)
        self.radioButton_lowpass_filter_mode_1 = tk.Radiobutton(self.labelFrame_lowpass_filter, text='Mode 1', variable=self.modeVal_lowpass_filter, value=1, command=self.getMode_lowpass_filter)
        self.radioButton_lowpass_filter_mode_1.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_lowpass_filter_mode_2 = tk.Radiobutton(self.labelFrame_lowpass_filter, text='Mode 2', variable=self.modeVal_lowpass_filter, value=2, command=self.getMode_lowpass_filter)
        self.radioButton_lowpass_filter_mode_2.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_lowpass_filter_mode_3 = tk.Radiobutton(self.labelFrame_lowpass_filter, text='Mode 3', variable=self.modeVal_lowpass_filter, value=3, command=self.getMode_lowpass_filter)
        self.radioButton_lowpass_filter_mode_3.pack(side='left', ipadx=ipadx, ipady=ipady)

        # Savgol filter
        self.modeVal_savgol_filter = tk.IntVar(self, 0)
        self.labelFrame_savgol_filter = tk.LabelFrame(self.labelFrame_all_filters, text='Savgol filter')
        self.labelFrame_savgol_filter.pack(side='top', ipadx=ipadx, ipady=ipady)
        self.radioButton_savgol_filter_mode_1 = tk.Radiobutton(self.labelFrame_savgol_filter, text='Mode 1', variable=self.modeVal_savgol_filter, value=1, command=self.getMode_savgol_filter)
        self.radioButton_savgol_filter_mode_1.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_savgol_filter_mode_2 = tk.Radiobutton(self.labelFrame_savgol_filter, text='Mode 2', variable=self.modeVal_savgol_filter, value=2, command=self.getMode_savgol_filter)
        self.radioButton_savgol_filter_mode_2.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_savgol_filter_mode_3 = tk.Radiobutton(self.labelFrame_savgol_filter, text='Mode 3', variable=self.modeVal_savgol_filter, value=3, command=self.getMode_savgol_filter)
        self.radioButton_savgol_filter_mode_3.pack(side='left', ipadx=ipadx, ipady=ipady)

        # clear space for readability
        self.labelDummy_31 = tk.Label(self.labelFrame_all_filters, text='').pack(side='top', ipadx=ipadx, ipady=ipady)
        
        # Combined filter
        self.labelFrame_combined_filter = tk.LabelFrame(self.labelFrame_all_filters, text='Combined filter')
        self.labelFrame_combined_filter.pack(side='top', ipadx=ipadx, ipady=ipady)

        # Gauss
        self.modeVal_combined_gaussian_filter = tk.IntVar(self, 0)
        self.labelFrame_gaussian_filter1d = tk.LabelFrame(self.labelFrame_combined_filter, text='Gaussian filter')
        self.labelFrame_gaussian_filter1d.pack(side='top', ipadx=ipadx, ipady=ipady)
        self.radioButton_gaussian_filter1d_mode_1 = tk.Radiobutton(self.labelFrame_gaussian_filter1d, text='Mode 1', variable=self.modeVal_combined_gaussian_filter, value=1, command=self.getMode_combined_gaussian_filter)
        self.radioButton_gaussian_filter1d_mode_1.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_gaussian_filter1d_mode_2 = tk.Radiobutton(self.labelFrame_gaussian_filter1d, text='Mode 2', variable=self.modeVal_combined_gaussian_filter, value=2, command=self.getMode_combined_gaussian_filter)
        self.radioButton_gaussian_filter1d_mode_2.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_gaussian_filter1d_mode_3 = tk.Radiobutton(self.labelFrame_gaussian_filter1d, text='Mode 3', variable=self.modeVal_combined_gaussian_filter, value=3, command=self.getMode_combined_gaussian_filter)
        self.radioButton_gaussian_filter1d_mode_3.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_gaussian_filter1d_mode_nouse = tk.Radiobutton(self.labelFrame_gaussian_filter1d, text='NO USE', variable=self.modeVal_combined_gaussian_filter, value=0, command=self.getMode_combined_gaussian_filter)
        self.radioButton_gaussian_filter1d_mode_nouse.pack(side='left', ipadx=ipadx, ipady=ipady)

        # Lowpass
        self.modeVal_combined_lowpass_filter = tk.IntVar(self, 0)
        self.labelFrame_lowpass_filter = tk.LabelFrame(self.labelFrame_combined_filter, text='Lowpass filter')
        self.labelFrame_lowpass_filter.pack(side='top', ipadx=ipadx, ipady=ipady)
        self.radioButton_lowpass_filter_mode_1 = tk.Radiobutton(self.labelFrame_lowpass_filter, text='Mode 1', variable=self.modeVal_combined_lowpass_filter, value=1, command=self.getMode_combined_lowpass_filter)
        self.radioButton_lowpass_filter_mode_1.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_lowpass_filter_mode_2 = tk.Radiobutton(self.labelFrame_lowpass_filter, text='Mode 2', variable=self.modeVal_combined_lowpass_filter, value=2, command=self.getMode_combined_lowpass_filter)
        self.radioButton_lowpass_filter_mode_2.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_lowpass_filter_mode_3 = tk.Radiobutton(self.labelFrame_lowpass_filter, text='Mode 3', variable=self.modeVal_combined_lowpass_filter, value=3, command=self.getMode_combined_lowpass_filter)
        self.radioButton_lowpass_filter_mode_3.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_lowpass_filter_mode_3_nouse = tk.Radiobutton(self.labelFrame_lowpass_filter, text='NO USE', variable=self.modeVal_combined_lowpass_filter, value=0, command=self.getMode_combined_lowpass_filter)
        self.radioButton_lowpass_filter_mode_3_nouse.pack(side='left', ipadx=ipadx, ipady=ipady)

        # Savgol
        self.modeVal_combined_savgol_filter = tk.IntVar(self, 0)
        self.labelFrame_savgol_filter = tk.LabelFrame(self.labelFrame_combined_filter, text='Savgol filter')
        self.labelFrame_savgol_filter.pack(side='top', ipadx=ipadx, ipady=ipady)
        self.radioButton_savgol_filter_mode_1 = tk.Radiobutton(self.labelFrame_savgol_filter, text='Mode 1', variable=self.modeVal_combined_savgol_filter, value=1, command=self.getMode_combined_savgol_filter)
        self.radioButton_savgol_filter_mode_1.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_savgol_filter_mode_2 = tk.Radiobutton(self.labelFrame_savgol_filter, text='Mode 2', variable=self.modeVal_combined_savgol_filter, value=2, command=self.getMode_combined_savgol_filter)
        self.radioButton_savgol_filter_mode_2.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_savgol_filter_mode_3 = tk.Radiobutton(self.labelFrame_savgol_filter, text='Mode 3', variable=self.modeVal_combined_savgol_filter, value=3, command=self.getMode_combined_savgol_filter)
        self.radioButton_savgol_filter_mode_3.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_savgol_filter_mode_3_nouse = tk.Radiobutton(self.labelFrame_savgol_filter, text='NO USE', variable=self.modeVal_combined_savgol_filter, value=0, command=self.getMode_combined_savgol_filter)
        self.radioButton_savgol_filter_mode_3_nouse.pack(side='left', ipadx=ipadx, ipady=ipady)

        # clear space for readability
        self.labelDummy_61 = tk.Label(self, text='').pack(side='top', ipadx=ipadx/5, ipady=ipady/5)

        # button to plot 4 figures with baseline and filtered signals
        text = ("Plot baseline and filtered signals\n(Always click on desired Modes)")
        self.button_plot_filters = tk.Button(self, text=text, command=self.pltBaselineFilters, fg='blue')
        self.button_plot_filters.pack(side='top', fill='x', ipadx=ipadx, ipady=ipady)
        #self.button_plot_filters.config(state='disabled') # inaccasable before choosing output file path
        
        # clear space for readability
        self.labelDummy_81 = tk.Label(self, text='').pack(side='top', ipadx=ipadx, ipady=ipady)
        
        # choose a filter to use 
        self.OneFilterVal = tk.IntVar(self, 0)
        self.labelFrame_choose_filter = tk.LabelFrame(self, text='Set one filter')
        self.labelFrame_choose_filter.pack(side='top', ipadx=ipadx, ipady=ipady)
        self.radioButton_use_gaussian_filter = tk.Radiobutton(self.labelFrame_choose_filter, text='Gaussian filter', variable=self.OneFilterVal, value=1) # , command=self.getOneFilter
        self.radioButton_use_gaussian_filter.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_use_lowpass_filter = tk.Radiobutton(self.labelFrame_choose_filter, text='Lowpass filter', variable=self.OneFilterVal, value=2)
        self.radioButton_use_lowpass_filter.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_use_savgol_filter = tk.Radiobutton(self.labelFrame_choose_filter, text='Savgol filter', variable=self.OneFilterVal, value=3)
        self.radioButton_use_savgol_filter.pack(side='left', ipadx=ipadx, ipady=ipady)
        self.radioButton_use_combined_filter = tk.Radiobutton(self.labelFrame_choose_filter, text='Combined filter', variable=self.OneFilterVal, value=4)
        self.radioButton_use_combined_filter.pack(side='left', ipadx=ipadx, ipady=ipady)

        # clear space for readability
        self.labelDummy_91 = tk.Label(self, text='').pack(side='top', ipadx=ipadx/5, ipady=ipady/5)

        # button to set a filter with parameters
        self.button_set_filter_border = tk.Label(self, bg='green', highlightthickness=3)
        self.button_set_filter_border.pack(side='top', fill='x')
        self.button_set_filter = tk.Button(self.button_set_filter_border, text="Set a filter using a specified mode", command=self.getOneFilter, bd=10, fg='green')
        self.button_set_filter.pack(side='top', fill='x', ipadx=ipadx, ipady=ipady) # , ipadx=ipadx
        #self.button_set_filter.config(state='disabled')

        # clear space for readability
        self.labelDummy_11 = tk.Label(self, text='').pack(side='top', ipadx=ipadx, ipady=ipady)

        # button to exit
        self.buttonExit_FiltersUtility = tk.Button(self, text="Exit (return to the main program)", command=self.confirm_exit, foreground='darkred')
        self.buttonExit_FiltersUtility.pack(side='top', fill='x', ipadx=ipadx, ipady=ipady) #  ipadx=ipadx, 
        self.buttonExit_FiltersUtility.config(state='disabled')

    # modes are ordered from less smooth to more smooth
    def getMode_gaussian_filter(self):
        self.gaussian_filter_mode_prmtrs = []
        self.modeVal_gauss = self.modeVal_gaussian_filter.get()
        if self.modeVal_gauss == 1: # 12, 1
            sigma = 5 #12
            truncate = 20 #1
            print(f'Gaussian filter: Mode {self.modeVal_gauss} selected')
        elif self.modeVal_gauss == 2: # 6, 7 
            sigma = 12 #6
            truncate = 1 #7
            print(f'Gaussian filter: Mode {self.modeVal_gauss} selected')
        elif self.modeVal_gauss == 3: # 5, 12
            sigma = 6 #5
            truncate = 7 #20
            print(f'Gaussian filter: Mode {self.modeVal_gauss} selected')
        self.gaussian_filter_mode_prmtrs.append(sigma)
        self.gaussian_filter_mode_prmtrs.append(truncate)   

    def getMode_lowpass_filter(self):
        self.lowpass_filter_mode_prmtrs = []
        self.modeVal_lowpass = self.modeVal_lowpass_filter.get()
        if self.modeVal_lowpass == 1: # 120, 5000, 2
            cutoff = 45 #120
            sample_rate = 2000 #5000
            poles = 4 #2
            print(f'Lowpass filter: Mode {self.modeVal_lowpass} selected')
        elif self.modeVal_lowpass == 2: # 45, 2000, 4
            cutoff = 75  #45
            sample_rate = 2000 #2000
            poles = 1 #4
            print(f'Lowpass filter: Mode {self.modeVal_lowpass} selected')
        elif self.modeVal_lowpass == 3: # 75, 2000, 1
            cutoff = 120 #75
            sample_rate = 5000 #2000
            poles = 2 #1
            print(f'Lowpass filter: Mode {self.modeVal_lowpass} selected')
        self.lowpass_filter_mode_prmtrs.append(cutoff)
        self.lowpass_filter_mode_prmtrs.append(sample_rate)
        self.lowpass_filter_mode_prmtrs.append(poles)    

    def getMode_savgol_filter(self):
        self.savgol_filter_mode_prmtrs = []
        self.modeVal_savgol = self.modeVal_savgol_filter.get()
        if self.modeVal_savgol == 1: # 65, 5
            window_length = 65
            polyorder = 5
            print(f'Savgol filter: Mode {self.modeVal_savgol} selected')
        elif self.modeVal_savgol == 2: # 25, 1 
            window_length = 40 #21
            polyorder = 2 #1
            print(f'Savgol filter: Mode {self.modeVal_savgol} selected')
        elif self.modeVal_savgol == 3: # 40, 2
            window_length = 21 #40
            polyorder = 1 #2
            print(f'Savgol filter: Mode {self.modeVal_savgol} selected')
        self.savgol_filter_mode_prmtrs.append(window_length)
        self.savgol_filter_mode_prmtrs.append(polyorder)

    def getMode_combined_gaussian_filter(self):
        self.combined_gaussian_filter_mode_prmtrs = []
        self.modeVal_combined_gauss = self.modeVal_combined_gaussian_filter.get()
        if self.modeVal_combined_gauss != 0:
            if self.modeVal_combined_gauss == 1:
                sigma = 12
                truncate = 1
                print(f'Gaussian component of Combined filter: Mode {self.modeVal_combined_gauss} selected')
            elif self.modeVal_combined_gauss == 2:
                sigma = 6
                truncate = 7
                print(f'Gaussian component of Combined filter: Mode {self.modeVal_combined_gauss} selected')
            elif self.modeVal_combined_gauss == 3:
                sigma = 5
                truncate = 20
                print(f'Gaussian component of Combined filter: Mode {self.modeVal_combined_gauss} selected')
            self.combined_gaussian_filter_mode_prmtrs.append(sigma)
            self.combined_gaussian_filter_mode_prmtrs.append(truncate)
        else:
            print(f'Gaussian component of Combined filter: WILL NOT BE USED')

    def getMode_combined_lowpass_filter(self):
        self.combined_lowpass_filter_mode_prmtrs = []
        self.modeVal_combined_lowpass = self.modeVal_combined_lowpass_filter.get()
        if self.modeVal_combined_lowpass != 0:
            if self.modeVal_combined_lowpass == 1:
                cutoff = 120
                sample_rate = 5000
                poles = 2
                print(f'Lowpass component of Combined filter: Mode {self.modeVal_combined_lowpass} selected')
            elif self.modeVal_combined_lowpass == 2:
                cutoff = 45
                sample_rate = 2000
                poles = 4
                print(f'Lowpass component of Combined filter: Mode {self.modeVal_combined_lowpass} selected')
            elif self.modeVal_combined_lowpass == 3:
                cutoff = 75
                sample_rate = 2000
                poles = 1
                print(f'Lowpass component of Combined filter: Mode {self.modeVal_combined_lowpass} selected')
            self.combined_lowpass_filter_mode_prmtrs.append(cutoff)
            self.combined_lowpass_filter_mode_prmtrs.append(sample_rate)
            self.combined_lowpass_filter_mode_prmtrs.append(poles)
        else:
            print(f'Lowpass component of Combined filter: WILL NOT BE USED')

    def getMode_combined_savgol_filter(self):
        self.combined_savgol_filter_mode_prmtrs = []
        self.modeVal_combined_savgol = self.modeVal_combined_savgol_filter.get()
        if self.modeVal_combined_savgol != 0:
            if self.modeVal_combined_savgol == 1:
                window_length = 65
                polyorder = 5
                print(f'Savgol component of Combined filter: Mode {self.modeVal_combined_savgol} selected')
            elif self.modeVal_combined_savgol == 2:
                window_length = 21
                polyorder = 1
                print(f'Savgol component of Combined filter: Mode {self.modeVal_combined_savgol} selected')
            elif self.modeVal_combined_savgol == 3:
                window_length = 40
                polyorder = 2
                print(f'Savgol component of Combined filter: Mode {self.modeVal_combined_savgol} selected')
            self.combined_savgol_filter_mode_prmtrs.append(window_length)
            self.combined_savgol_filter_mode_prmtrs.append(polyorder)    
        else:
            print(f'Savgol component of Combined filter: WILL NOT BE USED')                 

    def pltBaselineFilters(self):
        # checking if Gaussian Mode is selected 
        try:
            prmtrsGaussian_filter = self.gaussian_filter_mode_prmtrs
            self.y_gaussian_filter, _ = use_gaussian_filter1d(self.y, prmtrsGaussian_filter[0], prmtrsGaussian_filter[1])
        except:
            prmtrsGaussian_filter = None
        # checking if Lowpass Mode is selected    
        try:        
            prmtrsLowpass_filter = self.lowpass_filter_mode_prmtrs
            self.y_lowpass_filter, _ = use_lowpass_filter(self.y, prmtrsLowpass_filter[0], prmtrsLowpass_filter[1], prmtrsLowpass_filter[2])
        except:
            prmtrsLowpass_filter = None
        # checking if Savgol Mode is selected 
        try:    
            prmtrsSavgol_filter = self.savgol_filter_mode_prmtrs
            self.y_savgol_filter, _ = use_savgol_filter(self.y, prmtrsSavgol_filter[0], prmtrsSavgol_filter[1])
        except:
            prmtrsSavgol_filter = None    
        #print('\nprmtrsGaussian_filter:', prmtrsGaussian_filter[0], prmtrsGaussian_filter[1])
        #print('\nself.x: ', self.x)
        #print('\nself.y: ', self.y)
        #print('\nself.y.shape: ', self.y.shape[0])

        # plotting
        '''global gy_gaussian_filter
        global gy_lowpass_filter
        global gy_savgol_filter'''
        '''gy_gaussian_filter = self.y_gaussian_filter
        gy_lowpass_filter = self.y_lowpass_filter
        gy_savgol_filter = self.y_savgol_filter'''

        y_combined_filters = []
        y_combined_filters_used = ''
        self.modeVal_combined_gauss = self.modeVal_combined_gaussian_filter.get()
        if self.modeVal_combined_gauss != 0:
            prmtrsCombined_gauss = self.combined_gaussian_filter_mode_prmtrs
            y_combined_gaussian_filter, _ = use_gaussian_filter1d(self.y, prmtrsCombined_gauss[0], prmtrsCombined_gauss[1]) 
            y_combined_filters.append(y_combined_gaussian_filter)
            y_combined_filters_used += f'Gaussian, Mode {self.modeVal_combined_gauss};; '
        self.modeVal_combined_lowpass = self.modeVal_combined_lowpass_filter.get()    
        if self.modeVal_combined_lowpass != 0:
            prmtrsCombined_lowpass = self.combined_lowpass_filter_mode_prmtrs
            y_combined_lowpass_filter, _ = use_lowpass_filter(self.y, prmtrsCombined_lowpass[0], prmtrsCombined_lowpass[1], prmtrsCombined_lowpass[2])
            y_combined_filters.append(y_combined_lowpass_filter)
            y_combined_filters_used += f'Lowpass, Mode {self.modeVal_combined_lowpass};; '
        self.modeVal_combined_savgol = self.modeVal_combined_savgol_filter.get()    
        if self.modeVal_combined_savgol != 0:
            prmtrsCombined_savgol = self.combined_savgol_filter_mode_prmtrs
            y_combined_savgol_filter, _ = use_savgol_filter(self.y, prmtrsCombined_savgol[0], prmtrsCombined_savgol[1]) 
            y_combined_filters.append(y_combined_savgol_filter)
            y_combined_filters_used += f'Savgol, Mode {self.modeVal_combined_savgol};; '
        
        '''if self.modeVal_combined_gauss == 0 and self.modeVal_combined_lowpass == 0 and self.modeVal_combined_savgol == 0:
            y_combined_filter, _ = None
            x = None
        else:    
            y_combined_filter, _ = use_combined_filter(y_combined_filters)'''

        fig_w, fig_h = 20, 15
        rows, cols = 2, 2
        fig, axs = plt.subplots(rows, cols, figsize=(fig_w, fig_h))
        if prmtrsGaussian_filter == None:
            axs[0, 0].plot(self.x, self.y, label='Baseline')
            axs[0, 0].set_title(f'Gassuian filter: Mode NOT SELECTED')
        else:    
            axs[0, 0].plot(self.x, self.y, label='Baseline')
            axs[0, 0].plot(self.x, self.y_gaussian_filter, label='Gassuian filter')
            axs[0, 0].set_title(f'Gassuian filter: Mode {self.modeVal_gauss}')
        axs[0, 0].legend()

        if prmtrsLowpass_filter == None:
            axs[0, 1].plot(self.x, self.y, label='Baseline')
            axs[0, 1].set_title(f'Lowpass filter: Mode NOT SELECTED')
        else:
            axs[0, 1].plot(self.x, self.y, label='Baseline')
            axs[0, 1].plot(self.x, self.y_lowpass_filter, label='Lowpass filter')
            axs[0, 1].set_title(f'Lowpass filter: Mode {self.modeVal_lowpass}')
        axs[0, 1].legend()

        if prmtrsSavgol_filter == None:
            axs[1, 0].plot(self.x, self.y, label='Baseline')
            axs[1, 0].set_title(f'Savgol filter: Mode NOT SELECTED')
        else:
            axs[1, 0].plot(self.x, self.y, label='Baseline')    
            axs[1, 0].plot(self.x, self.y_savgol_filter, label='Savgol filter')
            axs[1, 0].set_title(f'Savgol filter: Mode {self.modeVal_savgol}')
        axs[1, 0].legend()

        if self.modeVal_combined_gauss == 0 and self.modeVal_combined_lowpass == 0 and self.modeVal_combined_savgol == 0:
            axs[1, 1].plot(self.x, self.y, label='Baseline')
            axs[1, 1].set_title(f'Combined filter is NOT USED')
        else:
            axs[1, 1].plot(self.x, self.y, label='Baseline')
            #global gy_combined_filter
            self.y_combined_filter, _ = use_combined_filter(y_combined_filters)
            #gy_combined_filter = self.y_combined_filter
            axs[1, 1].plot(self.x, self.y_combined_filter, label='Combined filter')   
            axs[1, 1].set_title(f'Combined filter:\n {y_combined_filters_used}')
        axs[1, 1].legend()

        for ax in axs.flat:
            ax.set(xlabel='time, s', ylabel='intensity')

        # Hide x labels and tick labels for top plots and y ticks for right plots.
        for ax in axs.flat:
            ax.label_outer()
        plt.show()    
        pass
    
    def getOneFilter(self):
        _OneFilterVal = self.OneFilterVal.get()
        if _OneFilterVal == 1:
            self.OneFilter_name = 'Gaussian filter'
            self.OneFilter_mode = self.modeVal_gauss
            self.OneFilterPrmtrs = self.gaussian_filter_mode_prmtrs
        elif _OneFilterVal == 2:
            self.OneFilter_name = 'Lowpass filter'
            self.OneFilter_mode = self.modeVal_lowpass
            self.OneFilterPrmtrs = self.lowpass_filter_mode_prmtrs
        elif _OneFilterVal == 3:
            self.OneFilter_name = 'Savgol filter'
            self.OneFilter_mode = self.modeVal_savgol
            self.OneFilterPrmtrs = self.savgol_filter_mode_prmtrs
        elif _OneFilterVal == 4:
            self.OneFilter_mode = []
            self.OneFilterPrmtrs = []
            self.CombinedFilter_components = ''
            #self.CombinedFilter_components_modes = ''
            if self.modeVal_combined_gauss != 4:
                self.CombinedFilter_components += f'Gaussian, Mode {self.modeVal_combined_gauss};; '
                self.OneFilter_mode.append(self.modeVal_combined_gauss)
                self.OneFilterPrmtrs.append(self.gaussian_filter_mode_prmtrs)
                #self.CombinedFilter_components_modes += str(self.modeVal_combined_gaussian_filter)+'_'
            else: self.OneFilter_mode.append(0); self.OneFilterPrmtrs.append([0]) 
            if self.modeVal_combined_lowpass != 4:
                self.CombinedFilter_components += f'Lowpass, Mode {self.modeVal_combined_lowpass};; '
                self.OneFilter_mode.append(self.modeVal_combined_lowpass)
                self.OneFilterPrmtrs.append(self.lowpass_filter_mode_prmtrs)
                #self.CombinedFilter_components_modes += str(self.modeVal_combined_lowpass_filter)+'_'
            else: self.OneFilter_mode.append(0); self.OneFilterPrmtrs.append([0])  
            if self.modeVal_combined_savgol != 4:
                self.CombinedFilter_components += f'Savgol, Mode {self.modeVal_combined_savgol};; '
                self.OneFilter_mode.append(self.modeVal_combined_savgol)
                self.OneFilterPrmtrs.append(self.savgol_filter_mode_prmtrs)
                #self.CombinedFilter_components_modes += str(self.modeVal_combined_savgol_filter)+'_'
            else: self.OneFilter_mode.append(0); self.OneFilterPrmtrs.append([0])    

            self.OneFilter_name = 'Combined filter:\n' + self.CombinedFilter_components 
            #self.OneFilter_mode = self.CombinedFilter_components_modes
            self.OneFilterPrmtrs = self.combined_gaussian_filter_mode_prmtrs

        if _OneFilterVal == 4:
            print(f'{self.OneFilter_name} set')
            message = f'Selected filter: {self.OneFilter_name}'
        else:    
            print(f'{self.OneFilter_name}: Mode {self.OneFilter_mode} set')
            message = f'Selected filter:\n{self.OneFilter_name}, Mode {self.OneFilter_mode}'
        showinfo(title='Selected filter', message=message) 
        self.buttonExit_FiltersUtility.config(state='normal')
        '''global gOneFilter_name
        global gOneFilter_mode
        global gOneFilterPrmtrs
        gOneFilter_name = self.OneFilter_name
        gOneFilter_mode = self.OneFilter_mode
        gOneFilterPrmtrs = self.OneFilterPrmtrs'''
        return self.OneFilter_name, self.OneFilter_mode, self.OneFilterPrmtrs

    def confirm_exit(self):
        answer = askquestion(title='Confirm exit', message='Did you set the right filter?', icon=WARNING)
        if answer == 'yes':
            self.destroy()

    # use it in MAIN prog to set a filter to be used
    #  
    def setOneFilter(self):
        return self.OneFilter_name, self.OneFilter_mode, self.OneFilterPrmtrs #gOneFilter_name, gOneFilter_mode, gOneFilterPrmtrs
    
    def getY_gaussian_filter(self):
        return self.y_gaussian_filter #gy_gaussian_filter
    
    def getY_lowpass_filter(self):
        return self.y_lowpass_filter
    
    def getY_savgol_filter(self):
        return self.y_savgol_filter

    def getY_combined_filter(self):
        return self.y_combined_filter


'''def main():
    print('inside of main func')
    some_path = MainWindow.setInputDataPath()
    print('some_path', some_path)

    peaks_min = [11,22,33,44]
    sub_app = PeriodsWindow(app, peaks_min)
    sub_app.grab_set()
    app.wait_window(sub_app)
    #sub_app.mainloop()

    periods_to_del = PeriodsWindow.setPeriodsToDelete()

    print('periods_to_del', periods_to_del)

    return 0

app = MainWindow(main)
app.mainloop() '''

'''peaks_min = [11,22,33,44]
sub_app = PeriodsWindow(peaks_min)
sub_app.mainloop()'''