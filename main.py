import tkinter as t
from tkinter import messagebox
import time
import requests
import os

THEME_COLOUR = '#5BC2E7'
SECONDARY_COLOUR = '#5B7CE7'
TERTIARY_COLOUR = '#5BE7C6'

MAX_PARAGRAPH_LENGTH = 300
WPM_THRESHOLD = 40
ACCURACY_THRESHOLD_1 = 80
ACCURACY_THRESHOLD_2 = 90
SENTENCE_REQUEST_LIMIT = 10

NORMAL_FONT = ('Arial', 18, 'normal')
HIGHLIGHT_FONT = ('Arial', 22, 'bold')
RESULTS_FONT = ('Constantia', 40, 'bold')

API_URL = 'https://api.api-ninjas.com/v1/facts'
API_KEY = os.environ.get('api_key')

headers = {
    'X-Api-Key': API_KEY
}

parameters = {
    'limit': SENTENCE_REQUEST_LIMIT
}


def get_text():
    """
    Retrieve text for the typing test from an API.

    Returns:
        str: The text for the typing test.
    """
    # Make API request to get facts
    response = requests.get(API_URL, headers=headers, params=parameters)

    # Check if the API request was successful
    if response.status_code == requests.codes.ok:
        facts = []
        length = 0

        # Process each fact from the API response
        for fact in response.json():
            length += len(fact['fact'])
            facts.append(fact['fact'])

            # Break if the total length exceeds the maximum paragraph length
            if length >= MAX_PARAGRAPH_LENGTH:
                break

        # Combine facts into a text string
        text = '. '.join(facts)
        return text
    else:
        # Return False if there's an issue with the API request
        return False


def get_index(n):
    """
    Generate index strings for the typing test.

    Args:
        n (int): The current index.

    Returns:
        tuple: A tuple containing two strings representing the current and next index.
    """
    num_string = '1.' + str(n)
    next_num_string = '1.' + str(n + 1)
    return num_string, next_num_string


