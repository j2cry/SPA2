import settings
import pathlib
import sounddevice as sd
import vosk
import queue
import sys
import json
from threading import Thread, Condition


class Recognizer(Thread):
    def __init__(self, callback, device=None):
        """
        :param callback: a function that processes the recognized value
        :param device: audio input device
        """
        super(Recognizer, self).__init__(daemon=True)
        device_info = sd.query_devices(device, kind='input')
        self.sample_rate = int(device_info['default_samplerate'])

        self.model = vosk.Model(pathlib.Path().joinpath(settings.use_model).as_posix())
        self.buffer = queue.Queue()
        self.callback = callback
        self.running = False
        self.suspended = True
        self.state = Condition()

    def fill_buffer(self, data, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.buffer.put(bytes(data))

    def start(self) -> None:
        super(Recognizer, self).start()
        self.running = True

    def stop(self):
        self.running = False

    def switch_pause(self):
        """ Suspend/Resume the thread loop """
        with self.state:
            if self.suspended:
                self.suspended = False
                self.state.notify()
            else:
                self.suspended = True

    def run(self) -> None:
        """ Recognizer loop """
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000, dtype='int16', channels=1,
                               callback=self.fill_buffer):
            rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
            while self.running:
                with self.state:
                    if self.suspended:
                        self.state.wait()       # suspend in required
                        self.buffer.queue.clear()
                # processing
                data = self.buffer.get()
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result())['text']       # get text from recognizer result
                    self.interpret(text)

    def interpret(self, data: str):
        """ Interpret the recognized text to float value or command and callback """
        if not data:
            return
        if data == 'утка':
            self.callback(settings.acceptable_words[data], False)
            return

        for key, value in settings.acceptable_words.items():
            data = data.replace(key, value)

        data = data.replace(' ', '.')
        # print(data)
        try:
            result = float(data)
            self.callback(str(result), False)
        except ValueError:
            if data in settings.acceptable_commands.keys():
                self.callback(settings.acceptable_commands[data], True)

