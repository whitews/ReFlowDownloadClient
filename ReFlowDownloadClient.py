import Tkinter
import ttk
import tkMessageBox
from PIL import Image, ImageTk
import re
import sys
import os

import reflowrestclient.utils as rest

VERSION = '0.1'

if hasattr(sys, '_MEIPASS'):
    # for PyInstaller 2.0
    # noinspection PyProtectedMember
    RESOURCE_DIR = sys._MEIPASS
else:
    # for development
    RESOURCE_DIR = 'resources'

LOGO_PATH = os.path.join(RESOURCE_DIR, 'reflow_text.gif')
if sys.platform == 'win32':
    ICON_PATH = os.path.join(RESOURCE_DIR, 'reflow2.ico')
elif sys.platform == 'darwin':
    ICON_PATH = os.path.join(RESOURCE_DIR, 'reflow.icns')
elif sys.platform == 'linux2':
    ICON_PATH = None  # haven't figured out icons on linux yet : (
else:
    sys.exit("Your operating system is not supported.")

BACKGROUND_COLOR = '#ededed'
INACTIVE_BACKGROUND_COLOR = '#e2e2e2'
INACTIVE_FOREGROUND_COLOR = '#767676'
BORDER_COLOR = '#bebebe'
HIGHLIGHT_COLOR = '#5489b9'
ROW_ALT_COLOR = '#f3f6fa'
SUCCESS_FOREGROUND_COLOR = '#00cc00'
ERROR_FOREGROUND_COLOR = '#ff0000'

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 600

PAD_SMALL = 2
PAD_MEDIUM = 4
PAD_LARGE = 8
PAD_EXTRA_LARGE = 14

LABEL_WIDTH = 16


class MyCheckbutton(Tkinter.Checkbutton):
    def __init__(self, *args, **kwargs):
        # We need to save the full path to populate the tree item later
        # Pop the value b/c the parent init is not expecting the kwarg
        self.file_path = kwargs.pop('file_path')

        # we create checkboxes dynamically and need to control the value
        # so we need to access the widget's value using our own attribute
        self.var = kwargs.get('variable', Tkinter.IntVar())
        kwargs['variable'] = self.var
        Tkinter.Checkbutton.__init__(self, *args, **kwargs)

    def is_checked(self):
        return self.var.get()

    def mark_checked(self):
        self.var.set(1)

    def mark_unchecked(self):
        self.var.set(0)


