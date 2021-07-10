from ast import literal_eval
with open('config.py', encoding='utf-8-sig') as f:
    text = f.read()
    exec(text)


def get_all_config_options(text):
    result = []
    N = len(text)
    for i in range(N):
        current = text[i]
        if current == '\n':
            if i + 1 < N:
                next_character = text[i + 1]
                if next_character.isalpha():
                    inds = text[i + 1:].index('=') - 1
                    current_config_options = text[i + 1:i + 1 + inds]
                    result.append(current_config_options)
    return result


def change(var, new, is_str=True):
    text = open('config.py', encoding='utf-8').read()
    text_ls = list(text)
    var_len = len(var) + 1
    var_ind = text.index('\n' + var + ' ') + var_len
    current_var_ind = all_config_options_ind[var]
    if current_var_ind < len(all_config_options) - 1:
        next_var = config_original[current_var_ind + 1]
        next_var_ind = text.index('\n' + next_var + ' ')
        next_comments_ind = text[var_ind:].find('\n\n')
        if next_comments_ind != -1:
            next_comments_ind += var_ind
            if next_comments_ind < next_var_ind:
                next_var_ind = next_comments_ind
    else:
        next_var_ind = -1
    if is_str:
        text_ls[var_ind:next_var_ind] = f" = '{new}'"
    else:
        text_ls[var_ind:next_var_ind] = f" = {new}"
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(''.join(text_ls))


