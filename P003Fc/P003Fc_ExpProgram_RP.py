#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Friday August 29 2025

Last updated: 2025-09-03

@author: Megan C. & Cyrus K.

This project investigated the roles of various scedules of reinforcement 
(Instrumental and omission) in dictating spatial and temoporal response 
variability using a between-subjects design. 
It also accounted for proximity to reinforcement by modifying the number of 
responses to reach each trial's outcome; this manipulation occured each phase.

All subjects underwent a single phase consisting of stimuli defined by either 
instrumental or omission RR2, RR5, RR20, and RR50 reward contingencies. 
Across each condition, trials could be one of four types (the reinforcement 
schedules described above), differentiated by stimulus color--four distinct 
color patterns counter-balanced across two groups of four subjects. 

Each trial lasted 10 seconds, and each ITI lasted 30 seconds. Within these 
10 s, responses on and off the presented cue were tracked and could impact 
the outcome of the trial.
"""
# Prior to running any code, its conventional to first import relevant 
# libraries for the entire script. These can range from python libraries (sys)
# or sublibraries (setrecursionlimit) that are downloaded to every computer
# along with python, or other files within this folder (like control_panel or 
# maestro).
# =============================================================================
from csv import writer, QUOTE_MINIMAL, DictReader
from datetime import datetime, timedelta, date
from sys import setrecursionlimit, path as sys_path
from tkinter import Toplevel, Canvas, BOTH, TclError, Tk, Label, Button, \
     StringVar, OptionMenu, IntVar, Radiobutton
from time import time, sleep
from os import getcwd, popen, mkdir, path as os_path
from random import choice, shuffle
from PIL import ImageTk, Image  

# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It is changed automatically based on whether
# the program is running in operant boxes (True) or not (False). It is
# automatically set to True if the user is "blaisdelllab" (e.g., running
# on a rapberry pi) or False if not. The output of os_path.expanduser('~')
# should be "/home/blaisdelllab" on the RPis.

if os_path.expanduser('~').split("/")[2] =="blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")

# Import hopper/other specific libraries from files on operant box computers
try:
    if operant_box_version:
        # Import additional libraries...
        import pigpio # import pi, OUTPUT
        import csv
        #...including art scripts
        sys_path.insert(0, str(os_path.expanduser('~')+"/Desktop/Experiments/P033/"))
        import graph
        import polygon_fill
        
        # Setup GPIO numbers (NOT PINS; gpio only compatible with GPIO num)
        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        house_light_GPIO_num = 21
        
        # Setup use of pi()
        rpi_board = pigpio.pi()
        
        # Then set each pin to output 
        rpi_board.set_mode(servo_GPIO_num,
                           pigpio.OUTPUT) # Servo motor...
        rpi_board.set_mode(hopper_light_GPIO_num,
                           pigpio.OUTPUT) # Hopper light LED...
        rpi_board.set_mode(house_light_GPIO_num,
                           pigpio.OUTPUT) # House light LED...
        
        # Setup the servo motor 
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    50) # Default frequency is 50 MhZ
        
        # Next grab the up/down 
        hopper_vals_csv_path = str(os_path.expanduser('~')+"/Desktop/Box_Info/Hopper_vals.csv")
        
        # Store the proper UP/DOWN values for the hopper from csv file
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        hopper_up_val = up_down_table[1][0]
        hopper_down_val = up_down_table[1][1]
        
        # Lastly, run the shell script that maps the touchscreen to operant box monitor
        popen("sh /home/blaisdelllab/Desktop/Hardware_Code/map_touchscreen.sh")
                             
        
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")

# Below  is just a safety measure to prevent too many recursive loops). It
# doesn't need to be changed.
setrecursionlimit(5000)

"""
The code below jumpstarts the loop by first building the hopper object and 
making sure everything is turned off, then passes that object to the
control_panel. The program is largely recursive and self-contained within each
object, and a macro-level overview is:
    
    ControlPanel -----------> MainScreen ------------> PaintProgram
         |                        |                         |
    Collects main           Runs the actual         Gets passed subject
    variables, passes      experiment, saves        name, but operates
    to Mainscreen          data when exited          independently
    

