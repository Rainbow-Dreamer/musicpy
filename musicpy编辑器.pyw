import traceback
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
from tkinter import filedialog
import musicpy.musicpy
function_names = dir(musicpy.musicpy) + ['direct_play', 'print']
from musicpy.musicpy import *
from io import BytesIO
import pygame
pygame.mixer.init(44100, -16, 1, 1024)


def print(obj):
    root.outputs.insert(END, obj)
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
         time1=0,
         track_num=1,
         name='temp.mid',
         modes='new2',
         instrument=None,
         save_as_file=True):
    file = write(name,
                 chord1,
                 tempo,
                 track=0,
                 channel=0,
                 time1=0,
                 track_num=1,
                 mode=modes,
                 instrument=instrument,
                 save_as_file=save_as_file)
    if save_as_file:
        result_file = name
        pygame.mixer.music.load(result_file)
        pygame.mixer.music.play()        
        #if sys.platform.startswith('win'):
            #os.startfile(result_file)
        #elif sys.platform.startswith('linux'):
            #import subprocess
            #subprocess.Popen(result_file)
        #elif sys.platform == 'darwin':
            #os.system(result_file)
    else:
        file.seek(0)
        pygame.mixer.music.load(file)
        file.close()
        pygame.mixer.music.play()


class Root(Tk):
    def __init__(self):
        super(Root, self).__init__()
        self.minsize(1200, 600)
        self.title('musicpy编辑器')
        # try:
            #self.bg = Image.open(background_image)
            #ratio = 600 / self.bg.height
            # self.bg = self.bg.resize(
                #(int(self.bg.width * ratio), int(self.bg.height * ratio)),
                # Image.ANTIALIAS)
            #self.bg = ImageTk.PhotoImage(self.bg)
            #self.bg_label = ttk.Label(self, image=self.bg)
            #self.bg_label.place(x=700, y=0)
        # except:
            # pass
        self.inputs_text = ttk.Label(self, text='清在这里输入musicpy音乐代码语句')
        self.inputs = Text(self,
                           wrap='none',
                           undo=True,
                           autoseparators=True,
                           maxundo=-1)
        self.inputs_text.place(x=0, y=0)
        self.inputs.place(x=0, y=30, width=700, height=200)
        self.inputs.focus_set()
        inputs_v = Scrollbar(self,
                             orient="vertical",
                             command=self.inputs.yview)
        inputs_h = Scrollbar(self,
                             orient="horizontal",
                             command=self.inputs.xview)
        self.inputs.configure(yscrollcommand=inputs_v.set,
                              xscrollcommand=inputs_h.set)
        inputs_v.place(x=700, y=30, height=200)
        inputs_h.place(x=0, y=230, width=700)
        self.outputs_text = ttk.Label(self, text='在这里显示运行结果')
        self.outputs = Text(self, wrap='none')
        self.outputs_text.place(x=0, y=250)
        self.outputs.place(x=0, y=280, width=700, height=300)
        outputs_v = Scrollbar(self,
                              orient="vertical",
                              command=self.outputs.yview)
        outputs_h = Scrollbar(self,
                              orient="horizontal",
                              command=self.outputs.xview)
        self.outputs.configure(yscrollcommand=outputs_v.set,
                               xscrollcommand=outputs_h.set)
        outputs_v.place(x=700, y=280, height=300)
        outputs_h.place(x=0, y=580, width=700)
        self.run_button = ttk.Button(self, text='运行', command=self.runs)
        self.run_button.place(x=750, y=100)
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
                                         text='不使用print',
                                         variable=self.no_print,
                                         command=self.check_print)
        self.realtime_box.place(x=750, y=200)
        self.print_box.place(x=750, y=250)
        self.save_button = ttk.Button(self, text='保存', command=self.save)
        self.save_button.place(x=750, y=50)
        self.is_print = 1
        self.auto = False
        self.pre_input = ''
        self.start = 0
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
        self.auto_complete_run()
        self.realtime_run()

    def save(self):
        filename = filedialog.asksaveasfilename(initialdir='.',
                                                title="保存输入文本",
                                                filetype=(("所有文件", "*.*"),),
                                                defaultextension=".txt")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.inputs.get('1.0', END))

    def get_current_select(self, e):
        if self.show_select:
            text = self.auto_complete_menu.get(self.select_ind)
            self.auto_complete_menu.place_forget()
            self.show_select = False
            self.inputs.delete('1.0', END)
            self.pre_input = self.pre_input[:self.start] + text
            self.inputs.insert(END, self.pre_input)
            if self.is_realtime:
                self.changed = True
                self.realtime_run()

    def close_select(self, e):
        if self.show_select:
            self.auto_complete_menu.place_forget()
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
        self.auto_complete_menu.place_forget()
        self.show_select = False
        self.inputs.delete('1.0', END)
        self.pre_input = self.pre_input[:self.start] + text
        self.inputs.insert(END, self.pre_input)
        if self.is_realtime:
            self.changed = True
            self.realtime_run()

    def auto_complete_run(self):
        current_text = self.inputs.get('1.0', END)[:-1]
        if current_text != self.pre_input:
            self.changed = True
            self.pre_input = current_text
            self.auto_complete_menu.destroy()
            self.show_select = False
            if current_text and current_text[-1] not in [' ', '\n']:
                if current_text[-1] == '(':
                    self.inputs.insert(END, ')')
                    self.pre_input += ')'
                    x, y = self.inputs.index(INSERT).split('.')
                    self.inputs.mark_set(INSERT, f'{x}.{int(y)-1}')
                elif current_text[-1] == '[':
                    self.inputs.insert(END, ']')
                    self.pre_input += ']'
                    x, y = self.inputs.index(INSERT).split('.')
                    self.inputs.mark_set(INSERT, f'{x}.{int(y)-1}')
                else:
                    space_ind, newline_ind, dot_ind = current_text.rfind(
                        ' ') + 1, current_text.rfind(
                            '\n') + 1, current_text.rfind('.') + 1
                    start = max(space_ind, newline_ind, dot_ind)
                    if dot_ind > space_ind and dot_ind > newline_ind:
                        dot_word_ind = max(space_ind, newline_ind)
                        if current_text[dot_word_ind] == '/':
                            dot_word_ind += 1
                        current_word = current_text[dot_word_ind:dot_ind - 1]
                        dot_content = current_text[dot_ind:]
                        try:
                            exec(current_text[:dot_word_ind], globals())
                        except:
                            pass
                        try:
                            current_func = dir(eval(current_word))
                            find_similar = [
                                x for x in current_func if dot_content in x
                            ]
                            if find_similar:
                                self.start = start
                                self.auto_complete(find_similar)
                        except:
                            pass
                    else:
                        if current_text[start] == '/':
                            start += 1
                        current_word = current_text[start:]
                        find_similar = [
                            x for x in function_names if current_word in x
                        ]
                        if find_similar:
                            self.start = start
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
        self.outputs.delete('1.0', END)
        text = self.inputs.get('1.0', END)
        lines = text.split('\n')
        lines = [f'play({each[1:]})' if each and each[0] == '/' else each for each in lines]
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
        self.outputs.delete('1.0', END)
        text = self.pre_input
        lines = text.split('\n')
        lines = [f'play({each[1:]})' if each and each[0] == '/' else each for each in lines]
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

    def realtime_run(self):
        if self.quit:
            self.quit = False
            return
        if self.changed:
            self.changed = False
            self.runs_2()
        self.after(100, self.realtime_run)

    def check_realtime(self):
        value = self.realtime.get()
        if value:
            if not self.is_realtime:
                self.is_realtime = 1
                self.update()
                self.realtime_run()
        else:
            if self.is_realtime:
                self.is_realtime = 0
                self.quit = True
                self.update()

    def check_print(self):
        self.is_print = self.no_print.get()
        self.update()


root = Root()
root.mainloop()