class Root2(Toplevel):
    def __init__(self):
        super(Root2, self).__init__(bg=root.background_color)
        self.protocol("WM_DELETE_WINDOW", root.close_visualize_config_box)
        self.title("Settings")
        self.minsize(800, 600)
        self.wm_iconbitmap('piano.ico')
        self.config_options_bar = Scrollbar(self)
        self.config_options_bar.place(x=235, y=120, height=170, anchor=CENTER)
        self.choose_config_options = Listbox(
            self, yscrollcommand=self.config_options_bar.set)
        self.choose_config_options.bind('<<ListboxSelect>>',
                                        self.show_current_config_options)
        global all_config_options
        all_config_options = get_all_config_options(text)
        self.options_num = len(all_config_options)
        self.all_config_options = all_config_options
        global all_config_options_ind
        all_config_options_ind = {
            all_config_options[i]: i
            for i in range(self.options_num)
        }
        global config_original
        config_original = all_config_options.copy()
        all_config_options.sort(key=lambda s: s.lower())
        global alpha_config
        alpha_config = all_config_options.copy()
        for k in all_config_options:
            self.choose_config_options.insert(END, k)
        self.choose_config_options.place(x=0, y=30, width=220)
        self.config_options_bar.config(
            command=self.choose_config_options.yview)
        self.config_name = ttk.Label(self, text='')
        self.config_name.place(x=300, y=20)
        self.config_contents = Text(self,
                                    undo=True,
                                    autoseparators=True,
                                    maxundo=-1)
        self.config_contents.bind('<KeyRelease>', self.config_change)
        self.config_contents.place(x=350, y=50, width=400, height=400)
        self.choose_filename_button = ttk.Button(self,
                                                 text='choose filename',
                                                 command=self.choose_filename)
        self.choose_directory_button = ttk.Button(
            self, text='choose directory', command=self.choose_directory)
        self.choose_filename_button.place(x=0, y=250, width=120)
        self.choose_directory_button.place(x=0, y=320, width=120)
        self.save = ttk.Button(self, text="save", command=self.save_current)
        self.save.place(x=0, y=400)
        self.saved_text = ttk.Label(self, text='saved')
        self.search_text = ttk.Label(self, text='search for config options')
        self.search_text.place(x=0, y=450)
        self.search_contents = StringVar()
        self.search_contents.trace_add('write', self.search)
        self.search_entry = Entry(self, textvariable=self.search_contents)
        self.search_entry.place(x=0, y=480)
        self.search_inds = 0
        self.up_button = ttk.Button(
            self,
            text='Previous',
            command=lambda: self.change_search_inds(-1),
            width=8)
        self.down_button = ttk.Button(
            self,
            text='Next',
            command=lambda: self.change_search_inds(1),
            width=8)
        self.up_button.place(x=170, y=480)
        self.down_button.place(x=250, y=480)
        self.search_inds_list = []
        self.value_dict = {i: str(eval(i)) for i in all_config_options}
        self.choose_bool1 = ttk.Button(
            self, text='True', command=lambda: self.insert_bool('True'))
        self.choose_bool2 = ttk.Button(
            self, text='False', command=lambda: self.insert_bool('False'))
        self.choose_bool1.place(x=120, y=270)
        self.choose_bool2.place(x=220, y=270)
        self.change_sort_button = ttk.Button(self,
                                             text="sort in alphabetical order",
                                             command=self.change_sort)
        self.sort_mode = 0
        self.change_sort_button.place(x=150, y=400, width=180)

    def change_sort(self):
        global all_config_options
        if self.sort_mode == 0:
            self.sort_mode = 1
            self.change_sort_button.config(text='sort in order of appearance')
            all_config_options = config_original.copy()
            self.choose_config_options.delete(0, END)
            for k in all_config_options:
                self.choose_config_options.insert(END, k)
        else:
            self.sort_mode = 0
            self.change_sort_button.config(text='sort in alphabetical order')
            all_config_options = alpha_config.copy()
            self.choose_config_options.delete(0, END)
            for k in all_config_options:
                self.choose_config_options.insert(END, k)
        self.search()

    def insert_bool(self, content):
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, content)
        self.config_change(0)

    def config_change(self, e):
        try:
            current = self.config_contents.get('1.0', 'end-1c')
            current = literal_eval(current)
            if type(current) == str:
                current = f"'{current}'"
            current_config = self.choose_config_options.get(ANCHOR)
            exec(f'{current_config} = {current}', globals())
        except:
            pass

    def change_search_inds(self, num):
        self.search_inds += num
        if self.search_inds < 0:
            self.search_inds = 0
        if self.search_inds_list:
            search_num = len(self.search_inds_list)
            if self.search_inds >= search_num:
                self.search_inds = search_num - 1
            first = self.search_inds_list[self.search_inds]
            self.choose_config_options.selection_clear(0, END)
            self.choose_config_options.selection_set(first)
            self.choose_config_options.selection_anchor(first)
            self.choose_config_options.see(first)
            self.show_current_config_options(0)

    def search(self, *args):
        current = self.search_entry.get()
        self.search_inds_list = [
            i for i in range(self.options_num)
            if current in all_config_options[i]
        ]
        if self.search_inds_list:
            self.search_inds = 0
            first = self.search_inds_list[self.search_inds]
            self.choose_config_options.selection_clear(0, END)
            self.choose_config_options.selection_set(first)
            self.choose_config_options.selection_anchor(first)
            self.choose_config_options.see(first)
            self.show_current_config_options(0)
        else:
            self.choose_config_options.selection_clear(0, END)

    def show_current_config_options(self, e):
        current_config = self.choose_config_options.get(ANCHOR)
        if current_config:
            self.config_name.configure(text=current_config)
            self.config_contents.delete('1.0', END)
            current_config_value = eval(current_config)
            if type(current_config_value) == str:
                current_config_value = f"'{current_config_value}'"
            else:
                current_config_value = str(current_config_value)
            self.config_contents.insert(END, current_config_value)

    def choose_filename(self):
        filename = filedialog.askopenfilename(parent=self,
                                              initialdir='.',
                                              title="choose filename",
                                              filetypes=(("all files",
                                                         "*.*"), ))
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, f"'{filename}'")
        self.config_change(0)

    def choose_directory(self):
        directory = filedialog.askdirectory(
            parent=self,
            initialdir='.',
            title="choose directory",
        )
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, f"'{directory}'")
        self.config_change(0)

    def show_saved(self):
        self.saved_text.place(x=140, y=350)
        self.after(1000, self.saved_text.place_forget)

    def save_current(self):
        changed = False
        for each in all_config_options:
            current_value = eval(each)
            current_value_str = str(current_value)
            before_value = self.value_dict[each]
            if current_value_str != before_value:
                change(each, current_value_str, type(current_value) == str)
                self.value_dict[each] = current_value_str
                changed = True
        if changed:
            self.show_saved()


root.visualize_config_window = Root2()
