"""
LLM Functions
Abiilities for the LLM using OpenAI format
Will expand to others as needed
"""
import os
import logging
import pyautogui as pag
import subprocess

class LLMFunctions:
    def __init__(self, console_display):
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # function schema
        self.functions = [
            # Updated function schema in __init__ method
            {
                "name": "mouse_actions",
                "description": "Performs a sequence of mouse actions, including moving, clicking, dragging, and directional movements",
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
                                        "description": "The type of action to perform (move, click, move_relative, drag)"
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
                                        "description": "The mouse button to click or drag (left, right)"
                                    },
                                    "end_x": {
                                        "type": "integer",
                                        "description": "The ending x coordinate for drag action"
                                    },
                                    "end_y": {
                                        "type": "integer",
                                        "description": "The ending y coordinate for drag action"
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
                        "text": {
                            "type": "string",
                            "description": "The text to type"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "bash_command",
                "description": "Executes a bash command in the terminal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        }
                    },
                    "required": ["command"]
                }
            }
        ]

        self.function_call="auto"

    def handle_call(self, name, args):
        if name == "mouse_actions":
            actions = args.get("actions")
            res = self.mouse_actions(actions)

            if self.console_display:
                self.console_display.add_text(f"AI used the 'mouse_actions' and did {len(res)} actions")
        elif name == "keyboard_typing":
            text = args.get("text")
            self.keyboard_typing(text)
            if self.console_display:
                self.console_display.add_text(f"AI used the 'keyboard_typing' to type: {text}")
        else:
            self.logger.error(f"function '{name}' not found")
    
    # Updated mouse_actions method
    def mouse_actions(self, actions):
        results = []
        for action in actions:
            if action['type'] == 'move':
                x = action['x']
                y = action['y']
                pag.moveTo(x, y)
                results.append(f"Moved mouse to ({x}, {y})")
            elif action['type'] == 'click':
                button = action.get('button', 'left')
                pag.click(button=button)
                results.append(f"Clicked {button} button")
            elif action['type'] == 'move_relative':
                dx = action['dx']
                dy = action['dy']
                pag.moveRel(dx, dy)
                results.append(f"Moved mouse relative by ({dx}, {dy})")
            elif action['type'] == 'drag':
                x = action['x']
                y = action['y']
                end_x = action['end_x']
                end_y = action['end_y']
                button = action.get('button', 'left')
                pag.moveTo(x, y)
                pag.dragTo(end_x, end_y, button=button)
                results.append(f"Dragged mouse from ({x}, {y}) to ({end_x}, {end_y}) with {button} button")
            else:
                results.append("Unknown action")
        return results
    
    # keyboard typing action
    def keyboard_typing(self, text):
        pag.typewrite(text)

    def bash_command(self, command):
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return e.output

