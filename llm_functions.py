"""
LLM Functions
Abiilities for the LLM using OpenAI format
Will expand to others as needed
"""
import os
import logging
import pyautogui as pag
import subprocess
import time

from oai_ict import OpenAIImageCoordinateTranslator

import pyautogui as pag
import time
import logging
import os

class LLMFunctions:
    def __init__(self, console_display, imgw: int=1920, imgh: int=1080):
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.image_width = imgw
        self.image_height = imgh

        self.coord_trans = OpenAIImageCoordinateTranslator(
            self.image_width,
            self.image_height
        )

        pag.FAILSAFE = False
        
        # function schema
        self.functions = [
            {
                "name": "mouse_actions",
                "description": "Performs a sequence of mouse actions, including moving, clicking, dragging, scrolling, and middle mouse button clicks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "actions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "description": "The type of action to perform",
                                        "enum": ["move", "click", "move_relative", "drag", "scroll", "click_scroll"]
                                    },
                                    "x": {
                                        "type": "integer",
                                        "description": "The x coordinate for move or drag action"
                                    },
                                    "y": {
                                        "type": "integer",
                                        "description": "The y coordinate for move or drag action"
                                    },
                                    "dx": {
                                        "type": "integer",
                                        "description": "The relative x movement for move_relative action"
                                    },
                                    "dy": {
                                        "type": "integer",
                                        "description": "The relative y movement for move_relative action"
                                    },
                                    "button": {
                                        "type": "string",
                                        "description": "The mouse button to click or drag (left, right, middle)"
                                    },
                                    "end_x": {
                                        "type": "integer",
                                        "description": "The ending x coordinate for drag action"
                                    },
                                    "end_y": {
                                        "type": "integer",
                                        "description": "The ending y coordinate for drag action"
                                    },
                                    "clicks": {
                                        "type": "integer",
                                        "description": "The number of scroll clicks for scroll action"
                                    }
                                },
                                "required": ["type"]
                            }
                        }
                    },
                    "required": ["actions"]
                }
            },
            {
                "name": "keyboard_typing",
                "description": "Types a given string using the keyboard",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text to type"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "keyboard_press",
                "description": "Presses a key or combination of keys",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keys": {"type": "array", "items": {"type": "string"}, "description": "The keys to press"}
                    },
                    "required": ["keys"]
                }
            },
            {
                "name": "bash_command",
                "description": "Executes a bash command in the terminal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The bash command to execute"}
                    },
                    "required": ["command"]
                }
            }
        ]

        self.function_call = "auto"

    def handle_call(self, name, args):
        self.logger.info(f"handle_call name: {name} args: {args}")

        if name == "mouse_actions":
            self.mouse_actions(args["actions"])
        elif name == "keyboard_typing":
            self.keyboard_typing(args["text"])
        elif name == "keyboard_press":
            self.keyboard_press(args["keys"])
        elif name == "bash_command":
            self.bash_command(args["command"])
        else:
            self.logger.error(f"Function '{name}' not found")

    def mouse_actions(self, actions):
        for action in actions:
            if action['type'] == 'move':
                # x, y = self.coord_trans.translate_coordinates(
                #     action['x'], action['y'])
                x, y = (action['x'], action['y'])
                pag.moveTo(x, y)
                self.logger.info(f"Moved mouse to ({x}, {y})")
                time.sleep(1)
            elif action['type'] == 'click':
                button = action.get('button', 'left')
                pag.click(button=button)
                self.logger.info(f"Clicked {button} button")
                time.sleep(1)
            elif action['type'] == 'move_relative':
                # dx, dy = self.coord_trans.translate_coordinates(
                #     action['dx'], action['dy'])
                dx, dy = action['dx'], action['dy']
                pag.moveRel(dx, dy)
                self.logger.info(f"Moved mouse relative by ({dx}, {dy})")
                time.sleep(1)
            elif action['type'] == 'drag':
                # x, y = self.coord_trans.translate_coordinates(
                #     action['x'], action['y'])
                x, y = (action['x'], action['y'])
                # end_x, end_y = self.coord_trans.translate_coordinates(
                #     action['end_x'], action['end_y'])
                end_x, end_y = (action['end_x'], action['end_y'])
                button = action.get('button', 'left')
                pag.mouseDown(x, y, button=button)
                pag.moveTo(end_x, end_y)
                pag.mouseUp(end_x, end_y, button=button)
                self.logger.info(f"Dragged mouse from ({x}, {y}) to ({end_x}, {end_y}) with {button} button")
                time.sleep(1)
            elif action['type'] == 'scroll':
                clicks = action.get('clicks', 1)
                pag.scroll(clicks)
                self.logger.info(f"Scrolled {clicks} clicks")
                time.sleep(1)
            elif action['type'] == 'click_scroll':
                pag.middleClick()
                self.logger.info("Clicked middle button (scroll wheel click)")
                time.sleep(1)

    def keyboard_typing(self, text):
        pag.typewrite(text)
        self.logger.info(f"Typed text: {text}")

    def keyboard_press(self, keys):
        for key in keys:
            pag.press(key)
        self.logger.info(f"Pressed keys: {keys}")

    def bash_command(self, command):
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return e.output
