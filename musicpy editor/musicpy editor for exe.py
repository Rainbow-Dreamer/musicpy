def print(obj):
    root.outputs.insert(END, str(obj))
    root.outputs.insert(END, '\n')


def direct_play(filename):
    if type(filename) == str:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
    else:
        try:
            result = BytesIO()
            filename.save(file=result)
            result.seek(0)
            pygame.mixer.music.load(result)
            result.close()
            pygame.mixer.music.play()
        except:
            pass


def play(chord1,
         tempo=80,
         track=0,
         channel=0,
         start_time=0,
         track_num=1,
         name='temp.mid',
         modes='quick',
         instrument=None,
         i=None,
         save_as_file=True,
         deinterleave=False):
    file = write(name,
                 chord1,
                 tempo,
                 track=0,
                 channel=0,
                 start_time=0,
                 track_num=1,
                 mode=modes,
                 instrument=instrument,
                 i=i,
                 save_as_file=save_as_file,
                 deinterleave=deinterleave)
    if save_as_file:
        result_file = name
        pygame.mixer.music.load(result_file)
        pygame.mixer.music.play()
    else:
        file.seek(0)
        pygame.mixer.music.load(file)
        file.close()
        pygame.mixer.music.play()


class Root(Tk):
    def __init__(self):
        super(Root, self).__init__()
        self.minsize(1200, 640)
        self.title('musicpy 编辑器')
        self.background_color = config_dict['background_color']
        self.foreground_color = config_dict['foreground_color']
        self.active_background_color = config_dict['active_background_color']
        self.day_color, self.night_color = config_dict['day_and_night_colors']
        self.search_highlight_color = config_dict['search_highlight_color']
        self.button_background_color = config_dict['button_background_color']
        self.active_foreground_color = config_dict['active_foreground_color']
        self.disabled_foreground_color = config_dict[
            'disabled_foreground_color']
        self.configure(background=self.background_color)
        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TButton',
                        background=self.background_color,
                        foreground=self.foreground_color,
                        width=10,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none')
        style.configure('TCheckbutton',
                        background=self.background_color,
                        foreground=self.foreground_color,
                        width=12,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none')
        style.configure('TLabel',
                        background=self.background_color,
                        foreground=self.foreground_color)
        style.configure('New.TButton',
                        background=self.button_background_color,
                        foreground=self.foreground_color,
                        width=10,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none')
        style.map('TButton',
                  background=[('active', self.active_background_color)])
        style.map('TCheckbutton',
                  background=[('active', self.active_background_color)])
        style.map('New.TButton',
                  background=[('active', self.active_background_color)])
        self.get_config_dict = copy(config_dict)
        self.get_config_dict = {
            i: str(j)
            for i, j in self.get_config_dict.items()
        }
        try:
            self.bg = PIL.Image.open(config_dict['background_image'])
            ratio = 600 / self.bg.height
            self.bg = self.bg.resize(
                (int(self.bg.width * ratio), int(self.bg.height * ratio)),
                PIL.Image.ANTIALIAS)
            self.bg = PIL.ImageTk.PhotoImage(self.bg)
            self.bg_label = ttk.Label(self, image=self.bg)
            bg_places = config_dict['background_places']
            self.bg_label.place(x=bg_places[0], y=bg_places[1])
        except:
            pass
        self.inputs_text = ttk.Label(self,
                                     text='请在这里输入 musicpy 音乐代码语句',
                                     background=self.background_color)
        self.inputs = Text(self,
                           wrap='none',
                           undo=True,
                           autoseparators=True,
                           maxundo=-1)
        self.font_type = config_dict['font_type']
        self.font_size = config_dict['font_size']
        self.inputs.configure(font=(self.font_type, self.font_size))
        self.inputs_text.place(x=0, y=30)
        self.inputs.place(x=0, y=60, width=700, height=200)
        inputs_v = ttk.Scrollbar(self,
                                 orient="vertical",
                                 command=self.inputs.yview)
        inputs_h = ttk.Scrollbar(self,
                                 orient="horizontal",
                                 command=self.inputs.xview)
        self.inputs.configure(yscrollcommand=inputs_v.set,
                              xscrollcommand=inputs_h.set)
        inputs_v.place(x=700, y=60, height=200)
        inputs_h.place(x=0, y=260, width=700)
        self.outputs_text = ttk.Label(self,
                                      text='在这里显示运行结果',
                                      background=self.background_color)
        self.outputs = Text(self, wrap='none')
        self.outputs.configure(font=(self.font_type, self.font_size))
        self.outputs_text.place(x=0, y=280)
        self.outputs.place(x=0, y=310, width=700, height=300)
        outputs_v = ttk.Scrollbar(self,
                                  orient="vertical",
                                  command=self.outputs.yview)
        outputs_h = ttk.Scrollbar(self,
                                  orient="horizontal",
                                  command=self.outputs.xview)
        self.outputs.configure(yscrollcommand=outputs_v.set,
                               xscrollcommand=outputs_h.set)
        outputs_v.place(x=700, y=310, height=300)
        outputs_h.place(x=0, y=600, width=700)
        self.run_button = ttk.Button(self, text='运行', command=self.runs)
        self.run_button.place(x=160, y=0)
        self.realtime = IntVar()
        self.realtime.set(1)
        self.realtime_box = ttk.Checkbutton(self,
                                            text='实时运行',
                                            variable=self.realtime,
                                            command=self.check_realtime)
        self.is_realtime = 1
        self.quit = False
        self.no_print = IntVar()
        self.no_print.set(1)
        self.print_box = ttk.Checkbutton(self,
                                         text='不使用 print',
                                         variable=self.no_print,
                                         command=self.check_print)
        self.auto = IntVar()
        self.auto.set(1)
        self.is_auto = 1
        self.auto_box = ttk.Checkbutton(self,
                                        text='自动补全',
                                        variable=self.auto,
                                        command=self.check_auto)
        self.is_grammar = 1
        self.grammar = IntVar()
        self.grammar.set(1)
        self.grammar_box = ttk.Checkbutton(self,
                                           text='语法高亮',
                                           variable=self.grammar,
                                           command=self.check_grammar)
        self.eachline_character = config_dict['eachline_character']
        self.pairing_symbols = config_dict['pairing_symbols']
        self.wraplines_number = config_dict['wraplines_number']
        self.wraplines_button = ttk.Button(self,
                                           text='自动换行',
                                           command=self.wraplines)
        self.realtime_box.place(x=400, y=0)
        self.auto_box.place(x=500, y=0)
        self.grammar_box.place(x=740, y=0)
        self.wraplines_button.place(x=750, y=350)
        self.print_box.place(x=620, y=0)

        self.save_button = ttk.Button(self,
                                      text='保存',
                                      command=self.save_current_file)
        self.save_button.place(x=80, y=0)
        self.is_print = 1
        self.pre_input = ''
        self.start = 0
        self.start2 = 0
        self.changed = False
        self.auto_complete_menu = Listbox(self)
        self.auto_complete_menu.bind("<<ListboxSelect>>",
                                     lambda e: self.enter_choose(e))
        self.update()
        self.select_ind = 0
        self.show_select = False
        self.bind('<Up>', lambda e: self.change_select(-1))
        self.bind('<Down>', lambda e: self.change_select(1))
        self.bind('<Left>', self.close_select)
        self.bind('<Right>', self.close_select)
        self.bind('<Return>', lambda e: self.get_current_select(e))
        self.file_top = ttk.Button(self,
                                   text='文件',
                                   command=self.file_top_make_menu)
        self.file_menu = Menu(
            self,
            tearoff=0,
            bg=self.background_color,
            activebackground=self.active_background_color,
            activeforeground=self.active_foreground_color,
            disabledforeground=self.disabled_foreground_color)
        self.file_menu.add_command(label='打开',
                                   command=self.openfile,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label='保存',
                                   command=self.save_current_file,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label='另存为',
                                   command=self.save,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label='设置',
                                   command=self.config_options,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label='导入midi文件',
                                   command=self.read_midi_file,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label='可视化钢琴设置',
                                   command=self.visualize_config,
                                   foreground=self.foreground_color)
        self.file_top.place(x=0, y=0)
        self.config_button = ttk.Button(self,
                                        text='设置',
                                        command=self.config_options)
        self.config_button.place(x=320, y=0)
        grammar_highlight = config_dict['grammar_highlight']
        for each in grammar_highlight:
            grammar_highlight[each].sort(key=lambda s: len(s), reverse=True)
        self.grammar_highlight = grammar_highlight
        for each in self.grammar_highlight:
            self.inputs.tag_configure(each, foreground=each)

        self.auto_complete_run()
        self.realtime_run()
        try:
            with open('browse memory.txt', encoding='utf-8-sig') as f:
                self.last_place = f.read()
        except:
            self.last_place = "/"
        self.bg_mode = config_dict['background_mode']
        self.turn_bg_mode = ttk.Button(
            self,
            text='开灯' if self.bg_mode == 'black' else '关灯',
            command=self.change_background_color_mode)
        self.turn_bg_mode.place(x=240, y=0)
        self.change_background_color_mode(turn=False)
        self.last_save = self.inputs.get('1.0', 'end-1c')

        self.menubar = Menu(self,
                            tearoff=False,
                            bg=self.background_color,
                            activebackground=self.active_background_color,
                            activeforeground=self.active_foreground_color,
                            disabledforeground=self.disabled_foreground_color)
        self.inputs.bind("<Button-3>", lambda x: self.rightKey(x, self.inputs))
        self.inputs.bind('<Control-f>', self.search_words)
        self.inputs.bind('<Control-e>', self.stop_play_midi)
        self.inputs.bind('<Control-d>', self.read_midi_file)
        self.inputs.bind('<Control-w>', self.openfile)
        self.inputs.bind('<Control-s>', self.save_current_file)
        self.inputs.bind('<Control-q>', lambda e: self.close_window())
        self.inputs.bind('<Control-r>', lambda e: self.runs())
        self.inputs.bind('<Control-g>',
                         lambda e: self.change_background_color_mode(True))
        self.inputs.bind('<Control-b>', lambda e: self.config_options())
        self.inputs.bind('<Control-t>', lambda e: self.visualize_config())
        self.inputs.bind('<Control-MouseWheel>',
                         lambda e: self.change_font_size(e))
        self.inputs.bind('<Alt-z>', lambda e: self.play_select_text(e))
        self.inputs.bind('<Alt-x>',
                         lambda e: self.visualize_play_select_text(e))
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.check_if_edited()
        self.current_filename_path = None
        self.search_box_open = False
        self.config_box_open = False
        self.visualize_config_box_open = False
        self.current_line_number = 1
        self.current_column_number = 1
        self.line_column = ttk.Label(
            self,
            text=
            f'Line {self.current_line_number} Col {self.current_column_number}'
        )
        self.line_column.place(x=750, y=500)
        self.get_current_line_column()

    def check_if_edited(self):
        current_text = self.inputs.get('1.0', 'end-1c')
        if current_text != self.last_save:
            self.title('musicpy 编辑器 *')
        else:
            self.title('musicpy 编辑器')
        self.after(100, self.check_if_edited)

    def close_window(self, e=None):
        current_text = self.inputs.get('1.0', 'end-1c')
        if current_text != self.last_save:
            self.ask_save_window = Toplevel(
                self,
                bg=self.background_color,
                highlightthickness=config_dict['highlight_thickness'],
                highlightbackground=config_dict['highlight_background'],
                highlightcolor=config_dict['highlight_color'])
            self.ask_save_window.wm_overrideredirect(True)
            self.ask_save_window.minsize(400, 150)
            ask_save_window_x = self.winfo_x()
            ask_save_window_y = self.winfo_y()
            self.ask_save_window.geometry(
                f"+{ask_save_window_x + 300}+{ask_save_window_y + 200}")
            self.ask_save_window.ask_save_label = ttk.Label(
                self.ask_save_window, text='文件已经更改,是否需要保存？')
            self.ask_save_window.ask_save_label.place(x=0, y=30)
            self.ask_save_window.save_button = ttk.Button(
                self.ask_save_window,
                text='保存',
                command=self.save_and_quit,
                style='New.TButton')
            self.ask_save_window.not_save_button = ttk.Button(
                self.ask_save_window,
                text='丢弃',
                command=self.destroy,
                style='New.TButton')
            self.ask_save_window.cancel_button = ttk.Button(
                self.ask_save_window,
                text='取消',
                command=self.ask_save_window.destroy,
                style='New.TButton')
            self.ask_save_window.save_button.place(x=0, y=100)
            self.ask_save_window.not_save_button.place(x=90, y=100)
            self.ask_save_window.cancel_button.place(x=200, y=100)
        else:
            self.destroy()

    def save_and_quit(self):
        self.save_current_file()
        if self.current_filename_path:
            self.destroy()

    def visualize_config(self):
        if self.visualize_config_box_open:
            return
        self.visualize_config_box_open = True
        os.chdir('visualization folder')
        with open('change_settings.pyw', encoding='utf-8-sig') as f:
            exec(f.read(), globals(), globals())

    def get_current_line_column(self):
        ind = self.inputs.index(INSERT)
        line, column = ind.split('.')
        self.current_line_number = int(line)
        self.current_column_number = int(column)
        self.line_column.config(
            text=
            f'Line {self.current_line_number} Col {self.current_column_number}'
        )
        self.after(10, self.get_current_line_column)

    def change_font_size(self, e):
        num = e.delta // 120
        self.font_size += num
        if self.font_size < 1:
            self.font_size = 1
        config_dict['font_size'] = self.font_size
        self.get_config_dict['font_size'] = str(self.font_size)
        self.inputs.configure(font=(self.font_type, self.font_size))
        self.outputs.configure(font=(self.font_type, self.font_size))
        self.save_config(True)

    def change_background_color_mode(self, turn=True):
        if turn:
            self.bg_mode = 'white' if self.bg_mode == 'black' else 'black'
        if self.bg_mode == 'white':
            self.inputs.configure(bg=self.day_color,
                                  fg='black',
                                  insertbackground='black')
            self.outputs.configure(bg=self.day_color,
                                   fg='black',
                                   insertbackground='black')
            self.bg_mode = 'white'
            self.turn_bg_mode.configure(text='关灯')
        elif self.bg_mode == 'black':
            self.inputs.configure(background=self.night_color,
                                  foreground='white',
                                  insertbackground='white')
            self.outputs.configure(background=self.night_color,
                                   foreground='white',
                                   insertbackground='white')
            self.bg_mode = 'black'
            self.turn_bg_mode.configure(text='开灯')
        if turn:
            config_dict['background_mode'] = self.bg_mode
            self.save_config(True)

    def openfile(self, e=None):
        filename = filedialog.askopenfilename(initialdir=self.last_place,
                                              title="选择文件",
                                              filetype=(("所有文件", "*.*"), ))
        if filename:
            self.current_filename_path = filename
            memory = filename[:filename.rindex('/') + 1]
            with open('browse memory.txt', 'w', encoding='utf-8-sig') as f:
                f.write(memory)
            self.last_place = memory
            try:
                with open(filename, encoding='utf-8-sig',
                          errors='ignore') as f:
                    self.inputs.delete('1.0', END)
                    self.inputs.insert(END, f.read())
                    self.inputs.see(INSERT)
                    self.inputs.mark_set(INSERT, '1.0')
                    self.last_save = self.inputs.get('1.0', 'end-1c')
                    if self.is_grammar:
                        self.after(100, self.grammar_highlight_func)
            except:
                self.inputs.delete('1.0', END)
                self.inputs.insert(END, '不是有效的文本文件类型')

    def file_top_make_menu(self):
        self.file_menu.tk_popup(x=self.winfo_pointerx(),
                                y=self.winfo_pointery())

    def wraplines(self):
        N = self.eachline_character
        text = self.outputs.get('1.0', END)
        K = len(text)
        text = ('\n' * self.wraplines_number).join(
            [text[i:i + N] for i in range(0, K, N)])
        self.outputs.delete('1.0', END)
        self.outputs.insert(END, text)

    def close_config_box(self):
        self.config_window.destroy()
        self.config_box_open = False

    def close_visualize_config_box(self):
        self.visualize_config_window.destroy()
        self.visualize_config_box_open = False
        os.chdir('../')

    def insert_bool(self, content):
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, content)
        self.config_change(0)

    def config_change(self, e):
        current = self.config_contents.get('1.0', 'end-1c')
        current_config = self.config_window.choose_config_options.get(ANCHOR)
        self.get_config_dict[current_config] = current

    def change_search_inds(self, num):
        self.config_window.search_inds += num
        if self.config_window.search_inds < 0:
            self.config_window.search_inds = 0
        if self.config_window.search_inds_list:
            search_num = len(self.config_window.search_inds_list)
            if self.config_window.search_inds >= search_num:
                self.config_window.search_inds = search_num - 1
            first = self.config_window.search_inds_list[
                self.config_window.search_inds]
            self.config_window.choose_config_options.selection_clear(0, END)
            self.config_window.choose_config_options.selection_set(first)
            self.config_window.choose_config_options.selection_anchor(first)
            self.config_window.choose_config_options.see(first)
            self.show_current_config_options(0)

    def search_config(self, *args):
        current = self.config_window.search_entry.get()
        self.config_window.search_inds_list = [
            i for i in range(self.config_window.options_num)
            if current in all_config_options[i]
        ]
        if self.config_window.search_inds_list:
            self.config_window.search_inds = 0
            first = self.config_window.search_inds_list[
                self.config_window.search_inds]
            self.config_window.choose_config_options.selection_clear(0, END)
            self.config_window.choose_config_options.selection_set(first)
            self.config_window.choose_config_options.selection_anchor(first)
            self.config_window.choose_config_options.see(first)
            self.show_current_config_options(0)
        else:
            self.config_window.choose_config_options.selection_clear(0, END)

    def show_current_config_options(self, e):
        current_config = self.config_window.choose_config_options.get(ANCHOR)
        self.config_window.config_name.configure(text=current_config)
        self.config_contents.delete('1.0', END)
        current_config_value = self.get_config_dict[current_config]
        self.config_contents.insert(END, current_config_value)

    def choose_filename(self):
        filename = filedialog.askopenfilename(initialdir='.',
                                              title="choose filename",
                                              filetype=(("all files",
                                                         "*.*"), ))
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, f"'{filename}'")
        self.config_change(0)

    def choose_directory(self):
        directory = filedialog.askdirectory(
            initialdir='.',
            title="choose directory",
        )
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, f"'{directory}'")
        self.config_change(0)

    def config_options(self):
        if self.config_box_open:
            self.config_window.focus_set()
            return
        self.get_config_dict = copy(config_dict)
        self.get_config_dict = {
            i: str(j)
            for i, j in self.get_config_dict.items()
        }
        self.config_box_open = True
        self.config_window = Toplevel(self, bg=self.background_color)
        self.config_window.minsize(800, 650)
        self.config_window.title('设置')
        self.config_window.protocol("WM_DELETE_WINDOW", self.close_config_box)

        global all_config_options
        all_config_options = list(self.get_config_dict.keys())
        self.options_num = len(all_config_options)
        global all_config_options_ind
        all_config_options_ind = {
            all_config_options[i]: i
            for i in range(self.options_num)
        }
        global config_original
        config_original = all_config_options.copy()
        global alpha_config
        alpha_config = all_config_options.copy()
        alpha_config.sort(key=lambda s: s.lower())
        self.config_window.options_num = len(all_config_options)
        self.config_window.config_options_bar = Scrollbar(self.config_window)
        self.config_window.config_options_bar.place(x=235,
                                                    y=120,
                                                    height=170,
                                                    anchor=CENTER)
        self.config_window.choose_config_options = Listbox(
            self.config_window,
            yscrollcommand=self.config_window.config_options_bar.set)
        for k in config_dict:
            self.config_window.choose_config_options.insert(END, k)
        self.config_window.choose_config_options.place(x=0, y=30, width=220)
        self.config_window.config_options_bar.config(
            command=self.config_window.choose_config_options.yview)
        self.config_window.config_name = ttk.Label(self.config_window, text='')
        self.config_window.config_name.place(x=300, y=20)
        self.config_window.choose_config_options.bind(
            '<<ListboxSelect>>', self.show_current_config_options)
        self.config_contents = Text(self.config_window,
                                    undo=True,
                                    autoseparators=True,
                                    maxundo=-1)
        self.config_contents.bind('<KeyRelease>', self.config_change)
        self.config_contents.place(x=350, y=50, width=400, height=200)
        self.config_window.choose_filename_button = ttk.Button(
            self.config_window,
            text='选择文件名',
            command=self.choose_filename,
            width=20)
        self.config_window.choose_directory_button = ttk.Button(
            self.config_window,
            text='选择路径',
            command=self.choose_directory,
            width=20)
        self.config_window.choose_filename_button.place(x=0, y=250)
        self.config_window.choose_directory_button.place(x=0, y=290)
        self.config_window.search_text = ttk.Label(self.config_window,
                                                   text='搜索设置参数')
        self.config_window.search_text.place(x=30, y=370)
        self.config_search_contents = StringVar()
        self.config_search_contents.trace_add('write', self.search_config)
        self.config_window.search_entry = Entry(
            self.config_window, textvariable=self.config_search_contents)
        self.config_window.search_entry.place(x=170, y=370)
        self.config_window.search_inds = 0
        self.config_window.up_button = ttk.Button(
            self.config_window,
            text='上一个',
            command=lambda: self.change_search_inds(-1),
            width=8)
        self.config_window.down_button = ttk.Button(
            self.config_window,
            text='下一个',
            command=lambda: self.change_search_inds(1),
            width=8)
        self.config_window.up_button.place(x=170, y=400)
        self.config_window.down_button.place(x=250, y=400)
        self.config_window.search_inds_list = []
        self.config_window.value_dict = config_dict
        self.config_window.choose_bool1 = ttk.Button(
            self.config_window,
            text='True',
            command=lambda: self.insert_bool('True'))
        self.config_window.choose_bool2 = ttk.Button(
            self.config_window,
            text='False',
            command=lambda: self.insert_bool('False'))
        self.config_window.choose_bool1.place(x=150, y=270)
        self.config_window.choose_bool2.place(x=250, y=270)
        save_button = ttk.Button(self.config_window,
                                 text='保存',
                                 command=self.save_config)
        save_button.place(x=30, y=330)
        self.saved_label = ttk.Label(self.config_window, text='保存成功')
        self.choose_font = ttk.Button(self.config_window,
                                      text='选择字体',
                                      command=self.get_font)
        self.choose_font.place(x=230, y=460)
        self.whole_fonts = list(font.families())
        self.whole_fonts.sort(
            key=lambda x: x if not x.startswith('@') else x[1:])
        self.font_list_bar = ttk.Scrollbar(self.config_window)
        self.font_list_bar.place(x=190, y=520, height=170, anchor=CENTER)
        self.font_list = Listbox(self.config_window,
                                 yscrollcommand=self.font_list_bar.set,
                                 width=25)
        for k in self.whole_fonts:
            self.font_list.insert(END, k)
        self.font_list.place(x=0, y=430)
        self.font_list_bar.config(command=self.font_list.yview)
        current_font_ind = self.whole_fonts.index(self.font_type)
        self.font_list.selection_set(current_font_ind)
        self.font_list.see(current_font_ind)
        self.change_sort_button = ttk.Button(
            self.config_window,
            text="sort in order of appearance",
            command=self.change_sort)
        self.sort_mode = 1
        self.change_sort_button.place(x=150, y=330, width=180)

    def change_sort(self):
        global all_config_options
        if self.sort_mode == 0:
            self.sort_mode = 1
            self.change_sort_button.config(text='sort in order of appearance')
            all_config_options = config_original.copy()
            self.config_window.choose_config_options.delete(0, END)
            for k in all_config_options:
                self.config_window.choose_config_options.insert(END, k)
        else:
            self.sort_mode = 0
            self.change_sort_button.config(text='sort in alphabetical order')
            all_config_options = alpha_config.copy()
            self.config_window.choose_config_options.delete(0, END)
            for k in all_config_options:
                self.config_window.choose_config_options.insert(END, k)
        self.search_config()

    def get_font(self):
        self.font_type = self.font_list.get(ACTIVE)
        self.font_size = eval(self.get_config_dict['font_size'])
        self.inputs.configure(font=(self.font_type, self.font_size))
        self.outputs.configure(font=(self.font_type, self.font_size))
        self.get_config_dict['font_type'] = str(self.font_type)
        config_dict['font_type'] = self.font_type
        config_dict['font_size'] = self.font_size
        self.save_config(True)

    def save_config(self, outer=False):
        if not outer:
            for each in config_dict:
                original = config_dict[each]
                changed = self.get_config_dict[each]
                if str(original) != changed:
                    if not isinstance(original, str):
                        config_dict[each] = eval(changed)
                    else:
                        config_dict[each] = changed
        with open('config.py', 'w', encoding='utf-8-sig') as f:
            formated_config = FormatCode(f'config_dict = {config_dict}\n')[0]
            f.write(formated_config)
        if not outer:
            self.saved_label.place(x=360, y=400)
            self.after(600, self.saved_label.place_forget)
        self.reload_config()

    def search_path(self, obj):
        filename = filedialog.askopenfilename(initialdir=self.last_place,
                                              parent=self.config_window,
                                              title="选择文件",
                                              filetype=(("所有文件", "*.*"), ))
        if filename:
            memory = filename[:filename.rindex('/') + 1]
            with open('browse memory.txt', 'w', encoding='utf-8-sig') as f:
                f.write(memory)
            self.last_place = memory
            obj.delete(0, END)
            obj.insert(END, filename)

    def reload_config(self):
        try:
            bg_path = config_dict['background_image']
            if not bg_path:
                self.bg_label.configure(image='')
            else:
                self.bg = PIL.Image.open(bg_path)
                ratio = 600 / self.bg.height
                self.bg = self.bg.resize(
                    (int(self.bg.width * ratio), int(self.bg.height * ratio)),
                    PIL.Image.ANTIALIAS)
                self.bg = PIL.ImageTk.PhotoImage(self.bg)
                self.bg_label.configure(image=self.bg)
                bg_places = config_dict['background_places']
                self.bg_label.place(x=bg_places[0], y=bg_places[1])

        except:
            bg_path = config_dict['background_image']
            if not bg_path:
                self.bg = ''
            else:
                self.bg = PIL.Image.open(bg_path)
            ratio = 600 / self.bg.height
            self.bg = self.bg.resize(
                (int(self.bg.width * ratio), int(self.bg.height * ratio)),
                PIL.Image.ANTIALIAS)
            self.bg = PIL.ImageTk.PhotoImage(self.bg)
            self.bg_label = ttk.Label(self, image=self.bg)
            bg_places = config_dict['background_places']
            self.bg_label.place(x=bg_places[0], y=bg_places[1])
        self.eachline_character = config_dict['eachline_character']
        self.pairing_symbols = config_dict['pairing_symbols']
        self.wraplines_number = config_dict['wraplines_number']
        self.grammar_highlight = config_dict['grammar_highlight']
        for each in self.grammar_highlight:
            self.inputs.tag_configure(each, foreground=each)

        try:
            self.font_size = eval(self.get_config_dict['font_size'])
            self.inputs.configure(font=(self.font_type, self.font_size))
            self.outputs.configure(font=(self.font_type, self.font_size))
        except:
            pass

    def save_current_file(self, e=None):
        current_text = self.inputs.get('1.0', 'end-1c')
        if current_text != self.last_save:
            if self.current_filename_path:
                self.last_save = self.inputs.get('1.0', 'end-1c')
                with open(self.current_filename_path,
                          'w',
                          encoding='utf-8-sig') as f:
                    f.write(self.last_save)
            else:
                self.save()
            self.title('musicpy 编辑器')

    def save(self, e=None):
        filename = filedialog.asksaveasfilename(initialdir=self.last_place,
                                                title="保存输入文本",
                                                filetype=(("所有文件", "*.*"), ),
                                                defaultextension=".txt")
        if filename:
            self.current_filename_path = filename
            memory = filename[:filename.rindex('/') + 1]
            with open('browse memory.txt', 'w', encoding='utf-8-sig') as f:
                f.write(memory)
            self.last_place = memory
            current_text = self.inputs.get('1.0', 'end-1c')
            with open(filename, 'w', encoding='utf-8-sig') as f:
                f.write(current_text)
            self.last_save = current_text

    def get_current_select(self, e):
        if self.show_select:
            text = self.auto_complete_menu.get(self.select_ind)
            self.auto_complete_menu.destroy()
            self.show_select = False
            self.inputs.delete('1.0', END)
            self.pre_input = self.pre_input[:self.
                                            start] + text + self.pre_input[
                                                self.start2:]
            self.inputs.insert(END, self.pre_input)
            self.inputs.mark_set(INSERT,
                                 '1.0' + f' + {self.start + len(text)} chars')
            self.inputs.see(INSERT)
            if self.is_realtime:
                self.changed = True
                self.realtime_run()

    def close_select(self, e):
        if self.show_select:
            self.auto_complete_menu.destroy()
            self.show_select = False

    def change_select(self, value):
        if self.show_select:
            sizes = self.auto_complete_menu.size()
            if 0 <= self.select_ind + value < sizes:
                self.auto_complete_menu.selection_set(self.select_ind + value)
                self.auto_complete_menu.selection_clear(self.select_ind)
                self.select_ind += value
                self.auto_complete_menu.see(self.select_ind)
            else:
                if self.select_ind + value >= sizes:
                    self.auto_complete_menu.selection_clear(self.select_ind)
                    self.select_ind = 0
                    self.auto_complete_menu.selection_set(self.select_ind)
                    self.auto_complete_menu.see(self.select_ind)
                else:
                    self.auto_complete_menu.selection_clear(self.select_ind)
                    self.select_ind = sizes - 1
                    self.auto_complete_menu.selection_set(self.select_ind)
                    self.auto_complete_menu.see(self.select_ind)

    def enter_choose(self, e):
        text = self.auto_complete_menu.get(ANCHOR)
        self.auto_complete_menu.destroy()
        self.show_select = False
        self.inputs.delete('1.0', END)
        self.pre_input = self.pre_input[:self.start] + text + self.pre_input[
            self.start2:]
        self.inputs.insert(END, self.pre_input)
        self.inputs.mark_set(INSERT,
                             '1.0' + f' + {self.start + len(text)} chars')
        self.inputs.see(INSERT)
        if self.is_realtime:
            self.changed = True
            self.realtime_run()

    def auto_complete_run(self):
        if not self.is_auto:
            return
        current_text = self.inputs.get('1.0', 'end-1c')
        if current_text != self.pre_input:
            self.changed = True
            is_deleted = len(current_text) < len(self.pre_input)
            self.pre_input = current_text
            self.auto_complete_menu.destroy()
            self.show_select = False
            current_text2 = self.inputs.get('1.0', INSERT)
            if current_text2 and current_text2[-1] not in [' ', '\n']:
                for each in self.pairing_symbols:
                    if current_text2[-1] == each[0] and not is_deleted:
                        self.inputs.insert(INSERT, each[1])
                        self.pre_input = self.inputs.get('1.0', 'end-1c')
                        x, y = self.inputs.index(INSERT).split('.')
                        self.inputs.mark_set(INSERT, f'{x}.{int(y)-1}')
                        break
                else:
                    newline_ind, dot_ind = current_text2.rfind(
                        '\n') + 1, current_text2.rfind('.') + 1
                    start = max(newline_ind, dot_ind)
                    if dot_ind > newline_ind:
                        dot_word_ind = newline_ind
                        if current_text2[dot_word_ind] in ['/', '?']:
                            dot_word_ind += 1
                        current_word = current_text2[dot_word_ind:dot_ind - 1]
                        dot_content = current_text2[dot_ind:].lower()
                        try:
                            current_func = dir(eval(current_word))
                            find_similar = [
                                x for x in current_func
                                if dot_content in x.lower()
                            ]
                            if find_similar:
                                self.start = start
                                self.start2 = start + len(dot_content)
                                self.auto_complete(find_similar)
                        except:
                            pass
                    else:
                        if current_text2[start] in ['/', '?']:
                            start += 1
                        current_word = current_text2[start:].lower()
                        find_similar = [
                            x for x in function_names
                            if current_word in x.lower()
                        ]
                        if find_similar:
                            self.start = start
                            self.start2 = start + len(current_word)
                            self.auto_complete(find_similar)
        else:
            if not self.is_realtime:
                self.changed = False
        self.after(10, self.auto_complete_run)

    def get_input_place(self):
        character = self.inputs.get(INSERT)
        x, y, width, height = self.inputs.bbox(INSERT)
        screen_x = x + (0 if character == '\n' else width)
        screen_y = y + height + 15
        return screen_x, screen_y

    def auto_complete(self, find_similar):
        self.auto_complete_menu = Listbox(self)
        self.auto_complete_menu.bind("<<ListboxSelect>>",
                                     lambda e: self.enter_choose(e))
        places = self.get_input_place()
        for each in find_similar:
            self.auto_complete_menu.insert(END, each)
        self.auto_complete_menu.place(x=places[0], y=places[1])
        self.show_select = True
        self.select_ind = 0
        self.auto_complete_menu.selection_set(0)

    def runs(self):
        if self.is_grammar and self.inputs.edit_modified():
            self.after(100, self.grammar_highlight_func)
        self.outputs.delete('1.0', END)
        text = self.inputs.get('1.0', 'end-1c')
        lines = text.split('\n')
        for i in range(len(lines)):
            each = lines[i]
            if each:
                if each[0] == '/':
                    lines[i] = f'play({each[1:]})'
                elif each[0] == '?':
                    lines[i] = f'detect({each[1:]})'
        text = '\n'.join(lines)
        try:
            exec(text, globals())
            if self.is_print:
                for each in lines:
                    try:
                        if 'play(' not in each:
                            print(eval(each))
                    except:
                        pass
        except:
            self.outputs.insert(END, '代码不合法\n')
            self.outputs.insert(END, traceback.format_exc())

    def runs_2(self):
        self.inputs.edit_modified(False)
        self.outputs.delete('1.0', END)
        text = self.pre_input
        lines = text.split('\n')
        for i in range(len(lines)):
            each = lines[i]
            if each:
                if each[0] == '/':
                    lines[i] = f'play({each[1:]})'
                elif each[0] == '?':
                    lines[i] = f'detect({each[1:]})'
        text = '\n'.join(lines)
        try:
            exec(text, globals())
            if self.is_print:
                for each in lines:
                    try:
                        if 'play(' not in each:
                            print(eval(each))
                    except:
                        pass
        except:
            pass

    def grammar_highlight_func(self):
        end_index = self.inputs.index(END)
        for color, texts in self.grammar_highlight.items():
            for i in texts:
                start_index = f"{self.inputs.index(INSERT).split('.')[0]}.0"
                current_last_index = '1.0'
                while self.inputs.compare(start_index, '<', end_index):
                    current_text_index = self.inputs.search(i,
                                                            start_index,
                                                            stopindex=END)
                    if current_text_index:
                        word_length = len(i)
                        x, y = current_text_index.split('.')
                        current_last_index = f"{x}.{int(y)+word_length}"
                        self.inputs.tag_add(color, current_text_index,
                                            current_last_index)
                        start_index = current_last_index
                    else:
                        x, y = current_last_index.split('.')
                        if self.inputs.get(current_last_index) == '\n':
                            x = int(x) + 1
                        y = int(y) + 1
                        current_last_index = f'{x}.{y}'
                        start_index = current_last_index

    def realtime_run(self):
        global function_names
        function_names = list(
            set(musicpy_vars + list(locals().keys()) + list(globals().keys())))
        if self.quit or (not self.is_realtime):
            self.quit = False
            return
        if self.is_grammar and self.inputs.edit_modified():
            self.after(100, self.grammar_highlight_func)
        if self.is_auto:
            if self.changed:
                self.changed = False
                self.runs_2()
        else:
            if self.inputs.edit_modified():
                self.pre_input = self.inputs.get('1.0', 'end-1c')
                self.runs_2()
        self.after(100, self.realtime_run)

    def check_realtime(self):
        value = self.realtime.get()
        if value:
            if not self.is_realtime:
                self.is_realtime = 1
                self.realtime_run()
        else:
            if self.is_realtime:
                self.is_realtime = 0
                self.quit = True

    def check_print(self):
        self.is_print = self.no_print.get()

    def check_auto(self):
        self.is_auto = self.auto.get()
        if self.is_auto:
            self.auto_complete_run()
        else:
            self.close_select(1)

    def check_grammar(self):
        self.is_grammar = self.grammar.get()

    def cut(self, editor, event=None):
        editor.event_generate("<<Cut>>")

    def copy(self, editor, event=None):
        editor.event_generate("<<Copy>>")

    def paste(self, editor, event=None):
        editor.event_generate('<<Paste>>')

    def choose_all(self, editor, event=None):
        editor.tag_add(SEL, '1.0', END)
        editor.mark_set(INSERT, END)
        editor.see(INSERT)

    def inputs_undo(self, editor, event=None):
        try:
            editor.edit_undo()
        except:
            pass

    def inputs_redo(self, editor, event=None):
        try:
            editor.edit_redo()
        except:
            pass

    def play_select_text(self, editor, event=None):
        try:
            selected_text = self.inputs.selection_get()
            exec(f"play({selected_text})")
        except:
            self.outputs.delete('1.0', END)
            self.outputs.insert(END, '选中的语句无法播放')

    def visualize_play_select_text(self, editor, event=None):
        try:
            selected_text = self.inputs.selection_get()
            exec(f"write('temp.mid', {selected_text})")
        except:
            self.outputs.delete('1.0', END)
            self.outputs.insert(END, '选中的语句无法播放')
            return
        os.chdir('visualization folder')
        with open('Ideal Piano start program.pyw', encoding='utf-8-sig') as f:
            exec(f.read(), globals(), globals())
        os.chdir('../')

    def read_midi_file(self, editor=None, event=None):
        filename = filedialog.askopenfilename(initialdir=self.last_place,
                                              title="选择midi文件",
                                              filetype=(("midi文件", "*.mid"),
                                                        ("所有文件", "*.*")))
        if filename:
            memory = filename[:filename.rindex('/') + 1]
            with open('browse memory.txt', 'w', encoding='utf-8-sig') as f:
                f.write(memory)
            self.last_place = memory
            self.inputs.insert(
                END,
                f"new_midi_file = read(\"{filename}\", mode='all', to_piece=True, get_off_drums=False)\n"
            )

    def stop_play_midi(self, editor, event=None):
        pygame.mixer.music.stop()

    def close_search_box(self):
        for each in self.search_inds_list:
            ind1, ind2 = each
            self.inputs.tag_remove('highlight', ind1, ind2)
            self.inputs.tag_remove('highlight_select', ind1, ind2)
        self.search_box.destroy()
        self.search_box_open = False

    def search_words(self, editor, event=None):
        if not self.search_box_open:
            self.search_box_open = True
        else:
            self.search_box.focus_set()
            self.search_entry.focus_set()
            return
        self.search_box = Toplevel(self, bg=self.background_color)
        self.search_box.protocol("WM_DELETE_WINDOW", self.close_search_box)
        self.search_box.title('搜索')
        self.search_box.minsize(300, 200)
        self.search_box.geometry('250x150+350+300')
        self.search_text = ttk.Label(self.search_box, text='请输入想要搜索的内容')
        self.search_text.place(x=0, y=0)
        self.search_contents = StringVar()
        self.search_contents.trace_add('write', self.search)
        self.search_entry = Entry(self.search_box,
                                  textvariable=self.search_contents)
        self.search_entry.place(x=0, y=30)
        self.search_entry.focus_set()
        self.search_inds = 0
        self.search_inds_list = []
        self.inputs.tag_configure('highlight',
                                  background=self.search_highlight_color[0])
        self.inputs.tag_configure('highlight_select',
                                  background=self.search_highlight_color[1])
        self.search_up = ttk.Button(self.search_box,
                                    text='上一个',
                                    command=lambda: self.change_search_ind(-1))
        self.search_down = ttk.Button(
            self.search_box,
            text='下一个',
            command=lambda: self.change_search_ind(1))
        self.search_up.place(x=0, y=60)
        self.search_down.place(x=100, y=60)
        self.case_sensitive = False
        self.check_case_sensitive = IntVar()
        self.check_case_sensitive.set(0)
        self.case_sensitive_box = ttk.Checkbutton(
            self.search_box, text='区分大小写', variable=self.check_case_sensitive)
        self.case_sensitive_box.place(x=170, y=30)

    def change_search_ind(self, ind):
        length = len(self.search_inds_list)
        if self.search_inds in range(length):
            current_inds = self.search_inds_list[self.search_inds]
            self.inputs.tag_remove('highlight_select', current_inds[0],
                                   current_inds[1])
        self.search_inds += ind
        if self.search_inds < 0:
            self.search_inds = length - 1
        elif self.search_inds >= length:
            self.search_inds = 0
        if self.search_inds in range(length):
            current_inds = self.search_inds_list[self.search_inds]
            self.inputs.tag_add('highlight_select', current_inds[0],
                                current_inds[1])
            self.inputs.see(current_inds[1])

    def search(self, *args):
        all_text = self.inputs.get('1.0', 'end-1c')[:-1]

        for each in self.search_inds_list:
            ind1, ind2 = each
            self.inputs.tag_remove('highlight', ind1, ind2)
            self.inputs.tag_remove('highlight_select', ind1, ind2)
        current = self.search_contents.get()
        self.case_sensitive = self.check_case_sensitive.get()
        if not self.case_sensitive:
            all_text = all_text.lower()
            current = current.lower()
        self.search_inds_list = [[m.start(), m.end()]
                                 for m in re.finditer(current, all_text)]
        for each in self.search_inds_list:
            ind1, ind2 = each
            newline = "\n"
            ind1 = f'{all_text[:ind1].count(newline)+1}.{ind1 - all_text[:ind1].rfind(newline) - 1}'
            ind2 = f'{all_text[:ind2].count(newline)+1}.{ind2 - all_text[:ind2].rfind(newline) - 1}'
            each[0] = ind1
            each[1] = ind2
        self.outputs.delete('1.0', END)
        if self.search_inds_list:
            for each in self.search_inds_list:
                ind1, ind2 = each
                self.inputs.tag_add('highlight', ind1, ind2)

    def rightKey(self, event, editor):
        self.menubar.delete(0, END)
        self.menubar.add_command(label='剪切',
                                 command=lambda: self.cut(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='复制',
                                 command=lambda: self.copy(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='粘贴',
                                 command=lambda: self.paste(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='全选',
                                 command=lambda: self.choose_all(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='撤销',
                                 command=lambda: self.inputs_undo(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='恢复',
                                 command=lambda: self.inputs_redo(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='播放选中语句',
                                 command=lambda: self.play_select_text(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(
            label='可视化播放选中语句',
            command=lambda: self.visualize_play_select_text(editor),
            foreground=self.foreground_color)
        self.menubar.add_command(label='导入midi文件',
                                 command=lambda: self.read_midi_file(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='停止播放',
                                 command=lambda: self.stop_play_midi(editor),
                                 foreground=self.foreground_color)
        self.menubar.add_command(label='搜索',
                                 command=lambda: self.search_words(editor),
                                 foreground=self.foreground_color)
        self.menubar.post(event.x_root, event.y_root)


function_names = list(
    set(musicpy_vars + list(locals().keys()) + list(globals().keys())))
root = Root()
root.focus_force()
root.inputs.focus_set()
root.mainloop()