class Application(Tkinter.Frame):

    def __init__(self, master):

        self.host = None
        self.username = None
        self.token = None

        # Using the names (project, site, etc.) as the key, pk as the value
        # for the choice dictionaries below.
        # The names need to be unique (and they should be) and
        # it's more convenient to lookup by key using the name.
        self.project_dict = dict()
        self.site_dict = dict()
        self.subject_dict = dict()
        self.visit_dict = dict()
        self.site_panel_dict = dict()
        self.stimulation_dict = dict()

        # dict of ChosenFile objects, key is file path, value is ChosenFile
        self.file_dict = dict()

        # start the metadata menus
        self.project_menu = None
        self.project_selection = Tkinter.StringVar()
        self.project_selection.trace("w", self.update_metadata)

        self.site_menu = None
        self.site_selection = Tkinter.StringVar()
        self.site_selection.trace("w", self.update_site_metadata)

        self.subject_menu = None
        self.subject_selection = Tkinter.StringVar()

        self.visit_menu = None
        self.visit_selection = Tkinter.StringVar()

        self.stimulation_menu = None
        self.stimulation_selection = Tkinter.StringVar()

        self.site_panel_menu = None
        self.site_panel_selection = Tkinter.StringVar()

        # can't call super on old-style class, call parent init directly
        Tkinter.Frame.__init__(self, master)
        if sys.platform == 'linux2':
            pass
        else:
            self.master.iconbitmap(ICON_PATH)
        self.master.title('ReFlow Download Client - ' + VERSION)
        self.master.minsize(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.master.config(bg=BACKGROUND_COLOR)

        self.menu_bar = Tkinter.Menu(master)
        self.master.config(menu=self.menu_bar)

        self.download_progress_bar = None
        self.file_list_canvas = None

        self.s = ttk.Style()
        self.s.map(
            'Inactive.TButton',
            foreground=[('disabled', INACTIVE_FOREGROUND_COLOR)])

        self.pack()

        self.login_frame = Tkinter.Frame(bg=BACKGROUND_COLOR)
        self.logo_image = ImageTk.PhotoImage(Image.open(LOGO_PATH))
        self.load_login_frame()
        # self.load_main_frame()

    def load_login_frame(self):
        # noinspection PyUnusedLocal
        def login(*args):
            host_text = host_entry.get()
            self.username = user_entry.get()
            password = password_entry.get()

            # remove 'http://' or trailing slash from host text if present
            matches = re.search('^(https://)?([^/]+)(/)*', host_text)

            try:
                self.host = matches.groups()[1]
                self.token = rest.get_token(self.host, self.username, password)
            except Exception, e:
                print e
            if not self.token:
                tkMessageBox.showwarning(
                    'Login Failed',
                    'Are the hostname, username, and password are correct?')
                return
            self.login_frame.destroy()
            self.master.unbind('<Return>')
            self.load_main_frame()

        self.master.bind('<Return>', login)

        logo_label = Tkinter.Label(self.login_frame, image=self.logo_image)
        logo_label.config(bg=BACKGROUND_COLOR)
        logo_label.pack(side='top', pady=PAD_EXTRA_LARGE)

        host_entry_frame = Tkinter.Frame(self.login_frame, bg=BACKGROUND_COLOR)
        host_label = Tkinter.Label(
            host_entry_frame,
            text='Hostname',
            bg=BACKGROUND_COLOR,
            width=8,
            anchor='e')
        host_label.pack(side='left')
        host_entry = Tkinter.Entry(
            host_entry_frame,
            highlightbackground=BACKGROUND_COLOR,
            width=24)
        host_entry.pack(padx=PAD_SMALL)
        host_entry_frame.pack(pady=PAD_SMALL)

        user_entry_frame = Tkinter.Frame(self.login_frame, bg=BACKGROUND_COLOR)
        user_label = Tkinter.Label(
            user_entry_frame,
            text='Username',
            bg=BACKGROUND_COLOR,
            width=8,
            anchor='e')
        user_label.pack(side='left')
        user_entry = Tkinter.Entry(
            user_entry_frame,
            highlightbackground=BACKGROUND_COLOR,
            width=24)
        user_entry.pack(padx=PAD_SMALL)
        user_entry_frame.pack(pady=PAD_SMALL)

        password_entry_frame = Tkinter.Frame(
            self.login_frame,
            bg=BACKGROUND_COLOR)
        password_label = Tkinter.Label(
            password_entry_frame,
            text='Password',
            bg=BACKGROUND_COLOR,
            width=8,
            anchor='e')
        password_label.pack(side='left')
        password_entry = Tkinter.Entry(
            password_entry_frame,
            show='*',
            highlightbackground=BACKGROUND_COLOR,
            width=24)
        password_entry.pack(padx=PAD_SMALL)
        password_entry_frame.pack(pady=PAD_SMALL)

        login_button_frame = Tkinter.Frame(
            self.login_frame,
            bg=BACKGROUND_COLOR)
        login_button_label = Tkinter.Label(
            login_button_frame,
            bg=BACKGROUND_COLOR)
        login_button = ttk.Button(
            login_button_label,
            text='Login',
            command=login)
        login_button.pack()
        login_button_label.pack(side='right')
        login_button_frame.pack(fill='x')

        self.login_frame.place(in_=self.master, anchor='c', relx=.5, rely=.5)

    def load_main_frame(self):
        main_frame = Tkinter.Frame(self.master, bg=BACKGROUND_COLOR)
        main_frame.pack(
            fill='both',
            expand=True,
            anchor='n',
            padx=PAD_MEDIUM,
            pady=PAD_MEDIUM
        )

        top_frame = Tkinter.Frame(
            main_frame,
            bg=BACKGROUND_COLOR)
        top_frame.pack(
            fill='x',
            expand=False,
            anchor='n'
        )

        middle_frame = Tkinter.Frame(main_frame, bg=BACKGROUND_COLOR)
        middle_frame.pack(
            fill='both',
            expand=True,
            anchor='n'
        )

        bottom_frame = Tkinter.Frame(main_frame, bg=BACKGROUND_COLOR)
        bottom_frame.pack(
            fill='x',
            expand=False,
            anchor='n',
            padx=0,
            pady=0
        )

        # Action buttons all go in top frame
        file_clear_all_button = ttk.Button(
            top_frame,
            text='Select All',
            command=self.select_all_files
        )

        file_clear_all_button.pack(side='right')

        middle_left_frame = Tkinter.Frame(
            middle_frame,
            bg=BACKGROUND_COLOR
        )
        middle_left_frame.pack(
            fill='both',
            expand=False,
            side='left'
        )

        middle_right_frame = Tkinter.Frame(
            middle_frame,
            bg=BACKGROUND_COLOR
        )
        middle_right_frame.pack(
            fill='both',
            expand=True,
            side='right'
        )

        # Metadata frame - for choosing project/subject/site etc.
        metadata_frame = Tkinter.LabelFrame(
            middle_left_frame,
            bg=BACKGROUND_COLOR
        )
        metadata_frame.pack(
            fill='x',
            expand=False,
            anchor='n',
            ipadx=PAD_MEDIUM,
            ipady=PAD_MEDIUM
        )
        metadata_frame.config(text="Filter FCS Files")

        # Download options frame
        download_options_frame = Tkinter.LabelFrame(
            middle_left_frame,
            bg=BACKGROUND_COLOR
        )
        download_options_frame.pack(
            fill='both',
            expand=False,
            anchor='n',
            ipadx=PAD_MEDIUM,
            ipady=PAD_MEDIUM
        )
        download_options_frame.config(text="Download Options")

        # overall project frame
        project_frame = Tkinter.Frame(
            metadata_frame,
            bg=BACKGROUND_COLOR)

        # project label frame
        project_chooser_label_frame = Tkinter.Frame(
            project_frame,
            bg=BACKGROUND_COLOR)
        project_chooser_label = Tkinter.Label(
            project_chooser_label_frame,
            text='Project:',
            bg=BACKGROUND_COLOR,
            width=LABEL_WIDTH,
            anchor=Tkinter.E)
        project_chooser_label.pack(side='left')
        project_chooser_label_frame.pack(side='left', fill='x')

        # project chooser listbox frame
        project_chooser_frame = Tkinter.Frame(
            project_frame,
            bg=BACKGROUND_COLOR)
        self.project_menu = Tkinter.OptionMenu(
            project_chooser_frame,
            self.project_selection,
            '')
        self.project_menu.config(
            bg=BACKGROUND_COLOR,
            width=36)
        self.project_menu.pack(fill='x', expand=True)
        project_chooser_frame.pack(fill='x', expand=True)

        project_frame.pack(side='top', fill='x', expand=True)

        # overall site frame
        site_frame = Tkinter.Frame(metadata_frame, bg=BACKGROUND_COLOR)

        # site label frame
        site_chooser_label_frame = Tkinter.Frame(
            site_frame,
            bg=BACKGROUND_COLOR)
        site_chooser_label = Tkinter.Label(
            site_chooser_label_frame,
            text='Site:',
            bg=BACKGROUND_COLOR,
            width=LABEL_WIDTH,
            anchor=Tkinter.E)
        site_chooser_label.pack(side='left')
        site_chooser_label_frame.pack(side='left', fill='x')

        # site chooser listbox frame
        site_chooser_frame = Tkinter.Frame(
            site_frame,
            bg=BACKGROUND_COLOR)
        self.site_menu = Tkinter.OptionMenu(
            site_chooser_frame,
            self.site_selection,
            '')
        self.site_menu.config(bg=BACKGROUND_COLOR)
        self.site_menu.pack(fill='x', expand=True)
        site_chooser_frame.pack(fill='x', expand=True)

        site_frame.pack(side='top', fill='x', expand=True)

        # overall subject frame
        subject_frame = Tkinter.Frame(metadata_frame, bg=BACKGROUND_COLOR)

        # subject label frame
        subject_chooser_label_frame = Tkinter.Frame(
            subject_frame,
            bg=BACKGROUND_COLOR)
        subject_chooser_label = Tkinter.Label(
            subject_chooser_label_frame,
            text='Subject:',
            bg=BACKGROUND_COLOR,
            width=LABEL_WIDTH,
            anchor=Tkinter.E)
        subject_chooser_label.pack(side='left')
        subject_chooser_label_frame.pack(side='left', fill='x')

        # subject chooser listbox frame
        subject_chooser_frame = Tkinter.Frame(
            subject_frame,
            bg=BACKGROUND_COLOR)
        self.subject_menu = Tkinter.OptionMenu(
            subject_chooser_frame,
            self.subject_selection,
            '')
        self.subject_menu.config(bg=BACKGROUND_COLOR)
        self.subject_menu.pack(fill='x', expand=True)
        subject_chooser_frame.pack(fill='x', expand=True)

        subject_frame.pack(side='top', fill='x', expand=True)

        # overall visit frame
        visit_frame = Tkinter.Frame(metadata_frame, bg=BACKGROUND_COLOR)

        # visit label frame
        visit_chooser_label_frame = Tkinter.Frame(
            visit_frame,
            bg=BACKGROUND_COLOR)
        visit_chooser_label = Tkinter.Label(
            visit_chooser_label_frame,
            text='Visit:',
            bg=BACKGROUND_COLOR,
            width=LABEL_WIDTH,
            anchor=Tkinter.E)
        visit_chooser_label.pack(side='left')
        visit_chooser_label_frame.pack(side='left', fill='x')

        # visit chooser listbox frame
        visit_chooser_frame = Tkinter.Frame(visit_frame, bg=BACKGROUND_COLOR)
        self.visit_menu = Tkinter.OptionMenu(
            visit_chooser_frame,
            self.visit_selection,
            '')
        self.visit_menu.config(bg=BACKGROUND_COLOR)
        self.visit_menu.pack(fill='x', expand=True)
        visit_chooser_frame.pack(fill='x', expand=True)

        visit_frame.pack(side='top', fill='x', expand=True)

        # overall stimulation frame
        stimulation_frame = Tkinter.Frame(
            metadata_frame,
            bg=BACKGROUND_COLOR)

        # stimulation label frame
        stimulation_chooser_label_frame = Tkinter.Frame(
            stimulation_frame,
            bg=BACKGROUND_COLOR)
        stimulation_chooser_label = Tkinter.Label(
            stimulation_chooser_label_frame,
            text='Stimulation:',
            bg=BACKGROUND_COLOR,
            width=LABEL_WIDTH,
            anchor=Tkinter.E)
        stimulation_chooser_label.pack(side='left')
        stimulation_chooser_label_frame.pack(side='left', fill='x')

        # stimulation chooser listbox frame
        stimulation_chooser_frame = Tkinter.Frame(
            stimulation_frame,
            bg=BACKGROUND_COLOR)
        self.stimulation_menu = Tkinter.OptionMenu(
            stimulation_chooser_frame,
            self.stimulation_selection,
            '')
        self.stimulation_menu.config(bg=BACKGROUND_COLOR)
        self.stimulation_menu.pack(fill='x', expand=True)
        stimulation_chooser_frame.pack(fill='x', expand=True)

        stimulation_frame.pack(side='top', fill='x', expand=True)

        # overall site_panel frame
        site_panel_frame = Tkinter.Frame(
            metadata_frame,
            bg=BACKGROUND_COLOR)

        # site_panel label frame
        site_panel_chooser_label_frame = Tkinter.Frame(
            site_panel_frame,
            bg=BACKGROUND_COLOR)
        site_panel_chooser_label = Tkinter.Label(
            site_panel_chooser_label_frame,
            text='Site Panel:',
            bg=BACKGROUND_COLOR,
            width=LABEL_WIDTH,
            anchor=Tkinter.E)
        site_panel_chooser_label.pack(side='left')
        site_panel_chooser_label_frame.pack(side='left', fill='x')

        # site_panel chooser listbox frame
        site_panel_chooser_frame = Tkinter.Frame(
            site_panel_frame,
            bg=BACKGROUND_COLOR)
        self.site_panel_menu = Tkinter.OptionMenu(
            site_panel_chooser_frame,
            self.site_panel_selection,
            '')
        self.site_panel_menu.config(bg=BACKGROUND_COLOR)
        self.site_panel_menu.pack(fill='x', expand=True)
        site_panel_chooser_frame.pack(fill='x', expand=True)

        site_panel_frame.pack(side='top', fill='x', expand=True)

        self.load_user_projects()

        # start file chooser widgets
        file_chooser_frame = Tkinter.Frame(
            middle_right_frame,
            bg=BACKGROUND_COLOR
        )

        file_list_frame = Tkinter.Frame(
            file_chooser_frame,
            bg=BACKGROUND_COLOR,
            highlightcolor=HIGHLIGHT_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        file_scroll_bar = Tkinter.Scrollbar(
            file_list_frame,
            orient='vertical'
        )
        self.file_list_canvas = Tkinter.Canvas(
            file_list_frame,
            yscrollcommand=file_scroll_bar.set,
            relief='flat',
            borderwidth=0
        )
        self.file_list_canvas.bind('<MouseWheel>', self._on_mousewheel)
        file_scroll_bar.config(command=self.file_list_canvas.yview)
        file_scroll_bar.pack(side='right', fill='y')
        self.file_list_canvas.pack(
            fill='both',
            expand=True
        )
        file_list_frame.pack(
            fill='both',
            expand=True
        )
        file_chooser_frame.pack(
            fill='both',
            expand=True,
            anchor='n'
        )

        # Progress bar
        progress_frame = Tkinter.Frame(bottom_frame, bg=BACKGROUND_COLOR)
        self.download_progress_bar = ttk.Progressbar(progress_frame)
        self.download_progress_bar.pack(side='bottom', fill='x', expand=True)
        progress_frame.pack(
            fill='x',
            expand=False,
            anchor='s',
            padx=PAD_MEDIUM,
            pady=PAD_SMALL)

    def _on_mousewheel(self, event):
        self.file_list_canvas.yview_scroll(-event.delta, "units")

    def select_all_files(self):
        for k, v in self.file_list_canvas.children.items():
            if isinstance(v, MyCheckbutton):
                v.mark_checked()

    def load_user_projects(self):
        try:
            response = rest.get_projects(self.host, self.token)
        except Exception, e:
            print e
            return

        if 'data' not in response:
            return

        self.project_menu['menu'].delete(0, 'end')
        self.site_menu['menu'].delete(0, 'end')
        self.subject_menu['menu'].delete(0, 'end')
        self.visit_menu['menu'].delete(0, 'end')
        self.stimulation_menu['menu'].delete(0, 'end')
        self.site_panel_menu['menu'].delete(0, 'end')

        for result in response['data']:
            self.project_dict[result['project_name']] = result['id']
        for project_name in sorted(self.project_dict.keys()):
            self.project_menu['menu'].add_command(
                label=project_name,
                command=lambda value=project_name:
                self.project_selection.set(value))

    def load_project_sites(self, project_id):
        self.site_menu['menu'].delete(0, 'end')
        self.site_selection.set('')
        self.site_dict.clear()

        response = None
        try:
            response = rest.get_sites(
                self.host,
                self.token,
                project_pk=project_id)
        except Exception, e:
            print e

        if 'data' not in response:
            return

        for result in response['data']:
            self.site_dict[result['site_name']] = result['id']
        for site_name in sorted(self.site_dict.keys()):
            self.site_menu['menu'].add_command(
                label=site_name,
                command=lambda value=site_name:
                self.site_selection.set(value))

    def load_project_subjects(self, project_id):
        self.subject_menu['menu'].delete(0, 'end')
        self.subject_selection.set('')
        self.subject_dict.clear()

        response = None
        try:
            response = rest.get_subjects(
                self.host,
                self.token,
                project_pk=project_id)
        except Exception, e:
            print e

        if 'data' not in response:
            return

        for result in response['data']:
            self.subject_dict[result['subject_code']] = result['id']
        for subject_code in sorted(self.subject_dict.keys()):
            self.subject_menu['menu'].add_command(
                label=subject_code,
                command=lambda value=subject_code:
                self.subject_selection.set(value))

    def load_project_visits(self, project_id):
        self.visit_menu['menu'].delete(0, 'end')
        self.visit_selection.set('')
        self.visit_dict.clear()

        response = None
        try:
            response = rest.get_visit_types(
                self.host,
                self.token,
                project_pk=project_id)
        except Exception, e:
            print e

        if 'data' not in response:
            return

        for result in response['data']:
            self.visit_dict[result['visit_type_name']] = result['id']
        for visit_type_name in sorted(self.visit_dict.keys()):
            self.visit_menu['menu'].add_command(
                label=visit_type_name,
                command=lambda value=visit_type_name:
                self.visit_selection.set(value))

    def load_stimulations(self, project_id):
        self.stimulation_menu['menu'].delete(0, 'end')
        self.stimulation_selection.set('')
        self.stimulation_dict.clear()

        try:
            response = rest.get_stimulations(
                self.host,
                self.token,
                project_pk=project_id)
        except Exception, e:
            print e
            return

        if 'data' not in response:
            return

        for result in response['data']:
            self.stimulation_dict[result['stimulation_name']] = result['id']
        for stimulation in sorted(self.stimulation_dict.keys()):
            self.stimulation_menu['menu'].add_command(
                label=stimulation,
                command=lambda value=stimulation:
                self.stimulation_selection.set(value))

    def update_site_metadata(self, *args, **kwargs):
        self.site_panel_menu['menu'].delete(0, 'end')
        self.site_panel_selection.set('')
        self.site_panel_dict.clear()

        if not self.site_selection.get():
            return
        site_pk = self.site_dict[self.site_selection.get()]
        rest_args = [self.host, self.token]
        rest_kwargs = {'site_pk': site_pk}

        try:
            response = rest.get_site_panels(*rest_args, **rest_kwargs)
        except Exception, e:
            print e
            return

        if 'data' not in response:
            return

        for result in response['data']:
            self.site_panel_dict[result['name']] = result['id']
        for panel_name in sorted(self.site_panel_dict.keys()):
            self.site_panel_menu['menu'].add_command(
                label=panel_name,
                command=lambda value=panel_name:
                self.site_panel_selection.set(value))

    def update_metadata(*args):
        self = args[0]

        option_value = self.project_selection.get()

        if option_value in self.project_dict:
            self.load_project_sites(self.project_dict[option_value])
            self.load_project_subjects(self.project_dict[option_value])
            self.load_project_visits(self.project_dict[option_value])
            self.load_stimulations(self.project_dict[option_value])

        self.update_add_to_queue_button_state()

root = Tkinter.Tk()
app = Application(root)
app.mainloop()