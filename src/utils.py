#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys
import re

#print in stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)  

#print with hyperlink
def hprint(text,path):
        print(f"{text} (\033]8;;file://{path}\033\\{path}\033]8;;\033\\)",flush=True)

#print a msg_box
def print_msg_box(msg, indent=1, width=None, title=None):
    """Print message-box with optional title."""
    lines = msg.split('\n')
    space = " " * indent
    if not width:
        width = max(map(len, lines))
    box = f'╔{"═" * (width + indent * 2)}╗\n'  # upper_border
    if title:
        box += f'║{space}{title:<{width}}{space}║\n'  # title
        box += f'║{space}{"-" * len(title):<{width}}{space}║\n'  # underscore
    box += ''.join([f'║{space}{line:<{width}}{space}║\n' for line in lines])
    box += f'╚{"═" * (width + indent * 2)}╝'  # lower_border
    print(box, flush=True)    
    
#print a msg_box with hyperlink
def hprint_msg_box(msg, indent=1, width=None, title=None):
    """Print a message box with clickable hyperlinks for file and directory paths."""
    lines = msg.split('\n')
    space = " " * indent

    # Calculate width based on plain text (without hyperlinks)
    if not width:
        plain_lines = [re.sub(r'(/\S+)', lambda x: x.group(1), line) for line in lines]  # Preserve paths as plain text
        width = max(len(line) for line in plain_lines)
    
    # Create the box top border and title
    box = f'╔{"═" * (width + indent * 2)}╗\n'
    if title:
        box += f'║{space}{title:<{width}}{space}║\n'
        box += f'║{space}{"-" * len(title):<{width}}{space}║\n'

    # Process each line to add hyperlinks only after padding is set
    for line in lines:
        # Plain text line for padding calculation
        plain_line = line

        # Identify paths and check if they should be clickable
        paths = re.findall(r'(/\S+)', line)
        for path in paths:
            if os.path.exists(path) and (os.path.isdir(path) or path.endswith((".txt", ".log", ".out"))):
                # Add plain path text for padding and alignment calculation
                plain_line = plain_line.replace(path, path)

        # Calculate padding based on plain text
        padding_needed = width - len(plain_line)
        padded_line = f"{line}{' ' * padding_needed}"

        # Add clickable hyperlinks only after padding is applied
        for path in paths:
            if os.path.exists(path) and (os.path.isdir(path) or path.endswith((".txt", ".log", ".out"))):
                # Replace path with clickable hyperlink in padded line
                clickable_path = f"\033]8;;file://{path}\033\\{path}\033]8;;\033\\"
                padded_line = padded_line.replace(path, clickable_path)

        # Add the line with padding to the box
        box += f'║{space}{padded_line}{space}║\n'
    
    # Close the box with a bottom border
    box += f'╚{"═" * (width + indent * 2)}╝'
    print(box, flush=True)



def format_list_multiline(items, items_per_line=5):
    """Format a list into multiple lines with a comma at the end of each line except the last.
       Returns a single line if the list has fewer items than items_per_line."""  
    # If the list has fewer items than items_per_line, return as a single comma-separated line
    if len(items) <= items_per_line:
        return items
    # Otherwise, format the list into multiple lines
    formatted_output = []
    total_items = len(items)
    for i in range(0, total_items, items_per_line):
        line = ", ".join(items[i:i + items_per_line])        
        # Add a comma at the end of the line if it's not the last batch
        if i + items_per_line < total_items:
            line += ","  
        formatted_output.append(line)
    return "\n".join(formatted_output)

    
#print data with keys and values    
def print_params(data):
    formatted_output = "Configuration:\n"
    for key, value in data.items():
        formatted_line = f"{key}: {value}"
       
        # Add warning if the key is `window_level` or `window_width`
        if key in ["window_level", "window_width"]:
            formatted_line += f" \033[33mWARNING: If 'window_name' is provided, {key} will be updated when windowing is performed. Please check the windowing log file.\033[0m"
        
        # Check if the value is a path (directory or file)
        if isinstance(value, str):
            if value.endswith((".txt", ".log", ".out")):
                # Make file paths clickable
                formatted_output += f"{key}: \033]8;;file://{value}\033\\{value}\033]8;;\033\\\n"
            elif os.path.isdir(value):
                # Make directory paths clickable
                formatted_output += f"{key}: \033]8;;file://{value}\033\\{value}\033]8;;\033\\\n"
            else:
                # Regular text output for non-clickable paths or other strings
                formatted_output += f"{formatted_line}\n"
        else:
            formatted_output += f"{formatted_line}\n"
    print(formatted_output, flush=True)



    