class TypingTestAttempt(t.Frame):
    """
    Represents a Typing Test Attempt.

    This class manages the UI and functionality for a typing test attempt.
    It tracks key presses, evaluates correctness, and displays results.

    Attributes:
    - root (Tk): The root Tkinter window.
    - text (str): The text for the typing test.
    - start_time (float): The timestamp when the typing test started.
    - key (str): The current key pressed during the test.
    - display (Text): The Tkinter Text widget for displaying the text.
    - progress (int): The current progress index in the text.
    - correct_key_presses (int): The count of correct key presses.
    - incorrect_key_presses (int): The count of incorrect key presses.
    - last_keypress_correct (bool): Flag indicating if the last key press was correct.
    - index (tuple): The current index range for tagging text.
    - summary (ResultsSummary): The summary widget displayed after completing the test.
    - running (bool): Flag indicating whether the test is still running.
    """
    def __init__(self, root, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize attributes
        self.start_time = time.time()
        self.root = root
        self.text = text
        self.root.bind("<Key>", self.key_pressed)
        self.key = None
        # Create and configure the Text widget for displaying the text
        self.display = t.Text(font=NORMAL_FONT, wrap=t.WORD)
        self.display.insert(t.END, self.text)
        self.display.tag_config('correct', background='lawn green', font=HIGHLIGHT_FONT)
        self.display.tag_config('incorrect', background='light coral', font=HIGHLIGHT_FONT)
        self.display.tag_config('normal', foreground=SECONDARY_COLOUR, background='white', font=NORMAL_FONT)
        self.display.tag_add('correct', '1.0', '1.1')   # Initial correct tag
        self.display.config(state='disabled')
        self.display.pack(padx=20, pady=20)
        # Initialize progress tracking variables
        self.progress = 0
        self.correct_key_presses = 0
        self.incorrect_key_presses = 0
        self.last_keypress_correct = True
        self.index = get_index(self.progress)
        self.summary = None
        self.running = True

    def apply_tags(self):
        """
        Apply text tags based on correctness and progress.

        This method applies formatting tags to the displayed text based on correctness
        of the last key press and the current progress in the typing test.
        """
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
        """
        Handle key presses during the typing test.

        This method is called when a key is pressed during the typing test.
        It checks the correctness of the key press, updates progress, and applies
        formatting tags to the displayed text.
        """
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
        """
        Compile and display the results of the typing test.

        This method is called when the typing test is completed.
        It calculates accuracy, words per minute (WPM), and displays a summary.
        """
        self.running = False
        accuracy = self.correct_key_presses / (self.correct_key_presses + self.incorrect_key_presses)
        elapsed_time = time.time() - self.start_time
        wpm = (len(self.text) / 5) / (elapsed_time / 60)
        self.display.destroy()
        self.summary = ResultsSummary(accuracy, wpm)
        self.summary.pack()
        self.root.complete_test()


class ResultsSummary(t.Frame):
    """
    Represents the Results Summary widget.

    This class displays the results summary after completing a typing test.

    Attributes:
    - accuracy (int): The accuracy of the typing test in percentage.
    - wpm (float): The words per minute (WPM) achieved in the typing test.
    - congrats (Label): The congratulatory label.
    - accuracy_title (Label): The label indicating accuracy.
    - speed_title (Label): The label indicating speed (WPM).
    - speed_label (Label): The label displaying the speed value.
    - accuracy_label (Label): The label displaying the accuracy value.
    """
    def __init__(self, accuracy, wpm):
        super().__init__()
        self.config(bg=THEME_COLOUR)
        self.accuracy = int(accuracy * 100)
        self.wpm = round(wpm, 1)
        # Create and configure UI elements
        self.congrats = t.Label(master=self, text='You have completed the typing test!\nHere are your results:',
                                font=RESULTS_FONT, background=THEME_COLOUR, foreground=SECONDARY_COLOUR,
                                padx=10, pady=10)
        frame = t.Frame(master=self, borderwidth=5, relief=t.RIDGE, padx=10, pady=10, background=THEME_COLOUR)
        self.accuracy_title = t.Label(master=frame, text=f'Accuracy: ', font=RESULTS_FONT, background=THEME_COLOUR,
                                      foreground=SECONDARY_COLOUR)
        self.speed_title = t.Label(master=frame, text='Speed: ', font=RESULTS_FONT, background=THEME_COLOUR,
                                   foreground=SECONDARY_COLOUR)
        self.speed_label = t.Label(master=frame, text=f'{self.wpm} wpm', font=RESULTS_FONT, bg=THEME_COLOUR)
        self.accuracy_label = t.Label(master=frame, text=f'{self.accuracy}%', font=RESULTS_FONT, bg=THEME_COLOUR)
        self.set_result_colours()
        self.congrats.pack(pady=5)
        frame.pack()
        self.speed_title.grid(column=0, row=0)
        self.speed_label.grid(column=1, row=0, sticky='ew')
        self.accuracy_title.grid(column=0, row=1)
        self.accuracy_label.grid(column=1, row=1, sticky='ew')

    def set_result_colours(self):
        """
        Set the color of result labels based on performance.

        This method sets the text color of result labels based on the achieved
        speed (WPM) and accuracy percentage in the typing test.
        """
        if self.wpm < WPM_THRESHOLD:
            green = int(self.wpm * (255 / 40))
            red = 255
        else:
            green = 255
            red = max(int((80 - self.wpm) * (255 / 40)), 0)
        hex_colour = "#%02x%02x%02x" % (red, green, 0)
        self.speed_label.config(fg=hex_colour)
        if self.accuracy < ACCURACY_THRESHOLD_1:
            green = 0
            red = 255
        elif self.accuracy < ACCURACY_THRESHOLD_2:
            green = int((self.accuracy - 80) * (255 / 10))
            red = 255
        else:
            green = 255
            red = int((100 - self.accuracy) * (255 / 10))
        hex_colour = "#%02x%02x%02x" % (red, green, 0)
        self.accuracy_label.config(fg=hex_colour)

    def clear_all(self):
        """
        Clear all widgets in the ResultsSummary frame.

        This method destroys all widgets within the ResultsSummary frame.
        """
        for widgets in self.winfo_children():
            widgets.destroy()
            self.destroy()


class TypingTester(t.Tk):
    """
    Represents the main application window for the Typing Speed Test.

    This class creates the main window for the typing speed test application.

    Attributes:
    - start_button (Button): The button to start or restart the typing test.
    - typing_test_attempt (TypingTestAttempt): The instance of the TypingTestAttempt class.
    """
    def __init__(self):
        super().__init__()
        self.title('Typing Speed Test')
        self.configure(bg=THEME_COLOUR)
        self.geometry('1000x700')
        self.start_button = t.Button(text='Start Test', command=self.start_test, font=RESULTS_FONT,
                                     bg=SECONDARY_COLOUR, fg=TERTIARY_COLOUR, activebackground=TERTIARY_COLOUR,
                                     activeforeground=SECONDARY_COLOUR)
        self.start_button.pack(padx=100, pady=100)
        self.typing_test_attempt = None

    def start_test(self):
        """
        Start or restart the typing test.

        This method is called when the user clicks the start button. It initiates
        the typing test by creating an instance of TypingTestAttempt and updating
        the user interface accordingly.
        """
        if self.typing_test_attempt:
            print('here')
            self.typing_test_attempt.summary.clear_all()
            self.typing_test_attempt.destroy()
        text = get_text()
        if text:
            self.typing_test_attempt = TypingTestAttempt(window, text)
            self.typing_test_attempt.pack(padx=20, pady=20)
            self.start_button.pack_forget()
        else:
            messagebox.showerror(title='Error',
                                 message='There was a problem accessing the test paragraph.\n'
                                         'Please try again.')

    def complete_test(self):
        """
        Handle completion of the typing test.

        This method is called when the typing test is completed. It updates the
        start button text to 'Restart' and makes it visible for the user to
        restart the test.
        """
        self.start_button.config(text='Restart')
        self.start_button.pack(padx=100, pady=100)


window = TypingTester()

window.mainloop()