"""

# ─────────────────────────────────────────────────────────────────────────────
#  ExperimentalControlPanel (CP) –– exists "behind the scenes" for a session.
# ─────────────────────────────────────────────────────────────────────────────
class ExperimenterControlPanel(object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self):
        # First, setup the data directory in "Documents"
        self.doc_directory = str(os_path.expanduser('~'))+"/Documents/"
        # Next up, we need to do a couple things that will be different based
        # on whether the program is being run in the operant boxes or on a 
        # personal computer. These include setting up the hopper object so it 
        # can be referenced in the future, or the location where data files
        # should be stored.
        if operant_box_version:
            # Setup the data directory in "Documents"
            self.data_folder = "P003Fc_data" # The folder within Documents where subject data is kept
            self.data_folder_directory = str(os_path.expanduser('~'))+"/Desktop/Data/" + self.data_folder
        else: # If not, just save in the current directory the program us being run in 
            self.data_folder_directory = getcwd() + "/data"
        
        # setup the root Tkinter window
        self.control_window = Tk()
        self.control_window.title("P003Fc Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = ["Herriot", "Peach", "Wario", "Kurt",
                                 "Hendrix", "Itzamna", "Iggy", "Hawthorne"]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list,
                                          command=self.set_pigeon_ID).pack()

        # Conditions
        self.condition_titles = ["INS", "OMS"]
        
        Label(self.control_window, text="Condition:").pack()
        self.cond_variable = StringVar(self.control_window)
        self.cond_variable.set("Select")
        self.cond_menu = OptionMenu(self.control_window,
                                         self.cond_variable,
                                         *self.condition_titles
                                         ).pack()
        
        # Record data variable?
        Label(self.control_window,
              text = "Record data in seperate data sheet?").pack()
        self.record_data_variable = IntVar()
        self.record_data_rad_button1 =  Radiobutton(self.control_window,
                                   variable = self.record_data_variable, text = "Yes",
                                   value = True).pack()
        self.record_data_rad_button2 = Radiobutton(self.control_window,
                                  variable = self.record_data_variable, text = "No",
                                  value = False).pack()
        self.record_data_variable.set(True) # Default set to True
        
        
        # Start button
        self.start_button = Button(self.control_window,
                                   text = 'Start program',
                                   bg = "green2",
                                   command = self.build_chamber_screen).pack()
        
        # This makes sure that the control panel remains onscreen until exited
        self.control_window.mainloop() # This loops around the CP object
        
        
    def set_pigeon_ID(self, pigeon_name):
        # This function checks to see if a pigeon's data folder currently 
        # exists in the respective "data" folder within the Documents
        # folder and, if not, creates one.
        try:
            if not os_path.isdir(self.data_folder_directory + pigeon_name):
                mkdir(os_path.join(self.data_folder_directory, pigeon_name))
                print("\n ** NEW DATA FOLDER FOR %s CREATED **" % pigeon_name.upper())
        except FileExistsError:
            print(f"DATA FOLDER FOR {pigeon_name.upper()} EXISTS")
                
                
    def build_chamber_screen(self):
        # Once the green "start program" button is pressed, then the mainscreen
        # object is created and pops up in a new window. It gets passed the
        # important inputs from the control panel.
        if self.subject_ID_variable.get() in self.pigeon_name_list:
            if self.cond_variable.get() != "Select":
               print("Operant Box Screen Built") 
               # new (correct) signature — exactly four args in the right order
               self.MS = MainScreen(
                   self.subject_ID_variable.get(),      # subject_ID
                   self.record_data_variable.get(),     # record_data flag
                   self.data_folder_directory,          # data_folder_directory
                   self.cond_variable.get()             # phase_type ("INS" or "OMS")
               )
            else:
               print("\n ERROR: Input Condition Before Starting Session")
        else:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")
            
            

# Then, setup the MainScreen object
class MainScreen(object):
    # First, we need to declare several functions that are 
    # called within the initial __init__() function that is 
    # run when the object is first built:
        
    def __init__(self, subject_ID, record_data, data_folder_directory, phase_type):
        
        #  Passed-in variables
        self.subject_ID           = subject_ID
        self.phase_type           = phase_type      # "INS" or "OMS"
        self.record_data          = record_data
        self.data_folder_directory = data_folder_directory

        # Set up the visual Canvas
        self.root = Toplevel() 
        self.root.title("P003Fc: Spatial Variability")
        self.mainscreen_height = 768 # height of the experimental canvas screen
        self.mainscreen_width = 1024 # width of the experimental canvas screen
        self.root.bind("<Escape>", self.exit_program) # bind exit program to the "esc" key
        
        # If the version is the one running in the boxes...
        if operant_box_version: 
            # Keybind relevant keys
            self.cursor_visible = True # Cursor starts on...
            self.change_cursor_state() # turn off cursor UNCOMMENT
            self.root.bind("<c>",
                           lambda event: self.change_cursor_state()) # bind cursor on/off state to "c" key
            # Then fullscreen (on a 1024x768p screen). Assumes that both screens
            # that are being used have identical dimensions
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
            self.root.attributes('-fullscreen',
                                 True)
            self.mastercanvas = Canvas(self.root,
                                   bg="black")
            self.mastercanvas.pack(fill = BOTH,
                                   expand = True)
        # If we want to run a "human-friendly" version
        else: 
            # No keybinds and  1024x768p fixed window
            self.mastercanvas = Canvas(self.root,
                                   bg="black",
                                   height=self.mainscreen_height,
                                   width = self.mainscreen_width)
            self.mastercanvas.pack()

        # Timing variables
        self.start_time = datetime.now()  # This will be reset once the session actually starts
        self.trial_start = datetime.now() # Duration into each trial as a second count, resets each trial
        self.ITI_duration = 30000 # duration of inter-trial interval (ms)
        self.trial_timer_duration = 10000 # Duration of each trial (ms)
        self.current_trial_counter = 0 # counter for current trial in session
        self.trial_stage = 0 # Trial substage (4 within DMTO)
        # Selective hopper timing by subject...
        # if self.subject_ID in ["Joplin"]:
           # self.hopper_duration = 5000 # duration of accessible hopper(ms)
        # elif self.subject_ID == "Meat Loaf":
           # self.hopper_duration = 7000 # duration of accessible hopper(ms)
        # if self.subject_ID in ["Herriot", "Jubilee"]:
           # self.hopper_duration = 3000 # duration of accessible hopper(ms)
        # else:
        self.hopper_duration = 4000 # duration of accessible hopperhe(ms)

        # These are additional "under the hood" variables that need to be declared
        self.max_trials = 80 # Max number of trials within a session
        self.session_data_frame = [] #This where trial-by-trial data is stored
        self.current_trial_counter = 0 # This counts the number of trials that have passed
        header_list = ["SessionTime", "Xcord","Ycord", "Event", "TrialTime", 
                       "TrialType","TargetPeckNum", "BackgroundPeckNum",
                       "TrialNum", "TrialColor", "Subject",
                       "Date"] # Column headers
        self.session_data_frame.append(header_list) # First row of matrix is the column headers
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL' # To be filled later on after Pig. ID is provided (in set vars func below)

        ## Finally, start the recursive loop that runs the program:
        self.place_birds_in_box()

    def place_birds_in_box(self):
        # This is the default screen run until the birds are placed into the
        # box and the space bar is pressed. It then proceedes to the ITI. It only
        # runs in the operant box version. After the space bar is pressed, the
        # "first_ITI" function is called for the only time prior to the first trial
        def first_ITI(event):
            # Is initial delay before first trial starts
            print("Spacebar pressed -- SESSION STARTED")
            self.mastercanvas.delete("all")
            self.root.unbind("<space>")
            self.start_time = datetime.now()
            self.trial_type = "NA"

            # 1) Read per‐subject CSV to get PNG filenames
            script_dir = getcwd()
            csv_path = os_path.join(script_dir, "P003Fc_stimulus_assignments.csv")
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = DictReader(f)
                row = next(r for r in reader if r["Subject"] == self.subject_ID)

            # only keep the non-empty trial-types
            all_trial_types = [
                "INS_2","INS_5","INS_20","INS_50",
                "OMS_2","OMS_5","OMS_20","OMS_50"
            ]
            self.stimulus_assignments_dict = {
                tt: row[tt]
                for tt in all_trial_types
                if row.get(tt, "").strip()  # only if there's a filename in the cell
            }

            # 2) Preload each PNG into PhotoImages
            # ---- work out the folder that contains *this* .py file ------------
            script_dir = os_path.dirname(os_path.abspath(__file__))          # …/P003/P003Fc
            # ---- stimuli folder sits right next to this script ----------------
            stimuli_folder = os_path.join(script_dir, "stimuli")             # …/P003/P003Fc/stimuli
            # ------------------------------------------------------------------

            KEY_PIXELS = 192          # ← hard-code the size you want

            self.stimulus_images = {}
            for tt, fname in self.stimulus_assignments_dict.items():
                img_path = os_path.join(stimuli_folder, fname)

                pil_img = (
                    Image.open(img_path)          # original file
                         .convert("RGBA")         # keep transparency if any
                         .resize((KEY_PIXELS, KEY_PIXELS), Image.LANCZOS)
                )
                self.stimulus_images[tt] = ImageTk.PhotoImage(pil_img)

            # 3) Build the trial‐order list, 160 trials, no >3 same in a row
            potential_trial_assignments = [
                "INS_2", "INS_5", "INS_20", "INS_50",
                "OMS_2", "OMS_5", "OMS_20", "OMS_50"
            ] * 20                       # 160 → we'll filter down to 80 next

            # keep only trials that match this bird’s between-subjects condition
            potential_trial_assignments = [
                tt for tt in potential_trial_assignments
                if tt.startswith(self.phase_type)         # "INS" or "OMS"
            ]

            # Now we have 4 distinct trial codes × 20 each  →  80 elements
            # Shuffle until no FOUR IDENTICAL trial codes appear consecutively
            while True:
                shuffle(potential_trial_assignments)

                # look for any run of four identical elements
                bad_run_found = any(
                    potential_trial_assignments[i]   == potential_trial_assignments[i-1] ==
                    potential_trial_assignments[i-2] == potential_trial_assignments[i-3]
                    for i in range(3, len(potential_trial_assignments))
                )

                if not bad_run_found:
                    self.trial_assignment_list = potential_trial_assignments[:]   # full 80
                    break            # good order found; leave the while-loop

            # After the order of stimuli per trial is determined, we can start.
            # If running a test session, the duration of intervals can be 
            # lowered significantly to make more efficient
            if self.subject_ID == "TEST": # If test, don't worry about ITI delays
                self.ITI_duration = 1000
                self.hopper_duration = 1000
                self.root.after(1000, self.ITI)
            else:
                self.root.after(2000, self.ITI)


        # The runs first, setting up the spacebar trigger
        self.root.bind("<space>", first_ITI) # bind cursor state to "space" key
        self.mastercanvas.create_text(512,374,
                                      fill="white",
                                      font="Times 25 italic bold",
                                      text=f"P003Fc \n"
                                            "Place bird in box, then press space \n"
                                            f"Subject: {self.subject_ID}\n"
                                            f"Condition: {self.phase_type}")
                
    ## %% ITI
    # Every trial (including the first) "starts" with an ITI. The ITI function
    # does several different things:
    #   1) Checks to see if any session constraints have been reached
    #   2) Resets the hopper and any trial-by-trial variables
    #   3) Increases the trial counter by one
    #   4) Moves on to the next trial after a delay
    # 
    def ITI(self):
        # This function just clear the screen. It will be used a lot in the future, too.
        self.clear_canvas()
        
        # Make sure pecks during ITI are saved
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "ITI_peck": 
                                       self.write_data(event, event_type))
            
        # This turns all the stimuli off from the previous trial (during the
        # ITI). Needs to happen every ITI.
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num,
                            False) # Turn off the hopper light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                           hopper_down_val) # Hopper down
            rpi_board.write(house_light_GPIO_num, 
                            False) # Turn off house light
        

        # First, check to see if any session limits have been reached (e.g.,
        # if the max time or reinforcers earned limits are reached).
        if self.current_trial_counter == self.max_trials:
            print("Trial max reached")
            self.exit_program("event")
        
        # Else, after a timer move on to the next trial. Note that,
        # although the after() function is given here, the rest of the code 
        # within this function is still executed before moving on.
        else: 
            # Print text on screen if a test (should be black if an experimental trial)
            if not operant_box_version or self.subject_ID == "TEST":
                self.mastercanvas.create_text(512,374,
                                              fill="white",
                                              font="Times 25 italic bold",
                                              text=f"ITI ({int(self.ITI_duration/1000)} sec.)")
                
            # Reset other variables for the following trial.
            self.trial_start = time() # Set trial start time (note that it includes the ITI, which is subtracted later)
            self.trial_peck_counter = 0 # Reset trial peck counter each trial
            self.background_peck_counter = 0 # Also reset background counter
            self.hidden_patch_peck_counter = 0 # And hidden patch trials
            
            self.write_comp_data(False) # update data .csv with trial data from the previous trial
            
            # First pick the trial type from the prexisting list....
            self.trial_type = self.trial_assignment_list[self.current_trial_counter - 1]
   
            # Increase trial counter by one
            self.current_trial_counter += 1
            
            if self.current_trial_counter == 1:
                self.root.after(self.ITI_duration, self.start_signal_period)
            else:
                # Next, set a delay timer to proceed to the next trial
                self.root.after(self.ITI_duration, self.build_keys)
                
            # Finally, print terminal feedback "headers" for each event within the next trial
            print(f"\n{'*'*30} Trial {self.current_trial_counter} begins {'*'*30}") # Terminal feedback...
            print(f"{'Event Type':>30} | Xcord. Ycord. | Trial | Session Time")
    
        
    #%%  
    """
    This function is called one single time at the very beginning of the
    session. It simply builds a blank square and requires one peck to start 
    the program. This was called to make sure that pigeons were "ready" to 
    start the session, given that trials progressed on a timer. More info
    about building Canvas widgets in the following section.
    """
    def start_signal_period(self):
        # We need to turn on the houselight as soon as the trial starts
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True) # Turn off house light
        # Border...
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        # Make it a button
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event: 
                                       self.background_press(event))
        
        # Next build the actual cue
        key_coord_list =  [416, 288, 608, 480]
        self.mastercanvas.create_rectangle(key_coord_list,
                                      outline = "black",
                                      fill = "white",
                                      tag = "key")

        # Then bind a function to a key press!
        self.mastercanvas.tag_bind("key",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "start_signal_press": 
                                       self.start_signal_press(event, event_type))
            
    def start_signal_press(self, event, event_type):
        # Write data for the peck
        self.write_data(event, event_type)
        self.clear_canvas()
        # Proceed to the first trial after 1 s
        self.root.after(1000, self.build_keys)
        
    
    """
    The code below is very straightforward. It builds the key for the specific
    trial, ties a function to the background and key, and then starts a 10s 
    timer for the trial. Key pecks are incrementally counted and calculated 
    at the end of the timer to see if the criterion is met.
    """
        
    def build_keys(self):
    # Reset trial time as soon as keys are built if 
        if self.current_trial_counter == 1:
            self.trial_start = time() - (self.ITI_duration/1000)  # includes ITI

    # This is a function that builds the all the buttons on the Tkinter
    # Canvas. The Tkinter code (and geometry) may appear a little dense
    # here, but it follows many of the same rules. All keys will be built
    # during non-ITI intervals, but they will only be filled in and active
    # during specific times. However, pecks to keys will be differentiated
    # regardless of activity.

    # We need to turn on the houselight as soon as the trial starts
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True)  # Turn on houselight

    # First, build the background. This basically builds a button the size of 
    # the screen to track any pecks; buttons built on top of this button will
    # NOT count as background pecks but as key pecks, because the object is
    # covering that part of the background.
        self.mastercanvas.create_rectangle(
            0, 0,
            self.mainscreen_width,
            self.mainscreen_height,
            fill="black",
            outline="black",
            tag="bkgrd"
        )
        self.mastercanvas.tag_bind(
            "bkgrd", "<Button-1>",
            lambda event: self.background_press(event)
        )

        # Coordinates for all the keys
        key_coord_list = [416, 288, 608, 480]   # ~192 px diameter
        midpoint_diameter = 10
        midpoint_coord_list = [
            key_coord_list[0] + ((key_coord_list[2] - key_coord_list[0]) // 2) - (midpoint_diameter // 2),
            key_coord_list[1] + ((key_coord_list[3] - key_coord_list[1]) // 2) - (midpoint_diameter // 2),
            key_coord_list[0] + ((key_coord_list[2] - key_coord_list[0]) // 2) + (midpoint_diameter // 2),
            key_coord_list[1] + ((key_coord_list[3] - key_coord_list[1]) // 2) + (midpoint_diameter // 2)
        ]

        # Key outline around the key
        outline_size = 20  # pixels beyond key circle
        outline_coords_list = [
            key_coord_list[0] - outline_size,
            key_coord_list[1] - outline_size,
            key_coord_list[2] + outline_size,
            key_coord_list[3] + outline_size
        ]

        # First up, build the actual circle that is the key and will
        # contain the stimulus. Order is important here, as shapes built
        # on top of each other will overlap/overdraw.
        self.mastercanvas.create_oval(
            outline_coords_list,
            outline="black",
            fill="black",
            tag="key")

        # Stimulus image .png
        cx = (key_coord_list[0] + key_coord_list[2]) // 2
        cy = (key_coord_list[1] + key_coord_list[3]) // 2
        img = self.stimulus_images.get(self.trial_type)
        if img:
            # draw the PNG centered in the key circle
            self.mastercanvas.create_image(
                cx, cy,
                image=img,
                anchor="center",
                tag="key")

        # redraw the fine outline around the key (inner circle)
        self.mastercanvas.create_oval(
            key_coord_list,
            outline="black",
            fill="",
            tag="key")

        # Then create the midpoint...
        self.mastercanvas.create_oval(
            midpoint_coord_list,
            fill="black",
            outline="black",
            tag="key")

        # Then bind a function to each key press!
        self.mastercanvas.tag_bind(
            "key", "<Button-1>",
            lambda event, event_type="key_peck": self.key_press(event, event_type))
            
        # Lastly, start a timer for the trial
        self.trial_timer = self.root.after(self.trial_timer_duration,
                                   self.calculate_trial_outcome)

    def key_press(self, event, event_type):
        # This is the function that is called whenever a key is pressed. It
        # simply increments the counter and writes a line of data.
        # Add to peck counter
        self.trial_peck_counter += 1
        # Write data for the peck
        self.write_data(event, event_type)
    

    def background_press(self, event):
        # This is the function that is called whenever the background is
        # pressed. It simply increments the counter and writes a line of data.
        # Add to background counter
        self.background_peck_counter += 1
        # Write data for the peck
        self.write_data(event, "background_peck")
    
    def calculate_trial_outcome(self):
    # This function is called once the 10s timer elapses and calculates
    # whether the trial will be reinforced or not.
    
        self.clear_canvas()
    
        # If INS/OMS trial, reinforcement is probabilistic
        # Extract the RR value from the trial type (e.g., INS_2 → rr_sched = 2)
        rr_sched = int(self.trial_type.split("_")[1])  # Extract 2, 5, 20, or 50       

        # Determine default reinforcement status
        if "INS" in self.trial_type:
                reinforced = False
        elif "OMS" in self.trial_type:
                reinforced = True

        # ─────────────────────────────────────────────────────────────
        # CHANGE: Count *all* pecks (key + background) toward RR rolls
        # ─────────────────────────────────────────────────────────────
        total_pecks = self.trial_peck_counter + self.background_peck_counter

        # Roll a dice a number of times equal to the number of pecks in the trial
        for _ in range(total_pecks): 
            if choice(range(rr_sched)) == 0:  # Simulates a die roll (0 = reinforcement occurs/cancelled)
                if "INS" in self.trial_type:
                    reinforced = True
                elif "OMS" in self.trial_type:
                    reinforced = False
        
        # If a reinforcement is earned...
        if reinforced:
            self.write_data(None, "reinforced_trial")
            if not operant_box_version or self.subject_ID == "TEST":
                self.mastercanvas.create_text(512,374,
                                              fill="white",
                                              font="Times 25 italic bold", 
                                              text=f"Trial Reinforced \nFood accessible ({int(self.hopper_duration/1000)} s)") # just onscreen feedback
            
            # Next send output to the box's hardware
            if operant_box_version:
                rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
                rpi_board.write(hopper_light_GPIO_num,
                                True) # Turn off the house light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_up_val) # Move hopper to up position
            
            self.root.after(self.hopper_duration, lambda: self.ITI())
        
        # If not reinforced, just proceed to the ITI
        else:
            self.write_data(None, "nonreinforced_trial")
            self.ITI()
        
        

    # %% Outside of the main loop functions, there are several additional
    # repeated functions that are called either outside of the loop or 
    # multiple times across phases.
    
    def change_cursor_state(self):
        # This function toggles the cursor state on/off. 
        # May need to update accessibility settings on your machince.
        if self.cursor_visible: # If cursor currently on...
            self.root.config(cursor="none") # Turn off cursor
            print("### Cursor turned off ###")
            self.cursor_visible = False
        else: # If cursor currently off...
            self.root.config(cursor="") # Turn on cursor
            print("### Cursor turned on ###")
            self.cursor_visible = True
    
    def clear_canvas(self):
         # This is by far the most called function across the program. It
         # deletes all the objects currently on the Canvas. A finer point to 
         # note here is that objects still exist onscreen if they are covered
         # up (rendering them invisible and inaccessible); if too many objects
         # are stacked upon each other, it can may be too difficult to track/
         # project at once (especially if many of the objects have functions 
         # tied to them. Therefore, its important to frequently clean up the 
         # Canvas by literally deleting every element.
        try:
            self.mastercanvas.delete("all")
        except TclError:
            print("No screen to exit")
        
    def exit_program(self, event): 
        # This function can be called two different ways: automatically (when
        # time/reinforcer session constraints are reached) or manually (via the
        # "End Program" button in the control panel or bound "esc" key).
            
        # The program does a few different things:
        #   1) Return hopper to down state, in case session was manually ended
        #       during reinforcement (it shouldn't be)
        #   2) Turn cursor back on
        #   3) Writes compiled data matrix to a .csv file 
        #   4) Destroys the Canvas object 
        #   5) Calls the Paint object, which creates an onscreen Paint Canvas.
        #       In the future, if we aren't using the paint object, we'll need 
        #       to 
        def other_exit_funcs():
            if operant_box_version:
                rpi_board.write(hopper_light_GPIO_num,
                                False) # turn off hopper light
                rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val) # set hopper to down state
                sleep(1) # Sleep for 1 s
                rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                            False)
                rpi_board.set_PWM_frequency(servo_GPIO_num,
                                            False)
                rpi_board.stop() # Kill RPi board
                
                # root.after_cancel(AFTER)
                if not self.cursor_visible:
                	self.change_cursor_state() # turn cursor back on, if applicable
            self.write_comp_data(True) # write data for end of session
            self.root.destroy() # destroy Canvas
            print("\n GUI window exited")
            
        self.clear_canvas()
        other_exit_funcs()
        print("\n You may now exit the terminal and operater windows now.")
        if operant_box_version:
            polygon_fill.main(self.subject_ID) # call paint object
        
    
    def write_data(self, event, outcome, hidden_patch="NA"):
            # This function writes a new data line after EVERY peck. Data is
            # organized into a matrix (just a list/vector with two dimensions,
            # similar to a table). This matrix is appended to throughout the 
            # session, then written to a .csv once at the end of the session.
            if event != None: 
                x, y = event.x, event.y
            else: # There are certain data events that are not pecks.
                x, y = "NA", "NA"   
                
            print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | {self.trial_type:^5} | {str(datetime.now() - self.start_time)}")
            # print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | Target: {self.current_target_location: ^2} | {str(datetime.now() - self.start_time)}")
            self.session_data_frame.append([
                str(datetime.now() - self.start_time), # SessionTime
                x,                                     # Xcord
                y,                                     # Ycord
                outcome,                               # Event
                round((time() - self.trial_start - (self.ITI_duration/1000)), 5),  # TrialTime
                self.trial_assignment_list[self.current_trial_counter - 1], # TrialType
                self.trial_peck_counter,              # TargetPeckNum
                self.background_peck_counter,         # BackgroundPeckNum
                self.current_trial_counter,           # TrialNum 
                self.stimulus_assignments_dict[self.trial_type],  # TrialColor 
                self.subject_ID,                      # Subject 
                hidden_patch,                         # Hidden Patch
                date.today()                          # Date 
            ])
        
            header_list = ["SessionTime", "Xcord","Ycord", "Event", "TrialTime", 
                           "TrialType","TargetPeckNum", "BackgroundPeckNum",
                            "TrialNum", "TrialColor",
                           "Subject", "Date"] # Column headers

        
    def write_comp_data(self, SessionEnded):
        # The following function creates a .csv data document. It is either 
        # called after each trial during the ITI (SessionEnded ==False) or 
        # one the session finishes (SessionEnded). If the first time the 
        # function is called, it will produce a new .csv out of the
        # session_data_matrix variable, named after the subject, date, and
        # training phase. Consecutive iterations of the function will simply
        # write over the existing document.
        if SessionEnded:
            self.write_data(None, "SessionEnds") # Writes end of session to df
        if self.record_data : # If experimenter has choosen to automatically record data in seperate sheet:
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P003Fc_data.csv"
            # This loop writes the data in the matrix to the .csv              
            edit_myFile = open(myFile_loc, 'w', newline='')
            with edit_myFile as myFile:
                w = writer(myFile, quoting=QUOTE_MINIMAL)
                w.writerows(self.session_data_frame) # Write all event/trial data 
            print(f"\n- Data file written to {myFile_loc}")
                
#%% Finally, this is the code that actually runs:
try:   
    if __name__ == '__main__':
        cp = ExperimenterControlPanel()
except:
    # If an unexpected error, make sure to clean up the GPIO board
    if operant_box_version:
        rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                    False)
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    False)
        rpi_board.stop()

