""" Audio device dialog. """

###########
# Imports #
###########
# Import GUI packages
import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip

# Import audio packages
import sounddevice as sd


#########
# BEGIN #
#########
class AudioDialog(tk.Toplevel):
    """ Audio device dialog. """
    def __init__(self, parent, sessionpars, *args, **kwargs):
        super().__init__(parent, *args, *kwargs)

        # Assign variables
        self.parent = parent
        self.sessionpars = sessionpars

        # Window setup
        self.withdraw()
        self.focus()
        self.title("Audio Settings")
        self.resizable(False, False)
        self.grab_set() # Disable root window (toplevel as modal window)

        # Get data
        self.devices = self._query_audio_devices()

        # Draw widgets
        self._draw_widgets()

        # Center calibration window dialog
        self.center_window()


    def _draw_widgets(self):
        """ Draw widgets to window. """
        #################
        # Custom Styles #
        #################
        self.style = ttk.Style()
        self.style.configure(
            'Bold.TLabel', 
            font=('TKDefaultFont', 10, 'bold')
        )


        ##########
        # Frames #
        ##########
        # Options for label frames
        options = {'padx':10, 'pady':10}

        # Channel routing entry box
        lfrm_routing = ttk.LabelFrame(self, text="Channel Routing")
        lfrm_routing.grid(column=5, row=5, **options, sticky='we')
        lfrm_routing.columnconfigure(10, weight=1)

        # Audio device table
        self.frm_tree = ttk.Frame(self)
        self.frm_tree.grid(column=5, row=10, **options)

        # Submit button
        frm_submit = ttk.Frame(self)
        frm_submit.grid(column=5, row=15, **options)

        ###########
        # Widgets #
        ###########
        tt_delay = 1000 #ms
        
        # Routing
        # Label
        lbl_routing = ttk.Label(lfrm_routing, text="Channels/Speakers:")
        lbl_routing.grid(column=5, row=5, padx=5, pady=10, sticky='e')
        routing_tt = Hovertip(
            anchor_widget=lbl_routing,
            text="Channel(s) over which to present audio."\
                + "\nSeparate multiple channels with a space: 1 2 3.",
            hover_delay=tt_delay
        )
        self.routing_var = tk.StringVar(
            value=self.sessionpars['channel_routing'].get())
        # Entry
        ttk.Entry(lfrm_routing, textvariable=self.routing_var, width=15
                  ).grid(column=10, row=5, sticky='w')
        
        # Display current audio device
        # Label
        ttk.Label(lfrm_routing, text="Audio Device:").grid(column=5, 
            row=10, padx=5, pady=(0,10), sticky='e'
        )
        # Entry
        audio_device_name = self._get_audio_device_name()
        self.audio_var = tk.StringVar(value=audio_device_name)
        ttk.Entry(lfrm_routing, textvariable=self.audio_var, state='disabled'
        ).grid(row=10, column=10, pady=(0,10), sticky='we', padx=(0,10))

        # Create treeview
        # Treeview instructions label
        ttk.Label(self.frm_tree, text="Click on an audio device below to " +
            "select it.", style='Bold.TLabel').grid(row=5, column=5)
        self.tree = self._create_tree_widget()

        # Submit button
        ttk.Button(frm_submit, text="Submit", command=self._on_submit).grid(
            column=5, columnspan=15, row=5)
        

    def _get_audio_device_name(self):
        """ Get the audio device name from the device ID. """
        try:
            audio_device_name = [item[1] for item in self.devices if \
                item[0] == self.sessionpars['audio_device'].get()][0]
        except IndexError:
            audio_device_name = "No audio device selected"

        return audio_device_name


    def _create_tree_widget(self):
        """ Create and populate treeview. """
        columns = ('device_id', 'device_name', 'channels_out')
        tree = ttk.Treeview(self.frm_tree, columns=columns, show='headings')

        # Define headings
        tree.heading('device_id', text='Device ID')
        tree.heading('device_name', text='Device Name')
        tree.heading('channels_out', text='Outputs')

        # Define columns
        tree.column('device_id', width=60, anchor=tk.CENTER)
        tree.column('device_name', width=400, anchor=tk.W)
        tree.column('channels_out', width=60, anchor=tk.CENTER)

        tree.bind('<<TreeviewSelect>>', self._item_selected)
        tree.grid(row=10, column=5, sticky=tk.NSEW)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(self.frm_tree, orient=tk.VERTICAL, 
            command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=10, column=6, sticky='ns')

        # Populate tree
        for self.device in self.devices:
            tree.insert('', tk.END, values=self.device)

        return tree


    def _query_audio_devices(self):
        """ Create list of tuples with specified device information. """
        # Get list of audio devices
        deviceList = sd.query_devices()
        #print("\naudioview: Full audio device list:")
        #print(deviceList)

        # Create list of tuples with device info
        devices = []
        for ii in range(0,len(deviceList)):
            if deviceList[ii]['max_output_channels'] > 0:
                devices.append((ii, deviceList[ii]['name'], 
                                deviceList[ii]['max_output_channels']))
        return devices


    #################
    # General Funcs #
    #################
    def center_window(self):
        """ Center the TopLevel window over the root window. """
        # Get updated window size (after drawing widgets)
        self.update_idletasks()

        # Calculate the x and y coordinates to center the window
        x = self.parent.winfo_x() \
            + (self.parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = self.parent.winfo_y() \
            + (self.parent.winfo_height() - self.winfo_reqheight()) // 2

        # Set the window position
        self.geometry("+%d+%d" % (x, y))

        # Display window
        self.deiconify()


    def _item_selected(self, event):
        """ Update audio device ID with the device selected
            from the tree.
        """
        for selected_item in self.tree.selection():
            item = self.tree.item(selected_item)
            record = item['values']

            # Update sessionpars with device id
            self.sessionpars['audio_device'].set(record[0])

            self.audio_var.set(record[1])


    def _on_submit(self):
        """ Update channel routing.
            Send submit event to controller. 
            Close window.
        """
        print("\naudioview: Sending save audio device event...")
        self.sessionpars['channel_routing'].set(self.routing_var.get())
        self.parent.event_generate('<<AudioDialogSubmit>>')
        self.destroy()
