import tkinter as t
from tkinter import messagebox
import time
import requests
import os

THEME_COLOUR = '#5BC2E7'
SECONDARY_COLOUR = '#5B7CE7'
TERTIARY_COLOUR = '#5BE7C6'


API_URL = 'https://api.api-ninjas.com/v1/facts'
API_KEY = os.environ.get('api_key')

headers = {
    'X-Api-Key': API_KEY
}

parameters = {
    'limit': 10
}

NORMAL_FONT = ('Arial', 18, 'normal')
HIGHLIGHT_FONT = ('Arial', 22, 'bold')
RESULTS_FONT = ('Constantia', 40, 'bold')


def get_text():
    response = requests.get(API_URL, headers=headers, params=parameters)
    if response.status_code == requests.codes.ok:
        facts = []
        length = 0
        for fact in response.json():
            length += len(fact['fact'])
            facts.append(fact['fact'])
            if length >= 300:
                break
        text = '. '.join(facts)
        return text
    else:
        return False


def get_index(n):
    num_string_1 = '1.' + str(n)
    num_string_2 = '1.' + str(n + 1)
    return num_string_1, num_string_2


class TypingTestAttempt(t.Frame):
    def __init__(self, root, text, **kwargs):
        super().__init__()
        self.start_time = time.time()
        self.root = root
        self.text = text
        self.root.bind("<Key>", self.key_pressed)
        self.key = None
        self.display = t.Text(font=NORMAL_FONT, wrap=t.WORD)
        self.display.insert(t.END, self.text)
        self.display.tag_config('correct', background='lawn green', font=HIGHLIGHT_FONT)
        self.display.tag_config('incorrect', background='light coral', font=HIGHLIGHT_FONT)
        self.display.tag_config('normal', foreground=SECONDARY_COLOUR, background='white', font=NORMAL_FONT)
        self.display.tag_add('correct', '1.0', '1.1')
        self.display.config(state='disabled')
        self.display.pack(padx=20, pady=20)
        self.progress = 0
        self.correct_key_presses = 0
        self.incorrect_key_presses = 0
        self.last_keypress_correct = True
        self.index = get_index(self.progress)
        self.summary = None
        self.running = True

    def apply_tags(self):
        if self.running:
            if self.last_keypress_correct:
                if self.correct_key_presses == len(self.text):
                    self.compile_results()
                else:
                    self.display.tag_add('normal', self.index[0], self.index[1])
                    self.index = get_index(self.progress)
                    self.display.tag_add('correct', self.index[0], self.index[1])
            else:
                self.display.tag_add('incorrect', self.index[0], self.index[1])

    def key_pressed(self, event):
        if self.running:
            if len(event.char) == 1:
                self.key = event.char
                key = self.display.get(self.index[0], self.index[1])
                if event.char == key:
                    self.correct_key_presses += 1
                    self.progress += 1
                    self.last_keypress_correct = True
                    self.apply_tags()
                else:
                    if self.last_keypress_correct:
                        self.incorrect_key_presses += 1
                    self.last_keypress_correct = False
                    self.apply_tags()

    def compile_results(self):
        self.running = False
        accuracy = self.correct_key_presses / (self.correct_key_presses + self.incorrect_key_presses)
        elapsed_time = time.time() - self.start_time
        wpm = (len(self.text) / 5) / (elapsed_time / 60)
        self.display.destroy()
        self.summary = ResultsSummary(accuracy, wpm)
        self.summary.pack()
        self.root.complete_test()


class ResultsSummary(t.Frame):
    def __init__(self, accuracy, wpm):
        super().__init__()
        self.config(bg=THEME_COLOUR)
        self.accuracy = int(accuracy * 100)
        self.wpm = round(wpm, 1)
        self.congrats = t.Label(master=self, text='You have completed the typing test!\nHere are your results:',
                                font=RESULTS_FONT, background=THEME_COLOUR, foreground=SECONDARY_COLOUR,
                                padx=10, pady=10)
        frame = t.Frame(master=self, borderwidth=5, relief=t.RIDGE, padx=10, pady=10, background=THEME_COLOUR)
        self.accuracy_title = t.Label(master=frame, text=f'Accuracy:', font=RESULTS_FONT, background=THEME_COLOUR,
                                      foreground=SECONDARY_COLOUR)
        self.speed_title = t.Label(master=frame, text='Speed:', font=RESULTS_FONT,background=THEME_COLOUR,
                                   foreground=SECONDARY_COLOUR)
        self.speed_label = t.Label(master=frame, text=f'{self.wpm} wpm', font=RESULTS_FONT, bg=THEME_COLOUR)
        self.accuracy_label = t.Label(master=frame, text=f'{self.accuracy}%', font=RESULTS_FONT, bg=THEME_COLOUR)
        self.set_result_colours()
        # self.congrats.grid(column=0, row=0, columnspan=2, pady=5)
        self.congrats.pack(pady=5)
        frame.pack()
        self.speed_title.grid(column=0, row=0)
        self.speed_label.grid(column=1, row=0, sticky='ew')
        self.accuracy_title.grid(column=0, row=1)
        self.accuracy_label.grid(column=1, row=1, sticky='ew')

    def set_result_colours(self):
        if self.wpm < 40:
            green = int(self.wpm * (255 / 40))
            red = 255
        else:
            green = 255
            red = max(int((80 - self.wpm) * (255 / 40)), 0)
        hex_colour = "#%02x%02x%02x" % (red, green, 0)
        self.speed_label.config(fg=hex_colour)
        if self.accuracy < 80:
            green = 0
            red = 255
        elif self.accuracy < 90:
            green = int((self.accuracy - 80) * (255 / 10))
            red = 255
        else:
            green = 255
            red = int((100 - self.accuracy) * (255 / 10))
        hex_colour = "#%02x%02x%02x" % (red, green, 0)
        self.accuracy_label.config(fg=hex_colour)

    def clear_all(self):
        for widgets in self.winfo_children():
            widgets.destroy()
            self.destroy()


class TypingTester(t.Tk):
    def __init__(self):
        super().__init__()
        self.title('Typing Speed Test')
        self.configure(bg=THEME_COLOUR)
        self.geometry('1000x700')
        self.start_button = t.Button(text='Start Test', command=self.start_test, font=RESULTS_FONT,
                                     bg=SECONDARY_COLOUR, fg=TERTIARY_COLOUR, activebackground=TERTIARY_COLOUR,
                                     activeforeground=SECONDARY_COLOUR)
        self.start_button.pack(padx=100, pady=100)
        self.tt = None

    def start_test(self):
        if self.tt:
            print('here')
            self.tt.summary.clear_all()
            self.tt.destroy()
        text = get_text()
        if text:
            self.tt = TypingTestAttempt(window, text)
            self.tt.pack(padx=20, pady=20)
            self.start_button.pack_forget()
        else:
            messagebox.showerror(title='Error',
                                 message='There was a problem accessing the test paragraph.\n'
                                         'Please try again.')

    def complete_test(self):
        self.start_button.config(text='Restart')
        self.start_button.pack(padx=100, pady=100)


window = TypingTester()

window.mainloop()
