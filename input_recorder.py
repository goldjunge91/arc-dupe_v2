"""
Input Recorder - Records keyboard and mouse input with precise timing
Press ESC to stop recording and save the data
"""

import time
import json
from pynput import keyboard, mouse
from collections import defaultdict
from threading import RLock

class InputRecorder:
    def __init__(self, capture_orphan_releases=True):
        self.events = []
        self.key_press_times = {}  # Track when keys were pressed
        self.mouse_press_times = {}  # Track when mouse buttons were pressed
        self.start_time = None
        self.lock = RLock()
        self.running = True
        self.capture_orphan_releases = capture_orphan_releases  # If True, record releases even without matching press

    def get_timestamp(self):
        """Get precise timestamp in milliseconds since recording started"""
        return (time.perf_counter() - self.start_time) * 1000

    def clear_recording(self):
        """Clear all recorded events and reset timing"""
        with self.lock:
            self.events = []
            self.key_press_times = {}
            self.mouse_press_times = {}
            self.start_time = time.perf_counter()
            print("\n" + "=" * 60)
            print("RECORDING CLEARED - Starting fresh!")
            print("=" * 60 + "\n")

    def on_key_press(self, key):
        if not self.running:
            return False

        with self.lock:
            timestamp = self.get_timestamp()
            key_name = self._get_key_name(key)

            # Check for ESC to stop
            if key == keyboard.Key.esc:
                self.running = False
                print("\n[ESC pressed - Stopping recording...]")
                return False

            # Check for ] to clear recording
            if key_name == ']':
                self.clear_recording()
                return  # Don't record the ] press

            # Only record if not already pressed (avoid key repeat)
            if key_name not in self.key_press_times:
                self.key_press_times[key_name] = timestamp
                event = {
                    "type": "key_press",
                    "key": key_name,
                    "timestamp_ms": round(timestamp, 3),
                    "action": "press"
                }
                self.events.append(event)
                print(f"[{timestamp:10.3f}ms] KEY PRESS: {key_name}")

    def on_key_release(self, key):
        if not self.running:
            return False

        # Don't record control keys
        if key == keyboard.Key.esc:
            return
        try:
            if key.char == ']':
                return
        except AttributeError:
            pass

        with self.lock:
            timestamp = self.get_timestamp()
            key_name = self._get_key_name(key)

            press_time = self.key_press_times.pop(key_name, None)

            # Handle orphan releases (no matching press recorded)
            if press_time is None:
                if not self.capture_orphan_releases:
                    return
                duration = 0
                orphan = True
            else:
                duration = timestamp - press_time
                orphan = False

            event = {
                "type": "key_release",
                "key": key_name,
                "timestamp_ms": round(timestamp, 3),
                "action": "release",
                "held_duration_ms": round(duration, 3),
                "orphan": orphan
            }
            self.events.append(event)
            orphan_tag = " [ORPHAN]" if orphan else ""
            print(f"[{timestamp:10.3f}ms] KEY RELEASE: {key_name} (held {duration:.3f}ms){orphan_tag}")

    def on_mouse_click(self, x, y, button, pressed):
        if not self.running:
            return False

        with self.lock:
            timestamp = self.get_timestamp()
            button_name = button.name

            if pressed:
                self.mouse_press_times[button_name] = timestamp
                event = {
                    "type": "mouse_press",
                    "button": button_name,
                    "x": x,
                    "y": y,
                    "timestamp_ms": round(timestamp, 3),
                    "action": "press"
                }
                self.events.append(event)
                print(f"[{timestamp:10.3f}ms] MOUSE PRESS: {button_name} at ({x}, {y})")
            else:
                press_time = self.mouse_press_times.pop(button_name, None)

                # Handle orphan releases (no matching press recorded)
                if press_time is None:
                    if not self.capture_orphan_releases:
                        return
                    duration = 0
                    orphan = True
                else:
                    duration = timestamp - press_time
                    orphan = False

                event = {
                    "type": "mouse_release",
                    "button": button_name,
                    "x": x,
                    "y": y,
                    "timestamp_ms": round(timestamp, 3),
                    "action": "release",
                    "held_duration_ms": round(duration, 3),
                    "orphan": orphan
                }
                self.events.append(event)
                orphan_tag = " [ORPHAN]" if orphan else ""
                print(f"[{timestamp:10.3f}ms] MOUSE RELEASE: {button_name} at ({x}, {y}) (held {duration:.3f}ms){orphan_tag}")

    def on_mouse_scroll(self, x, y, dx, dy):
        if not self.running:
            return False

        with self.lock:
            timestamp = self.get_timestamp()
            event = {
                "type": "mouse_scroll",
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
                "timestamp_ms": round(timestamp, 3)
            }
            self.events.append(event)
            print(f"[{timestamp:10.3f}ms] MOUSE SCROLL: ({dx}, {dy}) at ({x}, {y})")

    def on_mouse_move(self, x, y):
        if not self.running:
            return False

        with self.lock:
            timestamp = self.get_timestamp()
            event = {
                "type": "mouse_move",
                "x": x,
                "y": y,
                "timestamp_ms": round(timestamp, 3)
            }
            self.events.append(event)
            # Uncomment below to see mouse moves in console (very spammy)
            # print(f"[{timestamp:10.3f}ms] MOUSE MOVE: ({x}, {y})")

    def _get_key_name(self, key):
        """Convert key to readable string"""
        try:
            return key.char
        except AttributeError:
            return key.name

    def save_recording(self, filename="macro_recording.json"):
        """Save recording to JSON file"""
        output = {
            "total_duration_ms": round(self.get_timestamp(), 3),
            "total_events": len(self.events),
            "events": self.events
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nRecording saved to: {filename}")
        print(f"Total events: {len(self.events)}")
        print(f"Total duration: {output['total_duration_ms']:.3f}ms")

        # Also save a human-readable summary
        summary_file = filename.replace('.json', '_summary.txt')
        with open(summary_file, 'w') as f:
            f.write(f"Macro Recording Summary\n")
            f.write(f"=======================\n")
            f.write(f"Total Duration: {output['total_duration_ms']:.3f}ms ({output['total_duration_ms']/1000:.2f}s)\n")
            f.write(f"Total Events: {len(self.events)}\n\n")
            f.write(f"Event Log:\n")
            f.write(f"-" * 80 + "\n")

            for event in self.events:
                if event['type'] == 'key_press':
                    f.write(f"{event['timestamp_ms']:10.3f}ms | KEY DOWN   | {event['key']}\n")
                elif event['type'] == 'key_release':
                    orphan_tag = " [ORPHAN]" if event.get('orphan') else ""
                    f.write(f"{event['timestamp_ms']:10.3f}ms | KEY UP     | {event['key']} (held {event['held_duration_ms']:.3f}ms){orphan_tag}\n")
                elif event['type'] == 'mouse_press':
                    f.write(f"{event['timestamp_ms']:10.3f}ms | MOUSE DOWN | {event['button']} at ({event['x']}, {event['y']})\n")
                elif event['type'] == 'mouse_release':
                    orphan_tag = " [ORPHAN]" if event.get('orphan') else ""
                    f.write(f"{event['timestamp_ms']:10.3f}ms | MOUSE UP   | {event['button']} at ({event['x']}, {event['y']}) (held {event['held_duration_ms']:.3f}ms){orphan_tag}\n")
                elif event['type'] == 'mouse_scroll':
                    f.write(f"{event['timestamp_ms']:10.3f}ms | SCROLL     | ({event['dx']}, {event['dy']}) at ({event['x']}, {event['y']})\n")
                elif event['type'] == 'mouse_move':
                    f.write(f"{event['timestamp_ms']:10.3f}ms | MOVE       | ({event['x']}, {event['y']})\n")

        print(f"Summary saved to: {summary_file}")

    def start(self):
        """Start recording"""
        print("=" * 60)
        print("INPUT RECORDER - Macro Timing Capture")
        print("=" * 60)
        print("Recording all keyboard and mouse input...")
        print("  ] = Clear recording & restart timer")
        print("  ESC = Stop and save")
        print("")

        self.start_time = time.perf_counter()

        # Create listeners
        keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )

        mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
            # on_move disabled - can freeze system with too many events
        )

        # Start listeners
        keyboard_listener.start()
        mouse_listener.start()

        # Wait for keyboard listener to stop (ESC pressed)
        try:
            keyboard_listener.join()
        except KeyboardInterrupt:
            print("\n[Ctrl+C pressed - Stopping recording...]")
            self.running = False
            keyboard_listener.stop()

        # Stop mouse listener
        mouse_listener.stop()

        # Save the recording
        self.save_recording()


if __name__ == "__main__":
    recorder = InputRecorder()
    recorder.start()
