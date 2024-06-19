"""
LLM Functions
Abiilities for the LLM using OpenAI format
Will expand to others as needed
"""
import os
import logging
import pyautogui as pag

class LLMFunctions:
    def __init__(self, console_display):
        self.console_display = console_display
        self.logger = logging.getLogger(__name__)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # function schema
        self.functions = [
            {
                "name": "mouse_actions",
                "description": "Performs a sequence of mouse actions, including moving, clicking, and directional movements",
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
                                        "description": "The type of action to perform (move, click, move_relative)"
                                    },
                                    "x": {
                                        "type": "integer",
                                        "description": "The x coordinate for move action"
                                    },
                                    "y": {
                                        "type": "integer",
                                        "description": "The y coordinate for move action"
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
                                        "description": "The mouse button to click (left, right)"
                                    }
                                },
                                "required": ["type"]
                            }
                        }
                    },
                    "required": ["actions"]
                }
            }
        ]

        self.function_call="auto"

    def handle_call(self, name, args):
        if name == "mouse_actions":
            actions = args.get("actions")
            res = self.mouse_actions(actions)

            if self.console_display:
                self.console_display.add_text(f"AI used the 'move_actions' and did {len(res)} actions")
        else:
            self.logger.error(f"function '{name}' not found")
    
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
            else:
                results.append("Unknown action")
        return results